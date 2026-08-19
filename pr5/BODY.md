# Avoid `ax-ac` in `sigaclci` directly

Follow-up to #5442, opened at @tirix's suggestion there.

`sigaclci` closes a sigma-algebra under countable intersections, and one of its
own hypotheses is `A ~<_ _om`. To show the set of complements countable it goes
through `abrexdom2jm`, which dominates an indexed set by an *arbitrary* indexing
set and therefore needs choice:

    abrexdom2jm   ( A e. ~P S -> { y | E. z e. A y = ( U. S \ z ) } ~<_ A )
    domtr         ... composed with A ~<_ _om

`abrexct` states the countable case directly and is choice-free. `sigaclcu2`
already uses it for exactly this purpose a few statements away; `sigaclci` is
the one that did not.

    abrexct       ( A ~<_ _om -> { y | E. x e. A y = B } ~<_ _om )

The substitution takes the hypothesis the theorem already has, so **two steps
replace 68** and the proof goes from 1883 steps to 1849. The statement,
hypotheses and `$d` conditions are unchanged.

## Effect

Against `develop` as it stands, this frees 38 theorems. **36 of those are the
same 36 that #5442 frees** — that PR reroutes `difelsiga` around `sigaclci`,
this removes the dependency at its source. If #5442 merges first, the marginal
effect here is **2**: `sigaclci` itself and `sigapisys`.

The count is not the argument. The argument is that the detour existed only to
serve this one call: after this change `abrexdom2jm` has **no remaining users**,
and `abrexdomjm` is used only by `abrexdom2jm`. Three choice-dependent lemmas
were carrying one consumer that already had a countability hypothesis in hand.

## Verification

Against `develop` at f66bdd8:

- `scripts/verify set.mm` passes: `verify proof *` over the whole database and
  `verify markup * /top_date_skip` both report no errors.
- `scripts/rewrap` is a fixed point.
- `scripts/regen-discouraged` reproduces `discouraged` byte for byte.
- Axiom closure recomputed on the patched file: `sigaclci` no longer reaches
  `ax-ac` or `ax-ac2`.

The proof is as `save proof /compressed/fast` writes it.
