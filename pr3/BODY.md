# Shorten `madefi` and drop its `ax-ac` dependency

`madefi` proves that the made set of an ordinal natural is finite. Its proof
already establishes, two hundred steps before the end, that

    ( ~P U. ( _Made " x ) X. ~P U. ( _Made " x ) )

is finite — via `unifi`, `pwfi` and `xpfi`. It then needs the image of that set
under `|s` to be finite, and gets there the long way: `xpex` for sethood,
`ffun` for `Fun |s`, then `imadomg` to dominate the image by the set, then
`domfi` to turn dominance back into finiteness.

`imadomg` is stated for an arbitrary index set and so requires the axiom of
choice. None of it is needed once the set is known to be finite: `imafi` says
directly that the image of a finite set under a function is finite, it is
choice-free, and this proof already uses it earlier for a different subgoal.

So `xpex` / `cutsf` / `ffun` / `ax-mp` / `imadomg` / `mp2` / `domfi` /
`sylancl` collapses to one `imafi` step under `sylancr`.

## Effect

The statement is unchanged. The proof goes from **1003 steps to 804**, and
its label list loses `cvv`, `vex`, `funimaex`, `uniex`, `pwex`, `xpex`,
`cutsf`, `imadomg`, `mp2`, `domfi` and `sylancl`.

**12 theorems stop depending on `ax-ac`**, and none start:

```
bdayfin       bdayfinbnd    bdayfinbndlem1  bdayfinbndlem2  bdayfinlem
dfz12s2       eln0s2        madefi          n0cutlt         oldfi
onltn0s       onsfi
```

The library-wide count of statements reaching `ax-ac` or `ax-ac2` goes from
582 to 570.

## Verification

Against `develop` at f66bdd8:

- `scripts/verify set.mm` passes: `verify proof *` over the whole database and
  `verify markup * /top_date_skip` both report no errors.
- `scripts/rewrap` is a fixed point.
- `scripts/regen-discouraged` reproduces `discouraged` byte for byte.
- The axiom closure was recomputed on the patched file: `madefi` no longer
  reaches `ax-ac` or `ax-ac2`; `imadomg` still does, unchanged.

The proof is as `save proof /compressed/fast` writes it.
