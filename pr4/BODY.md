# Drop the `ax-ac` dependency from `disjinfi`

@glacode — this is in your mathbox, so I have left it as a draft for you to
look at before anything happens with it. The statement, the hypotheses and the
`$d` conditions are all unchanged; one step of the proof changes.

## What changes

`disjinfi` already assumes `( ph -> C e. Fin )`, and by step 83 its proof has
used that to establish

    ( ph -> ( U. ran ( x e. A |-> B ) i^i C ) e. Fin )

since that set is a subset of `C`. It then constructs a surjection from that
same set onto `{ x e. A | ( B i^i C ) =/= (/) }` and applies `fodomg` to get
dominance, followed by `domfi` to turn dominance back into finiteness.

`fodomg` is stated for an arbitrary domain, so it requires `ax-ac`. `fodomfi`
is the same statement for a finite domain and is choice-free, and the
finiteness it needs is the fact already proved at step 83. So the appeal to
choice is replaced by the theorem's own hypothesis.

Nothing new is introduced. The proof is ten steps longer (7327 to 7337),
which is why the comment says revised rather than shortened.

## Effect

**29 theorems stop depending on `ax-ac`**, and none start. All 29 are in your
mathbox:

```
disjinfi      dmvon         fsumiunss     hspmbl        isvonmbl
mblvon        ovnome        ovnsplit      ovnsubadd     ovnsubadd2
ovnsubadd2lem ovnsubaddlem1 ovnsubaddlem2 psmeasure     psmeasurelem
rrnmbl        sge0iun       sge0iunmpt    sge0iunmptlemre  sge0xp
unidmvon      von0val       voncmpl       vonmblss      vonmblss2
vonvol        vonvol2       vonvolmbl     vonvolmbl2
```

Only `disjinfi` is edited; the other 28 inherit the change untouched. The
library-wide count of statements reaching `ax-ac` or `ax-ac2` goes from 582
to 553.

## Verification

Against `develop` at f66bdd8:

- `scripts/verify set.mm` passes: `verify proof *` over the whole database and
  `verify markup * /top_date_skip` both report no errors.
- `scripts/rewrap` is a fixed point.
- `scripts/regen-discouraged` reproduces `discouraged` byte for byte.
- The axiom closure was recomputed on the patched file: `disjinfi` no longer
  reaches `ax-ac` or `ax-ac2`; `fodomg` still does, unchanged.

The proof is as `save proof /compressed/fast` writes it.

This is the same shape as #5445, where a finite set was established early,
forgotten, and recovered through a choice-dependent detour.
