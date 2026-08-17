# The revision every figure is measured against

set.mm changes daily. The copy read here took commits on the same day it was
downloaded. A count without the database it came from is not reproducible, so
every figure in this repository is quoted against one revision.

    database   set.mm
    revision   e38556cf4575  ("Shorten relresfld (#5440)", 2026-08-17)
    bytes      51,130,373
    sha256     9486e76e0614f66877837d02ae973fdfde52c1343e5bcc3dbc66605cc55c7054
    proved     47,655 statements, 50,661 labels

`necessity.py` prints this fingerprint on every run and writes it into its
JSON, so no figure can be separated from what produced it.

## The discrepancy this resolved

An earlier analysis used `closure.pkl`, built 2 August, and counted 47,621
proved statements against this revision's 47,655. The gap is 34, and it is
entirely a difference of snapshot:

    64  statements in this revision that the pickle never saw
    30  statements the pickle has that this revision no longer contains
    ---
    34  net

Four of the thirty are `*OLD` labels since deleted from set.mm — `biorfriOLD`,
`elOLD`, `s2rnOLD`, `s3rnOLD` — which is what identified it as a version
difference rather than a parsing fault. The remaining twenty-six were renamed
or restructured.

Both counts were correct for the library each was reading. Neither was
reproducible without saying which library that was.

## Figures at this revision

| axiom | reaching it | share | invoke directly | single-gateway |
|---|---|---|---|---|
| `ax-inf` | 6 | 0.01% | 1 | 83% |
| `ax-reg` | 517 | 1.08% | 5 | 76% |
| `ax-ac` + `ax-ac2` | 582 | 1.22% | 3 | 72% |
| `ax-pow` | 29,608 | 62.13% | 8 | 26% |

`iset.mm` at the same download, for `ax-pow`: 10,486 of 16,272 (64.44%),
27% single-gateway.
