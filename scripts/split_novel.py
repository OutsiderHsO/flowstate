#!/usr/bin/env python
"""
split_novel.py — turn a chaptered Chinese novel text into one content file
per chapter, ready for FLOWSTATE's fiction track.

This is the step after `pdf2md.py` for multi-chapter works: instead of one
giant article, it detects chapter headings, splits on them, tidies the
typography, and writes `src/content/fiction/<lang>/<slug>.md` per chapter
with shared series metadata.

Assumes the text has already been through `repair_cjk.py`.

Usage
-----
    python scripts/split_novel.py fixed.txt --lang zh --series leviathan \
        --title "利维坦" --dry-run
    python scripts/split_novel.py fixed.txt --lang zh --series leviathan \
        --title "利维坦" --write
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONTENT_ROOT = PROJECT_ROOT / "src" / "content"

CN_NUM = "一二三四五六七八九十百零〇一二三四五六七八九"

# 第一部：铁幕下的困兽  (1981)
RE_PART = re.compile(r"^第([%s\d]+)部[：:]\s*(.+?)\s*[(（](\d{4})[)）]\s*$" % CN_NUM)
# 第一章：利维坦的齿痕   /  第 12.5 章：衔尾蛇
RE_CHAPTER = re.compile(r"^第\s*([\d.]+|[%s]+)\s*章[：:]\s*(.+?)\s*$" % CN_NUM)
# Chapter 1: The Teeth Marks of Leviathan
RE_EN_TITLE = re.compile(r"^Chapter\s+([\d.]+)\s*[:：]\s*(.+?)\s*$")
# 地点：… / 时间：… / 载具：…
RE_META = re.compile(r"^(地点|时间|载具)[：:]")

CN_DIGITS = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
             "六": 6, "七": 7, "八": 8, "九": 9}


def cn_to_int(s: str) -> int | None:
    """Parse 一..二十 (enough for chapter numbers here)."""
    if s.isdigit():
        return int(s)
    if s == "十":
        return 10
    if "十" in s:
        head, _, tail = s.partition("十")
        tens = CN_DIGITS.get(head, 1) if head else 1
        ones = CN_DIGITS.get(tail, 0) if tail else 0
        return tens * 10 + ones
    if len(s) == 1:
        return CN_DIGITS.get(s)
    return None


def tidy(text: str) -> str:
    """
    Fix the spacing artefacts PDF extraction leaves in Chinese text.

    The extractor pads characters when a font subset changes, producing
    things like `目标：  维克多` and `“ 站住 ”`. We remove spaces that sit
    next to CJK characters or CJK punctuation, but keep the ones inside
    Latin words and between CJK and Latin where they aid reading.
    """
    # Quotes: no space just inside either half of a quote pair.
    text = re.sub(r"“\s+", "“", text)
    text = re.sub(r"\s+”", "”", text)
    text = re.sub(r"‘\s+", "‘", text)
    text = re.sub(r"\s+’", "’", text)

    # Brackets: no padding inside.
    text = re.sub(r"([（(《【「『])\s+", r"\1", text)
    text = re.sub(r"\s+([）)》】」』])", r"\1", text)

    # No space around CJK punctuation.
    text = re.sub(r"\s*([，。！？：；、])\s*", r"\1", text)

    # Em dash should hug the preceding character: "味道 ——那是" -> "味道——那是"
    text = re.sub(r"\s*(—+)\s*", r" \1 ", text)
    text = re.sub(r"\s+([，。！？：；、])", r"\1", text)

    # Ellipsis: keep it tight to quotes/punctuation.
    text = re.sub(r"\s*(…+)\s*", r"\1", text)

    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


# Timestamp / location / vehicle lines that open a chapter ("1981 年 11 月…")
RE_SCENE = re.compile(
    r"^(\d{4}\s*年.*\d{1,2}:\d{2}"
    r"|(地点|时间|载具|目标|死因|凶器推测|现场特征|环境数据|天气|音效|备注)[：:])"
)


def split_inline_stamp(para: str) -> list[str]:
    """
    Break a stamp+prose paragraph at a scene keyword glued mid-sentence.

    Example: `时间：1981 年 10 月 15 日，01：15环境数据：相对湿度…空气中
    悬浮着…` — the last stamp label is followed directly by prose. We find
    the *second* occurrence of a label and split before the prose it runs into.
    """
    if not RE_SCENE.match(para):
        return [para]

    # Position of the next label after the first one.
    labels = list(re.finditer(r"(地点|时间|载具|环境数据)[：:]", para))
    if len(labels) < 2:
        return [para]

    inner = labels[-1].start()
    first_stop = para.find("。")
    if first_stop != -1 and first_stop < inner:
        return [para]

    # Walk back from the first 。 to the nearest comma — that is where prose starts.
    head = para[: first_stop if first_stop != -1 else len(para)]
    cut = max(head.rfind("，"), head.rfind("。"), head.rfind("、"))
    if cut <= inner:
        return [para]
    return [para[: cut + 1].rstrip("，、"), para[cut + 1 :]]


def render_body(lines: list[str]) -> str:
    """
    Join wrapped lines into paragraphs and tidy each one.

    Two things stop a line from continuing the previous paragraph:
      * the previous paragraph already ended with closing punctuation, or
      * the line is a scene header (timestamp / 地点 / 时间 / 载具), which in
        the source always sits on its own line and would otherwise be glued
        onto the opening sentence.
    """
    paras: list[str] = []
    for raw in lines:
        line = raw.strip()
        if not line:
            continue

        starts_new = bool(RE_SCENE.match(line))
        prev_closed = bool(paras) and bool(re.search(r"[。！？…”』」]$", paras[-1]))

        if paras and not prev_closed and not starts_new:
            paras[-1] = f"{paras[-1]}{line}"
        else:
            paras.append(line)

    return "\n\n".join(tidy(p) for p in paras if p.strip())


def split_leading_scene(paras: list[str]) -> list[str]:
    """
    Separate a scene stamp that got glued to the opening prose.

    In the source the stamp occupies its own lines but with no blank line
    before the first sentence, so line-joining merges them:

        1981 年 11 月 14 日，23:42
        德意志民主共和国（DDR），东柏林
        普伦茨劳贝格区 (Prenzlauer Berg)，但泽大街
        十一月的柏林，寒风像尸检时的冰冷手指…

    A stamp is a list of noun phrases; the prose begins with narrative —
    either a month/time phrase ("2026 年 6 月的柏林，寒风…") or a proper
    name followed by an action. We therefore look for the comma that is
    followed by a *sentence*, not another fragment.
    """
    if not paras:
        return paras

    first = paras[0]
    if not RE_SCENE.match(first) or "。" not in first:
        return paras

    sentence = first[: first.find("。")]
    cuts = [i for i, ch in enumerate(sentence) if ch in "，,"]

    # A clause is prose if it is long enough AND does not look like an
    # address fragment (no time word, has a verb-ish structure).
    NARRATIVE = re.compile(
        r"(的[^，]{2,}，|^[^\s，]{2,6}(站|走|坐|抬|推|拉|看|说|低|转|握|靠|穿|开|跑|望|听|等|听)"
        r"|^(夜空|空气|这里|那|这|他|她|它|风|雨|雪|光|声音|街上|窗外|远处|一切))"
    )

    for cut in cuts:
        prose = sentence[cut + 1 :]
        if len(prose) >= 30 and NARRATIVE.search(prose):
            stamp = first[: cut + 1].rstrip("，,")
            return [stamp, first[cut + 1 :]] + paras[1:]

    return paras


def format_scene_blocks(body: str) -> str:
    """
    Render leading scene headers as a compact block.

    The source opens most chapters with a place/time stamp. Showing them as
    bold lines reads like a screenplay slug and keeps them out of the prose.
    """
    paras = split_leading_scene(body.split("\n\n"))
    out = []
    for p in paras:
        if RE_SCENE.match(p) and "。" not in p:
            out.append(f"**{p}**")
        else:
            out.append(p)
    return "\n\n".join(out)


def parse(lines: list[str]) -> list[dict]:
    chapters: list[dict] = []
    part: tuple[str, str, str] | None = None
    cur: dict | None = None

    for raw in lines:
        line = raw.strip()
        if not line:
            if cur is not None:
                cur["lines"].append("")
            continue

        m_part = RE_PART.match(line)
        if m_part:
            part = (m_part.group(1), m_part.group(2), m_part.group(3))
            continue

        m_ch = RE_CHAPTER.match(line)
        m_en = RE_EN_TITLE.match(line)

        # A chapter heading is either `第N章：标题` or a bare `Chapter N: Title`.
        # But in bilingual documents the English line is the *subtitle* of the
        # Chinese heading just above it — treating it as a new chapter would
        # double every chapter and leave half of them empty.
        if m_ch:
            if cur is not None:
                chapters.append(cur)
            cur = {
                "num": m_ch.group(1),
                "title": m_ch.group(2),
                "title_en": "",
                "part": part,
                "lines": [],
            }
            continue

        if m_en:
            if cur is not None and not cur["title_en"]:
                cur["title_en"] = m_en.group(2)
                cur["num"] = cur["num"] or m_en.group(1)
                continue
            # Standalone English heading with no Chinese counterpart.
            if cur is not None:
                chapters.append(cur)
            cur = {
                "num": m_en.group(1),
                "title": m_en.group(2),
                "title_en": "",
                "part": part,
                "lines": [],
            }
            continue

        if cur is not None:
            cur["lines"].append(line)

    if cur is not None:
        chapters.append(cur)
    return chapters


def make_slug(series: str, num: str) -> str:
    """leviathan + '十二' -> leviathan-ch12 ; '12.5' -> leviathan-ch12-5.

    Slugs must be ASCII: Chinese numerals in a URL are percent-encoded into
    an unreadable string, and some hosts treat them inconsistently.
    """
    n = chapter_number(num)
    label = f"{n:g}".replace(".", "-")
    if not label or label == "0":
        label = re.sub(r"[^a-z0-9]+", "-", num.lower()).strip("-") or "unknown"
    return f"{series}-ch{label}"


def build_frontmatter(ch: dict, lang: str, series_title: str,
                      part_no: int, part_title: str, part_year: str) -> str:
    # Headings may contain colons; always quote.
    title = ch["title"].replace('"', '\\"')
    series = f"{series_title} · 第{part_no}部 {part_title}（{part_year}）".replace('"', '\\"')
    num = chapter_number(ch["num"])
    # `part` is our ordering key inside the series, so keep decimals: 12.5
    # must sort between 12 and 13.
    part_value = int(num) if num == int(num) else num
    return (
        "---\n"
        f'title: "{title}"\n'
        "dek: \"\"\n"
        f"published: {dt.date.today().isoformat()}\n"
        "genre: serial\n"
        "nature: original\n"
        "rating: M                # 含暴力与成人主题，阅读页会显示分级提示\n"
        "status: complete\n"
        f'series: "{series}"\n'
        f"part: {part_value}\n"
        "tags: [小说, 谍战, 冷战]\n"
        "featured: false\n"
        "draft: true              # 确认正文无误后改为 false\n"
        "---\n\n"
    )


def chapter_number(num_s: str) -> float:
    """'一' -> 1.0, '十二' -> 12.0, '12.5' -> 12.5."""
    try:
        return float(num_s)
    except ValueError:
        pass
    n = cn_to_int(num_s)
    return float(n) if n else 0.0


def part_number(part_s: str | None) -> int:
    """'一' -> 1, '2' -> 2."""
    if not part_s:
        return 1
    n = cn_to_int(part_s)
    return n if n else 1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("--lang", default="zh")
    ap.add_argument("--series", required=True, help="slug prefix, e.g. leviathan")
    ap.add_argument("--title", required=True, help="work title, e.g. 利维坦")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--debug-chapters", action="store_true",
                    help="print every detected chapter heading with its line number")
    args = ap.parse_args()

    if not (args.dry_run or args.write or args.debug_chapters):
        sys.exit("Pass --dry-run, --write or --debug-chapters.")

    lines = args.source.read_text(encoding="utf-8").split("\n")

    if args.debug_chapters:
        for i, raw in enumerate(lines):
            s = raw.strip()
            if RE_CHAPTER.match(s) or RE_PART.match(s):
                print(f"L{i:>5}  {s[:80]!r}")
        return

    chapters = parse(lines)

    print(f"chapters found: {len(chapters)}")
    out_dir = CONTENT_ROOT / "fiction" / args.lang

    for ch in chapters:
        body = format_scene_blocks(render_body(ch["lines"]))
        part_no, part_title, part_year = ch["part"] or ("1", "", "")
        fm = build_frontmatter(ch, args.lang, args.title,
                               part_number(part_no), part_title, part_year)
        slug = make_slug(args.series, ch["num"])
        path = out_dir / f"{slug}.md"

        print(f"  ch{ch['num']:>6}  {ch['title'][:24]:<26} "
              f"{len(body):>6} chars  -> {path.name}")

        if args.write:
            out_dir.mkdir(parents=True, exist_ok=True)
            if path.exists():
                sys.exit(f"Refusing to overwrite {path}")
            path.write_text(fm + body + "\n", encoding="utf-8")

    if args.dry_run:
        print("\n(dry run, nothing written)")


if __name__ == "__main__":
    main()
