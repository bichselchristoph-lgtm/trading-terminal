"""`verify-failures.txt` is generated and must never be committed.

068 Part A. `verify.ps1`'s second exemption to writing nothing but its own
output file — the previous run's named-failure set, read before being
overwritten each run so section 1 can report a delta (`unchanged`/`new`/
`fixed`) instead of a note having to quote a count. It is per-machine,
describes a single moment, and would become a second source of truth about
the tree that ages badly, the same reasoning `test_verify_output_is_ignored.py`
already applies to `handoff/verify-output.md`.

**Asserted with `git check-ignore`, not by reading `.gitignore` for a
string**, for the same reason that file's tests do: a substring match proves
the line is present, not that it has effect.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
STATE_FILE = "verify-failures.txt"


def check_ignore(rel: str) -> bool:
    """Exit 0 = ignored, 1 = not ignored. `--no-index` so the answer is about
    the rules, not about whether the file happens to exist right now."""
    r = subprocess.run(["git", "check-ignore", "--no-index", "-q", rel],
                       cwd=REPO, capture_output=True)
    return r.returncode == 0


def test_verify_failures_state_is_ignored() -> None:
    assert check_ignore(STATE_FILE), (
        f"`git check-ignore` says {STATE_FILE} is NOT ignored. verify.ps1 "
        "writes it on every run, so an unignored file means the next "
        "`git add -A` commits a machine-local snapshot of one moment as "
        "though it described the tree.")


def test_it_is_ignored_even_before_it_exists() -> None:
    """A fresh clone has no `verify-failures.txt`, and that is exactly when
    someone runs `verify.ps1` and could commit the result by accident."""
    assert check_ignore(STATE_FILE)


def test_the_rule_is_anchored_to_the_repo_root() -> None:
    """Unanchored rules match at any depth. This file is written to the
    repository root and nowhere else."""
    assert not check_ignore("handoff/verify-failures.txt"), (
        "a nested handoff/verify-failures.txt is also ignored, so the rule "
        "is unanchored. Write it as `/verify-failures.txt`.")


def test_verify_ps1_writes_the_path_this_test_guards() -> None:
    """The two must not drift. If the script changes where it writes this
    state, this test keeps guarding a path nothing produces, and the real
    file becomes committable."""
    script = (REPO / "verify.ps1").read_text(encoding="utf-8")
    assert STATE_FILE in script, (
        f"verify.ps1 no longer names {STATE_FILE}. Either it writes "
        "elsewhere -- in which case that path is not ignored -- or it "
        "stopped writing the failure-delta state at all.")
