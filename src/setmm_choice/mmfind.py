#!/usr/bin/env python3
"""Pull a theorem's statement and proof out of set.mm.

    python tools/mmfind.py difelsiga unelsiga

Metamath statements look like

    label $p |- <assertion> $= <proof> $.

with optional $d/$e hypotheses in an enclosing ${ ... $} block. This finds the
block, so the hypotheses come with the statement rather than being lost.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SETMM = Path(__file__).resolve().parent.parent / "vendor" / "set.mm"


def find(text: str, label: str):
    m = re.search(r"(?m)^\s*" + re.escape(label) + r"\s+\$[pa]\s", text)
    if not m:
        return None
    # walk back to the opening ${ of the enclosing block, if there is one
    start = text.rfind("${", 0, m.start())
    prev_close = text.rfind("$}", 0, m.start())
    if start == -1 or start < prev_close:
        start = m.start()
    end = text.find("$.", m.start())
    end = text.find("$}", end)
    if end == -1:
        end = text.find("$.", m.start()) + 2
    else:
        end += 2
    return text[start:end]


def main() -> None:
    if not SETMM.exists():
        sys.exit(f"missing {SETMM}")
    text = SETMM.read_text(encoding="utf-8", errors="replace")
    print(f"set.mm: {len(text):,} chars, "
          f"{len(re.findall(r'(?m)^\\s*\\S+\\s+\\$p\\s', text)):,} proved statements")
    for label in sys.argv[1:]:
        block = find(text, label)
        print()
        print("=" * 74)
        print(label)
        print("=" * 74)
        if not block:
            print("  NOT FOUND")
            continue
        # strip the comment blocks $( ... $) for readability
        clean = re.sub(r"\$\([^$]*(?:\$(?!\))[^$]*)*\$\)", "", block)
        print("\n".join(l.rstrip() for l in clean.splitlines() if l.strip()))


if __name__ == "__main__":
    main()
