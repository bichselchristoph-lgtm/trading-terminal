"""**053 Part 5, test 5.** The inbound copier reports zero content conflicts.

`sync.ps1` refuses to overwrite a file that is present in the tree and differs
from the Drive copy, exits non-zero, and says so. That refusal is CORRECT -- a
handed-off file that changes breaks a reference another party is holding, and
may already have been read and acted on.

**But a refusal nobody clears is a refusal that stops carrying information.**
`040` and `043` have differed since `045` and `046` §9.4 and nobody has owned
them since; the copier has printed the same names on every run for days.
**That is the state this test makes loud.**

**No allowlist, deliberately.** The known conflicts are not exempted. An
allowlist for known conflicts is precisely how a red test becomes furniture,
which is what these two already became inside the copier's own output.

**Green means resolved, and resolving is a HUMAN act**: read both copies,
decide which is current, and either retire the Drive copy or record a genuine
divergence as a finding. It is never cleared by overwriting -- 053's own
instruction is *do not resolve any of those conflicts by overwriting.*

---

**056: this file matches the `refused` COUNT, never the `outcome` PROSE.**

`tools/sync_from_drive.py` describes the same condition -- files refused,
because they differ and were not overwritten -- two different ways depending
on whether anything else copied in the same run: `"0 new · N REFUSED"` when
nothing new copied alongside the refusal, `"N differing"` when something did.
The version of this test that matched `"N differing"` reported GREEN on
2026-08-16 while `040`, `043` and `052` were all being refused, because the
sync that ran that day happened to print the `"REFUSED"` wording -- it caught
the condition only by accident on runs where something else copied alongside
it. **Widening the regex to match both wordings was ruled out**: that leaves
the same defect one rewording away, and the rewording will happen, because the
outcome line is prose written for a human reader.

The fix is a MACHINE-READABLE `refused` field on the run record, one count per
pair, written by `tools/sync_from_drive.py` on every invocation. This test
reads that field and never inspects `outcome`'s wording at all.
"""

from __future__ import annotations

import pathlib
import re
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tools.sync_from_drive import write_record

RECORD = REPO / "sync-run-record.md"

#: `outcome      : <pair>: ... | <pair>: ...`. Tolerates leading whitespace for
#: the same reason `tools/sync_from_drive.py` does -- see its `_FIELD`.
_OUTCOME = re.compile(r"(?m)^\s*outcome\s*:\s*(.+?)\s*$")

#: `refused      : <pair>: <N> | <pair>: <N> ...`. Same tolerance, same reason.
_REFUSED = re.compile(r"(?m)^\s*refused\s*:\s*(.+?)\s*$")

#: One pair's segment of the `refused` field: `handoff_inbox: 3`.
_PAIR_COUNT = re.compile(r"([\w.-]+)\s*:\s*(\d+)")


def outcome() -> str:
    assert RECORD.exists(), (
        f"{RECORD.name} does not exist. The inbound copier writes it on every "
        "invocation; if it is missing the copier has not run, and this test "
        "cannot report on conflicts it never observed.")
    m = _OUTCOME.search(RECORD.read_text(encoding="utf-8"))
    assert m, (
        f"no `outcome` field parsed from {RECORD.name}; the reader has drifted "
        "from the writer and this test is no longer checking anything.")
    return m.group(1)


def refused_field(text: str) -> str:
    """The `refused` field's raw value. **Absence is a failure to report, not
    a clean run** -- tenet 2: an absent field is never read as zero."""
    m = _REFUSED.search(text)
    assert m, (
        "no `refused` field parsed. Absence is not zero: a run record that "
        "never reported a per-pair refusal count must not be read as a clean "
        "run -- it means the copier that wrote this record predates 056, or "
        "wrote a malformed field.")
    return m.group(1)


def offending_pairs(refused_text: str) -> list[str]:
    """Every pair segment whose refused count is nonzero."""
    return [f"{pair}: {n}" for pair, n in _PAIR_COUNT.findall(refused_text)
            if int(n) > 0]


def test_the_run_record_parses() -> None:
    assert outcome().strip(), f"{RECORD.name} has an empty outcome field."


def test_the_inbound_sync_reports_no_refusals() -> None:
    text = RECORD.read_text(encoding="utf-8")
    offenders = offending_pairs(refused_field(text))

    assert not offenders, (
        "the last inbound sync refused to overwrite files that are present in "
        "the tree and differ from the Drive copy, by pair:" + chr(10)
        + chr(10).join("  " + o for o in offenders) + chr(10) + chr(10)
        + "**The refusal is correct. Leaving it standing is not.** A handed-off "
          "file that differs means Drive and the tree disagree about a document "
          "one of them has already been read from, and until somebody rules, "
          "every session reads whichever copy it happens to reach." + chr(10)
        + "**Resolve by ruling, never by overwriting.** Decide which side is "
          "current; retire the Drive copy, or record a genuine divergence as a "
          "finding. Do not add an exemption here.")


# ---- 056: the field-based logic, proven on constructed fixtures -----------
#
# **Demonstrates the exact red/red/green sequence the task requires**, against
# fixtures built with the real `write_record()` rather than hand-typed text --
# so these tests exercise the same writer the committed record is built by.


def test_a_nonzero_refused_count_is_caught(tmp_path: pathlib.Path) -> None:
    rec = tmp_path / "rec.md"
    write_record(
        attempt="A", success="S",
        outcome="handoff_inbox: 0 new · 3 REFUSED · 23 unchanged",
        refused="regime_snapshots: 0 | handoff_inbox: 3 | christoph_open: 0",
        path=rec)
    offenders = offending_pairs(refused_field(rec.read_text(encoding="utf-8")))
    assert offenders == ["handoff_inbox: 3"]


def test_an_absent_refused_field_is_a_failure_to_report(
        tmp_path: pathlib.Path) -> None:
    """**Not the field missing by accident -- a record written before 056.**
    Absence must read as *unknown*, never as *clean*, exactly like `never` for
    `last_success` in `tools.sync_from_drive.read_field`."""
    rec = tmp_path / "rec.md"
    rec.write_text(
        "last_attempt : A\n\nlast_success : S\n\noutcome      : x\n",
        encoding="utf-8")
    with pytest.raises(AssertionError, match="no `refused` field parsed"):
        refused_field(rec.read_text(encoding="utf-8"))


def test_a_refused_count_of_zero_for_every_pair_is_clean(
        tmp_path: pathlib.Path) -> None:
    rec = tmp_path / "rec.md"
    write_record(
        attempt="A", success="S",
        outcome="regime_snapshots: 0 new · up to date (2 unchanged) | "
                "handoff_inbox: 0 new · up to date (23 unchanged) | "
                "christoph_open: 0 new · up to date (14 unchanged)",
        refused="regime_snapshots: 0 | handoff_inbox: 0 | christoph_open: 0",
        path=rec)
    offenders = offending_pairs(refused_field(rec.read_text(encoding="utf-8")))
    assert offenders == []
