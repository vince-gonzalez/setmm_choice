#!/usr/bin/env python3
r"""Census every `$j usage 'X' avoids 'A';` directive in a Metamath database.

    python analysis/guard_census.py vendor/set.mm

A guard directive is a contributor's machine-checked record that a named
theorem's proof does not reach a named axiom. The library verifies them, so
they are assertions about the proof and not comments about intent.

Counting them gives the **guard ratio** -- guarded theorems over the size of the
axiom's dependency cone -- which is how much of a seam previous contributors
have already removed. `ax-13` sits at 0.751 and yields nothing to a newcomer;
`ax-cc` sits at 0.003 and also yields nothing, for the opposite reason (its
uses are genuine). The ratio bounds the work already done, not the work left.

Reach is measured over the closed set of equivalent packagings. `ax-ac` alone
reaches 9 statements and `ax-ac` with `ax-ac2` reaches 546; a survey quoting the
former has measured a label rather than an axiom.
"""
from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))
import necessity as N  # noqa: E402

# Axioms set.mm carries in more than one packaging, with one derived from the
# other. Measuring either alone undercounts the cone.
PACKAGINGS = {
    "ax-ac": ["ax-ac", "ax-ac2"],
    "ax-ac2": ["ax-ac", "ax-ac2"],
    "ax-inf": ["ax-inf", "ax-inf2"],
    "ax-inf2": ["ax-inf", "ax-inf2"],
}

GUARD = re.compile(r"\$j\s+usage\s+'([^']+)'\s+avoids([^;]*);")


def census(text: str):
    """-> (pairs, guarded_by_axiom) where guarded_by_axiom[ax] is a set of labels."""
    pairs = 0
    guarded = defaultdict(set)
    for m in GUARD.finditer(text):
        who = m.group(1)
        for ax in re.findall(r"'([^']+)'", m.group(2)):
            pairs += 1
            guarded[ax].add(who)
    return pairs, guarded


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("database")
    ap.add_argument("--top", type=int, default=16)
    ap.add_argument("--csv")
    ap.add_argument("--all", action="store_true",
                    help="measure reach for every guarded axiom, not just --top")
    a = ap.parse_args()

    path = Path(a.database)
    text = path.read_text(encoding="utf-8", errors="replace")
    pairs, guarded = census(text)
    kind, refs = N.parse(path)

    proved = sum(1 for v in kind.values() if v == "p")
    axiomatic = sum(1 for v in kind.values() if v == "a")
    everyone = {w for s in guarded.values() for w in s}
    print(f"{a.database}: {proved:,} proved, {axiomatic:,} axiomatic")
    print(f"{pairs} axiom-guard pairs over {len(everyone)} distinct theorems\n")

    # One reach analysis per axiom is a full traversal of a 47k-node graph, and
    # there are over a hundred guarded axioms. Only the ones being reported get
    # measured; --all overrides when the full table is wanted.
    ranked = sorted(guarded.items(), key=lambda kv: -len(kv[1]))
    measure = ranked if a.all else ranked[:a.top]
    rows = []
    for ax, who in ranked:
        pack = PACKAGINGS.get(ax, [ax])
        if ax in {k for k, _ in measure}:
            try:
                reach = len(N.analyse(kind, refs, pack)["reach"])
            except Exception:
                reach = 0
        else:
            reach = None
        # guards on any packaging count toward the shared cone
        g = set().union(*(guarded.get(p, set()) for p in pack))
        ratio = (len(g) / reach) if reach else (float("nan") if reach == 0 else None)
        rows.append((len(who), ax, "/".join(pack), reach, len(g), ratio))

    print(f"{'axiom':<12} {'guards':>7} {'reach':>8} {'guarded':>8} {'ratio':>7}  read")
    print("-" * 74)
    for n, ax, pack, reach, g, ratio in rows[:a.top]:
        if reach is None:
            print(f"{ax:<12} {n:>7} {'-':>8} {g:>8} {'-':>7}  not measured")
            continue
        if reach == 0:
            read = "no cone under this label alone"
        elif ratio > 0.5:
            read = "mined out"
        elif ratio > 0.05:
            read = "partially worked"
        else:
            read = "little recorded avoidance"
        print(f"{ax:<12} {n:>7} {reach:>8} {g:>8} {ratio:>7.3f}  {read}")

    if a.csv:
        import csv
        with open(a.csv, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["axiom", "packaging", "guard_directives",
                        "reach", "guarded_theorems", "guard_ratio"])
            for n, ax, pack, reach, g, ratio in rows:
                w.writerow([ax, pack, n, "" if reach is None else reach, g,
                            "" if ratio is None else f"{ratio:.4f}"])
        print(f"\nfull table -> {a.csv}")


if __name__ == "__main__":
    main()
