#!/usr/bin/env python3
r"""difelsiga without the axiom of choice.

    python proofs/difelsiga.py

    ( ( S e. U. ran sigAlgebra /\ A e. S /\ B e. S ) -> ( A \ B ) e. S )

set.mm proves this by writing A \ B as the intersection of the pair
{ A, U. S \ B }, showing that pair countable, and applying closure under
countable intersection. That last step, sigaclci, establishes its countability
side-condition through a dominance argument, and dominance needs choice.

Sixty-four theorems sit below this one, Bayes' theorem among them.

The route here never forms a pair. A sigma-algebra is closed under complement
by definition, and closed under pairwise union without choice, so

    A \ B  =  U. S \ ( ( U. S \ A ) u. B )

does the whole job: complement A, union with B, complement again, then rewrite.
The complement lemma this needs does not exist in set.mm and is proved first in
compl.py; both are emitted here so the pair verifies together.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))
sys.path.insert(0, str(HERE))
from mmapi import Database  # noqa: E402
from mmassemble import Step, assemble, emit  # noqa: E402
import compl  # noqa: E402

SETMM = HERE.parent / "vendor" / "set.mm"
OUT = HERE.parent / "vendor" / "set_try.mm"

SIGA = "S e. U. ran sigAlgebra"
PHI = f"( {SIGA} /\\ A e. S /\\ B e. S )"
U = "U. S"
NA = f"( {U} \\ A )"                    # complement of A
UN = f"( {NA} u. B )"                   # that, unioned with B
CN = f"( {U} \\ {UN} )"                 # complemented again -- this is A \ B
NNA = f"( {U} \\ {NA} )"                # double complement, which is A


def steps():
    return [
        Step(f"|- ( {PHI} -> {SIGA} )", "simp1"),                        # 0
        Step(f"|- ( {PHI} -> A e. S )", "simp2"),                        # 1
        Step(f"|- ( {PHI} -> B e. S )", "simp3"),                        # 2
        Step(f"|- ( ( {SIGA} /\\ A e. S ) -> {NA} e. S )", "zzzcompl"),  # 3
        Step(f"|- ( {PHI} -> {NA} e. S )", "syl2anc", args=[0, 1, 3]),   # 4
        Step(f"|- ( ( {SIGA} /\\ {NA} e. S /\\ B e. S ) -> {UN} e. S )",
             "unelsiga"),                                                # 5
        Step(f"|- ( {PHI} -> {UN} e. S )", "syl3anc", args=[0, 4, 2, 5]),  # 6
        Step(f"|- ( ( {SIGA} /\\ {UN} e. S ) -> {CN} e. S )", "zzzcompl"),  # 7
        Step(f"|- ( {PHI} -> {CN} e. S )", "syl2anc", args=[0, 6, 7]),   # 8
        Step(f"|- ( ( {SIGA} /\\ A e. S ) -> A C_ {U} )", "elsigass"),    # 9
        Step(f"|- ( {PHI} -> A C_ {U} )", "syl2anc", args=[0, 1, 9]),    # 10
        Step(f"|- ( A C_ {U} <-> {NNA} = A )", "dfss4"),                 # 11
        Step(f"|- ( {PHI} -> {NNA} = A )", "sylib", args=[10, 11]),      # 12
        Step(f"|- ( {PHI} -> ( {NNA} \\ B ) = ( A \\ B ) )",
             "difeq1d", args=[12]),                                      # 13
        Step(f"|- {CN} = ( {NNA} \\ B )", "difun1"),                     # 14
        Step(f"|- ( {PHI} -> {CN} = ( {NNA} \\ B ) )", "a1i", args=[14]),  # 15
        Step(f"|- ( {PHI} -> {CN} = ( A \\ B ) )", "eqtrd", args=[15, 13]),  # 16
        Step(f"|- ( {PHI} -> ( A \\ B ) e. S )",
             "eqeltrrd", args=[16, 8]),                                  # 17
    ]


def main() -> None:
    db = Database(SETMM)

    text = SETMM.read_text(encoding="utf-8", errors="replace")
    # unelsiga is defined AFTER difelsiga in set.mm -- pairwise union did not
    # exist at the point difelsiga was proved, which is why that proof reached
    # for countable intersection instead. Splice after the last dependency.
    end = max(re.search(r"(?m)^[ \t]*" + lab + r"[ \t]+\$[pa][ \t]", text).end()
              for lab in ("unelsiga", "isrnsigau", "elsigass"))
    j = text.find("$}", end) + 2

    # the complement lemma has to exist before this proof can cite it
    helper_rpn = assemble(db, compl.steps())
    helper = emit(compl.LABEL, compl.STMT, helper_rpn,
                  dollar_d="$d x A $.  $d x S $.")
    staged = text[:j] + helper + text[j:]
    OUT.write_text(staged, encoding="utf-8")

    db2 = Database(OUT)
    st = steps()
    rpn = assemble(db2, st, verbose=True)
    print(f"\n{len(rpn)} tokens")

    block = emit("zzzdifel", f"|- ( {PHI} -> ( A \\ B ) e. S )", rpn,
                 dollar_d="$d x A $.  $d x B $.  $d x S $.")
    m2 = re.search(r"(?m)^[ \t]*" + compl.LABEL + r"[ \t]+\$p", staged)
    j2 = staged.find("$}", m2.end()) + 2
    OUT.write_text(staged[:j2] + block + staged[j2:], encoding="utf-8")

    r = subprocess.run(
        [sys.executable, "-X", "utf8",
         str(HERE.parent / "vendor" / "mmverify.py"), str(OUT),
         "-b", "zzzcompl", "-s", "zzzstop"],
        capture_output=True, text=True)
    print()
    if r.returncode == 0:
        print("VERIFIED  zzzcompl and zzzdifel")
        print(f"  |- ( {PHI} -> ( A \\ B ) e. S )")
        print("  without the axiom of choice")
    else:
        print(f"REJECTED (exit {r.returncode})")
        for l in (r.stderr or "").strip().splitlines()[-6:]:
            print("   ", l[:150])


if __name__ == "__main__":
    main()
