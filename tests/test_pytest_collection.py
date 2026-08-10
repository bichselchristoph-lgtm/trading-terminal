"""Every test directory in the tree is actually collected.

The predecessor set `testpaths = tests` in pytest.ini. Seven behavioural tests
lived in `live/tests/` and were never collected, and two separate consolidation
steps shipped a broken `live/` that stayed green -- because the only tests that
would have caught it were invisible to the runner.

A test suite that silently omits a directory is worse than one that is missing
it, because the green run is read as coverage. This test makes a new, uncollected
test directory fail rather than disappear.
"""
from __future__ import annotations

import configparser
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "venv", "node_modules"}


def declared_testpaths() -> list[str]:
    cfg = configparser.ConfigParser()
    cfg.read(REPO / "pytest.ini", encoding="utf-8")
    raw = cfg.get("pytest", "testpaths", fallback="")
    return [line.strip() for line in raw.splitlines() if line.strip()]


def discovered_test_dirs() -> set[str]:
    """Every directory that actually contains a test_*.py."""
    found = set()
    for p in REPO.rglob("test_*.py"):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        found.add(p.parent.relative_to(REPO).as_posix())
    return found


def test_every_directory_holding_tests_is_declared() -> None:
    declared = set(declared_testpaths())
    missing = sorted(d for d in discovered_test_dirs() if d not in declared)
    assert not missing, (
        "these directories contain test_*.py but are not in pytest.ini testpaths:\n  "
        + "\n  ".join(missing)
        + "\n\nThey will not be collected, and their absence will read as a green run. "
        "This is\nthe exact defect that let a broken live/ ship twice in the predecessor "
        "tree.\nAdd them to testpaths."
    )


def test_testpaths_is_not_narrowed_to_tests_only() -> None:
    """The specific regression. `testpaths = tests` is the value that caused it."""
    declared = declared_testpaths()
    assert declared != ["tests"], (
        "pytest.ini has been narrowed back to `testpaths = tests`. That is the exact "
        "setting that hid seven behavioural tests in live/tests/ while two consolidations "
        "shipped a broken live/."
    )


def test_quiet_mode_is_not_reintroduced() -> None:
    """`-q` suppresses the report header, and that header has carried a
    load-bearing caveat before -- that the orb_validator suite ran against a
    reference oracle rather than a real grader. A default that hides the caveat
    is a default that gets someone eventually."""
    cfg = configparser.ConfigParser()
    cfg.read(REPO / "pytest.ini", encoding="utf-8")
    addopts = cfg.get("pytest", "addopts", fallback="")
    assert " -q" not in f" {addopts}" and "--quiet" not in addopts, (
        f"pytest.ini addopts re-adds quiet mode: {addopts!r}. That suppresses the report "
        "header, which is where caveats about what the suite actually ran against live."
    )
