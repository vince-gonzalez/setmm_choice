#!/usr/bin/env python3
r"""The complement-closure lemma set.mm does not have, assembled and verified.

    python proofs/compl.py

    ( ( S e. U. ran sigAlgebra /\ A e. S ) -> ( U. S \ A ) e. S )

A sigma-algebra is closed under complement by definition -- `issiga` says so
outright -- yet nothing in the library states it as a lemma, so every use
unfolds the definition inline. That absence is why `difelsiga` reaches for
countable-intersection closure, and with it the axiom of choice.

The derivation is the unfolding, done once:

    isrnsigau  gives the definition unpacked from membership in the range
    simprd     drops the S C_ ~P U. S conjunct
    simp2d     keeps the complement clause, A. x e. S ( U. S \ x ) e. S
    difeq2     x = A -> ( U. S \ x ) = ( U. S \ A )
    eleq1d     lifts that to membership in S
    rspccva    instantiates the quantifier at A
    sylan      joins the two antecedents
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))
from mmapi import Database  # noqa: E402
from mmassemble import Step, assemble, emit  # noqa: E402

SETMM = HERE.parent / "vendor" / "set.mm"
OUT = HERE.parent / "vendor" / "set_try.mm"

LABEL = "zzzcompl"
SIGA = "S e. U. ran sigAlgebra"
CLAUSE = "A. x e. S ( U. S \\ x ) e. S"
CNTBL = "A. x e. ~P S ( x ~<_ _om -> U. x e. S )"
STMT = f"|- ( ( {SIGA} /\\ A e. S ) -> ( U. S \\ A ) e. S )"


def steps():
    return [
        Step(f"|- ( {SIGA} -> ( S C_ ~P U. S /\\ "
             f"( U. S e. S /\\ {CLAUSE} /\\ {CNTBL} ) ) )", "isrnsigau"),
        Step(f"|- ( {SIGA} -> ( U. S e. S /\\ {CLAUSE} /\\ {CNTBL} ) )",
             "simprd", args=[0]),
        Step(f"|- ( {SIGA} -> {CLAUSE} )", "simp2d", args=[1]),
        Step("|- ( x = A -> ( U. S \\ x ) = ( U. S \\ A ) )", "difeq2"),
        Step("|- ( x = A -> ( ( U. S \\ x ) e. S <-> ( U. S \\ A ) e. S ) )",
             "eleq1d", args=[3]),
        Step(f"|- ( ( {CLAUSE} /\\ A e. S ) -> ( U. S \\ A ) e. S )",
             "rspccva", args=[4]),
        Step(f"|- ( ( {SIGA} /\\ A e. S ) -> ( U. S \\ A ) e. S )",
             "sylan", args=[2, 5]),
    ]


def main() -> None:
    db = Database(SETMM)
    rpn = assemble(db, steps(), verbose=True)
    print(f"\n{len(rpn)} tokens")

    text = SETMM.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"(?m)^[ \t]*difelsiga[ \t]+\$p", text)
    j = text.rfind("${", 0, m.start())
    block = emit(LABEL, STMT, rpn, dollar_d="$d x A $.  $d x S $.")
    OUT.write_text(text[:j] + block + text[j:], encoding="utf-8")

    r = subprocess.run(
        [sys.executable, "-X", "utf8",
         str(HERE.parent / "vendor" / "mmverify.py"), str(OUT),
         "-b", LABEL, "-s", "difelsiga", "-v", "2"],
        capture_output=True, text=True)
    print()
    if r.returncode == 0:
        print(f"VERIFIED  {LABEL}")
        print(f"  {STMT}")
    else:
        print(f"REJECTED (exit {r.returncode})")
        for l in (r.stderr or "").strip().splitlines()[-6:]:
            print("   ", l)


if __name__ == "__main__":
    main()
