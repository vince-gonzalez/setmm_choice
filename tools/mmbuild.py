#!/usr/bin/env python3
r"""Compile a readable proof outline into a Metamath proof.

    python tools/mmbuild.py proofs/sigacompl.mmp

mmj2 is a proof assistant: you give it statements and it finds the justifying
steps by unification. That is more than this problem needs. Every step of the
proof being built here already has a known justification -- the work is turning
`( U. S \ A )` into `S cuni A cdif` and pushing each lemma's hypotheses in the
order its frame demands.

So this is a compiler, not a prover. It reads an outline of the form

    step-name | lemma | conclusion
    h1        |       | |- ( ph -> ps )          (a hypothesis, no lemma)
    2         | ax-mp | |- ps                    (justified by ax-mp)

and emits the reverse-Polish label sequence Metamath wants, using the same
frame construction the verifier uses to decide whether it is right.

Syntax is compiled from set.mm's own $a statements, so no grammar is hardcoded:
the constructor for `( A u. B )` is discovered by finding the $a whose
right-hand side matches that shape.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "vendor"))
import mmverify  # noqa: E402

mmverify.verbosity = 0
mmverify.logfile = sys.stderr
SETMM = HERE.parent / "vendor" / "set.mm"


def load():
    mm = mmverify.MM(None, None)
    with open(SETMM, "r", encoding="utf-8", errors="replace") as fh:
        mm.read(mmverify.Toks(fh))
    return mm


def syntax_axioms(mm):
    """Every $a whose typecode is not |- : the syntax constructors.

    Returns a list of (label, typecode, template, varlist) where template is the
    statement with its variables left in place, so a candidate expression can be
    matched against it.
    """
    out = []
    for lab, (kind, val) in mm.labels.items():
        if kind != "$a":
            continue
        _dv, _mand, _hyps, concl = val
        if not concl or concl[0] == "|-":
            continue
        out.append((lab, concl[0], list(concl[1:])))
    return out


def main() -> None:
    mm = load()
    syn = syntax_axioms(mm)
    print(f"loaded set.mm: {len(mm.labels):,} labels, "
          f"{len(syn):,} syntax constructors")
    # Report the handful this proof needs, to confirm they are discoverable
    # rather than assumed.
    want = {"cuni": None, "cdif": None, "cun": None, "wcel": None,
            "wceq": None, "wss": None, "wa": None, "w3a": None, "wi": None}
    for lab, tc, tmpl in syn:
        if lab in want:
            want[lab] = (tc, " ".join(tmpl))
    for lab, v in want.items():
        print(f"  {lab:<6} {v[0] if v else '??':<6} {v[1] if v else 'NOT FOUND'}")


if __name__ == "__main__":
    main()
