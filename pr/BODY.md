# Remove the `ax-ac` dependency from `difelsiga`

`difelsiga` — a sigma-algebra is closed under class differences — currently
depends on the axiom of choice. It does not need to.

The present proof writes `A \ B` as `|^| { A, ( U. S \ B ) }`, shows that pair
countable, and applies `sigaclci`, closure under countable intersections.
`sigaclci` gets its countability side condition from `abrexdom2jm`, which
reaches `ax-ac` through `fnrndomg` → `fodomg` → `numth3` → `cardeqv` →
`axac3`. Class difference is a binary operation, and it is paying for a
cardinality argument.

## Why it happened

`unelsiga` is defined *after* `difelsiga` in set.mm. Pairwise-union closure did
not exist yet when class difference was proved in September 2016, and it
arrived three months later, in December. Countable intersection was the only
closure property on the shelf at the time, so that is what the proof used.

Nothing here is a mathematical error. It is an artifact of the order the
library grew in, and it has stood since.

## The change

Three edits, in one contiguous region:

1. **`difunielsiga` is added** — closure under complement relative to the base
   set, `( ( S e. U. ran sigAlgebra /\ A e. S ) -> ( U. S \ A ) e. S )`.
   `issiga` asserts this by definition, but no statement in the library says
   it, so every use unfolds the definition inline.

2. **`difelsiga` and `unelsiga` swap places**, putting pairwise union first.

3. **`difelsiga` is reproved** through

       A \ B  =  U. S \ ( ( U. S \ A ) u. B )

   Complement `A`, union with `B`, complement again, then rewrite with
   `dfss4` and `difun1`. No pair is formed and nothing is counted.

`inelsiga` is proved from `difelsiga` through `dfin4`. It needs no edit and
loses the dependency as a consequence.

## Effect

| | labels | proof chars | steps |
|---|---:|---:|---:|
| `difelsiga` before | 47 | 334 | 1050 |
| `difelsiga` after | 24 | 188 | 381 |
| `difunielsiga` (new) | 23 | 106 | 142 |

The new `difelsiga` needs no disjoint-variable conditions; `$d x S` and
`$d x B` were there for a dummy variable the proof no longer introduces.

**36 theorems stop depending on `ax-ac`**, and none start:

```
aean          bayesth       cldssbrsiga   cndprob01     cndprobin
cndprobnul    cndprobtot    coinflippvt   difelsiga     dstfrvinc
dstfrvunirn   dya2icobrsiga dya2iocbrsiga inelsiga      ldgenpisys
ldsysgenld    measssd       measun        measunl       measxun2
orrvccel      orvccel       orvcgteel     orvclteel     prob01
probdif       probdsb       probinc       probtotrnd    probun
probvalrnd    sibfinima     sigainb       sigaldsys     sitgaddlemb
sxbrsigalem2
```

`bayesth` is Bayes' theorem. The rest are the conditional-probability family,
the discrete-random-variable results, and the measure and Borel lemmas built
on them. The library-wide count of statements reaching `ax-ac` or `ax-ac2`
goes from 582 to 546.

## Verification

Against set.mm at

    sha256  9486e76e0614f66877837d02ae973fdfde52c1343e5bcc3dbc66605cc55c7054
    bytes   51,130,373

- `mmverify.py` accepts the patched file from `difunielsiga` through the end of
  the file, so every statement after the change re-verifies with the new
  proofs in place.
- Both proofs were rejected under mutation — a swapped inference, a dropped
  final label, an altered conclusion — and the `$d` removal was checked the
  same way, by confirming that stripping a `$d` `difunielsiga` does need is
  refused.
- The axiom closure was recomputed on the patched file. `difelsiga`,
  `inelsiga`, `difunielsiga` and `bayesth` no longer reach `ax-ac` or `ax-ac2`;
  `sigaclci` still does, unchanged.

Not run here: `verify markup *` and `write source /rewrap`. The `~`
references in the added comments were checked to resolve, and no line in the
patched file exceeds 79 columns, but the proofs should be re-saved with
`save proof difunielsiga,difelsiga /compressed` before merge in case the
canonical encoder differs.

## Naming

`difunielsiga` follows `difunieq`, which leads with `dif` for the same
`( U. A \ ... )` shape, and `unielsiga` for the `U. S` constituent. `unidif`
is already taken for `U. ( A \ B )`, so `unidifelsiga` would read as the wrong
parse, and `cmpl` is the class constant for multivariate polynomials besides
meaning "complete" in `voncmpl` and `caragencmpl`. Happy to rename to whatever
you prefer.

## Provenance

The proofs were assembled from step outlines by a Python proof-construction
API written for this work, and checked with `mmverify.py`. Both are at
https://github.com/vince-gonzalez/setmm_choice — `tools/mmapi.py` does the
unification, `proofs/pr.py` builds and verifies this patch end to end.
