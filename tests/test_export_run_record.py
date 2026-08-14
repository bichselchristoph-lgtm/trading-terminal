"""The export leaves a record of every attempt, and this test is why it keeps doing so.

037. On 2026-08-13 the export ran at 22:12:59 and was not invoked again for
fifteen hours. Nothing said so. The only artifact it produced was a manifest
*inside each destination*, written *only on success*, so three different states
-- ran and copied nothing, never ran at all, ran and died -- all looked
identical from outside.

`export-run-record.md` is the fix, and this file is what stops the fix being
quietly removed.

NOT TIME-BASED, deliberately. A test that goes red because nothing ran last
night is a test that gets ignored, and this repository already carries several
of those. Nothing here asserts how OLD `last_success` is -- `verify.ps1`
section 5 prints the age and a human reads it. What is asserted is that the
record exists, parses, and is still being written by the copier.

SCOPED POSITIONALLY. Every assertion names one of exactly two paths --
`export-run-record.md` and `export-handoff.ps1`. Nothing here searches the tree
for timestamp-shaped strings: a repo-wide scan would match its own fixtures and
its own docstring, which is the self-reference trap that fired five times in one
session while 037 was being written.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

#: The two files this test is allowed to look at. Named once, here.
RUN_RECORD = REPO / "export-run-record.md"
COPIER = REPO / "export-handoff.ps1"

#: `^\s*` rather than `^`: the first cut of the copier indented these fields to
#: render them as a markdown code block, and the bare anchor stopped matching --
#: so every failed run silently reset `last_success` to `never`. Both the copier
#: and this test now tolerate leading whitespace, and the copier writes at
#: column zero. Either alone would do; having both is the point.
FIELD = r"(?m)^\s*{}\s*:\s*(.+?)\s*$"


def field(text: str, name: str) -> str | None:
    m = re.search(FIELD.format(name), text)
    return m.group(1) if m else None


def parse_stamp(value: str) -> datetime:
    """ISO-8601 with offset, matching the manifest's `exported` stamp.

    An offset-less timestamp is ambiguous across the DST change, and session
    logic in this project is US/Eastern while the copier runs on a machine in
    CEST -- so a naive stamp would be unreadable by whichever half was not
    holding the assumption.
    """
    return datetime.fromisoformat(value)


def test_the_run_record_exists() -> None:
    """Absent is red. It is tracked precisely so this assertion has a subject on
    a fresh clone, rather than being red for the uninteresting reason that
    nobody has run an export here yet."""
    assert RUN_RECORD.exists(), (
        f"{RUN_RECORD.name} is missing. The export writes it on every invocation, "
        "success and failure alike -- so its absence means either the copier stopped "
        "recording or somebody deleted the one artifact that can report a sync that "
        "never ran. See handoff/inbox/037-for-code-bug-drive-export-stopped.md."
    )


def test_it_carries_both_timestamps_and_they_parse() -> None:
    """`last_attempt` moving while `last_success` stays put IS the signature of
    a broken export. Both fields have to be there for that comparison to exist."""
    text = RUN_RECORD.read_text(encoding="utf-8")

    attempt = field(text, "last_attempt")
    assert attempt, f"{RUN_RECORD.name} has no `last_attempt` line"
    parse_stamp(attempt)  # raises ValueError, which is the failure we want

    success = field(text, "last_success")
    assert success, f"{RUN_RECORD.name} has no `last_success` line"
    if success != "never":
        parse_stamp(success)


def test_it_carries_an_outcome_and_a_head() -> None:
    """`outcome` is the line a human reads. `head` ties the run to a commit, so
    a mirror can be placed in history rather than merely dated."""
    text = RUN_RECORD.read_text(encoding="utf-8")
    for name in ("outcome", "head"):
        assert field(text, name), f"{RUN_RECORD.name} has no `{name}` line"


def test_the_outcome_is_one_line() -> None:
    """A nine-line outcome is a stack trace wearing a field name, and it breaks
    every parser above. The copier takes the first line of an exception message
    on purpose; this asserts it kept doing so."""
    text = RUN_RECORD.read_text(encoding="utf-8")
    outcome = field(text, "outcome")
    assert outcome and "\n" not in outcome


def _pwsh() -> str:
    exe = shutil.which("pwsh")
    assert exe, (
        "pwsh (PowerShell 7+) not found. export-handoff.ps1 is PowerShell 7 only -- "
        "it uses [IO.Path]::GetRelativePath and utf8NoBOM, both .NET Core -- so a "
        "machine without pwsh has no working export at all. This is a hard failure "
        "rather than a skip, because a skip renders as a bare `s` and invisibility "
        "is the entire defect 037 exists to fix."
    )
    return exe


def _run(tmp_path: Path, drive_root: Path) -> tuple[subprocess.CompletedProcess, Path]:
    record = tmp_path / "rec.md"
    proc = subprocess.run(
        [
            _pwsh(), "-NoProfile", "-File", str(COPIER),
            "-DriveRootOverride", str(drive_root),
            "-RunRecordOverride", str(record),
        ],
        capture_output=True, text=True, cwd=str(REPO),
    )
    return proc, record


def test_a_successful_run_writes_the_record(tmp_path: Path) -> None:
    """The behavioural half. A static check on the committed file would still
    pass against a copier that had stopped writing it -- the record would simply
    go stale, which is indistinguishable from an export nobody ran, which is the
    original bug.

    Both overrides point into tmp_path, so this never touches the real Drive
    folders and never touches the real run record.
    """
    drive = tmp_path / "drive"
    drive.mkdir()
    proc, record = _run(tmp_path, drive)

    assert proc.returncode == 0, f"export failed:\n{proc.stdout}\n{proc.stderr}"
    assert record.exists(), "a successful export wrote no run record"

    text = record.read_text(encoding="utf-8")
    attempt = field(text, "last_attempt")
    success = field(text, "last_success")
    assert attempt and success
    assert success != "never", "a successful run left `last_success` unset"
    assert parse_stamp(success) >= parse_stamp(attempt)


def test_an_unreachable_destination_still_writes_the_record(tmp_path: Path) -> None:
    """037's refusal test, executed rather than described.

    Three things at once, and all three were absent before 037: the copier says
    `destination unreachable` in those words, it exits non-zero, and it STILL
    writes the record -- carrying `last_success` forward untouched, because the
    gap between the two timestamps is the only thing that says how long the
    design session has been reading stale files.
    """
    drive = tmp_path / "drive"
    drive.mkdir()
    proc, record = _run(tmp_path, drive)
    assert proc.returncode == 0
    good_success = field(record.read_text(encoding="utf-8"), "last_success")
    assert good_success and good_success != "never"

    missing = tmp_path / "no-such-drive-root"
    proc2 = subprocess.run(
        [
            _pwsh(), "-NoProfile", "-File", str(COPIER),
            "-DriveRootOverride", str(missing),
            "-RunRecordOverride", str(record),
        ],
        capture_output=True, text=True, cwd=str(REPO),
    )

    assert proc2.returncode != 0, "an unreachable destination exited 0"
    assert "destination unreachable" in proc2.stdout, (
        "the copier did not name the failure on stdout:\n" + proc2.stdout
    )

    text = record.read_text(encoding="utf-8")
    assert field(text, "outcome", ).startswith("FAILED"), (
        "a failed run did not record itself as FAILED: " + str(field(text, "outcome"))
    )
    assert field(text, "last_success") == good_success, (
        "a failed run moved or cleared `last_success`. That is the bug 037 fixed, "
        "reintroduced: the whole value of the record is that `last_attempt` moves "
        "and `last_success` does not."
    )
    assert parse_stamp(field(text, "last_attempt")) >= parse_stamp(good_success)
