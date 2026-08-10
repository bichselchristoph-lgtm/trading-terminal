"""Carried evidence still hashes to what EVIDENCE-CARRY.md recorded.

M001 §4: evidence is carried byte-identical and must never be cleaned, deduped,
reformatted, pruned or regenerated. Those are all edits that leave a file looking
perfectly well-formed -- which is exactly why a hash, rather than a convention,
is what guards them. A tidied ledger reads as a record of what happened.

This test is the difference between "we said we would not touch it" and "we can
prove nobody did".
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
MANIFEST = REPO / "EVIDENCE-CARRY.md"

ROW = re.compile(r"^\|\s*\d{4}-\d{2}-\d{2}\s*\|\s*`(?P<rel>[^`]+)`\s*\|\s*`[^`]+`\s*\|\s*"
                 r"`(?P<sha>[0-9a-f]{64})`\s*\|")


def manifest_rows() -> list[tuple[str, str]]:
    if not MANIFEST.exists():
        return []
    out = []
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        m = ROW.match(line)
        if m:
            out.append((m.group("rel"), m.group("sha")))
    return out


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


ROWS = manifest_rows()


def test_the_manifest_parses() -> None:
    """A manifest this test cannot read would make every check below vacuous --
    the same 'passes by finding nothing' failure the old secrets test had."""
    assert MANIFEST.exists(), "EVIDENCE-CARRY.md is missing; the carry is unverifiable."
    assert ROWS, (
        "EVIDENCE-CARRY.md parsed to zero rows. Either the carry recorded nothing or the "
        "table shape changed and this test is now checking nothing at all."
    )


def test_every_carried_file_is_present() -> None:
    absent = sorted(rel for rel, _ in ROWS if not (REPO / rel).exists())
    assert not absent, (
        "evidence recorded as carried is missing from the tree:\n  " + "\n  ".join(absent)
        + "\n\nEvidence cannot be regenerated from a spec. If one of these was deleted, it "
        "is gone."
    )


def test_no_carried_file_has_been_modified() -> None:
    changed = []
    for rel, expected in ROWS:
        p = REPO / rel
        if not p.exists():
            continue
        actual = sha256(p)
        if actual != expected:
            changed.append(f"{rel}\n      recorded {expected}\n      now      {actual}")
    assert not changed, (
        "carried evidence has been modified since the carry:\n  " + "\n  ".join(changed)
        + "\n\nEvidence is carried verbatim and never cleaned, deduped, reformatted or "
        "regenerated.\nIf a file looked wrong, the rule was to say so and carry it anyway. "
        "Restore it from\nD:\\Dev\\momentum-harness, which is archived reference and still "
        "holds the original."
    )


@pytest.mark.parametrize("ledger", ["spend_ledger.jsonl", "membership_evidence.json"])
def test_the_named_ledgers_carried(ledger: str) -> None:
    """M001 §4 names these two explicitly. A carry that silently skipped one
    would still produce a green manifest of whatever it did copy."""
    assert any(rel == ledger for rel, _ in ROWS), (
        f"{ledger} is named in M001 §4's carry-list but is not in EVIDENCE-CARRY.md."
    )
