#!/usr/bin/env python3
r"""Replay a stored proof and print what each step actually proves.

    python tools/mmsteps.py vendor/set.mm madefi --grep imadomg

`mmdecomp.py` renders the label sequence, which tells you the shape of a proof
but not what any step says -- and it builds its reference table from the
floating hypotheses alone, so on a theorem with `$e`s the numbering silently
slides. To decide whether a use of a lemma is avoidable you need the
instantiation: not "imadomg is used here" but "imadomg is used here with
A := this set".

So this replays the proof through the verifier's own step function and prints
the stack top after each step. The statements are therefore the verifier's,
not a reconstruction of them.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from mmapi import Database  # noqa: E402
from mmcompress import _decompress, _hyp_labels  # noqa: E402


def steps_of(db: Database, label: str, source: str):
    """[(index, label, statement)] for each step of `label`'s stored proof."""
    import re
    m = re.search(r"(?ms)^[ \t]*" + re.escape(label) + r"[ \t]+\$p\s(.*?)\$=(.*?)\$\.",
                  source)
    if not m:
        raise KeyError(f"{label} has no stored $p proof")
    proof = m.group(2).split()
    _dv, mand, ess, _c = db.mm.labels[label][1]
    rpn = (_decompress(db, mand, ess, proof, label)
           if proof and proof[0] == "(" else proof)

    stack: list = []
    out = []
    for i, tok in enumerate(rpn):
        db.mm.treat_step(db.mm.labels[tok], stack)
        out.append((i, tok, list(stack[-1])))
    return out, _hyp_labels(db, label, mand)


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("database")
    ap.add_argument("label")
    ap.add_argument("--grep", help="only show steps whose label matches this")
    ap.add_argument("--context", type=int, default=0,
                    help="also show N steps either side of a match")
    ap.add_argument("--width", type=int, default=150)
    a = ap.parse_args()

    db = Database(a.database)
    src = Path(a.database).read_text(encoding="utf-8", errors="replace")
    rows, hyps = steps_of(db, a.label, src)
    print(f"{a.label}: {len(rows)} steps, hypotheses {hyps or '(none)'}\n")

    keep = range(len(rows))
    if a.grep:
        hit = [i for i, lab, _ in rows if a.grep in lab]
        if not hit:
            print(f"no step uses {a.grep!r}")
            return
        keep = sorted({j for i in hit
                       for j in range(max(0, i - a.context),
                                      min(len(rows), i + a.context + 1))})
    prev = None
    for i in keep:
        idx, lab, stmt = rows[i]
        if prev is not None and idx != prev + 1:
            print("   ...")
        s = " ".join(stmt)
        print(f"  {idx:>5} {lab:<14} {s[:a.width]}")
        prev = idx


if __name__ == "__main__":
    main()
