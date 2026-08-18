# Where set.mm spends the axiom of choice

set.mm is a formalisation of mathematics in Metamath, 47,621 theorems deep.
583 of them reach the axiom of choice. **Three invoke it.** Everything else
inherits, and 418 of the 583 inherit through exactly one step — which means
each of those has a single place where the dependence could be removed.

This repository is the study of those single places, and an attempt to remove
one of them.

It is the Metamath arm of **[gonzalgo](https://github.com/zengineco/gonzalgo)**,
an axiom-provenance toolkit for Lean 4 and Metamath: which step of a proof
introduced an axiom, and whether the statement being proved required it.
gonzalgo produced the measurements; the scripts here act on one of them.

## The finding

Choice enters set.mm at `ac2`, `axac3` and `zfac`. From there it fans out.
Counting theorems downstream of each node on the main chain:

| node | choice-reaching theorems below it |
|---|---|
| `axac3` | 573 |
| `cardeqv` | 550 |
| `numth3` | 541 |
| `fodomg` | 362 |
| `fnrndomg` | 303 |
| `abrexdomjm` | 68 |
| `abrexdom2jm` | 67 |
| `sigaclci` | 66 |
| `difelsiga` | 64 |

The lower half of that table is measure theory, and it has no business being
there. `difelsiga` says a sigma-algebra is closed under set difference. Below
it sit 64 results including **`bayesth` — Bayes' theorem** — along with
`boolesineq`, the `cndprob*` conditional-probability family, and the `dstfrv*`
discrete random variables.

## The bottleneck

`difelsiga` is one instance of a much narrower pattern. Following the chain up:

| lemma | choice-reaching theorems below it | what it says |
|---|---|---|
| `numth3` | 541 | every set can be well-ordered |
| `fodomg` | 362 | a surjection onto `B` gives `B ≼ A` |
| `fnrndomg` | **303 (52%)** | the range of a function is dominated by its domain |

`numth3` is the well-ordering theorem and is equivalent to choice; nothing to
be done there. `fnrndomg` is different. In full generality it does need choice
— picking a preimage for each element of the range is exactly a choice function
— but it is repeatedly applied to functions that are given explicitly, where an
injection can be written down without choosing anything.

Downstream of it: `bayesth`, `boolesineq`, `borelmbl`, `carageniuncl`,
`algextdeg`, `2sqr3nconstr`, `aean`. Measure theory, Borel sets, field
extension degree, and the constructibility results that prove an angle cannot
be trisected.

**Nothing here shows any individual use is avoidable.** The claim is
structural: the dependence is concentrated at one lemma, and that lemma's
general form is stronger than most of its uses require.

## necessity — the tool

`tools/necessity.py` generalises all of the above to any axiom in any Metamath
database. It reads the `.mm` directly, needs no precomputed index and no
verification pass, and finishes in about two seconds on a 51 MB library.

    python tools/necessity.py vendor/set.mm --axiom ax-ac ax-ac2
    python tools/necessity.py vendor/set.mm --axiom ax-pow --json out.json
    python tools/necessity.py vendor/iset.mm --axiom ax-pow --trace bayesth

Provenance tools answer *what does this theorem rest on*. This answers the next
question: *given that it rests on an axiom, where is the one place that could
change?*

Run across four axioms of set.mm, the shape of the dependence differs enough to
be the point:

| axiom | reaching it | via a single step |
|---|---|---|
| `ax-inf` infinity | 6 (0.01%) | 83% |
| `ax-reg` regularity | 517 (1.08%) | 76% |
| `ax-ac` choice | 582 (1.22%) | 72% |
| `ax-pow` power set | 29,608 (62.13%) | 26% |

Power set is woven through the library: most of it, and three quarters of those
theorems reach it by several independent routes, so no single change frees
them. Choice and regularity are the opposite — rare, and entering at a handful
of points. **That distinction is what makes one axiom auditable and another
not**, and it falls out of the reference graph without any mathematics.

The same run against `iset.mm`, the intuitionistic database, gives 64.44% and
27% for `ax-pow` — the same shape under a different foundation.

**What it does not do.** It never claims a dependence is removable. A single
gateway is a place to look. Real and accidental dependence are indistinguishable
from the graph: `zartopon` reaches choice through Krull's theorem and genuinely
needs it. Telling those apart is mathematics.

## A detector for the same pattern

`tools/sibling_asymmetry.py` looks for theorems that pay for choice while
near-identical siblings do not — the observation that first found `difelsiga`,
where pairwise union is choice-free and pairwise intersection and difference
are not. 114 theorems are in a split family and reach choice through a single
step.

It reports legitimate dependence too, which is the point. `zartopon` — the
Zariski topology is a topology — routes through `ssmxidl`, every proper ideal
lies in a maximal ideal. That is Krull's theorem and it genuinely needs choice.
A detector that only ever says yes would be worthless.

## Why it happens

A sigma-algebra over `O` is closed under complement by definition (`issiga`),
and `unelsiga` gives closure under pairwise union without touching choice.

But `difelsiga` is not proved that way. It builds the pair `{A, O∖B}`, proves
the pair countable and nonempty, and applies `sigaclci` — closure under
*countable* intersection. `sigaclci` establishes its countability side-condition
through `abrexdom2jm`, "an indexed set is dominated by the indexing set", and
that is a genuine use of choice.

A binary operation is being proved through countable machinery, and the
countable machinery is what costs the axiom.

The asymmetry is visible in the library itself: pairwise **union** is
choice-free, pairwise **intersection** and **difference** are not.

## The proposed proof

    1. A ⊆ O                              elsigass
    2. (O ∖ A) ∈ S                        complement (isrnsigau)
    3. ((O ∖ A) ∪ B) ∈ S                  unelsiga
    4. (O ∖ ((O ∖ A) ∪ B)) ∈ S            complement
    5. O ∖ ((O∖A) ∪ B) = (O ∖ (O∖A)) ∖ B  difun1
    6. (O ∖ (O∖A)) = A                    dfss4 with (1)
    7. ∴ (A ∖ B) ∈ S

No pair, no countability, no dominance. Every lemma it uses —  `unelsiga`,
`elsigass`, `isrnsigau`, `difun1`, `dfss4` — was checked against the closure
data and none reaches choice.

**This is a sketch. Nothing here has been through the verifier.** Until
`metamath` accepts a proof file, the claim is that a choice-free route appears
to exist, and no more than that.

## Status

- [x] necessity analysis over all 47,621 theorems
- [x] chain traced from `difelsiga` to `ax-ac2`
- [x] every ingredient of the proposed route confirmed choice-free
- [ ] proof written in Metamath
- [ ] proof verified
- [ ] the same treatment for `inelsiga` and the other 16

## Running it

    python tools/setmm_necessity.py analysis/closure.pkl

`closure.pkl` holds `clos` (theorem → axioms reached), `refs` (the proof DAG),
and the precomputed choice-reaching sets. Detect the choice axioms as *axioms
whose users all lie inside the choice-reaching set* — testing for "present in
every closure" returns nothing, because `ax-ac` and `ax-ac2` are alternatives
and no theorem uses both.

## mmapi — constructing proofs from code

Metamath has a verifier a program can call and a proof assistant it cannot.
mmj2 is a GUI: a person types into a worksheet and reads the result. It is
Java, it is from 2017, and its own issue tracker carries a thread titled
"mmj2 is difficult to install/compile/get running".

Nothing in the ecosystem lets a *program* say "here is the statement I want and
the lemma I think justifies it, give me the substitution and tell me what is
left". `tools/mmapi.py` does.

    from mmapi import Database
    db = Database("set.mm")
    sub = db.match("difun1",
        r"|- ( U. S \ ( ( U. S \ A ) u. B ) ) = ( ( U. S \ ( U. S \ A ) ) \ B )")
    #  A := U. S      B := ( U. S \ A )      C := B
    db.hypotheses("eqeltrd", sub)   # what still has to be proved

The piece that makes it work is unification, and in Metamath that is
first-order matching over token sequences: a lemma's conclusion is a template
whose variables stand for runs of tokens, and matching it against a goal is a
parse with backtracking. `set` variables bind to one token, `wff` and `class`
variables to a run. Everything downstream — pushing hypotheses in frame order,
emitting reverse Polish — follows from having the substitution.

No GUI, no Java, no install. Import it, call the CLI, or hand it to an agent.
