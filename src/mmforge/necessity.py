#!/usr/bin/env python3
r"""necessity -- where a Metamath library could stop depending on an axiom.

    python tools/necessity.py vendor/set.mm --axiom ax-ac ax-ac2
    python tools/necessity.py vendor/set.mm --axiom ax-inf --json out.json
    python tools/necessity.py vendor/set.mm --axiom ax-ac ax-ac2 --trace bayesth

Provenance tools answer "what does this theorem rest on". This answers the
next question: given that it rests on an axiom, where is the one place that
could change?

A theorem that reaches an axiom through several independent routes cannot be
freed by fixing any one of them. A theorem that reaches it through exactly one
step has a single point of attack, and that step is worth reading. Ranking
those steps by how much sits below them turns a list of 583 dependent theorems
into a handful of places to look.

The library is read directly. Direct references come from each proof's own
label list, so no verification pass and no external index is required, and the
same code runs against set.mm, iset.mm, nf.mm, ql.mm or hol.mm.

WHAT IT DOES NOT DO
    Nothing here shows a dependence is removable. A single gateway is a
    candidate for inspection, not a defect. Real dependence looks identical to
    accidental dependence from the graph alone -- `zartopon` in set.mm reaches
    choice through Krull's theorem, which genuinely needs it -- and telling
    them apart is mathematics, not graph theory.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict, deque
from pathlib import Path

STMT = re.compile(r"(?ms)^[ \t]*(\S+)[ \t]+\$([pa])\s(.*?)\$\.")
COMMENT = re.compile(r"\$\([^$]*(?:\$(?!\))[^$]*)*\$\)")


def parse(path: Path):
    """Return (kind, refs) where kind maps label -> 'p'/'a' and refs maps a
    proved label to the labels its proof cites."""
    text = COMMENT.sub(" ", path.read_text(encoding="utf-8", errors="replace"))
    kind, refs = {}, {}
    for m in STMT.finditer(text):
        label, k, body = m.group(1), m.group(2), m.group(3)
        kind[label] = k
        if k != "p":
            continue
        i = body.find("$=")
        if i < 0:
            refs[label] = []
            continue
        proof = body[i + 2:]
        c = re.match(r"\s*\((.*?)\)", proof, re.S)
        # compressed proofs name every label they use inside parentheses;
        # uncompressed ones are a bare sequence of labels
        toks = (c.group(1) if c else proof).split()
        refs[label] = [t for t in toks if t in kind or not c]
    return kind, refs


def closure(kind, refs, axioms):
    """Which proved statements transitively reach any of `axioms`."""
    target = set(axioms)
    reaches, order, temp = {}, [], set()

    def visit(lab):
        if lab in reaches:
            return reaches[lab]
        if lab in temp:                      # defensive; set.mm is acyclic
            return False
        temp.add(lab)
        got = False
        for r in refs.get(lab, ()):
            if r in target or (kind.get(r) == "p" and visit(r)):
                got = True
        temp.discard(lab)
        reaches[lab] = got
        return got

    sys.setrecursionlimit(100000)
    for lab in refs:
        visit(lab)
    return {l for l, v in reaches.items() if v}


def analyse(kind, refs, axioms):
    reach = closure(kind, refs, axioms)
    spenders = sorted(t for t in reach
                      if any(r in axioms for r in refs.get(t, ())))
    single, multi = {}, []
    for t in reach:
        if t in spenders:
            continue
        carriers = sorted({r for r in refs.get(t, ())
                           if r in reach or r in axioms})
        if len(carriers) == 1:
            single[t] = carriers[0]
        elif carriers:
            multi.append(t)

    users = defaultdict(set)
    for t in reach:
        for r in refs.get(t, ()):
            if r in reach:
                users[r].add(t)

    def below(x):
        seen, q = set(), deque([x])
        while q:
            for u in users.get(q.popleft(), ()):
                if u not in seen:
                    seen.add(u)
                    q.append(u)
        return seen

    gates = defaultdict(int)
    for g in single.values():
        gates[g] += 1
    ranked = sorted(gates.items(), key=lambda kv: -len(below(kv[0])))
    return dict(reach=reach, spenders=spenders, single=single, multi=multi,
                gates=gates, ranked=ranked, below=below)


def trace(refs, reach, start, out=print):
    t, depth, seen = start, 0, set()
    while True:
        car = sorted({r for r in refs.get(t, ()) if r in reach})
        out("   " + "  " * depth + f"{t} -> " +
            (", ".join(car) if car else "(the axiom enters here)"))
        if not car or len(car) != 1 or t in seen:
            if car and len(car) > 1:
                out("   " + "  " * depth + "  (branches; no single route)")
            return
        seen.add(t)
        t, depth = car[0], depth + 1


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("database")
    ap.add_argument("--axiom", nargs="+", required=True)
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--trace", nargs="*", default=[])
    ap.add_argument("--json")
    a = ap.parse_args()

    path = Path(a.database)
    # A Metamath library changes daily -- set.mm took commits on the day this
    # was written -- so a count without the database it came from is not
    # reproducible. Fingerprint what was actually read.
    import hashlib
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    kind, refs = parse(path)
    proved = sum(1 for k in kind.values() if k == "p")
    missing = [x for x in a.axiom if x not in kind]
    if missing:
        sys.exit(f"not in {path.name}: {', '.join(missing)}")

    r = analyse(kind, refs, set(a.axiom))
    reach, single = r["reach"], r["single"]
    print(f"{path.name}: {proved:,} proved statements, {len(kind):,} labels")
    print(f"sha256 {digest}")
    print(f"  ({len(raw):,} bytes -- quote this with any figure below)")
    print(f"axiom(s): {', '.join(a.axiom)}")
    print()
    print(f"  reach it            {len(reach):,}  ({len(reach)/proved:.2%})")
    print(f"  invoke it directly  {len(r['spenders']):,}"
          f"   {', '.join(r['spenders'][:8])}")
    print(f"  via a single step   {len(single):,}"
          f"  ({len(single)/max(1,len(reach)):.0%} of those reaching)")
    print(f"  via several         {len(r['multi']):,}")
    print()
    print(f"  {'gateway':<20}{'sole route for':>15}{'total below':>13}")
    for g, n in r["ranked"][:a.top]:
        print(f"  {g:<20}{n:>15}{len(r['below'](g)):>13}")

    for t in a.trace:
        print()
        print(f"trace {t}:")
        if t not in reach:
            print("   does not reach the axiom")
            continue
        trace(refs, reach, t)

    if a.json:
        Path(a.json).write_text(json.dumps({
            "database": path.name, "sha256": digest,
            "bytes": len(raw), "axioms": a.axiom,
            "proved": proved, "reach": sorted(reach),
            "spenders": r["spenders"],
            "single_gateway": single,
            "gateways": [{"gateway": g, "sole_route_for": n,
                          "total_below": len(r["below"](g))}
                         for g, n in r["ranked"]],
        }, indent=1), encoding="utf-8")
        print(f"\nwrote {a.json}")


if __name__ == "__main__":
    main()
