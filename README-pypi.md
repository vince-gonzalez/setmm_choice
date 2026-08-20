# setmm-choice

Find axiom dependencies a Metamath database does not need, and build the proofs
that remove them. No dependencies; runs against a stock `set.mm`.

```
pip install setmm-choice
```

Seven repairs built with this have been submitted to `metamath/set.mm`. The
first was merged on 19 August 2026, freeing 36 statements — Bayes' theorem among
them — from the axiom of choice.

## Finding them

```
setmm-necessity set.mm --axiom ax-ac ax-ac2          # what reaches the axiom
setmm-necessity set.mm --axiom ax-ac ax-ac2 --trace difelsiga
setmm-impact     set.mm --axiom ax-ac ax-ac2 --top 40
setmm-guards     set.mm                              # the library's own guard census
setmm-domination set.mm
```

**`setmm-necessity`** computes the reach of an axiom set — every statement whose
proof transitively cites it — and traces any one of them down to where the axiom
enters.

**`setmm-impact`** ranks candidates by how many theorems each repair would
actually free. That is not the number of theorems below a statement: it is the
dominator subtree of the proof DAG reversed and rooted at the axiom, because a
theorem with a second route to the axiom is not freed by repairing the first.
On `set.mm`, `difelsiga` has 64 theorems below it and frees 36.

**`setmm-guards`** counts the database's own `$j usage 'X' avoids 'A'`
directives, which the verifiers check and which record work previous
contributors already did. Guarded theorems over the size of the axiom's cone
gives a ratio that says whether a seam is worth working at all: `ax-13` sits at
0.751 and yields nothing to a newcomer.

**Measure reach over every packaging of an axiom.** `ax-ac` alone reaches 9
statements in `set.mm`; `ax-ac` with `ax-ac2` reaches 546. A survey quoting the
first has measured a label rather than an axiom.

## Building the replacement

```
mm-steps set.mm madefi --grep imadomg
mm-compress --database set.mm --selftest 300
```

**`mm-steps`** replays a stored proof through the verifier and prints what each
step *proves*, with its instantiation. This is what makes a general lemma
invoked on a special case visible — the statement in the file says one thing and
the step in the proof says what it was actually applied to. On `madefi` it puts
the `imadomg` call at step 968, two hundred steps after the finiteness that
would have avoided it.

**`mm-compress`** writes a proof back in the compressed format the database
stores. As far as the Metamath tool list records, the Python tooling verifies
compressed proofs and does not write them. The encoder agrees byte for byte with
`metamath.exe` on 2,839 of 3,000 proofs tested; `--selftest N` re-runs that
comparison over the first N proofs of a database and exits non-zero on a
mismatch. The two rules that took longest to find: a single-token leaf is never
tagged `Z`, and a repeat nested inside an already-shared subproof is not a
repeat.

The encoder itself is a library call:

```python
from setmm_choice.mmapi import Database
from setmm_choice.mmcompress import compress

db = Database("set.mm")
block, text = compress(db, "difelsiga", rpn)
```

The library also carries `mmapi` (frames, mandatory hypotheses, first-order
matching over token sequences), `mmassemble` (a proof from a list of justified
steps) and `mmswap` (locate a subproof as an RPN span and splice a replacement).
`mmframe`, `mmfind`, `mmstmt` and `mmdecomp` are importable but have no command:
they were written against this project's own repository layout.

## Vendored code

`setmm_choice._vendor.mmverify` is Raph Levien and David A. Wheeler's
`mmverify.py`, MIT licensed, included because there is no Metamath package on
PyPI to depend on. Its copyright notice travels with it in
`LICENSE-mmverify`.

## Licence

MIT.
