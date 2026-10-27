#!/usr/bin/env python
"""
repair_cjk.py — fix Chinese text mangled by PDF font subsetting.

The problem
-----------
Some PDFs embed a subset font whose "to-Unicode" map resolves many
characters to *radical* code points instead of the real ideograph:

    门 -> U+2ED4 ⻔     车 -> U+2ECB ⻋     风 -> U+2EDB ⻛
    一 -> U+2F00 ⼀     八 -> U+2F00-range

These look nearly identical on screen but are wrong: search engines,
screen readers and copy-paste all treat them as different characters.

Two classes occur here:

1. Kangxi Radicals (U+2F00–U+2FDF) — `unicodedata.normalize("NFKC", …)`
   fixes these correctly, because Unicode defines a compatibility mapping.

2. CJK Radicals Supplement (U+2E80–U+2EFF) — NFKC does NOT fix these
   (they are considered distinct characters). Each one is actually the
   simplified form of a whole character, so it must be mapped by hand.

This script applies both passes, then reports anything left over so a
silent corruption never reaches the site.

Usage
-----
    python scripts/repair_cjk.py INPUT.txt OUTPUT.txt
    python scripts/repair_cjk.py INPUT.txt --report      # inspect only
"""

from __future__ import annotations

import sys
import unicodedata
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------- mapping
# CJK Radicals Supplement -> the character it actually stands in for.
# Every entry below was verified against the surrounding sentences in the
# source text (see the counts in the report), not guessed from the name.
RADICAL_FIXES: dict[str, str] = {
    "\u2E9F": "母",  # ⺟  U+2E9F  "一个字⺟"      -> 字母
    "\u2EA0": "民",  # ⺠  U+2EA0  "德意志⺠主共和国" -> 民主
    "\u2EC5": "见",  # ⻅  U+2EC5  "看⻅"            -> 看见
    "\u2EC6": "角",  # ⻆  U+2EC6  "嘴⻆"            -> 嘴角
    "\u2EC9": "贝",  # ⻉  U+2EC9  "普伦茨劳⻉格"     -> 普伦茨劳贝格
    "\u2ECB": "车",  # ⻋  U+2ECB  "轿⻋"            -> 轿车
    "\u2ED3": "长",  # ⻓  U+2ED3  "⻓官"            -> 长官
    "\u2ED4": "门",  # ⻔  U+2ED4  "⻔锁"            -> 门锁
    "\u2ED8": "青",  # ⻘  U+2ED8  "淤⻘⾊"          -> 淤青色
    "\u2EDB": "风",  # ⻛  U+2EDB  "寒⻛"            -> 寒风
    "\u2EDC": "飞",  # ⻜  U+2EDC  "⻜机"            -> 飞机
    "\u2EDD": "食",  # ⻝  U+2EDD  "⻝道"            -> 食道
    "\u2EE2": "马",  # ⻢  U+2EE2  "⻢克思"          -> 马克思
    "\u2EE3": "骨",  # ⻣  U+2EE3  "肋⻣"            -> 肋骨
    "\u2EE4": "鬼",  # ⻤  U+2EE4  "魔⻤"            -> 魔鬼
    "\u2EE5": "鱼",  # ⻥  U+2EE5  "鲨⻥"            -> 鲨鱼
    "\u2EE6": "鸟",  # ⻦  U+2EE6  "⻦笼"            -> 鸟笼
    "\u2EE8": "麦",  # ⻨  U+2EE8  "喊⻨"            -> 喊麦
    "\u2EE9": "黄",  # ⻩  U+2EE9  "⻩⿊相间"         -> 黄黑相间
    "\u2EEC": "齐",  # ⻬  U+2EEC  "整⻬"            -> 整齐
    "\u2EEE": "齿",  # ⻮  U+2EEE  "⻮痕"            -> 齿痕
    "\u2EF0": "龙",  # ⻰  U+2EF0  "尼⻰绳"          -> 尼龙绳
}

# Characters that indicate extraction is still broken (hard failure).
BAD_RANGES = [(0x2E80, 0x2EFF), (0x2F00, 0x2FDF), (0xF900, 0xFAFF)]


def repair(text: str) -> str:
    """
    Repair radical substitution WITHOUT touching the rest of the text.

    Important: we must not run NFKC over the whole document. NFKC also
    rewrites legitimately full-width punctuation used throughout Chinese
    prose — '，' -> ',', '！' -> '!', '（' -> '(', '…' -> '...' — which
    silently degrades the typography of the entire article.

    So NFKC is applied *per character*, and only to characters that are
    actually radical forms; everything else is copied verbatim.
    """
    # 1) Supplement radicals: NFKC does not map these, so do it by hand.
    out = []
    for ch in text:
        mapped = RADICAL_FIXES.get(ch)
        if mapped is not None:
            out.append(mapped)
            continue
        code = ord(ch)
        if 0x2F00 <= code <= 0x2FDF or 0xF900 <= code <= 0xFAFF:
            # Kangxi radicals / CJK compatibility ideographs: NFKC is safe
            # and correct for these specific characters.
            out.append(unicodedata.normalize("NFKC", ch))
            continue
        out.append(ch)
    return "".join(out)


def find_bad(text: str) -> Counter:
    out: Counter = Counter()
    for ch in text:
        code = ord(ch)
        for lo, hi in BAD_RANGES:
            if lo <= code <= hi:
                out[ch] += 1
                break
    return out


def check_replacement_chars(text: str) -> int:
    """U+FFFD and '?' runs suggest encoding loss upstream."""
    return text.count("\uFFFD")


# Full-width punctuation that must survive a repair untouched.
PROTECTED_PUNCT = "，。！？：；（）《》〈〉「」『』【】…—、·"


def check_punctuation(before: str, after: str) -> list[str]:
    """
    Guard against the classic repair bug: NFKC silently converting full-width
    punctuation to ASCII. Report any protected mark whose count dropped.
    """
    problems = []
    for ch in PROTECTED_PUNCT:
        b, a = before.count(ch), after.count(ch)
        if a < b:
            problems.append(f"{ch!r} (U+{ord(ch):04X}): {b} -> {a}")
    return problems


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)

    src = Path(sys.argv[1])
    text = src.read_text(encoding="utf-8")

    before = find_bad(text)
    print(f"input: {src}  ({len(text)} chars)")
    print(f"radical-form chars before: {sum(before.values())} ({len(before)} distinct)")

    fixed = repair(text)

    after = find_bad(fixed)
    print(f"radical-form chars after:  {sum(after.values())} ({len(after)} distinct)")

    replacement = check_replacement_chars(fixed)
    if replacement:
        print(f"WARNING: {replacement} U+FFFD replacement characters present")

    punct_loss = check_punctuation(text, fixed)
    if punct_loss:
        print("ERROR: full-width punctuation was altered (NFKC leak):")
        for line in punct_loss:
            print(f"  {line}")
        sys.exit("Aborting: punctuation must not change during repair.")

    if after:
        print("STILL BROKEN (add these to RADICAL_FIXES):")
        for ch, n in after.most_common():
            print(f"  U+{ord(ch):04X} {ch} x{n}")
        if "--force" not in sys.argv:
            sys.exit("Refusing to write output with unresolved bad characters.")

    report_only = "--report" in sys.argv
    if report_only:
        print("(report only, nothing written)")
        return

    dst = Path(sys.argv[2])
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(fixed, encoding="utf-8")
    print(f"wrote {dst}")


if __name__ == "__main__":
    main()
