#!/usr/bin/env python3
"""Print the mandatory hypotheses of a theorem, in the order a proof must
supply them.

    python tools/mmframe.py unelsiga difun1 dfss4

Writing a Metamath proof by hand means pushing each lemma's hypotheses onto the
stack in exactly the right order before naming the lemma. That order is the
"mandatory frame": the floating hypotheses for every variable the statement
mentions, in the order they were declared, followed by the essential
hypotheses. Getting it wrong is the single most common way a hand-written proof
fails, and the error message points at the stack rather than at the mistake.

This uses mmverify's own frame construction, so the order shown is the order it
will demand.
"""
from __future__ import annotations

import sys
from pathlib import Path


from ._vendor import mmverify
from . import default_database

# mmverify sets these in main(); using it as a library means setting them here.
mmverify.verbosity = 0
mmverify.logfile = sys.stderr

SETMM = default_database()


def main() -> None:
    labels = sys.argv[1:]
    if not labels:
        sys.exit("give one or more labels")
    mm = mmverify.MM(None, None)
    with open(SETMM, "r", encoding="utf-8", errors="replace") as fh:
        mm.read(mmverify.Toks(fh))
    for lab in labels:
        entry = mm.labels.get(lab)
        print(f"--- {lab}")
        if entry is None:
            print("    NOT FOUND")
            continue
        kind, val = entry
        if kind not in ("$a", "$p"):
            print(f"    {kind} {' '.join(val)}")
            continue
        dvs, mand_hyps, hyps, concl = val
        print(f"    conclusion : {' '.join(concl)}")
        print(f"    mandatory hypotheses, in push order:")
        for h in mand_hyps:
            print(f"       {' '.join(h)}")
        if dvs:
            print(f"    disjoint    : {sorted(dvs)}")


if __name__ == "__main__":
    main()
