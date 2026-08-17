# The proof, and what it needs

## Two theorems, not one

Searching all 45,927 proved statements in set.mm for anything asserting
`( U. S \ A ) e. S` returns **nothing**. A sigma-algebra is closed under
complement by definition, and the library has no lemma saying so. Every use
unfolds `isrnsigau` inline.

That absence is probably why `difelsiga` went the way it did. With no
complement lemma to hand, the shortest available route to a set difference was
to write it as an intersection of a pair and reach for countable-intersection
closure — which is where the axiom of choice comes in.

So the contribution is two statements:

**1. The missing lemma.** `( S e. U. ran sigAlgebra /\ A e. S ) -> ( U. S \ A ) e. S`
Useful on its own terms, independent of anything about choice.

**2. `difelsiga` reproved** using it twice, plus `unelsiga`, `difun1`, `dfss4`.
Choice-free.

## The steps

With `U` for `U. S`:

    1  A C_ U                          elsigass
    2  ( U \ ( U \ A ) ) = A           dfss4, from 1
    3  ( U \ A ) e. S                  the new lemma, at A
    4  ( ( U \ A ) u. B ) e. S         unelsiga, from 3 and B e. S
    5  ( U \ ( ( U \ A ) u. B ) ) e. S the new lemma, at 4
    6  ( U \ ( ( U \ A ) u. B ) )
         = ( ( U \ ( U \ A ) ) \ B )   difun1
    7  ( ( U \ ( U \ A ) ) \ B )
         = ( A \ B )                   difeq1, from 2
    8  ( U \ ( ( U \ A ) u. B ) )
         = ( A \ B )                   eqtrd, 6 and 7
    9  ( A \ B ) e. S                  eqeltrd, 5 and 8

Every lemma named was checked against the dependency closure. None reaches
choice.

## Mandatory hypothesis order, from the verifier itself

    unelsiga    class A, class B, class S
    difun1      class A, class B, class C
    dfss4       class A, class B

`tools/mmframe.py <label>` prints these. Getting the push order wrong is the
usual way a hand-written proof fails, and the error names the stack rather than
the mistake.

## Status

Statements confirmed, route confirmed, ingredients confirmed choice-free,
verifier confirmed able to reject a bad proof. The RPN step sequence is not
written. That is the next block of work, and it is the only thing between this
and a submittable PR.
