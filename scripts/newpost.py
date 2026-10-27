#!/usr/bin/env python
"""
newpost.py 鈥?scaffold a new post for FLOWSTATE and check it before publishing.

Two jobs, one command:

  1. `new`   creates a .md with valid frontmatter and a short reminder of the
             fields, so you never have to copy a template by hand.
  2. `lint`  validates every post before you build: catches the mistakes that
             otherwise fail the build with a cryptic zod error, or worse,
             silently publish as broken YAML.

Usage
-----
    # Create an empty short story (Chinese)
    python scripts/newpost.py new --track fiction --type shortstory --lang zh --title "闆ㄧ殑閲嶉噺"

    # Create the next chapter of an existing serial
    python scripts/newpost.py new --track fiction --type serial --series leviathan --part 14 --lang zh --title "..."

    # Create an automotive article
    python scripts/newpost.py new --track automotive --type review --lang zh --title "..."

    # Validate everything
    python scripts/newpost.py lint
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
import unicodedata
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONTENT = PROJECT_ROOT / "src" / "content"

FICTION_GENRES = {"fanfiction", "shortstory", "flash", "serial"}
AUTO_CATEGORIES = {"culture", "modification", "driving", "review", "essay"}

# Frontmatter keys each track requires. Fields with a schema default
# (draft, tags, featured, ...) are intentionally absent from this list.
REQUIRED = {
    "fiction": ["title", "dek", "published", "genre", "nature", "rating", "status"],
    "automotive": ["title", "dek", "published", "category", "translationKey"],
}

# Fields that are valid YAML flow sequences/mappings rather than scalars,
# so the "must be quoted" check does not apply to them.
FLOW_FIELDS = {"tags"}


def slugify(title: str) -> str:
    """
    ASCII slug. Chinese titles produce nothing under NFKD, so fall back to a
    date stamp 鈥?an empty slug would create a file called `.md`.
    """
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_title).strip("-").lower()
    return slug[:60] or f"post-{dt.date.today().isoformat()}"


def q(value: str) -> str:
    """Always quote: titles regularly contain : # [ ] which break YAML."""
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def cmd_new(args) -> None:
    out_dir = CONTENT / args.track / args.lang
    slug = args.slug or (
        f"{args.series}-ch{args.part}" if args.series and args.part else slugify(args.title)
    )
    path = out_dir / f"{slug}.md"

    if path.exists():
        sys.exit(f"File already exists, refusing to overwrite: {path}")

    today = dt.date.today().isoformat()

    if args.track == "fiction":
        if args.type not in FICTION_GENRES:
            sys.exit(f"--type must be one of {sorted(FICTION_GENRES)}")
        lines = [
            "---",
            f"title: {q(args.title)}",
            'dek: ""                 # one-line summary shown on the card',
            f"published: {today}",
            f"genre: {args.type}",
            f"nature: {args.nature}   # fanwork shows the non-commercial notice",
        ]
        if args.nature == "fanwork":
            lines.append('fandom: ""          # source work, required for fanwork')
        lines += [
            f"rating: {args.rating}",
            f"status: {args.status}",
        ]
        if args.series:
            lines.append(f"series: {q(args.series)}")
        if args.part is not None:
            lines.append(f"part: {args.part:g}")
        lines += [
            "tags: []",
            "featured: false",
            "draft: true             # set to false to publish",
            "---",
            "",
            "Body text starts here.",
            "",
        ]
    else:
        if args.type not in AUTO_CATEGORIES:
            sys.exit(f"--type must be one of {sorted(AUTO_CATEGORIES)}")
        lines = [
            "---",
            f"title: {q(args.title)}",
            'dek: ""',
            f"published: {today}",
            f"category: {args.type}",
            "tags: []",
            'image: ""              # optional; put files in public/images/',
            'imageAlt: ""',
            "featured: false",
            f"translationKey: {q(slug)}",
            "draft: true",
            "---",
            "",
            "Body text starts here.",
            "",
        ]

    out_dir.mkdir(parents=True, exist_ok=True)
    write_md(path, "\n".join(lines))

    rel = path.relative_to(PROJECT_ROOT)
    print(f"Created {rel}")
    print(f"  title : {args.title}")
    if args.series:
        print(f"  series: {args.series} / part {args.part}")
    print("\nNext:")
    print(f"  1. write the body in {rel}")
    print("  2. set the dek (and tags)")
    print("  3. change `draft: true` to `draft: false` when ready")
    print("  4. run: python scripts/newpost.py lint")
    print("  5. run: .\\dev.ps1 dev")


# --------------------------------------------------------------------- lint
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def read_frontmatter(path: Path) -> dict[str, str] | None:
    text = path.read_text(encoding="utf-8")
    # Strip a UTF-8 BOM: Windows editors add it silently and it makes the
    # file start with '\ufeff---', which YAML frontmatter parsing rejects.
    text = text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    block = text[3:end]
    data: dict[str, str] = {}
    for line in block.split("\n"):
        line = line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        value = value.strip()
        if value and not value.startswith('"'):
            value = re.sub(r"\s+#.*$", "", value)
        data[key.strip()] = value
    return data


def has_bom(path: Path) -> bool:
    return path.read_bytes()[:3] == b"\xef\xbb\xbf"


def unquote(v: str) -> str:
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] == '"':
        return v[1:-1]
    if len(v) >= 2 and v[0] == v[-1] == "'":
        return v[1:-1]
    return v


def cmd_lint(args) -> int:
    problems: list[str] = []
    warnings: list[str] = []
    checked = 0
    series_seen: dict[str, list[float]] = {}

    for track in ("automotive", "fiction"):
        for lang_dir in sorted((CONTENT / track).glob("*")):
            if not lang_dir.is_dir():
                continue
            for path in sorted(lang_dir.glob("*.md")):
                checked += 1
                rel = path.relative_to(PROJECT_ROOT)

                if has_bom(path):
                    problems.append(
                        f"{rel}: starts with a UTF-8 BOM 鈥?save as UTF-8 (no BOM) or the "
                        "frontmatter will not parse"
                    )

                fm = read_frontmatter(path)
                if fm is None:
                    problems.append(f"{rel}: missing or unclosed frontmatter (---)")
                    continue

                for key in REQUIRED[track]:
                    if key not in fm:
                        problems.append(f"{rel}: missing required field `{key}`")

                # YAML safety: unquoted scalar values must not contain
                # characters that change meaning (": ", " #", leading markers).
                for key, raw in fm.items():
                    if key in FLOW_FIELDS:
                        continue
                    val = raw.strip()
                    if not val or val.startswith('"') or val.startswith("'"):
                        continue
                    if val.startswith("[") or val.startswith("{"):
                        continue
                    if re.search(r":\s|\s#|^[-?*&!|>@`]", val):
                        problems.append(
                            f"{rel}: `{key}` contains YAML special chars but is not quoted"
                        )

                pub = unquote(fm.get("published", ""))
                if pub and not DATE_RE.match(pub):
                    problems.append(f"{rel}: published `{pub}` is not YYYY-MM-DD")

                # `draft` may be omitted (schema default is false).
                draft = unquote(fm.get("draft", "false")).lower()
                if draft not in {"true", "false"}:
                    problems.append(f"{rel}: `draft` must be true or false")

                title = unquote(fm.get("title", ""))
                if not title.strip():
                    problems.append(f"{rel}: empty title")

                dek = unquote(fm.get("dek", ""))
                if draft == "false" and not dek.strip():
                    warnings.append(f"{rel}: published but `dek` is empty (card looks bare)")

                if track == "fiction":
                    genre = unquote(fm.get("genre", ""))
                    if genre and genre not in FICTION_GENRES:
                        problems.append(f"{rel}: genre `{genre}` invalid")
                    nature = unquote(fm.get("nature", ""))
                    if nature == "fanwork" and not unquote(fm.get("fandom", "")).strip():
                        problems.append(f"{rel}: nature is fanwork but `fandom` is empty")
                    rating = unquote(fm.get("rating", ""))
                    if rating and rating not in {"G", "T", "M", "E"}:
                        problems.append(f"{rel}: rating `{rating}` must be G/T/M/E")

                    series = unquote(fm.get("series", ""))
                    part_raw = unquote(fm.get("part", ""))
                    if series and not part_raw:
                        problems.append(f"{rel}: in a series but `part` is missing")
                    if part_raw and not series:
                        warnings.append(f"{rel}: has `part` but no `series`")
                    if series and part_raw:
                        try:
                            part = float(part_raw)
                        except ValueError:
                            problems.append(f"{rel}: part `{part_raw}` is not a number")
                        else:
                            bucket = series_seen.setdefault(f"{track}/{lang_dir.name}/{series}", [])
                            if part in bucket:
                                problems.append(f"{rel}: duplicate part {part:g} in series `{series}`")
                            bucket.append(part)

                    if "/" in title or "/" in genre:
                        pass  # filenames are independent of the title

                body = path.read_text(encoding="utf-8")
                if "\ufffd" in body:
                    problems.append(f"{rel}: contains U+FFFD replacement characters")
                if re.search(r"[\u2e80-\u2eff\u2f00-\u2fdf]", body):
                    bad = set(re.findall(r"[\u2e80-\u2eff\u2f00-\u2fdf]", body))
                    problems.append(
                        f"{rel}: contains radical-form characters {''.join(sorted(bad))[:12]} "
                        "鈥?run scripts/repair_cjk.py"
                    )

    print(f"checked {checked} files")
    for p in problems:
        print(f"  ERROR   {p}")
    if not args.quiet:
        for w in warnings:
            print(f"  warning {w}")

    if problems:
        print(f"\n{len(problems)} problem(s). Fix these before building.")
        return 1
    print("OK 鈥?no problems found.")
    return 0


def write_md(path: Path, content: str) -> None:
    """
    Write Markdown as UTF-8 *without* a BOM.

    Python's plain `write_text(encoding="utf-8")` does no BOM, but editors on
    Windows often add one when you edit the file later. Centralising the write
    means anything the tool touches stays BOM-free.
    """
    path.write_text(content.replace("\r\n", "\n"), encoding="utf-8", newline="\n")


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    n = sub.add_parser("new", help="scaffold a new post")
    n.add_argument("--track", required=True, choices=["fiction", "automotive"])
    n.add_argument("--type", required=True, help="fiction: shortstory|flash|fanfiction|serial ; automotive: review|culture|modification|driving|essay")
    n.add_argument("--lang", default="zh", choices=["zh", "en"])
    n.add_argument("--title", required=True)
    n.add_argument("--slug", help="filename override")
    n.add_argument("--nature", default="original", choices=["original", "fanwork"])
    n.add_argument("--rating", default="G", choices=["G", "T", "M", "E"])
    n.add_argument("--status", default="complete", choices=["complete", "ongoing"])
    n.add_argument("--series", help="series name for serials")
    n.add_argument("--part", type=float, help="chapter number within the series")

    l = sub.add_parser("lint", help="validate all posts")
    l.add_argument("--quiet", action="store_true", help="hide warnings")

    # ---- editing an existing post -------------------------------------
    ls = sub.add_parser("list", help="list every post with its status")
    ls.add_argument("--track", choices=["fiction", "automotive"], help="filter by track")
    ls.add_argument("--lang", choices=["zh", "en"], help="filter by language")

    sh = sub.add_parser("show", help="print one post's metadata and body")
    sh.add_argument("slug", help="filename without .md, or a unique fragment")

    ed = sub.add_parser("edit", help="change frontmatter fields of a post")
    ed.add_argument("slug")
    ed.add_argument("--title")
    ed.add_argument("--dek")
    ed.add_argument("--rating", choices=["G", "T", "M", "E"])
    ed.add_argument("--status", choices=["complete", "ongoing"])
    ed.add_argument("--genre", choices=sorted(FICTION_GENRES))
    ed.add_argument("--category", choices=sorted(AUTO_CATEGORIES))
    ed.add_argument("--tags", help="comma separated, e.g. 灏忚,璋嶆垬")
    ed.add_argument("--series")
    ed.add_argument("--part", type=float)
    ed.add_argument("--fandom")
    ed.add_argument("--nature", choices=["original", "fanwork"])
    ed.add_argument("--published", help="YYYY-MM-DD")
    ed.add_argument("--image")
    ed.add_argument("--body", help="replace the body from a text/markdown file")
    ed.add_argument("--yes", action="store_true", help="skip the confirmation prompt")

    pub = sub.add_parser("publish", help="flip draft: false")
    pub.add_argument("slug")

    unp = sub.add_parser("unpublish", help="flip draft: true (hide from the site)")
    unp.add_argument("slug")

    args = ap.parse_args()
    if args.cmd == "new":
        cmd_new(args)
    elif args.cmd == "lint":
        sys.exit(cmd_lint(args))
    elif args.cmd == "list":
        cmd_list(args)
    elif args.cmd == "show":
        cmd_show(args)
    elif args.cmd == "edit":
        cmd_edit(args)
    elif args.cmd == "publish":
        cmd_set_draft(args, False)
    elif args.cmd == "unpublish":
        cmd_set_draft(args, True)


# ------------------------------------------------------------ find posts
def all_posts() -> list[Path]:
    out: list[Path] = []
    for track in ("automotive", "fiction"):
        for lang_dir in sorted((CONTENT / track).glob("*")):
            if lang_dir.is_dir():
                out.extend(sorted(lang_dir.glob("*.md")))
    return out


def resolve(slug: str) -> Path:
    """
    Accept an exact filename or any unique fragment of it, so `ch12` or
    `leviathan-ch12` both find `leviathan-ch12.md` without ambiguity.
    """
    exact = [p for p in all_posts() if p.stem == slug]
    if len(exact) == 1:
        return exact[0]
    matches = [p for p in all_posts() if slug in p.stem]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        sys.exit(f"No post matching '{slug}'. Run: python scripts/newpost.py list")
    listing = "\n".join(f"  {p.relative_to(PROJECT_ROOT)}" for p in matches)
    sys.exit(f"'{slug}' is ambiguous, matches {len(matches)} posts:\n{listing}")


def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT))


# ---------------------------------------------------------------- list
def cmd_list(args) -> None:
    rows = []
    for path in all_posts():
        parts = path.relative_to(CONTENT).parts
        track, lang = parts[0], parts[1]
        if args.track and track != args.track:
            continue
        if args.lang and lang != args.lang:
            continue
        fm = read_frontmatter(path) or {}
        title = unquote(fm.get("title", ""))
        draft = unquote(fm.get("draft", "")).lower() == "true"
        kind = unquote(fm.get("genre", "") or fm.get("category", ""))
        series = unquote(fm.get("series", ""))
        part = unquote(fm.get("part", ""))
        label = f"{series} #{part}" if series and part else series
        rows.append((track, lang, "draft" if draft else "LIVE", kind, label, path.stem, title))

    if not rows:
        print("No posts found.")
        return

    w = [len("track"), len("lang"), len("status"), len("kind"), len("series")]
    for r in rows:
        for i in range(5):
            w[i] = max(w[i], len(str(r[i])))

    print(f"{'track':<{w[0]}}  {'lang':<{w[1]}}  {'status':<{w[2]}}  {'kind':<{w[3]}}  "
          f"{'series':<{w[4]}}  slug / title")
    print("-" * (sum(w) + 20 + 40))
    for r in rows:
        print(f"{r[0]:<{w[0]}}  {r[1]:<{w[1]}}  {r[2]:<{w[2]}}  {r[3]:<{w[3]}}  "
              f"{r[4]:<{w[4]}}  {r[5]}  {r[6][:34]}")

    live = sum(1 for r in rows if r[2] == "LIVE")
    print(f"\n{len(rows)} posts, {live} live, {len(rows) - live} draft")


# ---------------------------------------------------------------- show
def cmd_show(args) -> None:
    path = resolve(args.slug)
    text = path.read_text(encoding="utf-8").lstrip("\ufeff")
    print(f"# {rel(path)}\n")
    print(text)


# ---------------------------------------------------------------- edit
def set_field(block: str, key: str, raw_value: str) -> str:
    """Replace (or append) one frontmatter key, preserving every other line."""
    pattern = re.compile(rf"^{re.escape(key)}:.*$", re.M)
    new_line = f"{key}: {raw_value}"
    if pattern.search(block):
        return pattern.sub(new_line, block, count=1)
    return block.rstrip("\n") + "\n" + new_line + "\n"


def cmd_edit(args) -> None:
    path = resolve(args.slug)
    text = path.read_text(encoding="utf-8").lstrip("\ufeff").replace("\r\n", "\n")
    if not text.startswith("---"):
        sys.exit(f"{rel(path)} has no frontmatter block.")

    end = text.find("\n---", 3)
    if end == -1:
        sys.exit(f"{rel(path)} has an unclosed frontmatter block.")
    block = text[3:end]
    body = text[end + 4 :]

    changes: list[str] = []

    # Plain string fields, always quoted.
    for key in ("title", "dek", "series", "fandom", "image", "published"):
        value = getattr(args, key, None)
        if value is not None:
            block = set_field(block, key, q(value))
            changes.append(f"{key} = {value}")

    # Unquoted enum/number fields.
    for key in ("rating", "status", "genre", "category", "nature"):
        value = getattr(args, key, None)
        if value is not None:
            block = set_field(block, key, value)
            changes.append(f"{key} = {value}")

    if args.part is not None:
        block = set_field(block, "part", f"{args.part:g}")
        changes.append(f"part = {args.part:g}")

    if args.tags is not None:
        items = [t.strip() for t in args.tags.split(",") if t.strip()]
        block = set_field(block, "tags", "[" + ", ".join(items) + "]")
        changes.append(f"tags = {items}")

    if args.body:
        body_path = Path(args.body)
        if not body_path.is_absolute():
            body_path = PROJECT_ROOT / body_path
        if not body_path.exists():
            sys.exit(f"Body file not found: {body_path}")
        # Strip BOM and normalise newlines: a BOM pasted into the body would
        # render as a stray invisible character at the start of the article.
        incoming = body_path.read_text(encoding="utf-8-sig")
        incoming = incoming.replace("\r\n", "\n").replace("\r", "\n").strip()
        body = "\n\n" + incoming + "\n"
        changes.append(f"body replaced from {body_path.name} ({len(incoming)} chars)")

    if not changes:
        sys.exit("Nothing to change. Pass at least one option, e.g. --dek \"...\"")

    print(f"Editing {rel(path)}")
    for c in changes:
        print(f"  {c}")

    if not args.yes:
        answer = input("\nApply these changes? [y/N] ").strip().lower()
        if answer not in {"y", "yes"}:
            print("Cancelled. Nothing was written.")
            return

    write_md(path, "---" + block.rstrip("\n") + "\n---" + body)
    print(f"\nSaved. Run: python scripts/newpost.py show {path.stem}")


# ------------------------------------------------------------- publish
def cmd_set_draft(args, draft: bool) -> None:
    path = resolve(args.slug)
    text = path.read_text(encoding="utf-8").lstrip("\ufeff").replace("\r\n", "\n")
    end = text.find("\n---", 3)
    if not text.startswith("---") or end == -1:
        sys.exit(f"{rel(path)} has no valid frontmatter.")

    block, body = text[3:end], text[end + 4 :]
    block = set_field(block, "draft", "true" if draft else "false")
    write_md(path, "---" + block.rstrip("\n") + "\n---" + body)

    state = "draft (hidden)" if draft else "published"
    print(f"{path.stem}: {state}")
    if not draft:
        fm = read_frontmatter(path) or {}
        if not unquote(fm.get("dek", "")).strip():
            print("  note: `dek` is still empty 鈥?the card will look bare.")
        print("  run: python scripts/newpost.py lint   then   .\\publish.ps1 -Push")


if __name__ == "__main__":
    main()
