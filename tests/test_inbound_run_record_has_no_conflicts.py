"""**053 Part 5, test 5.** The inbound copier reports zero content conflicts.

`sync.ps1` refuses to overwrite a file that is present in the tree and differs
from the Drive copy, exits non-zero, and says so. That refusal is CORRECT -- a
handed-off file that changes breaks a reference another party is holding, and
may already have been read and acted on.

**But a refusal nobody clears is a refusal that stops carrying information.**
`040` and `043` have differed since `045` and `046` §9.4 and nobody has owned
them since; the copier has printed the same two names on every run for days,
and the run before this one printed three. **That is the state this test makes
loud.**

**No allowlist, deliberately.** The known conflicts are not exempted. An
allowlist for known conflicts is precisely how a red test becomes furniture,
which is what these two already became inside the copier's own output.

**Green means resolved, and resolving is a HUMAN act**: read both copies,
decide which is current, and either retire the Drive copy or record a genuine
divergence as a finding. It is never cleared by overwriting -- 053's own
instruction is *do not resolve any of those conflicts by overwriting.*
"""

from __future__ import annotations

import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[1]
RECORD = REPO / "sync-run-record.md"

#: `outcome      : <pair>: ... | <pair>: ...`. Tolerates leading whitespace for
#: the same reason `tools/sync_from_drive.py` does -- see its `_FIELD`.
_OUTCOME = re.compile(r"(?m)^\s*outcome\s*:\s*(.+?)\s*$")

#: `3 differing` inside one pair's segment.
_DIFFERING = re.compile(r"(\d+)\s+differing")


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


def test_the_run_record_parses() -> None:
    assert outcome().strip(), f"{RECORD.name} has an empty outcome field."


def test_the_inbound_sync_reports_no_content_conflicts() -> None:
    line = outcome()
    offenders = []
    for segment in line.split("|"):
        segment = segment.strip()
        m = _DIFFERING.search(segment)
        if m and int(m.group(1)) > 0:
            offenders.append("  " + segment)

    assert not offenders, (
        "the last inbound sync refused to overwrite files that are present in "
        "the tree and differ from the Drive copy:" + chr(10)
        + chr(10).join(offenders) + chr(10) + chr(10)
        + "**The refusal is correct. Leaving it standing is not.** A handed-off "
          "file that differs means Drive and the tree disagree about a document "
          "one of them has already been read from, and until somebody rules, "
          "every session reads whichever copy it happens to reach." + chr(10)
        + "Known standing conflicts as of 2026-08-16: **040** and **043**, "
          "differing since 045 / 046 s9.4, plus the 049/050/052/053 reissues -- "
          "the design session replaced task files under the same filenames, "
          "which the copy-and-keep rule forbids." + chr(10)
        + "**Resolve by ruling, never by overwriting.** Decide which side is "
          "current; retire the Drive copy, or record a genuine divergence as a "
          "finding. Do not add an exemption here.")
