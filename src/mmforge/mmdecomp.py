#!/usr/bin/env python3
"""Decompress a Metamath compressed proof into its step sequence.

    python tools/mmdecomp.py difelsiga

Compressed proofs are unreadable by design: a label list in parentheses
followed by letters encoding indices into it. To write a new proof by hand it
helps enormously to read an existing one that already does most of the same
work, step by step.

The encoding: A-T are the low digit (1..20), U-Y are high digits base 5, and Z
marks "save this step for later reference". An index points into
[mandatory hypotheses] + [the label list] + [saved steps], in that order.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from ._vendor import mmverify
from . import default_database

mmverify.verbosity = 0
mmverify.logfile = sys.stderr
SETMM = default_database()


def decode(letters: str):
    """Yield ('step', n) and ('save',) events."""
    n = 0
    for c in letters:
        if "U" <= c <= "Y":
            n = n * 5 + (ord(c) - ord("U") + 1)
        elif "A" <= c <= "T":
            n = n * 20 + (ord(c) - ord("A") + 1)
            yield ("step", n)
            n = 0
        elif c == "Z":
            yield ("save",)


def main() -> None:
    label = sys.argv[1]
    text = SETMM.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"(?m)^\s*" + re.escape(label) + r"\s+\$p\s+(.*?)\$=(.*?)\$\.",
                  text, re.S)
    if not m:
        sys.exit(f"{label} not found")
    proof = m.group(2)
    lm = re.match(r"\s*\((.*?)\)(.*)", proof, re.S)
    if not lm:
        sys.exit("not a compressed proof")
    labels = lm.group(1).split()
    letters = "".join(lm.group(2).split())

    mm = mmverify.MM(None, None)
    with open(SETMM, "r", encoding="utf-8", errors="replace") as fh:
        mm.read(mmverify.Toks(fh))
    _dv, mand, _h, _c = mm.labels[label][1]
    mand_labels = [mm.lookup_e_label(h) if False else " ".join(h) for h in mand]

    table = [f"[hyp] {h}" for h in mand_labels] + labels
    print(f"{label}: {len(mand_labels)} mandatory hypotheses, "
          f"{len(labels)} labels, {len(letters)} letters")
    print()
    # A reference beyond the table length points into the saved list, in the
    # order things were saved. Track what each save actually was so the trace
    # reads as "reuse of step 12" rather than an opaque index.
    saved: list[str] = []
    step = 0
    last = ""
    for ev in decode(letters):
        if ev[0] == "save":
            saved.append(f"step {step}")
            print(f"       ↳ saved as reference {len(saved)} "
                  f"(= step {step}, {last})")
            continue
        n = ev[1]
        step += 1
        if n <= len(table):
            last = table[n - 1]
        else:
            k = n - len(table)
            last = (f"REUSE {saved[k - 1]}" if k <= len(saved)
                    else f"<bad reference {n}>")
        print(f"  {step:>3}  {last}")


if __name__ == "__main__":
    main()
