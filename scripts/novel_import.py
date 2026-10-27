#!/usr/bin/env python
"""
novel_import.py — import a chaptered novel PDF into FLOWSTATE.

Extraction strategy (learned the hard way on a real file)
---------------------------------------------------------
* pypdf's default `extract_text()` returns lines in correct reading order
  for this document. Re-sorting by y-coordinate (the "obvious" thing to do)
  *breaks* it, because this PDF positions text with a matrix where larger y
  means earlier in the page.
* That same extraction drops blank lines, so paragraph breaks must be
  inferred from punctuation: a wrapped line never ends a paragraph, while the
  last line of a paragraph ends with terminal punctuation.

Scene stamps (地点/时间/环境数据…) are handled explicitly: each label line is
kept as its own block, which is where the naive approach glues them onto the
opening sentence.

Usage
-----
    python scripts/novel_import.py 利维坦.pdf --series leviathan \
        --title 利维坦 --lang zh --dry-run
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONTENT_ROOT = PROJECT_ROOT / "src" / "content"
sys.path.insert(0, str(Path(__file__).resolve().parent))

from repair_cjk import repair as repair_radicals  # noqa: E402
from split_novel import (  # noqa: E402
    RE_CHAPTER,
    RE_EN_TITLE,
    RE_PART,
    chapter_number,
    cn_to_int,
    make_slug,
)

# Lines that open a chapter: timestamp, or a labelled field.
RE_SCENE_LABEL = re.compile(
    r"^(地点|时间|载具|目标|死因|凶器推测|现场特征|环境数据|BGM|音效|身份|状态|天气)[：:]"
)
RE_TIMESTAMP = re.compile(r"^\d{4}\s*年.{0,20}\d{1,2}\s*[:：]\s*\d{2}")

# A paragraph ends when a line ends with terminal punctuation (ignoring a
# closing quote/bracket). A wrapped line never does.
RE_TERMINAL = re.compile(r"[。！？…”」』】）)]\s*$")


# ------------------------------------------------------------------ extract
def extract_lines(pdf_path: Path) -> list[str]:
    """Visual lines in reading order (blank lines are dropped by pypdf)."""
    try:
        from pypdf import PdfReader
    except ImportError:
        sys.exit("Missing dependency. Run: python -m pip install pypdf")

    reader = PdfReader(str(pdf_path))
    out: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        for line in text.split("\n"):
            if line.strip():
                out.append(line.strip())

    if not out:
        sys.exit(
            "No text extracted — this is almost certainly a scanned PDF.\n"
            "Run OCR first (OCRmyPDF / Adobe), or paste the text."
        )
    return out


# -------------------------------------------------------------------- tidy
PUNCT_BEFORE = "，。！？：；、》」』】）"
PUNCT_AFTER = "（《「『【("


def tidy(text: str) -> str:
    """Remove the spaces PDF extraction injects around CJK glyphs."""
    text = re.sub(r"“\s+", "“", text)
    text = re.sub(r"\s+”", "”", text)
    text = re.sub(r"‘\s+", "‘", text)
    text = re.sub(r"\s+’", "’", text)
    # Brackets: no padding inside, either full- or half-width.
    text = re.sub(r"([（(《【「『])\s+", r"\1", text)
    text = re.sub(r"\s+([）)》】」』])", r"\1", text)
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r"\s+\)", ")", text)
    # No space before CJK punctuation.
    text = re.sub(rf"\s+([{PUNCT_BEFORE}])", r"\1", text)
    # No space after CJK punctuation when a CJK character follows.
    text = re.sub(rf"([{PUNCT_BEFORE}])\s+(?=[{PUNCT_BEFORE}\u4e00-\u9fff])", r"\1", text)
    # Em dash: normalise spacing to the Chinese style.
    text = re.sub(r"\s*—{2}\s*", "——", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def render_body(lines: list[str]) -> str:
    """
    Rebuild paragraphs from wrapped lines.

    Rules:
      * `地点：…` / `时间：…` / timestamp lines open their own block,
      * a later label on the same logical stamp continues that block,
      * a line that reads like narration starts the prose, ending the stamp,
      * otherwise a line ends a paragraph when it ends with terminal
        punctuation; a wrapped line joins the previous one.
    """
    blocks: list[str] = []
    buf = ""
    in_stamp = False

    def flush():
        nonlocal buf
        if buf:
            blocks.append(tidy(buf))
            buf = ""

    for line in lines:
        is_label = bool(RE_SCENE_LABEL.match(line) or RE_TIMESTAMP.match(line))

        if is_label:
            # A new label while already in a stamp continues the same stamp.
            if not in_stamp:
                flush()
            buf = f"{buf}{line}" if in_stamp and buf else line
            in_stamp = True
            continue

        if in_stamp:
            # Short continuation = still the stamp (street name, date tail).
            if len(line) <= 40 and not RE_TERMINAL.search(line) and not looks_like_prose(line):
                buf = buf + line if not (buf[-1].isascii() and line[0].isascii()) else f"{buf} {line}"
                continue
            # Long or sentence-like: the stamp ends here and prose begins.
            flush()
            in_stamp = False

        if not buf:
            buf = line
        elif buf[-1].isascii() and line[0].isascii():
            buf += " " + line
        else:
            buf += line

        if RE_TERMINAL.search(line):
            flush()

    flush()
    return "\n\n".join(format_stamp(b) for b in blocks)


# Opening words that mark the start of narration rather than a place name.
PROSE_OPENERS = re.compile(
    r"^(空气|空气中|这|那|他|她|它|风|雨|夜|这里|街上|窗外|远处|一切|时间|光线|声音|"
    r"多少|没人|没有|一切|夜色|城市|门|墙)"
)


def looks_like_prose(line: str) -> bool:
    """Heuristic: does this line read as narration rather than a stamp field?"""
    if RE_TERMINAL.search(line):
        return True
    if PROSE_OPENERS.match(line):
        return True
    # A clause this long is almost certainly prose, not an address fragment.
    return len(line) > 30


def format_stamp(block: str) -> str:
    """
    Render a scene stamp as an italic block, one field per line.

    The extractor concatenates `地点：…时间：…载具：…` into a single string
    because the source has no blank lines between them. Re-inserting line
    breaks makes the opening of a chapter readable as a slug block rather
    than a run-on sentence.
    """
    if not (RE_SCENE_LABEL.match(block) or RE_TIMESTAMP.match(block)):
        return block

    # Split before any label that follows another character (not at pos 0).
    spaced = re.sub(
        r"(?<=.)(?=(地点|时间|载具|环境数据|目标|死因|现场特征|BGM|音效|身份|状态|天气|凶器推测)[：:])",
        "\n",
        block,
    )
    lines = [ln.strip() for ln in spaced.split("\n") if ln.strip()]
    # Markdown needs a trailing double space or a blank line to keep hard
    # breaks inside one italic block; use "  \n" (two trailing spaces).
    return f"*{'  \n'.join(lines)}*"


# ------------------------------------------------------------------- split
def parse_chapters(lines: list[str]) -> list[dict]:
    chapters: list[dict] = []
    part: tuple[str, str, str] | None = None
    cur: dict | None = None

    def close():
        nonlocal cur
        if cur is not None:
            chapters.append(cur)
            cur = None

    for line in lines:
        m_part = RE_PART.match(line)
        if m_part:
            part = (m_part.group(1), m_part.group(2), m_part.group(3))
            continue

        m_ch = RE_CHAPTER.match(line)
        if m_ch:
            close()
            cur = {"num": m_ch.group(1), "title": m_ch.group(2),
                   "title_en": "", "part": part, "lines": []}
            continue

        m_en = RE_EN_TITLE.match(line)
        if m_en:
            # Subtitle of the Chinese heading immediately above it.
            if cur is not None and not cur["title_en"] and not cur["lines"]:
                cur["title_en"] = m_en.group(2)
                continue
            close()
            if cur is None:
                cur = {"num": m_en.group(1), "title": m_en.group(2),
                       "title_en": "", "part": part, "lines": []}
                continue

        if cur is not None:
            cur["lines"].append(line)

    close()
    return chapters


def part_number(part_s: str | None) -> int:
    if not part_s:
        return 1
    try:
        return int(part_s)
    except ValueError:
        return cn_to_int(part_s) or 1


def frontmatter(ch: dict, series_title: str, part_no: int,
                part_title: str, part_year: str, rating: str) -> str:
    title = ch["title"].replace('"', '\\"')
    series = f"{series_title} · 第{part_no}部 {part_title}（{part_year}）".replace('"', '\\"')
    num = chapter_number(ch["num"])
    part_value = int(num) if num == int(num) else num
    return (
        "---\n"
        f'title: "{title}"\n'
        'dek: ""\n'
        f"published: {dt.date.today().isoformat()}\n"
        "genre: serial\n"
        "nature: original\n"
        f"rating: {rating}\n"
        "status: complete\n"
        f'series: "{series}"\n'
        f"part: {part_value}\n"
        "tags: [小说, 谍战, 冷战]\n"
        "featured: false\n"
        "draft: true              # 确认正文无误后改为 false\n"
        "---\n\n"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--series", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--lang", default="zh")
    ap.add_argument("--rating", default="M", choices=["G", "T", "M", "E"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    if not (args.dry_run or args.write):
        sys.exit("Pass --dry-run or --write.")

    lines = [repair_radicals(l) for l in extract_lines(args.pdf)]
    chapters = parse_chapters(lines)

    print(f"chapters found: {len(chapters)}")
    out_dir = CONTENT_ROOT / "fiction" / args.lang

    for ch in chapters:
        body = render_body(ch["lines"])
        part_no, part_title, part_year = ch["part"] or ("1", "", "")
        fm = frontmatter(ch, args.title, part_number(part_no),
                         part_title, part_year, args.rating)
        slug = make_slug(args.series, ch["num"])
        path = out_dir / f"{slug}.md"
        label = ch["title"] or ch["title_en"]
        print(f"  ch{ch['num']:>6}  {label[:20]:<22} {len(body):>6} chars  -> {path.name}")

        if len(body) < 200:
            print(f"    WARNING: very short chapter ({len(body)} chars)")

        if args.write:
            out_dir.mkdir(parents=True, exist_ok=True)
            if path.exists():
                sys.exit(f"Refusing to overwrite {path}")
            path.write_text(fm + body + "\n", encoding="utf-8")

    if args.dry_run:
        print("\n(dry run, nothing written)")


if __name__ == "__main__":
    main()
