#!/usr/bin/env python3
r"""madefi without the axiom of choice.

    python proofs/madefi.py

    ( A e. _om -> ( _Made ` A ) e. Fin )

The proof establishes, at step 800, that

    ( ~P U. ( _Made " x ) X. ~P U. ( _Made " x ) )

is finite. Two hundred steps later it wants the image of that set under |s to
be finite, and gets there by way of `imadomg` -- dominance of an image by an
arbitrary index set, which needs choice -- then `domfi` to turn dominance back
into finiteness.

None of that is necessary once the set is known finite. `imafi` says directly
that the image of a finite set under a function is finite, it is choice-free,
and this proof already uses it earlier for a different subgoal. So the whole
`xpex` / `ffun` / `imadomg` / `mp2` / `domfi` detour collapses to one step.

The statement does not change. Only the subproof of

    ( ph -> ( |s " ( ... ) ) e. Fin )

is replaced, in place, by way of tools/mmswap.py.
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

WHEN = "19-Aug-2026"   # this proof, this day -- not the date of the other PRs

VENDOR = HERE.parent / "vendor"
SETMM = VENDOR / "set.mm"
OUT = VENDOR / "set_madefi.mm"
PR = HERE.parent / "pr3"

MADE = '( _Made " x )'
XX = f"( ~P U. {MADE} X. ~P U. {MADE} )"
IM = f'( |s " {XX} )'
PH = "( x e. _om /\\ A. y e. x ( _Made ` y ) e. Fin )"

TARGET = f"|- ( {PH} -> {IM} e. Fin )"
FUN = "|- Fun |s"
FIN = f"|- ( {PH} -> {XX} e. Fin )"

STMT = "|- ( A e. _om -> ( _Made ` A ) e. Fin )"
COMMENT = (
    "The made set of an ordinal natural is finite.  (Contributed by Scott "
    f"Fenton, 20-Aug-2025.)  (Proof shortened by {WHO}, {WHEN}.)")


def main() -> None:
    PR.mkdir(exist_ok=True)
    db = Database(SETMM)
    src = SETMM.read_text(encoding="utf-8", errors="replace")
    rpn = rpn_of(db, "madefi", src)
    sp = spans(db, rpn)
    print(f"madefi: {len(rpn)} steps")

    tgt = find(sp, TARGET)
    fun = find(sp, FUN)
    fin = find(sp, FIN)
    for name, s in (("target", tgt), ("Fun |s", fun), ("finiteness", fin)):
        if s is None:
            sys.exit(f"could not locate {name}:\n  {TARGET if name=='target' else ''}")
        print(f"  {name:<12} [{s[1]}:{s[2]}] via {s[0]}")

    # everything the replacement needs is already proved inside this proof
    steps = [
        Step(FUN, rpn=rpn[fun[1]:fun[2]]),                                 # 0
        Step(FIN, rpn=rpn[fin[1]:fin[2]]),                                 # 1
        Step(f"|- ( ( Fun |s /\\ {XX} e. Fin ) -> {IM} e. Fin )", "imafi"),  # 2
        Step(TARGET, "sylancr", args=[0, 1, 2]),                           # 3
    ]
    new = assemble(db, steps, verbose=True)
    print(f"\nreplacing {tgt[2]-tgt[1]} steps with {len(new)}")

    out_rpn = splice(rpn, tgt, new)
    print(f"madefi: {len(rpn)} steps -> {len(out_rpn)}")

    bloc, txt = compress(db, "madefi", out_rpn)
    m = re.search(r"(?m)^[ \t]*madefi[ \t]+\$p", src)
    s = src.rfind("\n", 0, src.rfind("$(", 0, m.start())) + 1
    e = src.find("\n", src.find("$.", m.start())) + 1
    # the statement fits on one line and /rewrap does not reflow math, so
    # splitting it would survive into the diff as gratuitous churn
    body = block("madefi", COMMENT, STMT, bloc, txt)
    patched = src[:s] + body + src[e:]
    OUT.write_text(patched, encoding="utf-8")

    r = subprocess.run(
        [sys.executable, "-X", "utf8", str(VENDOR / "mmverify.py"), str(OUT),
         "-b", "madefi", "-s", "zzzstop"], capture_output=True, text=True)
    print()
    if r.returncode:
        print(f"REJECTED (exit {r.returncode})")
        for l in (r.stderr or "").strip().splitlines()[-5:]:
            print("   ", l[:170])
        sys.exit(1)
    print("VERIFIED  madefi through end of file")
    (PR / "set.mm").write_text(patched, encoding="utf-8")

    r = subprocess.run(
        [sys.executable, "-X", "utf8", str(HERE.parent / "tools" /
         "necessity.py"), str(OUT), "--axiom", "ax-ac", "ax-ac2",
         "--trace", "madefi", "imadomg"], capture_output=True, text=True)
    print()
    print("\n".join(r.stdout.strip().splitlines()[-9:]))


if __name__ == "__main__":
    main()
