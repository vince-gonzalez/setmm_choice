#!/usr/bin/env python3
r"""Replace one subproof of an existing proof, leaving the rest untouched.

Most avoidable axiom uses sit one step deep inside a long proof. `madefi` runs
1003 steps and only step 968 reaches for choice; rebuilding the other 1002 from
a step list to change that one would be absurd, and hand-editing a compressed
proof is how silent breakage happens.

A subproof occupies a contiguous run of the reverse-Polish sequence, so if the
replacement proves the same statement it can be spliced in place and the rest
of the proof neither knows nor cares. That is the whole idea:

    spans(db, rpn)          every subproof, as (label, start, end, statement)
    find(spans, statement)  the one proving what you want to replace
    splice(rpn, span, new)  swap it out

The replacement is built with mmassemble, and subtrees already present in the
proof can be handed to it as given steps, so nothing already proved is proved
twice.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from mmapi import Database  # noqa: E402
from mmcompress import _decompress  # noqa: E402


def rpn_of(db: Database, label: str, source: str) -> list[str]:
    """The flat reverse-Polish proof stored for `label`."""
    m = re.search(r"(?ms)^[ \t]*" + re.escape(label) + r"[ \t]+\$p\s(.*?)\$=(.*?)\$\.",
                  source)
    if not m:
        raise KeyError(f"{label} has no stored $p proof")
    proof = m.group(2).split()
    _dv, mand, ess, _c = db.mm.labels[label][1]
    if proof and proof[0] == "(":
        return _decompress(db, mand, ess, proof, label)
    return proof


def spans(db: Database, rpn: list[str]):
    """Every subproof as (label, start, end, statement).

    Replaying through the verifier's own step function gives the statement;
    tracking where each stack entry began gives the span. `end` is exclusive,
    so rpn[start:end] is exactly that subproof.
    """
    stack: list = []
    starts: list[int] = []
    out = []
    for i, tok in enumerate(rpn):
        kind, val = db.mm.labels[tok]
        n = 0 if kind in ("$f", "$e") else len(val[1]) + len(val[2])
        before = len(stack)
        db.mm.treat_step(db.mm.labels[tok], stack)
        if n:
            begin = starts[before - n] if n <= before else i
            del starts[before - n:]
        else:
            begin = i
        starts.append(begin)
        out.append((tok, begin, i + 1, list(stack[-1])))
    return out


def find(sp, statement):
    """The outermost subproof proving `statement`, or None."""
    want = statement.split() if isinstance(statement, str) else list(statement)
    hits = [s for s in sp if s[3] == want]
    if not hits:
        return None
    return max(hits, key=lambda s: s[2] - s[1])


def splice(rpn, span, new_rpn):
    _lab, start, end, _stmt = span
    return list(rpn[:start]) + list(new_rpn) + list(rpn[end:])


def _cli() -> None:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("database")
    ap.add_argument("label")
    ap.add_argument("--uses", help="show subproofs whose top label is this")
    ap.add_argument("--width", type=int, default=120)
    a = ap.parse_args()
    db = Database(a.database)
    src = Path(a.database).read_text(encoding="utf-8", errors="replace")
    rpn = rpn_of(db, a.label, src)
    sp = spans(db, rpn)
    print(f"{a.label}: {len(rpn)} steps")
    for lab, s, e, stmt in sp:
        if a.uses and lab != a.uses:
            continue
        if not a.uses and stmt[0] != "|-":
            continue
        print(f"  [{s:>5}:{e:<5}] {lab:<14} {' '.join(stmt)[:a.width]}")


if __name__ == "__main__":
    _cli()
