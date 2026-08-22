```
╔════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                            ║
║              ███╗   ███╗███╗   ███╗███████╗ ██████╗ ██████╗  ██████╗ ███████╗              ║
║              ████╗ ████║████╗ ████║██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝              ║
║              ██╔████╔██║██╔████╔██║█████╗  ██║   ██║██████╔╝██║  ███╗█████╗                ║
║              ██║╚██╔╝██║██║╚██╔╝██║██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝                ║
║              ██║ ╚═╝ ██║██║ ╚═╝ ██║██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗              ║
║              ╚═╝     ╚═╝╚═╝     ╚═╝╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝              ║
║                                                                                            ║
║                              what a formal database rests on                               ║
║                                                                                            ║
╚════════════════════════════════════════════════════════════════════════════════════════════╝
```

# mmforge

Find axiom dependencies a Metamath database does not need, and build the proofs
that remove them. No dependencies; runs against a stock `set.mm`.

```
pip install mmforge
```

Six repairs built with this were submitted to `metamath/set.mm`. **The first was
merged on 19 August 2026**, freeing 36 statements — Bayes' theorem among them —
from the axiom of choice. The author of another said he had not noticed the
dependency when he wrote the theorem.

## Related work

For **reading and verifying** Metamath databases in Python, see
[`metamath-py`](https://pypi.org/project/metamath-py/) (Katz & Smith) and
[`mmverify.py`](https://github.com/david-a-wheeler/mmverify.py) (Levien,
Wheeler). `mmforge` is for the other direction — analysing where an axiom is
spent and **constructing** the proof that avoids it — and it hands its output to
those verifiers rather than replacing them.

## One loop, two halves

```
mmforge reach       set.mm --axiom ax-ac ax-ac2
mmforge impact      set.mm --axiom ax-ac ax-ac2 --top 40
mmforge guards      set.mm
mmforge domination  set.mm
mmforge steps       set.mm madefi --grep imadomg
mmforge compress    --selftest 300
mmforge conformance set.mm
```

**`reach`** gives every statement whose proof transitively cites an axiom, and
traces any one of them down to where it enters.

**`impact`** ranks candidates by how many theorems a repair would actually free.
That is not the count of theorems below a statement — it is the dominator
subtree of the proof DAG reversed and rooted at the axiom, because a theorem
with a second route to the axiom is not freed by repairing the first. In
`set.mm`, `difelsiga` has 64 theorems below it and frees 36.

**`guards`** counts the database's own `$j usage 'X' avoids 'A'` directives,
which the verifiers check and which record work earlier contributors already
did. Guarded theorems over the size of the cone gives a ratio that says whether
a seam is worth working at all: `ax-13` sits at 0.751 and yields nothing.

**`steps`** replays a stored proof through a verifier and prints what each step
*proves*, with its instantiation. That is what makes a general lemma applied to
a special case visible — the file says one thing, the step says what it was
actually used on. On `madefi` it puts the `imadomg` call at step 968, two
hundred steps after the finiteness that would have avoided it.

**`compress`** writes a proof back in the compressed format the database stores.
As far as the Metamath tool list records, the Python tooling verifies compressed
proofs and does not write them. `compress --selftest N` re-encodes the first N
proofs of a database and reports how many came out byte-identical to what is
stored; `conformance` below is the check that decides correctness.

**Measure reach over every packaging of an axiom.** `ax-ac` alone reaches 9
statements in `set.mm`; `ax-ac` with `ax-ac2` reaches 546. A survey quoting the
first has measured a label rather than an axiom.

## `conformance` — why byte-agreement is the wrong test

The obvious check for a proof encoder is whether its output matches what
`metamath.exe` stored. That number is worth reporting and it is not the
correctness criterion, because the compressed format admits more than one valid
encoding of the same proof. Two encodings can differ in a tie-break, have
identical length and label count, and both be right.

`mmforge conformance` re-encodes every proof in a database, writes the database
back, and hands it to a verifier this package did not write. If it verifies, the
encoding is correct whatever bytes it chose.

That is the Metamath community's own epistemology, stated in `mmverify.py`'s
README — *"Multiple Metamath verifiers (written in different languages by
different people) are used to verify them, reducing the risk that a software
defect will lead to an incorrectly verified proof."* This applies it to the
encoder rather than asking to be trusted.

The suite is checked against a deliberately corrupted database before it is
believed: flipping one letter of `idi`'s proof gets a hard rejection, so an
accept carries information.

## Library use

```python
from mmforge.mmapi import Database
from mmforge.mmcompress import compress

db = Database("set.mm")
bloc, text = compress(db, "difelsiga", rpn)
```

`mmapi` carries frames, mandatory hypotheses and first-order matching over token
sequences; `mmassemble` builds a proof from a list of justified steps; `mmswap`
locates a subproof as an RPN span and splices a replacement. `mmframe`,
`mmfind`, `mmstmt` and `mmdecomp` are importable but have no subcommand — they
were written against this project's own repository layout.

## Vendored code

`mmforge._vendor.mmverify` is Raph Levien and David A. Wheeler's `mmverify.py`,
MIT licensed, included because there is no Metamath package on PyPI to depend
on. Its copyright notice travels with it in `LICENSE-mmverify`.

## Licence

MIT.

---

```
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║      ███████╗      ██╗  ██╗███████╗██╗   ██╗███████╗       ║
║      ██╔════╝      ██║ ██╔╝██╔════╝╚██╗ ██╔╝██╔════╝       ║
║      █████╗  █████╗█████╔╝ █████╗   ╚████╔╝ ███████╗       ║
║      ██╔══╝  ╚════╝██╔═██╗ ██╔══╝    ╚██╔╝  ╚════██║       ║
║      ██║           ██║  ██╗███████╗   ██║   ███████║       ║
║      ╚═╝           ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝       ║
║                                                            ║
║               ·   C  R  E  A  T  I  V  E   ·               ║
║                                                            ║
║          ────────────────────────────────────────          ║
║                                                            ║
║                      Vincent Gonzalez                      ║
║                         f-keys.com                         ║
║                 ORCID 0009-0005-3640-014X                  ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

Part of [F-Keys](https://f-keys.com) — independent hardware, software
and internet products. See the [working log](https://f-keys.com/log/)
and [live status](https://f-keys.com/status/).
