#!/usr/bin/env python3
r"""Compress a Metamath proof into the format set.mm stores.

    python tools/mmcompress.py --selftest 300

set.mm keeps every proof compressed, and its CI re-saves the whole file and
diffs the result, so a normal-format proof fails the build no matter how
correct it is. An uncompressed proof is also unreadable at scale: difelsiga
runs 200 steps normal and 12 lines compressed.

The format is a label bloc followed by a letter string. Indices count the
assertion's own mandatory hypotheses first, then the blocked labels, then
subproofs tagged for reuse with `Z`. Numbers are base-20 in A-T with a
bijective base-5 prefix in U-Y.

Reuse is where the size actually goes. A subproof appearing twice is emitted
once, tagged, and referenced thereafter -- so compressing well means finding
repeated subtrees, not packing digits.

Correctness of the encoder is checked by round-tripping set.mm against itself:
decompress a stored proof, recompress it, compare bytes.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "vendor"))
from mmapi import Database  # noqa: E402


# ------------------------------------------------------------------ numbers
def encode_int(n: int) -> str:
    """0 -> 'A'. The low digit is base 20 in A-T; the high digits are
    bijective base 5 in U-Y, so there is no zero digit and no ambiguity."""
    out = chr(ord("A") + n % 20)
    q = n // 20
    pre = ""
    while q:
        q, d = divmod(q, 5)
        if d == 0:
            d, q = 5, q - 1
        pre = chr(ord("U") + d - 1) + pre
    return pre + out


def decode(s: str) -> list[int]:
    """Inverse of encode_int over a whole letter string; -1 marks a Z."""
    out, cur = [], 0
    for ch in s:
        if ch == "Z":
            out.append(-1)
        elif "A" <= ch <= "T":
            out.append(20 * cur + ord(ch) - 65)
            cur = 0
        else:
            cur = 5 * cur + ord(ch) - 84
    return out


# -------------------------------------------------------------------- trees
def arity(db: Database, label: str) -> int:
    kind, val = db.mm.labels[label]
    if kind in ("$f", "$e"):
        return 0
    return len(val[1]) + len(val[2])


def parse_rpn(db: Database, rpn: list[str]) -> tuple:
    """Fold a reverse-Polish proof into a tree of (label, children)."""
    stack = []
    for tok in rpn:
        n = arity(db, tok)
        if n:
            if len(stack) < n:
                raise ValueError(f"{tok} wants {n} operands, stack has "
                                 f"{len(stack)}")
            stack, kids = stack[:-n], tuple(stack[-n:])
        else:
            kids = ()
        stack.append((tok, kids))
    if len(stack) != 1:
        raise ValueError(f"proof leaves {len(stack)} entries on the stack")
    return stack[0]


def _key(node) -> str:
    lab, kids = node
    return lab if not kids else lab + "(" + ",".join(map(_key, kids)) + ")"


def _steps(key: str) -> int:
    """Number of proof steps in a subproof, read off its key."""
    return key.count(",") + key.count("(") + 1


def _count(node, c: Counter, seen: set | None = None) -> None:
    """Count occurrences the way the emitter will actually meet them.

    A repeat nested inside an already-shared subproof is not a repeat: the
    outer back-reference stands in for the whole subtree, so the inner copy is
    never emitted and must not be counted. Descend into a key's first
    occurrence only.
    """
    seen = set() if seen is None else seen
    k = _key(node)
    c[k] += 1
    if k in seen:
        return
    seen.add(k)
    for kid in node[1]:
        _count(kid, c, seen)


# ---------------------------------------------------------------- compress
def compress(db: Database, label: str, rpn: list[str],
             frame=None) -> tuple[list[str], str]:
    """Return (label bloc, letter string) for `rpn` proving `label`.

    `frame` overrides the database's own frame, which is what you want when
    the assertion is new and not yet in the database.
    """
    dv, mand, ess, _c = frame if frame else db.frame(label)
    hyp_labels = _hyp_labels(db, label, mand)

    tree = parse_rpn(db, rpn)
    counts = Counter()
    _count(tree, counts)

    # Tagging a single-token leaf is always a loss: the Z costs a character
    # and the back-reference costs at least as much as re-emitting the label.
    # Only repeated subproofs of two steps or more pay for themselves.
    shared = {k for k, n in counts.items() if n > 1 and _steps(k) > 1}

    bloc: list[str] = []
    bloc_ix: dict[str, int] = {}
    saved: dict[str, int] = {}
    out: list[str] = []

    def idx_for(lab: str) -> int:
        if lab in hyp_labels:
            return hyp_labels.index(lab)
        if lab not in bloc_ix:
            bloc_ix[lab] = len(bloc)
            bloc.append(lab)
        return len(hyp_labels) + bloc_ix[lab]

    n_hyp = len(hyp_labels)

    def walk(node) -> None:
        k = _key(node)
        if k in saved:
            out.append(("SAVED", saved[k]))
            return
        for kid in node[1]:
            walk(kid)
        out.append(("LABEL", node[0]))
        if k in shared:
            out.append(("Z", 0))
            saved[k] = len(saved)

    walk(tree)

    # The bloc is assigned during the walk, so its size is only known now.
    # Saved-step indices sit above the whole bloc and have to be resolved
    # afterwards.
    pieces = []
    for kind, val in out:
        if kind == "Z":
            pieces.append("Z")
        elif kind == "LABEL":
            pieces.append(encode_int(idx_for(val)))
        else:
            pieces.append(("S", val))
    base = n_hyp + len(bloc)
    text = "".join(p if isinstance(p, str) else encode_int(base + p[1])
                   for p in pieces)
    return bloc, text


def render(bloc: list[str], text: str, indent: int = 6,
           width: int = 79) -> str:
    """Lay the proof out the way set.mm wraps it."""
    room = width - indent
    lines, cur = [], "( "
    for lab in bloc:
        # the closing ")" has to fit on the last line too, so reserve for it
        if len(cur) + len(lab) + 1 > room:
            lines.append(cur.rstrip())
            cur = ""
        cur += lab + " "
    cur += ")"
    lines.append(cur)
    body = " " + text
    first = room - len(lines[-1])
    lines[-1] += body[:first]
    rest = body[first:]
    for i in range(0, len(rest), room):
        lines.append(rest[i:i + room])
    # The caller appends " $." to the last line, so it needs three characters
    # the chunking never reserved. Spill them rather than run over.
    if indent + len(lines[-1]) + 3 > width:
        keep = width - indent - 3
        lines.append(lines[-1][keep:])
        lines[-2] = lines[-2][:keep]
    pad = " " * indent
    return "\n".join(pad + ln for ln in lines)


# ------------------------------------------------------------------ selftest
def selftest(db: Database, n: int) -> int:
    """Recompress set.mm's own proofs and compare to what it stores.

    A proof that merely verifies proves nothing about the encoder -- many
    encodings verify. Reproducing the stored bytes does.
    """
    import re
    ok = bad = skip = 0
    shown = 0
    # mmverify keeps only (dv, floating, essential, conclusion) per label and
    # throws the proof away after reading, so the proofs come from the source.
    src = Path(db.path).read_text(encoding="utf-8", errors="replace")
    pat = re.compile(r"(?m)^[ \t]*(\S+)[ \t]+\$p\s(.*?)\$=(.*?)\$\.", re.S)
    for m in pat.finditer(src):
        if ok + bad >= n:
            break
        lab = m.group(1)
        if lab not in db.mm.labels or db.mm.labels[lab][0] != "$p":
            continue
        dv, mand, ess, concl = db.mm.labels[lab][1]
        proof = m.group(3).split()
        if not proof or proof[0] != "(":
            skip += 1
            continue
        idx = proof.index(")")
        orig_bloc = proof[1:idx]
        orig_text = "".join(proof[idx + 1:])
        try:
            flat = _decompress(db, mand, ess, proof, lab)
            bloc, text = compress(db, lab, flat, frame=(dv, mand, ess, concl))
        except Exception as e:
            bad += 1
            if shown < 5:
                print(f"  {lab}: {type(e).__name__}: {e}")
                shown += 1
            continue
        if bloc == orig_bloc and text == orig_text:
            ok += 1
        else:
            bad += 1
            if shown < 5:
                print(f"  {lab}: mismatch")
                print(f"    stored {len(orig_text)} chars, {len(orig_bloc)} labels")
                print(f"    ours   {len(text)} chars, {len(bloc)} labels")
                shown += 1
    print(f"\n{ok} reproduced exactly, {bad} differ, {skip} not compressed")
    return bad


def _fmap(db: Database) -> dict:
    """(typecode, variable) -> its $f label, preferring the global one.

    mmverify mangles block-local floating hypotheses with a dot, so a variable
    can carry several labels; a top-level proof wants the undotted one.
    """
    if getattr(db, "_fm", None) is None:
        out = {}
        for lab, (kind, val) in db.mm.labels.items():
            if kind == "$f":
                k = (val[0], val[1])
                if k not in out or ("." in out[k] and "." not in lab):
                    out[k] = lab
        db._fm = out
    return db._fm


def _elabels(db: Database) -> dict:
    """theorem label -> its essential-hypothesis labels, in scope order.

    mmverify pops each frame as it leaves the block, so by the time reading
    finishes the essential labels are gone. Every active $e is mandatory, so
    a scope scan of the source recovers them exactly.
    """
    if getattr(db, "_el", None) is None:
        import re
        text = Path(db.path).read_text(encoding="utf-8", errors="replace")
        text = re.sub(r"\$\(.*?\$\)", " ", text, flags=re.S)
        tok = re.compile(r"\$\{|\$\}|(\S+)[ \t\r\n]+\$([ep])")
        scopes, out = [[]], {}
        for m in tok.finditer(text):
            s = m.group(0)
            if s == "${":
                scopes.append([])
            elif s == "$}":
                scopes.pop()
            elif m.group(2) == "e":
                scopes[-1].append(m.group(1))
            else:
                out[m.group(1)] = [x for sc in scopes for x in sc]
        db._el = out
    return db._el


def _hyp_labels(db: Database, lab: str, mand) -> list[str]:
    fm = _fmap(db)
    return ([fm[(tc, v)] for tc, v in mand]
            + _elabels(db).get(lab, []))


def _decompress(db: Database, mand, ess, proof, lab) -> list[str]:
    """Compressed proof -> flat reverse-Polish label list."""
    hyp = _hyp_labels(db, lab, mand)
    idx = proof.index(")")
    plabels = hyp + list(proof[1:idx])
    ints = decode("".join(proof[idx + 1:]))
    end = len(plabels)
    stack: list[list[str]] = []
    saved: list[list[str]] = []
    for i in ints:
        if i == -1:
            saved.append(stack[-1])
        elif i < end:
            lab = plabels[i]
            n = arity(db, lab)
            if n:
                stack, kids = stack[:-n], stack[-n:]
                stack.append([t for k in kids for t in k] + [lab])
            else:
                stack.append([lab])
        else:
            stack.append(list(saved[i - end]))
    return stack[0]


def _cli() -> None:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--database", default=str(HERE.parent / "vendor" / "set.mm"))
    ap.add_argument("--selftest", type=int, metavar="N")
    a = ap.parse_args()
    db = Database(a.database)
    if a.selftest:
        sys.exit(1 if selftest(db, a.selftest) else 0)
    ap.error("nothing to do; pass --selftest N")


if __name__ == "__main__":
    _cli()
