#!/usr/bin/env python3
r"""The general-domination defect class in set.mm, and what repairing it is worth.

    python analysis/domination_class.py vendor/set.mm

Three lemmas in set.mm state that an image is dominated by its domain:

    fodomg     ( B e. C -> ( F : A -onto-> B -> B ~<_ A ) )
    fnrndomg   ( A e. B -> ( F Fn A -> ran F ~<_ A ) )
    imadomg    ( A e. B -> ( Fun F -> ( F " A ) ~<_ A ) )

Each is correct and each requires choice as stated, because selecting a preimage
per element of the image is exactly what choice provides. Each also has a
choice-free specialisation for well-orderable domains: `fodomnum` is already in
the library, `fodomfi` and `imafi` cover the finite case, and `numdom` with
`cardom` supplies `A e. dom card` from `A ~<_ _om`.

Callers holding a finiteness or countability hypothesis and reaching for the
general lemma anyway are repairable. This script enumerates the callers,
separates those from the ones whose domain is genuinely arbitrary, and severs
the repairable edges to measure what the class is worth.

The severing is the number. A dominator subtree over-reports where subtrees nest
and under-reports where independent routes compound; only the counterfactual
says how many theorems actually leave the cone.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))
import necessity as N  # noqa: E402
from mmapi import Database  # noqa: E402

AXIOM = ["ax-ac", "ax-ac2"]
GENERAL = {"fodomg", "fnrndomg", "imadomg"}

# Classification is by reading each caller's hypotheses, so it is recorded here
# as data with its reason rather than inferred. The mechanical test that would
# replace it -- do the caller's hypotheses entail `A e. dom card` -- is
# decidable in the library's own logic and is not implemented.
ELIGIBLE = {
    "disjinfi":    "its own hypothesis proves the domain finite",
    "madefi":      "( _Made ` A ) is finite for A e. _om",
    "omeiunle":    "indexes over Z = ( ZZ>= ` N )",
    "subsaliuncl": "indexes over NN",
    "fnct":        "hypothesis A ~<_ _om",
    "dmct":        "hypothesis A ~<_ _om",
    "fimact":      "hypothesis A ~<_ _om",
    "ffsrn":       "concludes ran F e. Fin from finite support",
    "smflimlem6":  "indexes over Z = ( ZZ>= ` M )",
}
REPAIRED = {"disjinfi", "madefi", "omeiunle", "subsaliuncl"}
GENERAL_BY_DESIGN = {
    "fodom", "fodomb", "abrexdom", "abrexdomjm", "indexdom",
    "konigthlem", "uniimadom", "unirnfdomd", "hausmapdom",
}


def sever(kind, refs, callers):
    """Callers switch to the well-orderable-domain specialisation.

    The general lemmas keep their own proofs and their own dependence: they are
    correct as stated and are not what is being repaired.
    """
    r2 = dict(refs)
    for c in callers:
        r2[c] = [x for x in refs.get(c, ()) if x not in GENERAL]
    return N.analyse(kind, r2, AXIOM)["reach"]


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("database")
    a = ap.parse_args()

    path = Path(a.database)
    kind, refs = N.parse(path)
    db = Database(path)
    base = N.analyse(kind, refs, AXIOM)["reach"]
    print(f"{a.database}: {len(base)} theorems reach {'/'.join(AXIOM)}\n")

    callers = sorted(x for x, v in refs.items()
                     if GENERAL & set(v) and kind.get(x) == "p")
    print(f"{len(callers)} direct callers of {', '.join(sorted(GENERAL))}\n")
    print(f"{'caller':<14} {'calls':<22} {'class':<24} reason / statement")
    print("-" * 112)
    for c in callers:
        which = ",".join(sorted(GENERAL & set(refs[c])))
        if c in GENERAL:
            cls, why = "the general lemma", "correct as stated"
        elif c in ELIGIBLE:
            cls = "REPAIRED" if c in REPAIRED else "ELIGIBLE, open"
            why = ELIGIBLE[c]
        elif c in GENERAL_BY_DESIGN:
            cls, why = "general by design", "domain is an arbitrary set"
        else:
            cls, why = "UNCLASSIFIED", " ".join(db.frame(c)[3])[:56]
        print(f"{c:<14} {which:<22} {cls:<24} {why}")

    unknown = [c for c in callers if c not in ELIGIBLE
               and c not in GENERAL_BY_DESIGN and c not in GENERAL]
    if unknown:
        print(f"\n!! {len(unknown)} callers not classified: {unknown}")
        print("   the database has moved; reclassify before quoting any figure below")

    print(f"\n{'counterfactual':<44} {'still reach':>11} {'freed':>7}")
    print("-" * 66)
    everyone = [c for c in callers if c not in GENERAL]
    for name, cs in (
            ("present state", []),
            (f"all {len(everyone)} callers switch (upper bound)", everyone),
            (f"the {len(REPAIRED)} already repaired", sorted(REPAIRED)),
            ("the open eligible callers", sorted(set(ELIGIBLE) - REPAIRED)),
            (f"all {len(ELIGIBLE)} eligible callers", sorted(ELIGIBLE)),
    ):
        r = sever(kind, refs, cs)
        print(f"{name:<44} {len(r):>11} {len(base) - len(r):>7}")

    ub = len(base) - len(sever(kind, refs, everyone))
    got = len(base) - len(sever(kind, refs, sorted(ELIGIBLE)))
    print("-" * 66)
    print(f"achievable {got} of {ub}; residual {ub - got} sits behind callers whose "
          f"domain is arbitrary")
    print(f"{got / len(base):.1%} of the {'/'.join(AXIOM)} cone, from "
          f"{len(ELIGIBLE)} rewritten proof steps")

    done = sever(kind, refs, sorted(REPAIRED))
    both = sever(kind, refs, sorted(ELIGIBLE))
    marginal = sorted(done - both)
    print(f"\nmarginal prize of the open callers, on top of the repaired ones: "
          f"{len(marginal)}")
    for i in range(0, len(marginal), 4):
        print("   " + "  ".join(f"{x:<22}" for x in marginal[i:i + 4]))


if __name__ == "__main__":
    main()
