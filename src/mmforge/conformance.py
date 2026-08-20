#!/usr/bin/env python3
r"""Round-trip every proof in a database and verify the result.

    mm-conformance set.mm                 # the whole database
    mm-conformance set.mm --limit 500     # a fast slice, for CI
    mm-conformance set.mm --write out.mm  # keep the re-encoded database

Exit code 1 if any re-encoded proof fails to verify.

WHY BYTE-AGREEMENT IS THE WRONG TEST
    The obvious check for a proof encoder is whether its output matches what
    `metamath.exe` stored. That number is worth reporting and it is not the
    correctness criterion, because the compressed format admits more than one
    valid encoding of the same proof. Two encodings can differ in a tie-break,
    have identical length and label count, and both be right. Scoring on byte
    agreement counts those as failures, and says nothing at all about the ones
    it counts as passes.

    The criterion that means something: re-encode a proof, put it back in the
    database, and hand the database to a verifier somebody else wrote. If it
    verifies, the encoding is correct, whatever bytes it chose.

    That is the Metamath community's own epistemology, stated in mmverify.py's
    README -- "Multiple Metamath verifiers (written in different languages by
    different people) are used to verify them, reducing the risk that a software
    defect will lead to an incorrectly verified proof." This applies it to the
    encoder instead of asking to be trusted.

WHAT IT REPORTS
    identical    re-encoded byte for byte as stored
    differing    not byte-identical; correctness decided by the verifier
    raised       the encoder failed outright        <- a failure
    REJECTED     the verifier refused the result    <- a failure

A run passes when nothing raised and the verifier accepts. `identical` is a
statistic about agreement with one implementation's choices, not a measure of
correctness.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
from pathlib import Path

from . import default_database
from .mmapi import Database
from .mmcompress import IncompleteProof, _decompress, compress

# label, everything up to $=, the proof body. Mirrors mmcompress.selftest so the
# two cannot disagree about what a proof is.
PROOF = re.compile(r"(?m)^[ \t]*(\S+)[ \t]+\$p\s(.*?)\$=(.*?)\$\.", re.S)

COMMENT = re.compile(r"\$\(.*?\$\)", re.S)


def mask_comments(text: str) -> str:
    """Blank every `$( ... $)` region, keeping offsets identical.

    Comments in set.mm quote Metamath syntax. `dpval` is written out inside one
    as `dpval $p |- ( A . B ) = _ A B $.` -- a `$p` with no `$=`, which is not a
    statement at all. A regex that does not know about comments matches it, then
    scans forward to the next `$=` and `$.` and assembles a proof body belonging
    to some later theorem. Decoding that against the wrong frame fails somewhere
    unrelated, which is how it was first seen: `dpval: IndexError`.

    Spaces rather than deletion, so every match offset still indexes the real
    source and splices land where they should.
    """
    return COMMENT.sub(lambda m: " " * (m.end() - m.start()), text)


def verify_with(database: Path, verifier: Path) -> tuple[bool, str]:
    """Hand the database to an independent verifier. True when it accepts."""
    started = time.time()
    r = subprocess.run([sys.executable, "-X", "utf8", str(verifier), str(database)],
                       capture_output=True, text=True)
    took = time.time() - started
    tail = [l for l in (r.stderr or r.stdout or "").strip().splitlines() if l.strip()]
    return r.returncode == 0, (f"exit {r.returncode} in {took:.0f}s"
                               + (f" — {tail[-1][:110]}" if tail else ""))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("database", nargs="?", default=None)
    ap.add_argument("--limit", type=int, metavar="N",
                    help="round-trip only the first N compressed proofs")
    ap.add_argument("--write", metavar="OUT", help="where to keep the re-encoded database")
    ap.add_argument("--verifier", metavar="MMVERIFY",
                    help="path to mmverify.py; defaults to the vendored copy")
    ap.add_argument("--no-verify", action="store_true",
                    help="round-trip only, do not run a verifier")
    a = ap.parse_args()

    db_path = Path(a.database) if a.database else default_database()
    if not db_path.exists():
        sys.exit(f"no database at {db_path} — pass a path or set $SETMM")

    src = db_path.read_text(encoding="utf-8", errors="replace")
    scan = mask_comments(src)
    db = Database(db_path)

    identical = differing = skipped = 0
    raised: list[str] = []
    incomplete: list[str] = []
    edits: list[tuple[int, int, str]] = []
    started = time.time()
    done = 0

    for m in PROOF.finditer(scan):
        if a.limit and done >= a.limit:
            break
        lab = m.group(1)
        if lab not in db.mm.labels or db.mm.labels[lab][0] != "$p":
            continue
        proof = m.group(3).split()
        if not proof or proof[0] != "(":
            skipped += 1          # normal format: nothing for the encoder to do
            continue
        dv, mand, ess, concl = db.mm.labels[lab][1]
        idx = proof.index(")")
        orig_bloc, orig_text = proof[1:idx], "".join(proof[idx + 1:])
        try:
            flat = _decompress(db, mand, ess, proof, lab)
            bloc, text = compress(db, lab, flat, frame=(dv, mand, ess, concl))
        except IncompleteProof:
            # A proof with an unproved step is not a proof to round-trip.
            incomplete.append(lab)
            continue
        except Exception as e:
            raised.append(f"{lab}: {type(e).__name__}: {e}")
            done += 1
            continue
        done += 1
        if bloc == orig_bloc and text == orig_text:
            identical += 1
        else:
            differing += 1
            body = " ( " + " ".join(bloc) + " ) " + text + " "
            edits.append((m.start(3), m.end(3), body))
        if done % 2000 == 0:
            print(f"  {done:,}  identical {identical:,}  differing {differing:,}"
                  f"  raised {len(raised)}  ({time.time() - started:.0f}s)")

    total = identical + differing
    agree = f"{identical / total:.1%}" if total else "n/a"
    print(f"\n  {db_path.name}: {total:,} round-tripped, {skipped:,} not compressed"
          + (f", {len(incomplete):,} incomplete" if incomplete else ""))
    print(f"  identical {identical:,}   differing {differing:,}   "
          f"raised {len(raised)}   (byte agreement {agree})")
    if incomplete:
        print(f"  incomplete — carry '?', so there is no proof to round-trip: "
              f"{', '.join(incomplete[:6])}"
              + (f" +{len(incomplete) - 6} more" if len(incomplete) > 6 else ""))

    out_path = Path(a.write) if a.write else db_path.with_suffix(".roundtrip.mm")
    out = src
    for lo, hi, body in sorted(edits, reverse=True):
        out = out[:lo] + body + out[hi:]
    out_path.write_text(out, encoding="utf-8", newline="\n")
    print(f"  re-encoded -> {out_path.name}  ({len(out):,} bytes, "
          f"{len(edits):,} proofs replaced)")

    if raised:
        print(f"\n  {len(raised)} encoder failure(s):")
        for f in raised[:10]:
            print(f"    {f}")

    if a.no_verify:
        print("\n  verification skipped")
        sys.exit(1 if raised else 0)

    verifier = Path(a.verifier) if a.verifier else (
        Path(__file__).resolve().parent / "_vendor" / "mmverify.py")
    ok, detail = verify_with(out_path, verifier)
    print(f"\n  {verifier.name}: {'ACCEPTED' if ok else 'REJECTED'}  ({detail})")
    print()
    if ok and not raised:
        print("PASS — every re-encoded proof verifies under an implementation "
              "this package did not write")
        sys.exit(0)
    print("FAIL")
    sys.exit(1)


if __name__ == "__main__":
    main()
