#!/usr/bin/env python
"""
pdf2md.py — turn a PDF (or .docx) draft into a frontmatter-ready Markdown file
for FLOWSTATE.

Why this exists
---------------
Moving finished writing into the site should not mean re-typing. This script
extracts the text, cleans up PDF line breaks, and writes a .md with the
frontmatter fields pre-filled so you only edit the metadata block.

Usage
-----
    python scripts/pdf2md.py input.pdf --track fiction --lang zh --slug my-story
    python scripts/pdf2md.py draft.docx --track automotive --lang en --slug foo
    python scripts/pdf2md.py input.pdf --track fiction --lang zh --slug s --dry-run

Options
-------
    --track   fiction | automotive   (which content folder to write into)
    --lang    zh | en
    --slug    output filename (no extension); defaults to a slugified title
    --title   override the detected title
    --dry-run print the Markdown instead of writing it

Notes
-----
* Text PDFs only. A scanned PDF (images of pages) yields no text — this script
  will say so explicitly rather than produce an empty article.
* Paragraph reconstruction is heuristic: PDFs break lines at the margin, so
  the script re-joins lines that clearly continue a sentence. Review the
  output — especially around lists, poetry and dialogue.
* Frontmatter values are always quoted, because titles often contain
  characters (:, #, [, ]) that break YAML.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
import unicodedata
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONTENT_ROOT = PROJECT_ROOT / "src" / "content"

CJK = r"\u4e00-\u9fff\u3040-\u30ff"


# --------------------------------------------------------------------- text in
def read_pdf(path: Path) -> list[tuple[str, float]]:
    """
    Extract (text, y-position) pairs.

    Plain text extraction flattens paragraphs: the extractor emits \\n for
    every visual line, so an intentional paragraph gap is indistinguishable
    from a normal line wrap. Keeping the y coordinate lets us measure the
    gap — a larger step down the page means a new paragraph.
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        sys.exit("Missing dependency. Run: python -m pip install pypdf")

    reader = PdfReader(str(path))
    rows: list[tuple[str, float]] = []

    for page in reader.pages:
        chunks: list[tuple[float, float, str]] = []

        def visit(text, cm, tm, font_dict=None, font_size=None, _c=chunks):
            if text and text.strip():
                # tm is the text matrix; tm[5] is the baseline y.
                y = tm[5] if tm and len(tm) > 5 else 0.0
                x = tm[4] if tm and len(tm) > 4 else 0.0
                _c.append((y, x, text))

        try:
            page.extract_text(visitor_text=visit)
        except Exception:
            # Fall back to plain extraction if the visitor path fails.
            plain = page.extract_text() or ""
            rows.extend((ln, 0.0) for ln in plain.split("\n"))
            continue

        # Group fragments that share a baseline into one visual line.
        chunks.sort(key=lambda c: (-c[0], c[1]))
        current_y = None
        buf: list[str] = []
        for y, _x, text in chunks:
            if current_y is None:
                current_y = y
            if abs(y - current_y) > 2.0:
                rows.append(("".join(buf), current_y))
                buf, current_y = [], y
            buf.append(text)
        if buf:
            rows.append(("".join(buf), current_y or 0.0))

    if not any(t.strip() for t, _ in rows):
        sys.exit(
            "No text found in this PDF.\n"
            "It is almost certainly a scanned document (images of pages).\n"
            "Options: run OCR first (e.g. OCRmyPDF / Adobe), or paste the text."
        )
    return rows


def rebuild_from_rows(rows: list[tuple[str, float]]) -> str:
    """
    Rebuild paragraphs using vertical gaps.

    A step of more than ~1.55x the typical line spacing means a paragraph
    break; anything smaller is a wrap.
    """
    clean = [(t.rstrip(), y) for t, y in rows if t.strip()]
    if not clean:
        return ""

    gaps = [
        clean[i - 1][1] - clean[i][1]
        for i in range(1, len(clean))
        if clean[i - 1][1] - clean[i][1] > 0
    ]
    typical = sorted(gaps)[len(gaps) // 2] if gaps else 12.0
    threshold = typical * 1.55

    blocks: list[list[str]] = [[clean[0][0].strip()]]
    for i in range(1, len(clean)):
        text, y = clean[i]
        gap = clean[i - 1][1] - y
        if gap > threshold:
            blocks.append([text.strip()])
        else:
            blocks[-1].append(text.strip())

    out = []
    for block in blocks:
        joined = block[0]
        for nxt in block[1:]:
            # CJK lines butt together; latin lines need a space.
            sep = "" if (is_cjk(joined[-1:]) or is_cjk(nxt[:1])) else " "
            joined = f"{joined}{sep}{nxt}".replace("  ", " ")
        out.append(joined)
    return "\n\n".join(out)


def read_docx(path: Path) -> str:
    try:
        import docx
    except ImportError:
        sys.exit("Missing dependency. Run: python -m pip install python-docx")

    document = docx.Document(str(path))
    return "\n\n".join(p.text for p in document.paragraphs)


def read_any(path: Path) -> tuple[str, str]:
    """
    Return (cleaned_text, source_kind).

    PDFs go through position-aware extraction so paragraph gaps survive;
    other formats already carry their own line structure.
    """
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        rows = read_pdf(path)
        return rebuild_from_rows(rows), "pdf-layout"
    if suffix in {".docx", ".doc"}:
        return rebuild_paragraphs(normalise(read_docx(path))), "docx"
    if suffix in {".md", ".txt"}:
        return rebuild_paragraphs(normalise(path.read_text(encoding="utf-8", errors="replace"))), "text"
    sys.exit(f"Unsupported file type: {suffix}")


# --------------------------------------------------------------------- cleanup
def normalise(text: str) -> str:
    """Undo PDF extraction artefacts without touching the words."""
    text = unicodedata.normalize("NFC", text)
    # Windows/PDF line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Ligatures and typographic quotes are fine to keep; strip control chars.
    text = "".join(ch for ch in text if ch == "\n" or ch == "\t" or ord(ch) >= 32)
    # Hyphenated line breaks: "inter-\nesting" -> "interesting"
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    # Collapse runs of spaces (but not indentation of blank lines)
    text = re.sub(r"[ \t]{2,}", " ", text)
    # Three or more blank lines -> two
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def is_cjk(text: str) -> bool:
    sample = re.sub(r"\s", "", text)[:400]
    if not sample:
        return False
    cjk_chars = len(re.findall(f"[{CJK}]", sample))
    return cjk_chars / len(sample) > 0.3


def rebuild_paragraphs(text: str) -> str:
    """
    Re-join lines broken by the PDF's page width.

    A PDF gives us lines, not paragraphs — every paragraph break looks like
    any other newline. We only treat a line as a paragraph break when it is
    *obviously* a heading or already-structured Markdown; everything else is
    joined into flowing paragraphs.

    Latin text: join with a space. CJK text: join with nothing, since the
    line break was purely visual.
    """
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    out = []

    for block in blocks:
        lines = [ln.rstrip() for ln in block.split("\n") if ln.strip()]
        if not lines:
            continue

        # Keep things that were already structured.
        if re.match(r"^(#{1,6}\s|[-*+]\s|>\s|\||```|\d+[.)]\s)", lines[0]):
            out.append("\n".join(lines))
            continue

        if is_cjk(block):
            out.append("".join(ln.strip() for ln in lines))
            continue

        out.append(" ".join(ln.strip() for ln in lines))

    return "\n\n".join(out)


def split_title(text: str) -> tuple[str, str]:
    """
    Separate a leading title line from the body.

    Heuristics, in order:
      1. The first block is short (<= 80 chars) and has no sentence-ending
         punctuation -> treat it as the title.
      2. Otherwise there is no title; use the first sentence and keep the
         whole text as body.
    This is deliberately conservative: a wrong title is easy to fix by hand,
    silently eating the opening paragraph is not.
    """
    blocks = text.split("\n\n")
    if not blocks:
        return "Untitled", ""

    first = blocks[0].strip()
    rest = "\n\n".join(blocks[1:]).strip()

    looks_like_title = (
        len(first) <= 80
        and "\n" not in first
        and not re.search(r"[.!?。！？,，;；:：]$", first)
    )

    if looks_like_title and rest:
        return first, rest

    # No reliable title: derive one from the first sentence.
    sentence = re.split(r"(?<=[.!?。！？])\s*", first, maxsplit=1)[0]
    return sentence[:80].strip() or "Untitled", text


def slugify(title: str) -> str:
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_title).strip("-").lower()
    return slug[:60] or "untitled"


# ------------------------------------------------------------------ frontmatter
FICTION_TEMPLATE = """---
title: "{title}"
dek: ""
published: {date}
genre: shortstory        # fanfiction | shortstory | flash | serial
nature: original         # fanwork triggers the non-commercial notice
fandom: ""               # only for nature: fanwork
rating: G                # G | T | M | E
status: complete         # complete | ongoing
tags: []
featured: false
draft: true              # flip to false when you are ready to publish
---

"""

AUTOMOTIVE_TEMPLATE = """---
title: "{title}"
dek: ""
published: {date}
category: essay          # culture | modification | driving | review | essay
tags: []
featured: false
draft: true
translationKey: "{slug}"
---

"""


def build(title: str, body: str, track: str, slug: str) -> str:
    today = dt.date.today().isoformat()
    safe_title = title.replace('"', '\\"')
    template = FICTION_TEMPLATE if track == "fiction" else AUTOMOTIVE_TEMPLATE
    front = template.format(title=safe_title, date=today, slug=slug)
    return front + body + "\n"


# ----------------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser(description="Import a PDF/DOCX draft as Markdown.")
    ap.add_argument("source", type=Path, help="input .pdf / .docx / .txt / .md")
    ap.add_argument("--track", choices=["fiction", "automotive"], required=True)
    ap.add_argument("--lang", choices=["zh", "en"], required=True)
    ap.add_argument("--slug", help="output filename without extension")
    ap.add_argument("--title", help="override the auto-detected title")
    ap.add_argument("--keep-title-line", action="store_true",
                    help="keep the first line in the body (it is stripped by default)")
    ap.add_argument("--dry-run", action="store_true", help="print, do not write")
    args = ap.parse_args()

    if not args.source.exists():
        sys.exit(f"File not found: {args.source}")

    raw, source_kind = read_any(args.source)
    cleaned = raw

    detected_title, body = split_title(cleaned)
    title = args.title or detected_title
    slug = args.slug or slugify(title)

    if args.keep_title_line and args.title:
        # Caller supplied a title but wants the original heading kept in the body.
        body = cleaned

    markdown = build(title, body, args.track, slug)
    out_dir = CONTENT_ROOT / args.track / args.lang
    out_path = out_dir / f"{slug}.md"

    if args.dry_run:
        print(f"--- would write to {out_path} ---\n")
        print(markdown)
        return

    if out_path.exists():
        sys.exit(f"Refusing to overwrite existing file: {out_path}")

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown, encoding="utf-8")
    print(f"Wrote {out_path}")
    print(f"Title: {title}")
    print(f"Chars: {len(body)}  Paragraphs: {body.count(chr(10) + chr(10)) + 1}")
    print("\nNext: fill in dek/genre/tags, review the body, then set draft: false.")


if __name__ == "__main__":
    main()
