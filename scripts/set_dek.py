"""
set_dek.py — write one shared blurb onto every chapter of a series.

Why a separate script: a serial's chapters mostly share one premise, and
repeating it by hand in 14 files invites typos and inconsistencies. Passing
no --dek sets the same text on all of them in one pass.

Usage
-----
    python scripts/set_dek.py --series 利维坦 --lang zh --dek "一句话简介"
    python scripts/set_dek.py --series 利维坦 --lang zh --show
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "src" / "content"


def quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--series", required=True, help="exact series name, e.g. 利维坦")
    ap.add_argument("--lang", default="zh", choices=["zh", "en"])
    ap.add_argument("--track", default="fiction", choices=["fiction", "automotive"])
    ap.add_argument("--dek", help="text to set on every chapter")
    ap.add_argument("--show", action="store_true", help="print current deks and exit")
    args = ap.parse_args()

    target = quote(args.series)
    folder = CONTENT / args.track / args.lang
    files = sorted(folder.glob("*.md"))

    hits: list[Path] = []
    for path in files:
        text = path.read_text(encoding="utf-8").lstrip("\ufeff")
        m = re.search(r"^series:\s*(.+)$", text, re.M)
        if m and m.group(1).strip() == target:
            hits.append(path)

    if not hits:
        sys.exit(f"No posts found with series {target} in {folder}")

    if args.show or not args.dek:
        for path in hits:
            text = path.read_text(encoding="utf-8").lstrip("\ufeff")
            m = re.search(r"^dek:\s*(.*)$", text, re.M)
            current = m.group(1).strip() if m else "(none)"
            print(f"{path.stem}: {current}")
        if not args.dek:
            print("\nPass --dek \"...\" to set a shared blurb on all of them.")
        return

    new_value = f"dek: {quote(args.dek)}"
    changed = 0
    for path in hits:
        text = path.read_text(encoding="utf-8").lstrip("\ufeff")
        if re.search(r"^dek:.*$", text, re.M):
            updated = re.sub(r"^dek:.*$", new_value, text, count=1, flags=re.M)
        else:
            updated = text.replace("---", new_value, 1)
        if updated != text:
            path.write_text(updated, encoding="utf-8", newline="\n")
            changed += 1

    print(f"series: {args.series}")
    print(f"dek   : {args.dek}")
    print(f"updated {changed} of {len(hits)} files")


if __name__ == "__main__":
    main()
