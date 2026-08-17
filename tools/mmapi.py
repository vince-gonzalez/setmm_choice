#!/usr/bin/env python3
r"""mmapi -- construct Metamath proofs from code.

Metamath has a verifier you can call and a proof assistant you cannot. mmj2 is
a GUI: a human sits in front of it, types a worksheet, and reads the result. It
is Java, it is from 2017, and its own issue tracker carries a thread titled
"mmj2 is difficult to install/compile/get running".

Nothing in the ecosystem lets a *program* say "here is the statement I want and
the lemmas I think justify it, give me a proof". That is what this is.

    from mmapi import Database
    db = Database("set.mm")
    sub = db.match("unelsiga", "|- ( ( S e. U. ran sigAlgebra /\\ A e. S /\\ "
                              "B e. S ) -> ( A u. B ) e. S )")
    #  -> {'A': ['A'], 'B': ['B'], 'S': ['S']}

The piece that makes it possible is unification, and in Metamath that is
first-order matching over token sequences rather than anything higher-order: a
lemma's conclusion is a template whose variables stand for token runs, and
matching it against a goal is a parse. Everything else -- pushing hypotheses in
frame order, emitting reverse Polish -- is bookkeeping that follows from it.

No GUI, no Java, no install. Import it, or call the CLI, or hand it to an
agent.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "vendor"))
import mmverify  # noqa: E402

mmverify.verbosity = 0
mmverify.logfile = sys.stderr


class MatchFailure(Exception):
    """The goal is not an instance of the template."""


class Database:
    """A Metamath database, loaded once and queried many times."""

    def __init__(self, path):
        self.path = Path(path)
        self.mm = mmverify.MM(None, None)
        with open(self.path, "r", encoding="utf-8", errors="replace") as fh:
            self.mm.read(mmverify.Toks(fh))
        # variable -> its typecode, from the $f statements
        self.vartype = {}
        for lab, (kind, val) in self.mm.labels.items():
            if kind == "$f":
                tc, var = val[0], val[1]
                self.vartype[var] = tc

    # ------------------------------------------------------------------ info
    def frame(self, label):
        """(disjoint, mandatory hypotheses in push order, essentials, concl)."""
        kind, val = self.mm.labels[label]
        if kind not in ("$a", "$p"):
            raise KeyError(f"{label} is {kind}, not an assertion")
        return val

    def conclusion(self, label):
        return list(self.frame(label)[3])

    def is_var(self, tok):
        return tok in self.vartype

    # ------------------------------------------------------- the useful part
    def match(self, label, goal):
        """Unify a lemma's conclusion against `goal`.

        Returns {variable: [tokens]}. Raises MatchFailure if the goal is not an
        instance. Variables of type `set` bind to a single token; `wff` and
        `class` variables bind to runs, which is why this needs a search rather
        than a scan.
        """
        tmpl = self.conclusion(label)
        goal = goal.split() if isinstance(goal, str) else list(goal)
        out = {}
        if not self._match(tmpl, goal, out):
            raise MatchFailure(
                f"{label} does not match:\n  template {' '.join(tmpl)}"
                f"\n  goal     {' '.join(goal)}")
        return out

    def _match(self, tmpl, goal, sub, ti=0, gi=0):
        """Backtracking first-order match. Constants must line up exactly; a
        variable already bound must reproduce its binding; an unbound variable
        takes the shortest run that lets the rest succeed."""
        if ti == len(tmpl):
            return gi == len(goal)
        tok = tmpl[ti]
        if not self.is_var(tok):
            if gi < len(goal) and goal[gi] == tok:
                return self._match(tmpl, goal, sub, ti + 1, gi + 1)
            return False
        if tok in sub:
            n = len(sub[tok])
            if goal[gi:gi + n] == sub[tok]:
                return self._match(tmpl, goal, sub, ti + 1, gi + n)
            return False
        # `set` variables are single tokens; everything else may span a run
        spans = ([1] if self.vartype[tok] == "set"
                 else range(1, len(goal) - gi + 1))
        for n in spans:
            if gi + n > len(goal):
                break
            sub[tok] = goal[gi:gi + n]
            if self._match(tmpl, goal, sub, ti + 1, gi + n):
                return True
            del sub[tok]
        return False

    def instantiate(self, label, sub):
        """Apply a substitution to a lemma's conclusion."""
        out = []
        for tok in self.conclusion(label):
            out.extend(sub.get(tok, [tok]) if self.is_var(tok) else [tok])
        return out

    def hypotheses(self, label, sub):
        """The lemma's essential hypotheses under a substitution -- i.e. what
        still has to be proved to use it."""
        _dv, _mand, hyps, _c = self.frame(label)
        out = []
        for h in hyps:
            inst = []
            for tok in h:
                inst.extend(sub.get(tok, [tok]) if self.is_var(tok) else [tok])
            out.append(inst)
        return out


def _cli():
    import argparse
    ap = argparse.ArgumentParser(description="match a goal against a lemma")
    ap.add_argument("database")
    ap.add_argument("label")
    ap.add_argument("goal", nargs="+")
    a = ap.parse_args()
    db = Database(a.database)
    goal = " ".join(a.goal)
    print(f"template  {' '.join(db.conclusion(a.label))}")
    print(f"goal      {goal}")
    try:
        sub = db.match(a.label, goal)
    except MatchFailure as e:
        print()
        print(e)
        sys.exit(1)
    print()
    for v, toks in sorted(sub.items()):
        print(f"  {v:<6} := {' '.join(toks)}")
    hyps = db.hypotheses(a.label, sub)
    if hyps:
        print()
        print("  still to prove:")
        for h in hyps:
            print(f"    {' '.join(h)}")


if __name__ == "__main__":
    _cli()
