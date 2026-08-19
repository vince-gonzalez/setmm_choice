#!/usr/bin/env python3
r"""imadomnum -- imadomg without the axiom of choice.

    python proofs/imadomnum.py

    ( ( A e. dom card /\ Fun F ) -> ( F " A ) ~<_ A )

The third member of a pattern set.mm only half wrote. For dominance of an
image by its index set the library has

    imadomg   ( A e. B     -> ( Fun F -> ( F " A ) ~<_ A ) )   uses ax-ac
    imadomfi  ( A e. Fin /\ Fun F  -> ( F " A ) ~<_ A )        does not

and nothing in between: no version for a domain that is merely well-orderable.
`imadomfi` fixes the shape to follow -- hypotheses conjoined, not curried.

The route never touches a surjection. Restricting F to A gives a function on
` ( A i^i dom F ) `, that set is a subset of a numerable set and so numerable
itself by ssnum, and fnrndomnum bounds its range without choosing anything.
Rewriting ` ran ( F |` A ) ` as ` ( F " A ) ` and composing with
` ( A i^i dom F ) ~<_ A ` finishes it.

Builds against a database that already carries fnrndomnum, so this stacks on
the fnrndomnum pull request.
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

VENDOR = HERE.parent / "vendor"
BASE = HERE.parent / "pr2" / "set.mm"          # has fnrndomnum
OUT = VENDOR / "set_imadom.mm"

LABEL = "imadomnum"
NUM = "A e. dom card"
RES = "( F |` A )"
INT = "( A i^i dom F )"
IMA = "( F \" A )"
PHI = f"( {NUM} /\\ Fun F )"
STMT = f"|- ( {PHI} -> {IMA} ~<_ A )"


def steps():
    return [
        Step(f"|- ( Fun F -> Fun {RES} )", "funres"),                        # 0
        Step(f"|- ( Fun {RES} <-> {RES} Fn dom {RES} )", "funfn"),           # 1
        Step(f"|- ( Fun F -> {RES} Fn dom {RES} )", "sylib", args=[0, 1]),   # 2
        Step(f"|- dom {RES} = {INT}", "dmres"),                              # 3
        Step(f"|- ( {RES} Fn dom {RES} <-> {RES} Fn {INT} )",
             "fneq2i", args=[3]),                                            # 4
        Step(f"|- ( Fun F -> {RES} Fn {INT} )", "sylib", args=[2, 4]),       # 5
        Step(f"|- ( {PHI} -> {RES} Fn {INT} )", "adantl", args=[5]),         # 6
        Step(f"|- {INT} C_ A", "inss1"),                                     # 7
        Step(f"|- ( ( {NUM} /\\ {INT} C_ A ) -> {INT} e. dom card )",
             "ssnum"),                                                       # 8
        Step(f"|- ( {NUM} -> {INT} e. dom card )", "mpan2", args=[7, 8]),    # 9
        Step(f"|- ( {PHI} -> {INT} e. dom card )", "adantr", args=[9]),      # 10
        Step(f"|- ( {INT} e. dom card -> ( {RES} Fn {INT} -> "
             f"ran {RES} ~<_ {INT} ) )", "fnrndomnum"),                      # 11
        Step(f"|- ( {PHI} -> ran {RES} ~<_ {INT} )",
             "sylc", args=[10, 6, 11]),                                      # 12
        Step(f"|- {IMA} = ran {RES}", "df-ima"),                             # 13
        Step(f"|- ( {PHI} -> {IMA} ~<_ {INT} )",
             "eqbrtrid", args=[13, 12]),                                     # 14
        Step(f"|- ( {NUM} -> A e. _V )", "elex"),                            # 15
        Step("|- ( A e. _V -> ( " + INT + " C_ A -> " + INT + " ~<_ A ) )",
             "ssdomg"),                                                      # 16
        Step(f"|- ( {NUM} -> ( {INT} C_ A -> {INT} ~<_ A ) )",
             "syl", args=[15, 16]),                                          # 17
        Step(f"|- ( {NUM} -> {INT} ~<_ A )", "mpi", args=[7, 17]),           # 18
        Step(f"|- ( {PHI} -> {INT} ~<_ A )", "adantr", args=[18]),           # 19
        Step(f"|- ( ( {IMA} ~<_ {INT} /\\ {INT} ~<_ A ) -> {IMA} ~<_ A )",
             "domtr"),                                                       # 20
        Step(STMT, "syl2anc", args=[14, 19, 20]),                            # 21
    ]


def main() -> None:
    src = BASE if BASE.exists() else VENDOR / "set.mm"
    if src != BASE:
        sys.exit("pr2/set.mm not built -- run proofs/pr2.py first "
                 "(imadomnum stacks on fnrndomnum)")
    db = Database(src)
    rpn = assemble(db, steps(), verbose=True)
    print(f"\n{len(rpn)} tokens")

    text = src.read_text(encoding="utf-8", errors="replace")
    end = max(re.search(r"(?m)^[ \t]*" + lab + r"[ \t]+\$[pa][ \t]", text).end()
              for lab in ("fnrndomnum", "ssnum", "imadomg"))
    j = text.find("\n", text.find("$.", end)) + 1
    OUT.write_text(text[:j] + emit(LABEL, STMT, rpn) + text[j:],
                   encoding="utf-8")

    r = subprocess.run(
        [sys.executable, "-X", "utf8", str(VENDOR / "mmverify.py"), str(OUT),
         "-b", LABEL, "-s", "zzzstop"], capture_output=True, text=True)
    print()
    if r.returncode:
        print(f"REJECTED (exit {r.returncode})")
        for l in (r.stderr or "").strip().splitlines()[-5:]:
            print("   ", l[:160])
        sys.exit(1)
    print(f"VERIFIED  {LABEL}\n  {STMT}")

    r = subprocess.run(
        [sys.executable, "-X", "utf8", str(HERE.parent / "tools" /
         "necessity.py"), str(OUT), "--axiom", "ax-ac", "ax-ac2",
         "--trace", LABEL, "imadomg"], capture_output=True, text=True)
    print()
    print("\n".join(r.stdout.strip().splitlines()[-9:]))


if __name__ == "__main__":
    main()
