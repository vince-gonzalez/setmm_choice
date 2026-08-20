#!/usr/bin/env python3
r"""mmforge — find avoidable axiom dependencies in Metamath databases, and build
the proofs that remove them.

    mmforge reach       set.mm --axiom ax-ac ax-ac2
    mmforge impact      set.mm --axiom ax-ac ax-ac2 --top 40
    mmforge guards      set.mm
    mmforge domination  set.mm
    mmforge steps       set.mm madefi --grep imadomg
    mmforge compress    --selftest 300
    mmforge conformance set.mm

One entry point rather than seven, so there is one name to remember and nothing
else lands in anyone's PATH. Each subcommand keeps its own flags; `mmforge CMD
--help` reaches them.

The two halves are one loop. The analysis finds a theorem that pays for an axiom
it does not need; the construction writes the replacement proof and checks it.
Six of the repairs that came out of that loop were submitted to metamath/set.mm
and the first was merged.
"""
from __future__ import annotations

import sys

# subcommand -> (module attribute path, one-line summary)
COMMANDS: dict[str, tuple[str, str]] = {
    "reach": ("necessity", "which theorems reach an axiom, and how each gets there"),
    "impact": ("impact", "rank theorems by how many others a repair would free"),
    "guards": ("guard_census", "census the database's own $j 'avoids' directives"),
    "domination": ("domination_class", "the general-domination defect class"),
    "steps": ("mmsteps", "replay a proof, printing what each step proves"),
    "compress": ("mmcompress", "re-encode proofs in the stored compressed format"),
    "conformance": ("conformance", "round-trip every proof and verify the result"),
}
# a couple of modules front their CLI under a different name
ENTRY = {"compress": "_cli"}


def usage(code: int = 0) -> None:
    print(__doc__.split("\n\n")[0].strip())
    print()
    print("usage: mmforge <command> [options]")
    print("       mmforge <command> --help")
    print()
    width = max(len(c) for c in COMMANDS)
    for name, (_, summary) in COMMANDS.items():
        print(f"  {name:<{width}}  {summary}")
    print()
    print("A database path may be given per command, or once in $SETMM.")
    sys.exit(code)


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        usage(0)
    name = sys.argv[1]
    if name in ("-V", "--version"):
        from . import __version__
        print(f"mmforge {__version__}")
        sys.exit(0)
    if name not in COMMANDS:
        print(f"mmforge: unknown command {name!r}\n", file=sys.stderr)
        usage(2)

    module_name, _ = COMMANDS[name]
    module = __import__(f"{__package__}.{module_name}", fromlist=["main"])
    entry = getattr(module, ENTRY.get(name, "main"))

    # Each subcommand parses its own argv, so present it with one that reads
    # correctly in its --help and error messages.
    sys.argv = [f"mmforge {name}"] + sys.argv[2:]
    entry()


if __name__ == "__main__":
    main()
