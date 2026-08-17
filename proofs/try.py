#!/usr/bin/env python3
r"""Assemble a proof, splice it into set.mm, and verify just that label.

    python proofs/try.py

Writes vendor/set_try.mm rather than touching the database, and asks mmverify
to check only the new statement, which takes about six seconds including the
parse of the whole library.
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

PHI = "( S e. U. ran sigAlgebra /\\ A e. S /\\ B e. S )"


def build_proof(db):
    """A C_ U. S from the three-way antecedent.

    Not the target theorem -- a sub-derivation of it, used to find out whether
    the assembler produces something the verifier accepts before anything
    larger is attempted."""
    s = [
        Step(f"|- ( {PHI} -> S e. U. ran sigAlgebra )", "simp1"),
        Step(f"|- ( {PHI} -> A e. S )", "simp2"),
        Step("|- ( ( S e. U. ran sigAlgebra /\\ A e. S ) -> A C_ U. S )",
             "elsigass"),
        Step(f"|- ( {PHI} -> A C_ U. S )", "syl2anc", args=[0, 1, 2]),
    ]
    return s


def main() -> None:
    db = Database(SETMM)
    steps = build_proof(db)
    rpn = assemble(db, steps, verbose=True)
    print(f"\n{len(rpn)} tokens")

    label = "zzztest"
    stmt = f"|- ( {PHI} -> A C_ U. S )"
    text = SETMM.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"(?m)^[ \t]*difelsiga[ \t]+\$p", text)
    if not m:
        sys.exit("anchor not found")
    j = text.rfind("${", 0, m.start())
    block = emit(label, stmt, rpn)
    OUT.write_text(text[:j] + block + text[j:], encoding="utf-8")
    print(f"wrote {OUT.name}, verifying {label} ...")

    r = subprocess.run(
        [sys.executable, "-X", "utf8", str(HERE.parent / "vendor" / "mmverify.py"),
         str(OUT), "-b", label, "-s", "difelsiga", "-v", "2"],
        capture_output=True, text=True)
    tail = (r.stderr or "").strip().splitlines()
    print()
    if r.returncode == 0:
        print("VERIFIED")
        for l in tail[-3:]:
            print("   ", l)
    else:
        print(f"REJECTED (exit {r.returncode})")
        for l in tail[-8:]:
            print("   ", l)


if __name__ == "__main__":
    main()
