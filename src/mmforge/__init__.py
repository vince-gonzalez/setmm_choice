"""Axiom-dependency analysis and proof repair for Metamath databases."""
from __future__ import annotations

import os
from pathlib import Path

__version__ = "0.1.2"


def default_database() -> Path:
    """Where to look for a database when none is given on the command line.

    `set.mm` is 51 MB and is not shipped with this package, so there is nothing
    sensible next to the installed module to point at. Resolution order:

        $SETMM                      an explicit path
        ./set.mm                    the usual name, in the working directory
        ./vendor/set.mm             the layout this package's own repo uses

    Returns the first that exists, and otherwise the bare name, so the error a
    caller sees names a file rather than a path inside site-packages.
    """
    env = os.environ.get("SETMM")
    if env:
        return Path(env)
    for candidate in (Path("set.mm"), Path("vendor") / "set.mm"):
        if candidate.exists():
            return candidate
    return Path("set.mm")
