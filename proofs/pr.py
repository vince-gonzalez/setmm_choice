#!/usr/bin/env python3
r"""Build the set.mm patch: difunielsiga added, difelsiga reproved without choice.

    python proofs/pr.py

Writes the patched database to `pr/set.mm`, verifies it from the first changed
statement to the end of the file, and re-runs the axiom closure to confirm the
dependence is gone.

Three things change, all in one contiguous region:

  1. `difunielsiga` is added -- closure under complement, which the library
     states nowhere despite `issiga` asserting it by definition.
  2. `difelsiga` and `unelsiga` swap places. `unelsiga` currently sits *after*
     `difelsiga`, so pairwise union did not exist when class difference was
     proved. That ordering is the whole reason difference was routed through
     countable intersection, and countable intersection is where choice enters.
  3. `difelsiga` is reproved from the two of them.

`inelsiga` is proved from `difelsiga` through `dfin4` and needs no edit; it
stops depending on choice as a consequence.
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
from mmcompress import _decompress, compress, render  # noqa: E402
import compl  # noqa: E402
import difelsiga as D  # noqa: E402

VENDOR = HERE.parent / "vendor"
SETMM = VENDOR / "set.mm"
OUT = VENDOR / "set_pr.mm"
PR = HERE.parent / "pr"

# Matches his ORCID, Zenodo and OEIS records. set.mm credits are permanent and
# are read as an identity, so this is the one string to change if he wants a
# different form of the name.
WHO = "Vincent Gonzalez"
WHEN = "17-Aug-2026"
NEW = "difunielsiga"

CMPL_STMT = ("|- ( ( S e. U. ran sigAlgebra /\\ A e. S ) ->\n"
             "{i}( U. S \\ A ) e. S )")
DIF_STMT = ("|- ( ( S e. U. ran sigAlgebra /\\ A e. S /\\ B e. S ) ->\n"
            "{i}( A \\ B ) e. S )")

CMPL_COMMENT = (
    "A sigma-algebra is closed under complement relative to its base set. "
    "This is immediate from the definition, see ~ issiga , but the library "
    f"states it nowhere in this form.  (Contributed by {WHO}, {WHEN}.)")

DIF_COMMENT = (
    "A sigma-algebra is closed under class differences. The proof goes "
    f"through ~ {NEW} and ~ unelsiga rather than countable intersection, and "
    "so does not use ~ ax-ac .  (Contributed by Thierry Arnoux, "
    f"13-Sep-2016.)  (Proof shortened by {WHO}, {WHEN}.)")


def wrap_comment(body: str, indent: int, width: int = 79) -> str:
    """Wrap a comment the way set.mm does: `$(` on the first line, three-space
    hanging indent, two spaces after a sentence. Hand-wrapping this is how a
    long name silently pushes a line over the limit."""
    import textwrap
    lines = textwrap.wrap(body, width=width - indent - 3,
                          fix_sentence_endings=True)
    pad = " " * (indent + 3)
    out = ["$( " + lines[0]] + [pad + ln for ln in lines[1:]]
    if len(out[-1]) + 3 > width:
        out.append(pad + "$)")
    else:
        out[-1] += " $)"
    return "\n".join(out)


def block(label, comment, statement, bloc, text, dollar_d=""):
    """Render a theorem the way set.mm lays one out.

    A `${ $}` wrapper exists only to scope `$d` and `$e`; a theorem with
    neither is written bare at two-space indent, the way `inelsiga` is. So the
    indent, and whether there are braces at all, both follow from `$d`.
    """
    wrap = bool(dollar_d)
    ind = 4 if wrap else 2
    i = " " * ind
    body = render(bloc, text, indent=ind + 2)
    out = (f"{i}{wrap_comment(comment, ind)}\n"
           f"{i}{label} $p {statement.format(i=i + '  ')} $=\n{body} $.\n")
    if wrap:
        out = f"  ${{\n{i}{dollar_d}\n{out}  $}}\n"
    over = [ln for ln in out.splitlines() if len(ln) > 79]
    assert not over, f"{label}: line over 79 columns: {over[0]!r}"
    return out


def dif_steps():
    """difelsiga's step list, with the helper under its real name."""
    return [Step(s.goal, NEW if s.by == "zzzcompl" else s.by, s.args)
            for s in D.steps()]


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

    def blk(lab):
        """Line-aligned bounds of a theorem's whole block, braces included.

        Slicing at the `${` itself leaves its indentation stranded in the
        preceding text, which then double-indents whatever gets spliced in.
        """
        m = re.search(r"(?m)^[ \t]*" + lab + r"[ \t]+\$p", text)
        s = text.rfind("${", 0, text.rfind("$(", 0, m.start()))
        e = text.find("$}", m.start()) + 2
        return text.rfind("\n", 0, s) + 1, text.find("\n", e) + 1

    ds, de = blk("difelsiga")
    us, ue = blk("unelsiga")
    assert de < us and not text[de:us].strip(), "blocks are not adjacent"
    head, mid, tail = text[:ds], text[us:ue], text[ue:]

    def size(src, dbx, lab):
        """(labels, letters, steps) for a stored compressed proof."""
        m = re.search(r"(?ms)^[ \t]*" + lab + r"[ \t]+\$p\s(.*?)\$=(.*?)\$\.",
                      src)
        proof = m.group(2).split()
        i = proof.index(")")
        _dv, mand, ess, _c = dbx.mm.labels[lab][1]
        flat = _decompress(dbx, mand, ess, proof, lab)
        return len(proof[1:i]), len("".join(proof[i + 1:])), len(flat)

    was = size(text, db, "difelsiga")

    # difunielsiga mentions only S and A, so its frame is difelsiga's minus B.
    mand = [p for p in db.frame("difelsiga")[1] if p[1] in ("S", "A")]
    bloc_c, txt_c = compress(db, NEW, assemble(db, compl.steps()),
                             frame=(set(), mand, [], compl.STMT.split()))

    def make(dd_cmpl, dd_dif):
        cm = block(NEW, CMPL_COMMENT, CMPL_STMT, bloc_c, txt_c, dd_cmpl)
        # The staging file keeps difelsiga's original block: inelsiga cites it,
        # so removing it before the replacement exists breaks the read.
        OUT.write_text(head + cm + "\n" + mid + "\n" + text[ds:de] + tail,
                       encoding="utf-8")
        db2 = Database(OUT)
        rpn = assemble(db2, dif_steps())
        bloc_d, txt_d = compress(db2, "difelsiga", rpn)
        dm = block("difelsiga", DIF_COMMENT, DIF_STMT, bloc_d, txt_d, dd_dif)
        return head + cm + "\n" + mid + "\n" + dm + tail, bloc_d, txt_d

    # `x` never enters the new difelsiga -- it lives inside difunielsiga and
    # unelsiga -- so the dummy-variable conditions it has carried since 2016
    # may now be dead. Only keep them if dropping them fails.
    DD_C = "$d x A $.  $d x S $."
    print("dropping difelsiga's dummy-variable conditions:")
    src, bloc_d, txt_d = make(DD_C, "")
    code, err = verify(src, NEW)
    print(f"  no $d          -> {'accepted' if not code else 'REJECTED ' + err}")
    dd_dif = ""
    if code:
        dd_dif = "$d x S $.  $d x B $."
        src, bloc_d, txt_d = make(DD_C, dd_dif)
        code, err = verify(src, NEW)
        print(f"  $d as before   -> "
              f"{'accepted' if not code else 'REJECTED ' + err}")
    if code:
        sys.exit(1)

    print(f"\nverified {NEW} through end of file: yes")
    (PR / "set.mm").write_text(src, encoding="utf-8")
    dbn = Database(PR / "set.mm")
    now = size(src, dbn, "difelsiga")
    new = size(src, dbn, NEW)
    print(f"\n{'':<12}{'labels':>8}{'chars':>8}{'steps':>8}")
    for lab, s, tag in (("difelsiga", was, "before"),
                        ("difelsiga", now, "after"),
                        (NEW, new, "new")):
        print(f"{lab:<12}{s[0]:>8}{s[1]:>8}{s[2]:>8}   {tag}")
    print(f"{'':<12}{'':>8}{was[1] - now[1] - new[1]:>+8}"
          f"{was[2] - now[2] - new[2]:>+8}   net, both proofs counted")

    print(f"\npatched database -> {PR / 'set.mm'}")

    r = subprocess.run(
        [sys.executable, "-X", "utf8", str(HERE.parent / "tools" /
         "necessity.py"), str(OUT), "--axiom", "ax-ac", "ax-ac2",
         "--trace", "difelsiga", "inelsiga", NEW, "sigaclci"],
        capture_output=True, text=True)
    print()
    print("\n".join(r.stdout.strip().splitlines()[-14:]))


if __name__ == "__main__":
    main()
