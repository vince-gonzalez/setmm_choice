#!/usr/bin/env python3
r"""omeiunle without the axiom of choice.

    python proofs/omeiunle.py

The theorem bounds the outer measure of a countable indexed union. Its index set
is fixed by a hypothesis, ` Z = ( ZZ>= ` N ) `, so it is countable, and the proof
derives ` Z ~<_ _om ` from `uzct` at step 631.

To get ` ran E ~<_ _om ` it nevertheless goes the long way: `fnrndomg` for
` ran E ~<_ Z `, which dominates a range by an arbitrary domain and so needs
choice, then `domtr` against the countability it just derived.

`fnrndomnum` is the same statement for a well-orderable domain and is
choice-free. ` Z ~<_ _om ` makes Z numerable through `ondomen`, and the proof
already has both ` ( ph -> E Fn Z ) ` and ` ( ph -> Z ~<_ _om ) `, so the
substitution needs nothing new.

Same shape as sigaclci: a countability hypothesis in hand, and a general
dominance lemma reached for anyway.
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

import os

VENDOR = HERE.parent / "vendor"
# SETMM_BASE lets this stack on another patch -- the disjinfi change is in the
# same mathbox and travels in the same pull request, so the two must be built
# one on top of the other rather than each against pristine upstream.
SETMM = Path(os.environ.get("SETMM_BASE") or (VENDOR / "set.mm"))
OUT = VENDOR / "set_omeiunle.mm"
PR = HERE.parent / "pr6"

FN = "|- ( ph -> E Fn Z )"
CT = "|- ( ph -> Z ~<_ _om )"
TARGET = "|- ( ph -> ran E ~<_ _om )"

STMT = ("|- ( ph -> ( O ` U_ n e. Z ( E ` n ) ) <_ ( sum^ ` ( n e. Z |->\n"
        "{i}( O ` ( E ` n ) ) ) ) )")
COMMENT = (
    "The outer measure of the indexed union of a countable set is the less "
    "than or equal to the extended sum of the outer measures.  The proof uses "
    "~ fnrndomnum rather than ~ fnrndomg , and so does not require ~ ax-ac .  "
    f"(Contributed by Glauco Siliprandi, 17-Aug-2020.)  (Revised by {WHO}, "
    f"{WHEN}.)")

DOLLAR_D = "$d E m $.  $d O m n $.  $d X m n $.  $d Z m n $."
HYPS = """    omeiunle.nph $e |- F/ n ph $.
    omeiunle.ne $e |- F/_ n E $.
    omeiunle.o $e |- ( ph -> O e. OutMeas ) $.
    omeiunle.x $e |- X = U. dom O $.
    omeiunle.z $e |- Z = ( ZZ>= ` N ) $.
    omeiunle.e $e |- ( ph -> E : Z --> ~P X ) $."""


def main() -> None:
    PR.mkdir(exist_ok=True)
    db = Database(SETMM)
    src = SETMM.read_text(encoding="utf-8", errors="replace")
    rpn = rpn_of(db, "omeiunle", src)
    sp = spans(db, rpn)
    print(f"omeiunle: {len(rpn)} steps")

    tgt, fn, ct = find(sp, TARGET), find(sp, FN), find(sp, CT)
    for name, s in (("target", tgt), ("E Fn Z", fn), ("Z ~<_ _om", ct)):
        if s is None:
            sys.exit(f"could not locate {name}")
        print(f"  {name:<10} [{s[1]}:{s[2]}] via {s[0]}")

    # abrexct would do this in one step, but it lives in Thierry Arnoux's
    # mathbox and omeiunle is in Glauco Siliprandi's; set.mm forbids one
    # mathbox referencing another and `verify markup` rejects it. mmverify.py
    # has no notion of mathboxes and accepts it, so only the real tool catches
    # this. Every lemma below is in main set.mm except uzct, which is
    # Siliprandi's own.
    steps = [
        Step(FN, rpn=rpn[fn[1]:fn[2]]),                                    # 0
        Step(CT, rpn=rpn[ct[1]:ct[2]]),                                    # 1
        Step("|- _om e. On", "omelon"),                                    # 2
        Step("|- ( ( _om e. On /\ Z ~<_ _om ) -> Z e. dom card )",
             "ondomen"),                                                   # 3
        Step("|- ( Z ~<_ _om -> Z e. dom card )", "mpan", args=[2, 3]),    # 4
        Step("|- ( ph -> Z e. dom card )", "syl", args=[1, 4]),            # 5
        Step("|- ( Z e. dom card -> ( E Fn Z -> ran E ~<_ Z ) )",
             "fnrndomnum"),                                                # 6
        Step("|- ( ph -> ran E ~<_ Z )", "sylc", args=[5, 0, 6]),          # 7
        Step("|- ( ( ran E ~<_ Z /\ Z ~<_ _om ) -> ran E ~<_ _om )",
             "domtr"),                                                     # 8
        Step(TARGET, "syl2anc", args=[7, 1, 8]),                           # 9
    ]
    new = assemble(db, steps, verbose=True)
    out_rpn = splice(rpn, tgt, new)
    print(f"\nreplacing {tgt[2]-tgt[1]} steps with {len(new)}")
    print(f"omeiunle: {len(rpn)} steps -> {len(out_rpn)}")

    bloc, txt = compress(db, "omeiunle", out_rpn)
    m = re.search(r"(?m)^[ \t]*omeiunle[ \t]+\$p", src)
    s = src.rfind("\n", 0, src.rfind("${", 0, m.start())) + 1
    e = src.find("\n", src.find("$}", src.find("$=", m.start()))) + 1
    body = ("  ${\n    " + DOLLAR_D + "\n" + HYPS + "\n"
            + block("omeiunle", COMMENT, STMT, bloc, txt, dollar_d=None)
            + "  $}\n")
    patched = src[:s] + body + src[e:]
    OUT.write_text(patched, encoding="utf-8")

    r = subprocess.run(
        [sys.executable, "-X", "utf8", str(VENDOR / "mmverify.py"), str(OUT),
         "-b", "omeiunle", "-s", "zzzstop"], capture_output=True, text=True)
    print()
    if r.returncode:
        print(f"REJECTED (exit {r.returncode})")
        for l in (r.stderr or "").strip().splitlines()[-6:]:
            print("   ", l[:170])
        sys.exit(1)
    print("VERIFIED  omeiunle through end of file")
    (PR / "set.mm").write_text(patched, encoding="utf-8")

    r = subprocess.run(
        [sys.executable, "-X", "utf8", str(HERE.parent / "tools" /
         "necessity.py"), str(OUT), "--axiom", "ax-ac", "ax-ac2",
         "--trace", "omeiunle"], capture_output=True, text=True)
    print()
    print("\n".join(r.stdout.strip().splitlines()[-5:]))


if __name__ == "__main__":
    main()
