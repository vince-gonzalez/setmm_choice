#!/usr/bin/env python3
r"""disjinfi without the axiom of choice.

    python proofs/disjinfi.py

    ( ph -> { x e. A | ( B i^i C ) =/= (/) } e. Fin )

One of the theorem's own hypotheses is ` ( ph -> C e. Fin ) `, and at step 83
the proof has already used it to show

    ( ph -> ( U. ran ( x e. A |-> B ) i^i C ) e. Fin )

since that set is a subset of C. It then builds a surjection from that finite
set onto the answer and reaches for `fodomg`, which is stated for an arbitrary
domain and so needs choice, before `domfi` converts dominance back into
finiteness.

`fodomfi` is the same statement for a finite domain and is choice-free. The
finiteness it wants is the fact proved at step 83, so nothing new is needed --
the proof already knows everything required, it just asked the general lemma.

Same shape as madefi: a finite set, established early, forgotten, and
recovered through a choice-dependent detour.
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
OUT = VENDOR / "set_disjinfi.mm"
PR = HERE.parent / "pr4"

DOM = "( U. ran ( x e. A |-> B ) i^i C )"
RES = "{ x e. A | ( B i^i C ) =/= (/) }"
MPT = f"( y e. {DOM} |-> ( iota_ x e. A y e. ( B i^i C ) ) )"

FIN = f"|- ( ph -> {DOM} e. Fin )"
ONTO = f"|- ( ph -> {MPT} : {DOM} -onto-> {RES} )"
TARGET = f"|- ( ph -> {RES} ~<_ {DOM} )"

STMT = f"|- ( ph -> {RES} e. Fin )"
COMMENT = (
    "Only a finite number of disjoint sets can have a nonempty intersection "
    "with a finite set ` C ` .  "
    "The proof uses ~ fodomfi rather than ~ fodomg , and so does not require "
    f"~ ax-ac .  (Contributed by Glauco Siliprandi, 17-Aug-2020.)  "
    f"(Revised by {WHO}, {WHEN}.)")

DOLLAR_D = ("$d A w x y z $.  $d B w y z $.  $d C w x y z $.  $d V x $.  "
            "$d ph w x y $.")
HYPS = """    disjinfi.b $e |- ( ( ph /\\ x e. A ) -> B e. V ) $.
    disjinfi.d $e |- ( ph -> Disj_ x e. A B ) $.
    disjinfi.c $e |- ( ph -> C e. Fin ) $."""


def main() -> None:
    PR.mkdir(exist_ok=True)
    db = Database(SETMM)
    src = SETMM.read_text(encoding="utf-8", errors="replace")
    rpn = rpn_of(db, "disjinfi", src)
    sp = spans(db, rpn)
    print(f"disjinfi: {len(rpn)} steps")

    tgt, fin, onto = find(sp, TARGET), find(sp, FIN), find(sp, ONTO)
    for name, s in (("target", tgt), ("finiteness", fin), ("surjection", onto)):
        if s is None:
            sys.exit(f"could not locate {name}")
        print(f"  {name:<11} [{s[1]}:{s[2]}] via {s[0]}")

    steps = [
        Step(FIN, rpn=rpn[fin[1]:fin[2]]),                                  # 0
        Step(ONTO, rpn=rpn[onto[1]:onto[2]]),                               # 1
        Step(f"|- ( ( {DOM} e. Fin /\\ {MPT} : {DOM} -onto-> {RES} ) -> "
             f"{RES} ~<_ {DOM} )", "fodomfi"),                              # 2
        Step(TARGET, "syl2anc", args=[0, 1, 2]),                            # 3
    ]
    new = assemble(db, steps, verbose=True)
    out_rpn = splice(rpn, tgt, new)
    print(f"\nreplacing {tgt[2]-tgt[1]} steps with {len(new)}")
    print(f"disjinfi: {len(rpn)} steps -> {len(out_rpn)}")

    bloc, txt = compress(db, "disjinfi", out_rpn)
    m = re.search(r"(?m)^[ \t]*disjinfi[ \t]+\$p", src)
    s = src.rfind("\n", 0, src.rfind("${", 0, m.start())) + 1
    e = src.find("\n", src.find("$.", src.find("$=", m.start()))) + 1
    e = src.find("\n", src.find("$}", e)) + 1
    body = ("  ${\n    " + DOLLAR_D + "\n" + HYPS + "\n"
            + block("disjinfi", COMMENT, STMT, bloc, txt, dollar_d=None)
            + "  $}\n")
    patched = src[:s] + body + src[e:]
    OUT.write_text(patched, encoding="utf-8")

    r = subprocess.run(
        [sys.executable, "-X", "utf8", str(VENDOR / "mmverify.py"), str(OUT),
         "-b", "disjinfi", "-s", "zzzstop"], capture_output=True, text=True)
    print()
    if r.returncode:
        print(f"REJECTED (exit {r.returncode})")
        for l in (r.stderr or "").strip().splitlines()[-5:]:
            print("   ", l[:170])
        sys.exit(1)
    print("VERIFIED  disjinfi through end of file")
    (PR / "set.mm").write_text(patched, encoding="utf-8")

    r = subprocess.run(
        [sys.executable, "-X", "utf8", str(HERE.parent / "tools" /
         "necessity.py"), str(OUT), "--axiom", "ax-ac", "ax-ac2",
         "--trace", "disjinfi"], capture_output=True, text=True)
    print()
    print("\n".join(r.stdout.strip().splitlines()[-5:]))


if __name__ == "__main__":
    main()
