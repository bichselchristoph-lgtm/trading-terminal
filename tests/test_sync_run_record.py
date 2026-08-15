"""043 part 2 — the inbound copier leaves a record, **including when it fails.**

`037` gave the outbound export a run record on every attempt and said plainly
that `tools/sync_from_drive.py` had the same defect and was worse off: three
stdout lines and nothing on disk. This is the follow-through.

**The record's whole value is in the failure case.** A copier that succeeds is
already visible — the files are there. A copier that has not run since Tuesday
looks exactly like one that ran and found nothing, and `verify.ps1` cannot tell
those apart without a timestamp on disk.

----

**`037` reintroduced its own bug inside its own fix.** It indented the record's
fields four spaces so they would render as a markdown code block, which meant
`^last_success` never matched — so every failed run read the previous success as
`never` and wrote that back. **The record silently forgot every success it had
ever had, and it looked perfectly fine to a reader.**

It was found by executing the refusal, not by reading the code. These tests do
the same: they run both failure paths for real and read the file afterwards.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tools.sync_from_drive import RUN_RECORD, read_field, write_record

TOOL = REPO / "tools" / "sync_from_drive.py"


def run_sync(config: Path, record: Path) -> subprocess.CompletedProcess:
    """The tool as a PROGRAM, not as an import.

    `032` and `029` are both about the gap between a library that passes its
    tests and a program that cannot start. The record is written by `main()`, so
    `main()` is what runs here.
    """
    return subprocess.run(
        [sys.executable, str(TOOL), "--config", str(config), "--record", str(record)],
        capture_output=True, text=True, cwd=str(REPO))


def write_config(path: Path, *, src: Path, dst: Path) -> Path:
    path.write_text(
        "pairs:\n"
        "  - id: p\n"
        f"    from: '{src}'\n"
        f"    to: '{dst}'\n"
        "    glob: '*.md'\n"
        "    checks: []\n", encoding="utf-8")
    return path


# ---- the record in the repository ----------------------------------------


def test_the_committed_record_exists_and_parses() -> None:
    """**Red if the record stops existing or stops parsing** — which is exactly
    what `037`'s indentation defect did without changing how the file looked."""
    assert RUN_RECORD.is_file(), (
        f"{RUN_RECORD} is missing. It is tracked, not gitignored, so a fresh "
        f"clone has a subject for this test.")
    for name in ("last_attempt", "last_success", "outcome"):
        assert read_field(name, RUN_RECORD) != "never" or name == "last_success", (
            f"`{name}` did not parse out of {RUN_RECORD}. The fields are at "
            f"column zero and indenting them into a code block is what broke "
            f"the equivalent parse in 037.")


def test_an_indented_field_still_parses_which_is_037s_remedy(tmp_path: Path) -> None:
    """**`037`'s defect cannot recur here, and this is the half that stops it.**

    `037` indented its fields four spaces to render them as a markdown code
    block while its reader anchored on a bare `^`. The field was *present and
    unmatched*, so every failed run read the previous success as `never` and
    wrote that back — the record forgot every success it had ever had, and it
    looked perfectly fine to a reader.

    **037 fixed it twice over on purpose**: fields at column zero *and* an
    anchor that tolerates whitespace, *"either alone would be enough, which is
    the point."* This asserts the second half. `test_the_committed_records_fields
    _are_at_column_zero` asserts the first.

    **The first cut of 043 asserted the opposite** — that an indented field must
    read as `never` — which pinned the intolerance as a feature and left this
    record one reformat away from the bug it was written to prevent.
    """
    good = tmp_path / "good.md"
    write_record(attempt="A", success="S", outcome="O", path=good)
    assert read_field("last_success", good) == "S"

    indented = tmp_path / "indented.md"
    indented.write_text(good.read_text(encoding="utf-8").replace(
        "last_success : S", "    last_success : S"), encoding="utf-8")
    assert read_field("last_success", indented) == "S", (
        "an indented field read as absent. That is 037's exact defect: the "
        "field is present, the anchor misses it, and the caller treats "
        "`never` as `no success has ever happened`.")


def test_the_committed_records_fields_are_at_column_zero() -> None:
    """The other half of the belt-and-braces, asserted separately.

    Tolerating indentation does not make indenting them *fine* — a reader
    comparing this file with `export-run-record.md` should see one format, and
    the two parsers agreeing is worth more than either being clever.
    """
    assert RUN_RECORD.is_file(), (
        f"{RUN_RECORD} is missing — see test_the_committed_record_exists_and_parses. "
        f"Asserted here too so this test FAILS rather than raising "
        f"FileNotFoundError: a traceback reads as a broken test, and a broken "
        f"test is the one people delete.")
    text = RUN_RECORD.read_text(encoding="utf-8")
    for name in ("last_attempt", "last_success", "outcome"):
        assert re.search(rf"(?m)^{name}\s*:", text), (
            f"`{name}` is not at column zero in {RUN_RECORD.name}. The reader "
            f"tolerates indentation, deliberately, but the written format is "
            f"column-zero and matches export-run-record.md.")


def test_an_absent_record_reads_as_never(tmp_path: Path) -> None:
    assert read_field("last_success", tmp_path / "nothing-here.md") == "never"


# ---- both failure paths, executed ----------------------------------------


@pytest.mark.parametrize("case,expect", [
    ("source", "source folder UNREACHABLE"),
    ("destination", "destination UNREACHABLE"),
])
def test_a_failing_run_exits_non_zero_and_still_writes_the_record(
        tmp_path: Path, case: str, expect: str) -> None:
    """**Both failures write the record.** 043: a copier that dies before
    recording anything is indistinguishable from one that never ran.

    **The destination case was not a failure at all before 043** — `dest.mkdir`
    raised `FileNotFoundError` and the tool died with a traceback, exiting
    non-zero only because an unhandled exception happens to exit 1. Luck, not a
    contract, and no record written either way.
    """
    src = tmp_path / "src"
    src.mkdir()
    (src / "001-for-code-a.md").write_text("x", encoding="utf-8")

    if case == "source":
        cfg = write_config(tmp_path / "c.yaml", src=tmp_path / "gone", dst=tmp_path / "dst")
    else:
        cfg = write_config(tmp_path / "c.yaml", src=src, dst=Path("Q:/nonexistent/dst"))

    record = tmp_path / "rec.md"
    proc = run_sync(cfg, record)

    assert proc.returncode != 0, (
        f"a {case} failure exited 0.\nstdout:\n{proc.stdout}")
    assert expect in proc.stdout, (
        f"expected {expect!r} on stdout, got:\n{proc.stdout}")
    assert "Traceback" not in proc.stderr, (
        f"the failure surfaced as a traceback rather than a named outcome:\n"
        f"{proc.stderr}")
    assert record.is_file(), "the failing run wrote no record at all"
    assert expect in read_field("outcome", record), (
        f"the record does not name the failure. outcome reads: "
        f"{read_field('outcome', record)!r}")


def test_a_failure_after_a_success_keeps_the_earlier_success(tmp_path: Path) -> None:
    """**The signature to look for**, and the one `037` destroyed.

    A run killed or refused mid-copy must leave `last_attempt` moved and
    `last_success` STALE. If a failure resets the success to `never`, the record
    can no longer answer *when did this last work* — which is its only question.
    """
    src = tmp_path / "src"
    src.mkdir()
    (src / "001-for-code-a.md").write_text("x", encoding="utf-8")
    record = tmp_path / "rec.md"

    ok = write_config(tmp_path / "ok.yaml", src=src, dst=tmp_path / "dst")
    assert run_sync(ok, record).returncode == 0
    succeeded_at = read_field("last_success", record)
    assert succeeded_at != "never"

    bad = write_config(tmp_path / "bad.yaml", src=tmp_path / "gone", dst=tmp_path / "dst")
    assert run_sync(bad, record).returncode != 0

    assert read_field("last_success", record) == succeeded_at, (
        "a failing run overwrote last_success. That is 037's defect: the "
        "record forgets every success it ever had, and looks fine doing it.")

    # **NOT `last_attempt != succeeded_at`.** That was the first version of this
    # assertion and it is flaky: `_now()` has one-second resolution, the two runs
    # complete inside the same second, and the test fails on a fast machine while
    # the code is correct. **A flaky test is worse than no test** — it teaches
    # people to re-run rather than to read.
    #
    # The deterministic form of the same property: the attempt is never EARLIER
    # than the last success, and the outcome now names the failure while the
    # success still names the earlier run.
    assert read_field("last_attempt", record) >= succeeded_at, (
        "last_attempt is earlier than last_success, which cannot happen")
    assert "UNREACHABLE" in read_field("outcome", record), (
        f"the outcome does not name the failure: "
        f"{read_field('outcome', record)!r}")


# ---- the four outcomes are four different sentences ----------------------


def test_a_refused_file_does_not_read_as_up_to_date(tmp_path: Path) -> None:
    """**043: a refused file is its own outcome.**

    Before this, a run whose only event was a refusal printed
    `0 new · up to date` — the same sentence as a run where everything was
    already in place. **The `035` collision made the copier exit 1 on every run
    for two days under a headline that said nothing was wrong.**
    """
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    dst.mkdir()
    # Same name, different bytes: refused, never overwritten.
    (src / "001-for-code-a.md").write_text("new", encoding="utf-8")
    (dst / "001-for-code-a.md").write_text("old", encoding="utf-8")

    cfg = write_config(tmp_path / "c.yaml", src=src, dst=dst)
    proc = run_sync(cfg, tmp_path / "rec.md")

    assert proc.returncode != 0, "a refusal must exit non-zero"
    assert "REFUSED" in proc.stdout, (
        f"a refusal did not get its own headline:\n{proc.stdout}")
    assert "up to date" not in proc.stdout, (
        f"a refusal still reads as `up to date`:\n{proc.stdout}")
    assert (dst / "001-for-code-a.md").read_text(encoding="utf-8") == "old", (
        "the refused file was overwritten")
