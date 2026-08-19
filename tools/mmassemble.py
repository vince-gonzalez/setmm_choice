#!/usr/bin/env python3
r"""Assemble a Metamath proof from a list of justified steps.

A step is a goal, the lemma that justifies it, and the earlier steps that
discharge that lemma's essential hypotheses:

    steps = [
      dict(goal="|- ( ph -> A C_ U. S )", by="elsigass", args=[0, 1]),
      ...
    ]

For each step the lemma is unified against the goal, which fixes every
variable. The mandatory hypotheses are then walked in the order the frame
demands: a floating hypothesis becomes the reverse-Polish construction of
whatever its variable bound to, an essential hypothesis becomes the proof of
the step supplied for it. The lemma's own label goes last.

That is the whole of proof assembly. The parts it stands on -- unification,
expression compilation, frame order -- are in mmapi.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from mmapi import Database, MatchFailure  # noqa: E402


class Step:
    __slots__ = ("goal", "by", "args", "rpn", "sub")

    def __init__(self, goal, by, args=()):
        self.goal = goal.split() if isinstance(goal, str) else list(goal)
        self.by = by
        self.args = list(args)
        self.rpn = None
        self.sub = None


def assemble(db: Database, steps: list[Step], verbose=False) -> list[str]:
    """Emit the reverse-Polish proof for the last step."""
    for i, st in enumerate(steps):
        _dv, mand, ess, _c = db.frame(st.by)
        concl = db.conclusion(st.by)

        # A conclusion can match a goal several ways, and the shortest binding
        # is often the wrong one: `eqbrtrid` concludes `( ph -> A R C )`, three
        # class variables in a row, so against `( F " A ) ~<_ ( A i^i dom F )`
        # the matcher will happily take A := `(`. Only the hypotheses reveal
        # which split was meant, so try the alternatives and keep the first
        # that lets every argument fit.
        #
        # Matching the conclusion also binds only the variables appearing in
        # it: syl2anc concludes ( ph -> th ) and leaves ps and ch to be fixed
        # by the arguments. Both concerns are handled by the same loop.
        st.sub = None
        failure = None
        for cand in db._matches(concl, st.goal):
            trial = dict(cand)
            for h, argi in zip(ess, st.args):
                if not db._match(list(h), steps[argi].goal, trial):
                    failure = (argi, h)
                    break
            else:
                st.sub = trial
                break
        if st.sub is None:
            if failure is None:
                raise MatchFailure(
                    f"step {i} ({st.by}) does not match:\n"
                    f"  template {' '.join(concl)}\n"
                    f"  goal     {' '.join(st.goal)}")
            argi, h = failure
            raise MatchFailure(
                f"step {i} ({st.by}): no reading of the conclusion lets "
                f"argument step {argi}\n    {' '.join(steps[argi].goal)}\n"
                f"  fit the hypothesis\n    {' '.join(h)}")
        # The verifier pops len(floating) + len(essential) and reads the
        # floating ones first, so a proof pushes every variable's construction
        # before any hypothesis proof. mmverify keeps the two in separate
        # lists; treating them as one interleaved list silently emits too few
        # and shows up as a stack underflow at the label.
        out = []
        for tc, var in mand:
            if var not in st.sub:
                raise MatchFailure(
                    f"step {i} ({st.by}): {var} is not fixed by the goal or "
                    f"by any argument")
            out.extend(db.build(st.sub[var], tc))
        if len(st.args) != len(ess):
            raise MatchFailure(
                f"step {i} ({st.by}) has {len(ess)} hypotheses but "
                f"{len(st.args)} argument(s)")
        for argi in st.args:
            out.extend(steps[argi].rpn)
        out.append(st.by)
        st.rpn = out
        if verbose:
            print(f"  step {i:>2} {st.by:<12} {len(out):>4} tokens  "
                  f"{' '.join(st.goal)[:64]}")
    return steps[-1].rpn


def emit(label: str, statement: str, rpn: list[str], dollar_d: str = "") -> str:
    """Render a $p statement with an uncompressed proof."""
    body = " ".join(rpn)
    d = f"    {dollar_d}\n" if dollar_d else ""
    # leading newline: splicing straight after a `$}` would otherwise produce
    # `$}${`, and Metamath tokens must be whitespace separated
    return (f"\n${{\n{d}  {label} $p {statement} $=\n"
            f"    {body} $.\n$}}\n")
