# src/ — the installable package

`src/setmm_choice/` is what `pip install setmm-choice` gets. It is the same code
as `tools/` and `analysis/`, with three differences forced by packaging:

- the `sys.path` bootstrap at the top of each script is gone
- intra-project imports are package-relative (`from . import necessity`)
- `mmverify.py` is vendored at `_vendor/mmverify.py` rather than reached through
  `vendor/`, since there is no Metamath package on PyPI to depend on

## Why both exist

`proofs/*.py` — one script per submitted repair — run `tools/necessity.py` and
`tools/impact.py` as subprocesses and put `tools/` on `sys.path`. Package
modules use relative imports and cannot be run directly as scripts, so pointing
those thirteen scripts at `src/` would break every one of them.

Those scripts are the provenance of six pull requests currently in review
against `metamath/set.mm`. They stay working until those resolve.

**This duplication is a defect with an expiry date.** When the PRs are settled,
the repair scripts should call `python -m setmm_choice.necessity` and import
from the installed package, and `tools/` and `analysis/` should be deleted. Until
then, a change to an analysis tool has to be made in both places.

Files affected: `tools/` (14) and `analysis/` (2) against `src/setmm_choice/`
(17, the extra being `__init__.py`).
