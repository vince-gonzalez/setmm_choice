#!/usr/bin/env python3
r"""Build the second set.mm patch: fnrndomnum added, fnrndomg proved from it.

    python proofs/pr2.py

set.mm already draws this distinction one step down:

    fodomg    ( A e. V        -> ( F : A -onto-> B -> B ~<_ A ) )   uses ax-ac
    fodomnum  ( A e. dom card -> ( F : A -onto-> B -> B ~<_ A ) )   does not

and `fodomg` is proved from `fodomnum` by `numth3`, so the choice step is one
visible line. The `Fn` form was only ever written in the `ax-ac` version.

This adds the missing half and proves `fnrndomg` from it the same way, so the
pair matches the pattern already in the library. `fnrndomg`'s statement does
not change.
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
from mmcompress import _decompress, compress  # noqa: E402
from pr import WHO, WHEN, block  # noqa: E402

VENDOR = HERE.parent / "vendor"
SETMM = VENDOR / "set.mm"
OUT = VENDOR / "set_pr2.mm"
PR = HERE.parent / "pr2"

NEW = "fnrndomnum"
NEW_STMT = "|- ( A e. dom card -> ( F Fn A -> ran F ~<_ A ) )"
OLD_STMT = "|- ( A e. B -> ( F Fn A -> ran F ~<_ A ) )"

NEW_COMMENT = (
    f"A version of ~ fnrndomg that doesn't require the Axiom of Choice "
    f"~ ax-ac .  (Contributed by {WHO}, {WHEN}.)")

OLD_COMMENT = (
    "The range of a function is dominated by its domain.  This theorem uses "
    "the axiom of choice ~ ac7g ; see ~ fnrndomnum for a version that does "
    f"not.  (Contributed by NM, 1-Sep-2004.)  (Proof shortened by {WHO}, "
    f"{WHEN}.)")


def new_steps():
    return [
        Step("|- ( F Fn A <-> F : A -onto-> ran F )", "dffn4"),
        Step("|- ( A e. dom card -> ( F : A -onto-> ran F -> ran F ~<_ A ) )",
             "fodomnum"),
        Step(NEW_STMT, "biimtrid", args=[0, 1]),
    ]


def old_steps():
    """fnrndomg, restructured exactly the way fodomg sits on fodomnum."""
    return [
        Step("|- ( A e. B -> A e. dom card )", "numth3"),
        Step(NEW_STMT, NEW),
        Step(OLD_STMT, "syl", args=[0, 1]),
    ]


def verify(src, first):
    OUT.write_text(src, encoding="utf-8")
    r = subprocess.run(
        [sys.executable, "-X", "utf8", str(VENDOR / "mmverify.py"), str(OUT),
         "-b", first, "-s", "zzzstop"], capture_output=True, text=True)
    return r.returncode, ((r.stderr or "").strip().splitlines() or [""])[-1]


def main() -> None:
    PR.mkdir(exist_ok=True)
    text = SETMM.read_text(encoding="utf-8", errors="replace")
    db = Database(SETMM)

    m = re.search(r"(?m)^[ \t]*fnrndomg[ \t]+\$p", text)
    s = text.rfind("\n", 0, text.rfind("$(", 0, m.start())) + 1
    e = text.find("\n", text.find("$.", m.start())) + 1
    head, tail = text[:s], text[e:]

    def size(src, dbx, lab):
        mm = re.search(r"(?ms)^[ \t]*" + lab + r"[ \t]+\$p\s(.*?)\$=(.*?)\$\.",
                       src)
        p = mm.group(2).split()
        i = p.index(")")
        _dv, mand, ess, _c = dbx.mm.labels[lab][1]
        return len(p[1:i]), len("".join(p[i + 1:])), len(
            _decompress(dbx, mand, ess, p, lab))

    was = size(text, db, "fnrndomg")

    mand = [p for p in db.frame("fnrndomg")[1] if p[1] in ("A", "F")]
    bloc_n, txt_n = compress(db, NEW, assemble(db, new_steps()),
                             frame=(set(), mand, [], NEW_STMT.split()))
    nb = block(NEW, NEW_COMMENT, NEW_STMT, bloc_n, txt_n)

    # stage with the new lemma in place so fnrndomg can be assembled against it
    OUT.write_text(head + nb + "\n" + text[s:], encoding="utf-8")
    db2 = Database(OUT)
    bloc_o, txt_o = compress(db2, "fnrndomg", assemble(db2, old_steps()))
    ob = block("fnrndomg", OLD_COMMENT, OLD_STMT, bloc_o, txt_o)

    src = head + nb + "\n" + ob + tail
    code, err = verify(src, NEW)
    print(f"verified {NEW} through end of file: "
          f"{'yes' if not code else 'NO -- ' + err}")
    if code:
        sys.exit(1)

    (PR / "set.mm").write_text(src, encoding="utf-8")
    dbn = Database(PR / "set.mm")
    now, new = size(src, dbn, "fnrndomg"), size(src, dbn, NEW)
    print(f"\n{'':<12}{'labels':>8}{'chars':>8}{'steps':>8}")
    for lab, st, tag in (("fnrndomg", was, "before"),
                         ("fnrndomg", now, "after"), (NEW, new, "new")):
        print(f"{lab:<12}{st[0]:>8}{st[1]:>8}{st[2]:>8}   {tag}")

    r = subprocess.run(
        [sys.executable, "-X", "utf8", str(HERE.parent / "tools" /
         "necessity.py"), str(OUT), "--axiom", "ax-ac", "ax-ac2",
         "--trace", NEW, "fnrndomg"], capture_output=True, text=True)
    print()
    print("\n".join(r.stdout.strip().splitlines()[-10:]))


if __name__ == "__main__":
    main()
