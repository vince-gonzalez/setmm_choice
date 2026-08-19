# Drop the `ax-ac` dependency from `omeiunle`

**Depends on #5443.** This branch is built on it, so the diff shows that PR's
commits too — only the last commit, `omeiunle`, is new here. I will rebase once
#5443 lands.

@glacode — this is in your mathbox, alongside #5446. The statement, hypotheses
and `$d` conditions are unchanged; one step of the proof changes.

## What changes

`omeiunle` bounds the outer measure of a countable indexed union. Its index set
is fixed by the hypothesis `Z = ( ZZ>= ` N )`, so it is countable, and the proof
derives `Z ~<_ _om` from `uzct` at step 631.

To reach `ran E ~<_ _om` it nevertheless goes through `fnrndomg`, which
dominates a range by an *arbitrary* domain and so requires choice, and then
composes that with the countability it had just derived.

`fnrndomnum` (#5443) is the same statement for a well-orderable domain and is
choice-free. `Z ~<_ _om` makes `Z` numerable through `ondomen`, and the proof
already has both `( ph -> E Fn Z )` and `( ph -> Z ~<_ _om )`, so the
substitution needs nothing that is not already there.

The proof goes from 912 steps to 938, which is why the comment says revised
rather than shortened.

## Effect

**9 theorems stop depending on `ax-ac`**, and none start:

```
carageniuncl  carageniuncllem2  caragensal   caragenunicl  caratheodory
caratheodorylem2  omeiunle  omeiunlempt  omeiunltfirp
```

`caratheodory` is Carathéodory's theorem. Only `omeiunle` is edited; the other
eight inherit the change untouched.

Note for #5446: these two changes compound. `disjinfi` alone frees 29 and this
one alone frees 9, but applied together they free 69, because 31 theorems reach
`ax-ac` by both routes and neither fix alone releases them.

## A note on `abrexct`

The shorter route here would be `abrexct`, which states directly that an image
of a countable set is countable. It cannot be used: `abrexct` is in Thierry
Arnoux's mathbox and `omeiunle` is in Glauco Siliprandi's, and
`verify markup` rejects the cross-mathbox reference. Every lemma used above is
in main set.mm except `uzct`, which is in this mathbox already.

## Verification

- `scripts/verify set.mm` passes: `verify proof *` over the whole database and
  `verify markup * /top_date_skip` both report no errors, including the
  mathbox independence check.
- `scripts/rewrap` is a fixed point.
- `scripts/regen-discouraged` reproduces `discouraged` byte for byte.
- Axiom closure recomputed: `omeiunle` no longer reaches `ax-ac` or `ax-ac2`.
