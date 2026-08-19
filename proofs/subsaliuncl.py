#!/usr/bin/env python3
r"""subsaliuncl without the axiom of choice.

    SETMM_BASE=<a set.mm carrying fnrndomnum> python proofs/subsaliuncl.py

    ( ph -> U_ n e. NN ( F ` n ) e. T )

A subspace sigma-algebra is closed under countable union. The union is indexed
by ` NN `, and to show the corresponding family countable the proof builds the
map

    ( n e. NN |-> { x e. S | ( F ` n ) = ( x i^i D ) } )

then applies `fnrndomg` to bound its range by ` NN `, and composes with
` NN ~<_ _om `. `fnrndomg` dominates a range by an arbitrary domain, which
needs choice; ` NN ` is not arbitrary.

`fnrndomnum` is the same statement for a well-orderable domain. ` NN ` is
numerable choice-free -- `nnct` gives ` NN ~<_ _om `, `omelon` gives
` _om e. On `, and `ondomen` turns those into ` NN e. dom card ` with both
antecedents closed. Everything else the substitution needs the proof already
has.

This does NOT make the theorem choice-free in the wider sense: it also uses
`axccdom`, which comes from `ax-cc`. That is countable choice, a separate and
strictly weaker axiom that set.mm tracks on its own, and it is untouched here.
What goes away is the dependence on full choice.

Every lemma used is in main set.mm, so no cross-mathbox reference is created.
"""
from __future__ import annotations

import os
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
SETMM = Path(os.environ.get("SETMM_BASE") or (VENDOR / "set.mm"))
OUT = VENDOR / "set_subsaliuncl.mm"
PR = HERE.parent / "pr7"

MPT = "( n e. NN |-> { x e. S | ( F ` n ) = ( x i^i D ) } )"
FN = f"|- ( ph -> {MPT} Fn NN )"
TARGET = f"|- ( ph -> ran {MPT} ~<_ _om )"

STMT = "|- ( ph -> U_ n e. NN ( F ` n ) e. T )"
COMMENT = (
    "A subspace sigma-algebra is closed under countable union.  This is Lemma "
    "121A (iii) of [Fremlin1] p. 35.  The proof uses ~ fnrndomnum rather than "
    "~ fnrndomg , and so does not require ~ ax-ac .  (Contributed by Glauco "
    f"Siliprandi, 26-Jun-2021.)  (Revised by {WHO}, {WHEN}.)")

DOLLAR_D = ("$d D e f n z $.  $d D e m n z $.  $d D f n x y z $.  "
            "$d F e f n z $.\n    $d F e m n z $.  $d F f n x y z $.  "
            "$d S e f n z $.  $d S e m n z $.\n    $d S f n x y z $.  "
            "$d T e $.  $d e f n ph z $.  $d m n x y z $.\n    $d ph y z $.")
HYPS = """    subsaliuncl.1 $e |- ( ph -> S e. SAlg ) $.
    subsaliuncl.2 $e |- ( ph -> D e. V ) $.
    subsaliuncl.3 $e |- T = ( S |`t D ) $.
    subsaliuncl.4 $e |- ( ph -> F : NN --> T ) $."""


def main() -> None:
    PR.mkdir(exist_ok=True)
    db = Database(SETMM)
    if "fnrndomnum" not in db.mm.labels:
        sys.exit("base has no fnrndomnum -- point SETMM_BASE at the #5443 branch")
    src = SETMM.read_text(encoding="utf-8", errors="replace")
    rpn = rpn_of(db, "subsaliuncl", src)
    sp = spans(db, rpn)
    print(f"subsaliuncl: {len(rpn)} steps")

    tgt, fn = find(sp, TARGET), find(sp, FN)
    for name, s in (("target", tgt), ("Fn NN", fn)):
        if s is None:
            sys.exit(f"could not locate {name}")
        print(f"  {name:<8} [{s[1]}:{s[2]}] via {s[0]}")

    steps = [
        Step(FN, rpn=rpn[fn[1]:fn[2]]),                                     # 0
        Step("|- NN ~<_ _om", "nnct"),                                      # 1
        Step("|- _om e. On", "omelon"),                                     # 2
        Step("|- ( ( _om e. On /\\ NN ~<_ _om ) -> NN e. dom card )",
             "ondomen"),                                                    # 3
        Step("|- NN e. dom card", "mp2an", args=[2, 1, 3]),                 # 4
        Step(f"|- ( NN e. dom card -> ( {MPT} Fn NN -> ran {MPT} ~<_ NN ) )",
             "fnrndomnum"),                                                 # 5
        Step(f"|- ( {MPT} Fn NN -> ran {MPT} ~<_ NN )",
             "ax-mp", args=[4, 5]),                                         # 6
        Step(f"|- ( ph -> ran {MPT} ~<_ NN )", "syl", args=[0, 6]),         # 7
        Step(f"|- ( ph -> NN ~<_ _om )", "a1i", args=[1]),                  # 8
        Step(f"|- ( ( ran {MPT} ~<_ NN /\\ NN ~<_ _om ) -> "
             f"ran {MPT} ~<_ _om )", "domtr"),                              # 9
        Step(TARGET, "syl2anc", args=[7, 8, 9]),                            # 10
    ]
    new = assemble(db, steps, verbose=True)
    out_rpn = splice(rpn, tgt, new)
    print(f"\nreplacing {tgt[2]-tgt[1]} steps with {len(new)}")
    print(f"subsaliuncl: {len(rpn)} steps -> {len(out_rpn)}")

    bloc, txt = compress(db, "subsaliuncl", out_rpn)
    m = re.search(r"(?m)^[ \t]*subsaliuncl[ \t]+\$p", src)
    s = src.rfind("\n", 0, src.rfind("${", 0, m.start())) + 1
    e = src.find("\n", src.find("$}", src.find("$=", m.start()))) + 1
    body = ("  ${\n    " + DOLLAR_D + "\n" + HYPS + "\n"
            + block("subsaliuncl", COMMENT, STMT, bloc, txt, dollar_d=None)
            + "  $}\n")
    patched = src[:s] + body + src[e:]
    OUT.write_text(patched, encoding="utf-8")

    r = subprocess.run(
        [sys.executable, "-X", "utf8", str(VENDOR / "mmverify.py"), str(OUT),
         "-b", "subsaliuncl", "-s", "zzzstop"], capture_output=True, text=True)
    print()
    if r.returncode:
        print(f"REJECTED (exit {r.returncode})")
        for l in (r.stderr or "").strip().splitlines()[-6:]:
            print("   ", l[:170])
        sys.exit(1)
    print("VERIFIED  subsaliuncl through end of file")
    (PR / "set.mm").write_text(patched, encoding="utf-8")

    r = subprocess.run(
        [sys.executable, "-X", "utf8", str(HERE.parent / "tools" /
         "necessity.py"), str(OUT), "--axiom", "ax-ac", "ax-ac2",
         "--trace", "subsaliuncl"], capture_output=True, text=True)
    print()
    print("\n".join(r.stdout.strip().splitlines()[-5:]))


if __name__ == "__main__":
    main()
