#!/usr/bin/env python3
r"""sigaclci without the axiom of choice.

    python proofs/sigaclci.py

    ( ( ( S e. U. ran sigAlgebra /\ A e. ~P S ) /\ ( A ~<_ _om /\ A =/= (/) ) )
      -> |^| A e. S )

`sigaclci` closes a sigma-algebra under countable intersections, and one of its
own hypotheses is ` A ~<_ _om `. To show the set of complements countable it
takes a detour:

    abrexdom2jm   ( A e. ~P S -> { y | E. z e. A y = ( U. S \ z ) } ~<_ A )
    domtr         ... together with A ~<_ _om

`abrexdom2jm` dominates an indexed set by an arbitrary indexing set, which needs
choice -- it is proved from `abrexdomjm`, which is proved from `fnrndomg`. That
whole chain exists to serve this one call: `abrexdomjm` is used only by
`abrexdom2jm`, and `abrexdom2jm` only here.

`abrexct` states the countable case directly, is choice-free, and is in the same
mathbox by the same author:

    abrexct       ( A ~<_ _om -> { y | E. x e. A y = B } ~<_ _om )

It gives the conclusion in one step from the hypothesis the theorem already has,
so the detour and its three choice-dependent lemmas drop out.
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
from mmassemble import Step, assemble  # noqa: E402
from mmcompress import compress  # noqa: E402
from mmswap import rpn_of, spans, find, splice  # noqa: E402
from pr import block, WHO  # noqa: E402

WHEN = "19-Aug-2026"

VENDOR = HERE.parent / "vendor"
SETMM = VENDOR / "set.mm"
OUT = VENDOR / "set_sigaclci.mm"
PR = HERE.parent / "pr5"

IMG = "{ y | E. z e. A y = ( U. S \\ z ) }"
TARGET = f"|- ( ( A e. ~P S /\\ A ~<_ _om ) -> {IMG} ~<_ _om )"
CT = f"|- ( A ~<_ _om -> {IMG} ~<_ _om )"

STMT = ("|- ( ( ( S e. U. ran sigAlgebra /\\ A e. ~P S ) /\\\n"
        "{i}( A ~<_ _om /\\ A =/= (/) ) ) -> |^| A e. S )")
COMMENT = (
    "A sigma-algebra is closed under countable intersections.  Deduction "
    "version.  The proof uses ~ abrexct rather than ~ abrexdom2jm , and so "
    f"does not require ~ ax-ac .  (Contributed by Thierry Arnoux, "
    f"19-Sep-2016.)  (Revised by {WHO}, {WHEN}.)")

DOLLAR_D = "$d x y z A $.  $d x y z S $."


def main() -> None:
    PR.mkdir(exist_ok=True)
    db = Database(SETMM)
    src = SETMM.read_text(encoding="utf-8", errors="replace")
    rpn = rpn_of(db, "sigaclci", src)
    sp = spans(db, rpn)
    print(f"sigaclci: {len(rpn)} steps")

    tgt = find(sp, TARGET)
    if tgt is None:
        sys.exit("could not locate the countability subproof")
    print(f"  target [{tgt[1]}:{tgt[2]}] via {tgt[0]}")

    steps = [
        Step(CT, "abrexct"),                       # 0
        Step(TARGET, "adantl", args=[0]),          # 1
    ]
    new = assemble(db, steps, verbose=True)
    out_rpn = splice(rpn, tgt, new)
    print(f"\nreplacing {tgt[2]-tgt[1]} steps with {len(new)}")
    print(f"sigaclci: {len(rpn)} steps -> {len(out_rpn)}")

    bloc, txt = compress(db, "sigaclci", out_rpn)
    m = re.search(r"(?m)^[ \t]*sigaclci[ \t]+\$p", src)
    s = src.rfind("\n", 0, src.rfind("${", 0, m.start())) + 1
    e = src.find("\n", src.find("$}", src.find("$=", m.start()))) + 1
    body = block("sigaclci", COMMENT, STMT, bloc, txt, dollar_d=DOLLAR_D)
    patched = src[:s] + body + src[e:]
    OUT.write_text(patched, encoding="utf-8")

    r = subprocess.run(
        [sys.executable, "-X", "utf8", str(VENDOR / "mmverify.py"), str(OUT),
         "-b", "sigaclci", "-s", "zzzstop"], capture_output=True, text=True)
    print()
    if r.returncode:
        print(f"REJECTED (exit {r.returncode})")
        for l in (r.stderr or "").strip().splitlines()[-5:]:
            print("   ", l[:170])
        sys.exit(1)
    print("VERIFIED  sigaclci through end of file")
    (PR / "set.mm").write_text(patched, encoding="utf-8")

    r = subprocess.run(
        [sys.executable, "-X", "utf8", str(HERE.parent / "tools" /
         "necessity.py"), str(OUT), "--axiom", "ax-ac", "ax-ac2",
         "--trace", "sigaclci", "difelsiga"], capture_output=True, text=True)
    print()
    print("\n".join(r.stdout.strip().splitlines()[-10:]))


if __name__ == "__main__":
    main()
