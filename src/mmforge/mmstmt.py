#!/usr/bin/env python3
"""Print just the assertion (and any $e hypotheses) of labels in set.mm.

    python tools/mmstmt.py isrnsigau unelsiga dfss4 difun1

mmfind.py prints whole blocks including the proof, which is unreadable for a
dozen lemmas at once. This prints what a proof author needs: the hypotheses in
order, and the conclusion.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SETMM = Path(__file__).resolve().parent.parent / "vendor" / "set.mm"
text = SETMM.read_text(encoding="utf-8", errors="replace")


def block_of(label: str):
    m = re.search(r"(?m)^\s*" + re.escape(label) + r"\s+\$[pa]\s", text)
    if not m:
        return None
    start = text.rfind("${", 0, m.start())
    if start == -1 or start < text.rfind("$}", 0, m.start()):
        start = m.start()
    end = text.find("$.", m.start())
    return text[start:end + 2]


def show(label: str) -> None:
    b = block_of(label)
    print(f"--- {label}")
    if not b:
        print("    NOT FOUND")
        return
    b = re.sub(r"\$\([^$]*(?:\$(?!\))[^$]*)*\$\)", "", b)      # drop comments
    b = re.sub(r"\$=.*", "", b, flags=re.S)                    # drop the proof
    for m in re.finditer(r"(?m)^\s*(\S+)\s+\$e\s+(.*?)\$\.", b, re.S):
        print(f"    hyp {m.group(1):<12} {' '.join(m.group(2).split())}")
    for m in re.finditer(r"(?m)^\s*(\S+)\s+\$d\s+(.*?)\$\.", b):
        print(f"    $d  {' '.join(m.group(2).split())}")
    m = re.search(r"(?m)^\s*" + re.escape(label) + r"\s+\$[pa]\s+(.*)", b, re.S)
    if m:
        print(f"    ==> {' '.join(m.group(1).split())}")


for lab in sys.argv[1:]:
    show(lab)
