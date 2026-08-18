#!/usr/bin/env python3
r"""fnrndomnum -- fnrndomg without the axiom of choice.

    python proofs/fnrndomnum.py

    ( A e. dom card -> ( F Fn A -> ran F ~<_ A ) )

`fnrndomg` says the range of a function is dominated by its domain. In full
generality that needs choice, and legitimately so: an injection from the range
back into the domain picks a preimage for every value, which is a choice
function. Nothing can remove that.

What can be removed is the generality. If the domain is well-orderable you take
the *least* preimage and choose nothing. set.mm already draws exactly this
distinction one step down --

    fodomg    ( A e. V        -> ( F : A -onto-> B -> B ~<_ A ) )   uses ax-ac
    fodomnum  ( A e. dom card -> ( F : A -onto-> B -> B ~<_ A ) )   does not

-- but the `Fn` form was only ever written in the `ax-ac` version. This is the
missing half of that pair, and it is `fnrndomg`'s own three-step proof with
`fodomnum` in place of `fodomg`.
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
OUT = HERE.parent / "vendor" / "set_fnrnd.mm"

LABEL = "fnrndomnum"
STMT = "|- ( A e. dom card -> ( F Fn A -> ran F ~<_ A ) )"


def steps():
    return [
        Step("|- ( F Fn A <-> F : A -onto-> ran F )", "dffn4"),
        Step("|- ( A e. dom card -> ( F : A -onto-> ran F -> ran F ~<_ A ) )",
             "fodomnum"),
        Step(STMT, "biimtrid", args=[0, 1]),
    ]


def main() -> None:
    db = Database(SETMM)
    rpn = assemble(db, steps(), verbose=True)
    print(f"\n{len(rpn)} tokens")

    text = SETMM.read_text(encoding="utf-8", errors="replace")
    # place it after everything it cites
    end = max(re.search(r"(?m)^[ \t]*" + lab + r"[ \t]+\$[pa][ \t]",
                        text).end()
              for lab in ("fodomnum", "dffn4", "biimtrid"))
    j = text.find("$}", end)
    j = text.find("\n", j) + 1 if j > 0 else end
    OUT.write_text(text[:j] + emit(LABEL, STMT, rpn) + text[j:],
                   encoding="utf-8")

    r = subprocess.run(
        [sys.executable, "-X", "utf8", str(HERE.parent / "vendor" /
         "mmverify.py"), str(OUT), "-b", LABEL, "-s", "zzzstop"],
        capture_output=True, text=True)
    print()
    if r.returncode == 0:
        print(f"VERIFIED  {LABEL}")
        print(f"  {STMT}")
    else:
        print(f"REJECTED (exit {r.returncode})")
        for l in (r.stderr or "").strip().splitlines()[-5:]:
            print("   ", l[:150])
        sys.exit(1)

    r = subprocess.run(
        [sys.executable, "-X", "utf8", str(HERE.parent / "tools" /
         "necessity.py"), str(OUT), "--axiom", "ax-ac", "ax-ac2",
         "--trace", LABEL, "fnrndomg"], capture_output=True, text=True)
    print()
    print("\n".join(r.stdout.strip().splitlines()[-12:]))


if __name__ == "__main__":
    main()
