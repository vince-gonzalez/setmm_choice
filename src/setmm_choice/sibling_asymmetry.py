#!/usr/bin/env python3
"""Find theorems that pay for choice while a near-identical sibling does not.

    python tools/sibling_asymmetry.py analysis/closure.pkl

`difelsiga` was found by noticing an asymmetry: in the sigma-algebra family,
pairwise union is choice-free while pairwise intersection and set difference
are not. Three theorems about the same object, one costs an axiom and its
siblings do not. That is a smell, and it generalises.

set.mm labels are systematic -- `unelsiga`, `inelsiga`, `difelsiga` share the
stem `elsiga` -- so a family can be recovered from the labels themselves. This
looks for families that are split: some members choice-free, at least one not.
A split family means the library already contains a choice-free treatment of
the same subject, which is the strongest available hint that the dependent
member has one too.

It proves nothing. It produces a ranked list of places to look.
"""
from __future__ import annotations

import pickle
import re
import sys
from collections import defaultdict
from pathlib import Path

DEFAULT = Path(__file__).resolve().parent.parent / "analysis" / "closure.pkl"
path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
d = pickle.loads(path.read_bytes())
clos, refs, kind = d["clos"], d["refs"], d["kind"]
full = set(d["full"])

# Only proved statements; skip syntax and definitions.
theorems = [t for t in clos if kind.get(t) == "p"]
dep = [t for t in theorems if t in full]
free = set(t for t in theorems if t not in full)
print(f"proved statements: {len(theorems):,}")
print(f"  reach choice: {len(dep)}")

# Family = longest shared suffix stem of length >= 5. Suffix rather than prefix
# because set.mm names the subject last: unelsiga / inelsiga / difelsiga.
#
# Trailing lemma numbering has to come off first. `1arithufdlem1` and
# `1pthdlem1` share the suffix `dlem1` and are about nothing in common; that
# is Metamath's naming convention, not a family. Strip `lem<n>` / `<n>` from
# the end before taking stems.
LEMNUM = re.compile(r"(?:lem)?\d*$")


def stemify(label: str) -> str:
    s = LEMNUM.sub("", label)
    return s or label


by_suffix = defaultdict(set)
for t in theorems:
    s = stemify(t)
    for n in range(5, min(len(s), 12) + 1):
        by_suffix[s[-n:]].add(t)

rows = []
for t in dep:
    best = None
    for n in range(min(len(stemify(t)), 12), 4, -1):
        stem = stemify(t)[-n:] if len(stemify(t))>=n else None
        if not stem: continue
        fam = by_suffix.get(stem, set())
        sibs = sorted(s for s in fam if s != t and s in free)
        if len(sibs) >= 2:
            best = (stem, sibs)
            break
    if not best:
        continue
    stem, sibs = best
    carriers = sorted({r for r in refs.get(t, []) if r in full})
    rows.append({
        "thm": t, "stem": stem, "siblings": sibs,
        "gateways": carriers,
        "single": len(carriers) == 1,
    })

rows.sort(key=lambda r: (not r["single"], -len(r["siblings"])))
single = [r for r in rows if r["single"]]
print(f"  in a family with >=2 choice-free siblings: {len(rows)}")
print(f"  ...and reaching choice through exactly one step: {len(single)}")
print()
print("Ranked candidates -- one gateway, and the library already treats the")
print("same subject without choice:")
print()
for r in single[:24]:
    print(f"  {r['thm']:<18} stem -{r['stem']:<10} via {r['gateways'][0]}")
    print(f"      choice-free siblings: {', '.join(r['siblings'][:7])}"
          f"{' …' if len(r['siblings']) > 7 else ''}")
print()
byg = defaultdict(list)
for r in single:
    byg[r["gateways"][0]].append(r["thm"])
print("Gateways serving several split families at once -- fix one, several")
print("families stop paying:")
for g, ts in sorted(byg.items(), key=lambda kv: -len(kv[1]))[:10]:
    if len(ts) < 2:
        continue
    print(f"  {g:<16} {len(ts)} candidates: {', '.join(sorted(ts)[:8])}")
