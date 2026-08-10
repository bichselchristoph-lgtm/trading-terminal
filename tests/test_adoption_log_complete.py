"""Every tracked file arrived through the gate, the evidence carry, or bootstrap.

This is the test that makes M001 stick. Without it the adoption gate is prose,
and a convention that lives in prose depends on someone remembering -- which is
exactly how the predecessor tree came to hold a README describing another
repository.

With it, wholesale import is not discouraged. It is impossible without a visible
failing test.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

#: The M001 §2 bootstrap. These files were WRITTEN for this tree, not carried,
#: so they have no source path and no adoption row. Everything else must be
#: accounted for. Keep this list short -- every entry is a hole in the gate.
BOOTSTRAP_ALLOWLIST = {
    ".gitignore",
    # Not in M001 §2's list. Added because without it git normalises line endings
    # on checkout, which rewrites the bytes of hash-verified carried evidence and
    # turns test_evidence_carry_intact red on a fresh clone -- automated tidying
    # of exactly the kind §4 forbids.
    ".gitattributes",
    "pytest.ini",
    "requirements.txt",
    "CLAUDE.md",
    "README.md",
    "ADOPTION-LOG.md",
    "EVIDENCE-CARRY.md",
    "tools/adopt.py",
    "tests/test_adoption_log_complete.py",
    "tests/test_no_secrets.py",
    "tests/test_pytest_collection.py",
    "tests/test_evidence_carry_intact.py",
}


def tracked_files() -> list[str]:
    """`-z` is load-bearing. Without it git quotes and octal-escapes any path
    containing non-ASCII bytes -- a task file whose name holds an em-dash comes
    back as `"handoff/inbox/H9 \\342\\200\\224 ...md"` and never matches the real
    name in the log, so a correctly-carried file reports as an orphan."""
    out = subprocess.run(
        ["git", "ls-files", "-z"], cwd=REPO, capture_output=True, check=True
    ).stdout.decode("utf-8")
    return [p for p in out.split("\0") if p]


def logged_paths(filename: str, column: int) -> set[str]:
    """Pull the backticked path out of the given column of a markdown table."""
    path = REPO / filename
    if not path.exists():
        return set()
    found = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or line.startswith("|---") or " date " in line[:10]:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) <= column:
            continue
        m = re.match(r"^`(.+?)`$", cells[column])
        if m:
            found.add(m.group(1))
    return found


def accounted_for() -> set[str]:
    return (
        BOOTSTRAP_ALLOWLIST
        | logged_paths("ADOPTION-LOG.md", 1)
        | logged_paths("EVIDENCE-CARRY.md", 1)
    )


def test_every_tracked_file_is_accounted_for() -> None:
    """The rule. A file in git that nobody logged arrived by copying."""
    known = accounted_for()
    orphans = sorted(f for f in tracked_files() if f not in known)
    assert not orphans, (
        "these tracked files arrived by neither adoption nor evidence carry:\n  "
        + "\n  ".join(orphans)
        + "\n\nEvery file in this tree enters through tools/adopt.py (logged in "
        "ADOPTION-LOG.md)\nor the evidence carry (logged in EVIDENCE-CARRY.md). "
        "Copying a file in directly is\nthe failure mode this repository was created to "
        "prevent -- see CLAUDE.md.\nIf one of these is genuinely bootstrap, it belongs in "
        "BOOTSTRAP_ALLOWLIST, and\nadding it there should feel like a decision."
    )


def test_the_allowlist_does_not_rot() -> None:
    """An allowlist entry for a file that no longer exists is a hole nobody can
    see. It would silently re-admit a future file of the same name."""
    stale = sorted(e for e in BOOTSTRAP_ALLOWLIST if not (REPO / e).exists())
    assert not stale, (
        f"BOOTSTRAP_ALLOWLIST names files that do not exist: {stale}. "
        "Remove them -- a stale entry silently pre-authorises any future file with that name."
    )


def test_the_check_can_actually_fail() -> None:
    """A test that cannot fail proves nothing. Confirm an unlogged path would be
    caught, so a future refactor that quietly widens `accounted_for` is visible."""
    assert "core/definitely_not_adopted.py" not in accounted_for()


@pytest.mark.parametrize("required", ["ADOPTION-LOG.md", "EVIDENCE-CARRY.md"])
def test_the_logs_exist(required: str) -> None:
    """If a log is deleted, `logged_paths` returns an empty set and this test
    would pass vacuously while the gate silently stopped accounting for anything."""
    assert (REPO / required).exists(), (
        f"{required} is missing. Without it the completeness check above still passes, "
        "but accounts for nothing -- the same 'deleting the file is the cheapest route to "
        "green' failure the open-questions gate was rewritten to close."
    )
