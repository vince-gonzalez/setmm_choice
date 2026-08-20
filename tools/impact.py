#!/usr/bin/env python3
r"""Rank every axiom-dependent theorem by how much removing it would free.

    python tools/impact.py vendor/set.mm --axiom ax-ac ax-ac2

`sibling_asymmetry.py` says where to look. It does not say what a find is
worth, and that turned out to be the number that mattered: `difelsiga` has 64
theorems below it but freeing it freed 36, because the other 28 reach choice
by another route as well. Counting what sits below a theorem overstates the
prize every time there is more than one path.

What actually gets freed by fixing T is the set of theorems whose *every*
route to the axiom passes through T. That is the dominator relation on the
proof DAG, rooted at the axiom, so it is one traversal rather than one
re-analysis per candidate -- 546 closure recomputations collapse to a single
dominator tree.

Output is the ranked list: for each dependent theorem, how many theorems it
alone is responsible for, and whether the library already proves a sibling of
it without the axiom.
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import necessity as N  # noqa: E402

ROOT = "\x00root"


def dominators(succ, root, order):
    """Cooper-Harvey-Kennedy iterative dominators.

    `succ[x]` are the nodes x can reach in one step; `order` is a reverse
    postorder from `root`. Returns idom, the immediate dominator of each node.
    """
    pred = defaultdict(list)
    for u in succ:
        for v in succ[u]:
            pred[v].append(u)
    rpo = {n: i for i, n in enumerate(order)}
    idom = {root: root}

    def isect(a, b):
        while a is not b:
            while rpo[a] > rpo[b]:
                a = idom[a]
            while rpo[b] > rpo[a]:
                b = idom[b]
        return a

    changed = True
    while changed:
        changed = False
        for n in order:
            if n == root:
                continue
            new = None
            for p in pred[n]:
                if p in idom:
                    new = p if new is None else isect(p, new)
            if new is not None and idom.get(n) is not new:
                idom[n] = new
                changed = True
    return idom


def family_index(labels):
    """Group labels by shared suffix, the way set.mm names families.

    `unelsiga` / `inelsiga` / `difelsiga` share `elsiga`. Suffixes of length 4
    and up, kept only where at least three distinct labels agree, which is
    enough to separate a real family from a coincidence of spelling.
    """
    # `lem1`, `lem2`, `ALT`, `OLD` are numbering and variant conventions, not
    # family membership. Left in, they match `ax13lem1` against `aaliou3lem1`
    # and `baerlem3lem1`, which share nothing but a counter.
    def stem(lab):
        s = re.sub(r"(?:ALT|OLD|VD)$", "", lab)
        return re.sub(r"(?:lem)?\d*$", "", s) or lab

    groups = defaultdict(set)
    for lab in labels:
        s = stem(lab)
        if len(s) < 4:
            continue
        for k in range(4, min(len(s), 13)):
            groups[s[-k:]].add(lab)
    fam = {}
    for suf, members in groups.items():
        if len(members) < 3:
            continue
        for m in members:
            # keep the most specific (longest) suffix that still has a family
            if m not in fam or len(suf) > len(fam[m][0]):
                fam[m] = (suf, members)
    return fam


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("database")
    ap.add_argument("--axiom", nargs="+", required=True)
    ap.add_argument("--top", type=int, default=40)
    ap.add_argument("--min-freed", type=int, default=2)
    ap.add_argument("--csv")
    a = ap.parse_args()

    kind, refs = N.parse(Path(a.database))
    res = N.analyse(kind, refs, a.axiom)
    reach = res["reach"]
    axioms = set(a.axiom)
    print(f"{a.database}: {sum(1 for v in kind.values() if v == 'p'):,} proved")
    print(f"reaching {'/'.join(a.axiom)}: {len(reach)}\n")

    # Reverse edges, so the axiom is the root and "dominates" means
    # "everything below here needs it".
    succ = defaultdict(set)
    nodes = reach | axioms
    for t in reach:
        for r in refs.get(t, ()):
            if r in nodes:
                succ[r].add(t)          # r is used BY t -> reversed edge
    for ax in axioms:
        succ[ROOT].add(ax)

    # reverse postorder from ROOT
    seen, order, stack = set(), [], [(ROOT, iter(sorted(succ[ROOT])))]
    seen.add(ROOT)
    while stack:
        node, it = stack[-1]
        adv = next(it, None)
        if adv is None:
            order.append(node)
            stack.pop()
        elif adv not in seen:
            seen.add(adv)
            stack.append((adv, iter(sorted(succ.get(adv, ())))))
    order.reverse()

    idom = dominators(succ, ROOT, order)

    # subtree size in the dominator tree = theorems freed by fixing this node
    kids = defaultdict(list)
    for n, d in idom.items():
        if n != d:
            kids[d].append(n)
    size = {}

    def subtree(n):
        if n in size:
            return size[n]
        s = 1
        for c in kids[n]:
            s += subtree(c)
        size[n] = s
        return s

    for n in order:
        subtree(n)

    fam = family_index([t for t in kind if kind[t] == "p"])
    rows = []
    for t in reach:
        if t in axioms:
            continue
        freed = size.get(t, 1)
        if freed < a.min_freed:
            continue
        suf, members = fam.get(t, (None, set()))
        clean = sorted(m for m in members if m not in reach and m != t)
        rows.append((freed, t, suf, clean))
    rows.sort(key=lambda r: (-r[0], r[1]))

    print(f"{'freed':>6}  {'theorem':<18} {'family':<12} choice-free siblings")
    print("-" * 78)
    for freed, t, suf, clean in rows[:a.top]:
        sib = ", ".join(clean[:4]) + ("  +%d" % (len(clean) - 4) if len(clean) > 4 else "")
        print(f"{freed:>6}  {t:<18} {(suf or '-'):<12} {sib or '(none -- whole family pays)'}")

    split = [r for r in rows if r[3]]
    print(f"\n{len(rows)} theorems free 2 or more; {len(split)} of them have a "
          f"choice-free sibling")
    if a.csv:
        import csv
        with open(a.csv, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["freed", "theorem", "family_suffix", "choice_free_siblings"])
            for freed, t, suf, clean in rows:
                w.writerow([freed, t, suf or "", " ".join(clean)])
        print(f"full table -> {a.csv}")


if __name__ == "__main__":
    main()
