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
    # Authored here under H9, not adopted. Caught by this very test when
    # docs/specs/ lost its native-prefix carve-out, which is the gate working
    # as designed on its own author.
    "tests/test_spec_pointers.py",
    "tests/test_regime_snapshot_path.py",
    "tests/test_regime_prompt_invariants.py",
    "tests/test_resupplied_docs_are_repaired.py",
    "tests/test_adopt_supersession.py",
    # Authored here under H11, not supplied from outside. It is the one file
    # in docs/specs/ that documents the tree rather than specifying the system.
    "docs/specs/RE-SUPPLY.md",
    "tests/test_handoff_state_declared.py",
    # Authored here under task 012, not adopted from anywhere. tools/ is a code
    # tree and deliberately has no native-prefix carve-out, so the gate demanded
    # this entry -- correctly, and it surfaced on 013's full-suite run rather
    # than 012's, which only ran the tool.
    "tools/capture_tape.py",

    # ---- S009: the first slice to author NEW CODE in this tree -------------
    # The gate has three routes in: adoption, evidence carry, and this list.
    # None of them is "code written fresh here for a slice", because M001 built
    # the gate for a migration and every file until now either came from the
    # predecessor or was scaffolding.
    #
    # These are natively authored, in a CODE TREE, which deliberately has no
    # native-prefix carve-out — so they land here. **The allowlist is now doing
    # two jobs**, and the second one will grow by roughly this many entries per
    # slice. That is the "list that becomes a hiding place" this project keeps
    # naming, and it needs a proper fourth route rather than more entries.
    # Flagged in S009's done-note as a decision, not taken here.
    "config/layout.yaml",
    "live/__init__.py",
    "live/tui/__init__.py",
    "live/tui/grammar.py",
    "live/tui/day_record.py",
    "live/tui/layout.py",
    "live/tui/app.py",
    "live/tests/__init__.py",
    "live/tests/test_tui_grammar.py",
    "live/tests/test_tui_frame.py",
    "live/tests/snapshots/empty-record.txt",
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


#: Surfaces where files are AUTHORED in this tree rather than arriving from
#: anywhere. A done-note written here is native work: it was neither adopted nor
#: carried, and demanding a log row for it would make the log meaningless.
#:
#: The trade-off, stated rather than left implicit: a file could be copied
#: wholesale into handoff/ or docs/observations/ without tripping the gate. That
#: is accepted because these hold prose, not behaviour -- nothing here is
#: imported and then silently relied on, which is the failure the gate exists to
#: stop. NO CODE TREE gets this carve-out; core/, live/, harness/ and tools/
#: always need a row.
#: `docs/specs/` was here until H9 and has been REMOVED. The specs turned out to
#: be adopted, not authored, and all thirteen carry ADOPTION-LOG rows -- so the
#: carve-out was buying nothing and costing the gate its reach over a directory
#: that now holds the system's most load-bearing documents.
NATIVE_PREFIXES = ("handoff/", "docs/observations/", "docs/regime-snapshots/",
                   "christoph/")


def is_native(path: str) -> bool:
    return path.startswith(NATIVE_PREFIXES)


def accounted_for() -> set[str]:
    return (
        BOOTSTRAP_ALLOWLIST
        | logged_paths("ADOPTION-LOG.md", 1)
        | logged_paths("EVIDENCE-CARRY.md", 1)
    )


def test_every_tracked_file_is_accounted_for() -> None:
    """The rule. A file in git that nobody logged arrived by copying."""
    known = accounted_for()
    orphans = sorted(f for f in tracked_files() if f not in known and not is_native(f))
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


def test_no_code_tree_is_native() -> None:
    """The carve-out must never reach a directory that holds behaviour. If
    NATIVE_PREFIXES ever grows to include one, every file in it stops needing an
    adoption row and the gate quietly stops applying to code."""
    for tree in ("core/", "live/", "harness/", "tools/"):
        assert not is_native(tree + "anything.py"), (
            f"NATIVE_PREFIXES now exempts {tree} -- that is a code tree, and exempting it "
            "means files with behaviour can arrive with no provenance and no test."
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
