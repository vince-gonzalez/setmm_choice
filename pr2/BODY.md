# Add `fnrndomnum`, and prove `fnrndomg` from it

set.mm already separates the choice and choice-free forms of dominance one
step down:

    fodomg    ( A e. V        -> ( F : A -onto-> B -> B ~<_ A ) )   uses ax-ac
    fodomnum  ( A e. dom card -> ( F : A -onto-> B -> B ~<_ A ) )   does not

and `fodomg` is proved from `fodomnum` by `numth3`, so the appeal to choice is
a single visible line.

The `Fn` form has only ever existed in the `ax-ac` version. This adds the
missing half:

    fnrndomnum  ( A e. dom card -> ( F Fn A -> ran F ~<_ A ) )

and reproves `fnrndomg` from it the same way `fodomg` is proved from
`fodomnum`. The two proofs come out with the same shape:

    fodomg    ( ... wfo cdom wbr wi numth3 fodomnum     syl ) ADEAFGEABCHBAIJKADLABCMN
    fnrndomg  ( ... wfn crn cdom wbr wi numth3 fnrndomnum syl ) ABDAEFDCAGCHAIJKABLACMN

`fnrndomg`'s statement is unchanged. Its proof goes from 26 steps to 23, and
its route to `ax-ac` is now `numth3` directly rather than by way of `fodomg`.

Following `fodomg`, its comment now points at the choice-free version.

## Why

The general statement genuinely needs choice — an injection from the range
back into the domain picks a preimage for every value — so `fnrndomg` is not
going anywhere. But most of what stands on it applies it to a domain that is
already well-orderable, where the least preimage works and nothing is chosen.
Those uses currently have no lemma to reach for.

To be clear about what this PR does on its own: it frees no theorem. It is the
lemma the callers need before any of them can be switched, and the follow-up
is `subsaliuncl`, whose domain is `NN`. That one carries the `smf*` family.
Splitting it out so this can be reviewed on its own terms.

## Verification

Against `develop` at 79deb54:

- `scripts/verify set.mm` passes: `verify proof *` on the whole database and
  `verify markup * /top_date_skip` both report no errors.
- `scripts/rewrap` is a fixed point.
- `scripts/regen-discouraged` reproduces `discouraged` byte for byte.

Both proofs are as `save proof /compressed/fast` writes them.

## Naming

`fnrndomnum` follows `fodomnum`, and `fodomfi` for the finite case.
