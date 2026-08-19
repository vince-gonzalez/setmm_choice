#!/usr/bin/env python3
r"""Move abrexct into main set.mm, and use it in omeiunle.

    python proofs/abrexct_move.py

`omeiunle` needs "an image of a countable set is countable". `abrexct` says
exactly that in one step and is choice-free, but it sits in Thierry Arnoux's
mathbox while `omeiunle` is in Glauco Siliprandi's, and set.mm forbids the
cross-reference -- `verify markup` rejects it.

tirix offered on #5448 to move `abrexct` into the main part of the library,
which is what this does. The move is clean: `abrexct`'s entire transitive
closure is already in main, so it is the only mathbox statement in its own
dependency tree, and `sigaclcu2` is its only existing user.

It lands immediately after `1stcrestlem`, the latest-defined of its
dependencies, which is where it can first be stated.

The `omeiunle` proof then drops the `fnrndomnum` route entirely, so this no
longer stacks on #5443.
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
OUT = VENDOR / "set_abrexct.mm"
PR = HERE.parent / "pr6"

IMG = "{ m | E. n e. Z m = ( E ` n ) }"
FUN = "( n e. Z |-> ( E ` n ) )"
MPT = f"|- ( ph -> ran E = ran {FUN} )"
CT = "|- ( ph -> Z ~<_ _om )"
TARGET = "|- ( ph -> ran E ~<_ _om )"

OME_STMT = ("|- ( ph -> ( O ` U_ n e. Z ( E ` n ) ) <_ ( sum^ ` ( n e. Z |->\n"
            "{i}( O ` ( E ` n ) ) ) ) )")
OME_COMMENT = (
    "The outer measure of the indexed union of a countable set is the less "
    "than or equal to the extended sum of the outer measures.  The proof uses "
    "~ abrexct rather than ~ fnrndomg , and so does not require ~ ax-ac .  "
    f"(Contributed by Glauco Siliprandi, 17-Aug-2020.)  (Revised by {WHO}, "
    f"{WHEN}.)")
OME_DD = "$d E m $.  $d O m n $.  $d X m n $.  $d Z m n $."
OME_HYPS = """    omeiunle.nph $e |- F/ n ph $.
    omeiunle.ne $e |- F/_ n E $.
    omeiunle.o $e |- ( ph -> O e. OutMeas ) $.
    omeiunle.x $e |- X = U. dom O $.
    omeiunle.z $e |- Z = ( ZZ>= ` N ) $.
    omeiunle.e $e |- ( ph -> E : Z --> ~P X ) $."""


def main() -> None:
    PR.mkdir(exist_ok=True)
    src = SETMM.read_text(encoding="utf-8", errors="replace")

    # ---- 1. lift abrexct out of the mathbox
    m = re.search(r"(?m)^[ \t]*abrexct[ \t]+\$p", src)
    a_s = src.rfind("\n", 0, src.rfind("$(", 0, m.start())) + 1
    a_e = src.find("\n", src.find("$.", m.start())) + 1
    old_block = src[a_s:a_e]
    src = src[:a_s] + src[a_e:]

    # abrexct shares an enclosing ${ } with mpocti, and the $d conditions it
    # needs -- $d x y A, $d y B -- live on that shared block. Removing the
    # statement alone strips them, and the proof then fails on "Disjoint
    # variable violation: B , y". So the move re-creates them in a block of
    # its own and leaves mpocti and its enclosing block alone.
    # Take the statement by structure -- from the label to its closing `$.` --
    # rather than by guessing which lines look like proof text; comment lines
    # are indistinguishable from proof lines by shape alone.
    sm = re.search(r"(?ms)^[ \t]*abrexct[ \t]+\$p.*?\$\.", old_block)
    if sm is None:
        sys.exit("could not isolate the abrexct statement")
    stmt = "\n".join(l[2:] if l.startswith("      ") else l.lstrip()
                     for l in sm.group(0).splitlines())
    moved = ("  ${\n    $d x y A $.  $d y B $.\n"
             "    $( An image set of a countable set is countable.  "
             "(Contributed by\n       Thierry Arnoux, 29-Dec-2016.)  "
             f"(Moved to the main part of\n       set.mm by {WHO}, "
             f"{WHEN}.) $)\n"
             + "\n".join("  " + l for l in stmt.splitlines()) + "\n  $}\n")

    # place it after 1stcrestlem, the latest-defined of its dependencies
    # 1stcrestlem sits inside a ${ } whose $d covers a t v w x y z A and which
    # runs well past it. Landing inside that block would give abrexct foreign
    # disjointness and put its own ${ } in someone else's scope, so go after
    # the enclosing block closes and sit at top level.
    anchor = re.search(r"(?m)^[ \t]*1stcrestlem[ \t]+\$p", src)
    close = src.find("\n", src.find("$}", anchor.start())) + 1
    src = src[:close] + "\n" + moved + src[close:]
    OUT.write_text(src, encoding="utf-8")
    print("abrexct moved into main set.mm")

    # ---- 2. reprove omeiunle against it
    db = Database(OUT)
    rpn = rpn_of(db, "omeiunle", src)
    sp = spans(db, rpn)
    tgt, mpt, ct = find(sp, TARGET), find(sp, MPT), find(sp, CT)
    for name, s in (("target", tgt), ("ran E = ran mpt", mpt), ("Z ~<_ _om", ct)):
        if s is None:
            sys.exit(f"could not locate {name}")
        print(f"  {name:<16} [{s[1]}:{s[2]}] via {s[0]}")

    steps = [
        Step(MPT, rpn=rpn[mpt[1]:mpt[2]]),                                 # 0
        Step(CT, rpn=rpn[ct[1]:ct[2]]),                                    # 1
        Step(f"|- {FUN} = {FUN}", "eqid"),                                 # 2
        Step(f"|- ran {FUN} = {IMG}", "rnmpt", args=[2]),                  # 3
        Step(f"|- ( ph -> ran E = {IMG} )", "eqtrdi", args=[0, 3]),        # 4
        Step(f"|- ( Z ~<_ _om -> {IMG} ~<_ _om )", "abrexct"),             # 5
        Step(f"|- ( ph -> {IMG} ~<_ _om )", "syl", args=[1, 5]),           # 6
        Step(TARGET, "eqbrtrd", args=[4, 6]),                              # 7
    ]
    new = assemble(db, steps, verbose=True)
    out_rpn = splice(rpn, tgt, new)
    print(f"\nomeiunle: {len(rpn)} steps -> {len(out_rpn)}")

    bloc, txt = compress(db, "omeiunle", out_rpn)
    mo = re.search(r"(?m)^[ \t]*omeiunle[ \t]+\$p", src)
    o_s = src.rfind("\n", 0, src.rfind("${", 0, mo.start())) + 1
    o_e = src.find("\n", src.find("$}", src.find("$=", mo.start()))) + 1
    body = ("  ${\n    " + OME_DD + "\n" + OME_HYPS + "\n"
            + block("omeiunle", OME_COMMENT, OME_STMT, bloc, txt, dollar_d=None)
            + "  $}\n")
    src = src[:o_s] + body + src[o_e:]
    OUT.write_text(src, encoding="utf-8")

    r = subprocess.run(
        [sys.executable, "-X", "utf8", str(VENDOR / "mmverify.py"), str(OUT),
         "-b", "abrexct", "-s", "zzzstop"], capture_output=True, text=True)
    print()
    if r.returncode:
        print(f"REJECTED (exit {r.returncode})")
        for l in (r.stderr or "").strip().splitlines()[-6:]:
            print("   ", l[:170])
        sys.exit(1)
    print("VERIFIED  abrexct through end of file")
    (PR / "set.mm").write_text(src, encoding="utf-8")

    r = subprocess.run(
        [sys.executable, "-X", "utf8", str(HERE.parent / "tools" /
         "necessity.py"), str(OUT), "--axiom", "ax-ac", "ax-ac2",
         "--trace", "omeiunle"], capture_output=True, text=True)
    print()
    print("\n".join(r.stdout.strip().splitlines()[-5:]))


if __name__ == "__main__":
    main()
