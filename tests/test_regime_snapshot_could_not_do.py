"""Rule 15's precondition, enforced. The grouping itself is NOT built here.

027 part 2. Five `could_not_do` entries sat in a daily file for four consecutive
sessions and nothing broke, because rule 15 lived in prose. The fix this project
uses everywhere is that *something has to fail*.

**But the grouping cannot be built soundly against the current format, and 027
says so before asking for it**: `could_not_do` is a list of FREE-TEXT STRINGS in
`docs/specs/REGIME-PROMPT.md` --

    could_not_do:
      - "Row 10 gap breadth -- no source wired"

-- with no `id` and no key, and the 2026-08-13 entries embed that session's own
numbers ("0 shares traded through 05:15 ET"), so exact matching cannot group
them across sessions. **A matcher that silently mis-groups is worse than no
test, because its green would mean nothing.** So no heuristic was written.

What IS built here is the precondition, and it is sound because it does no
grouping at all:

1. **Every `could_not_do` entry must carry a stable `id`.** Zero snapshots exist
   today, so this is vacuous *now* -- and it goes red the moment a snapshot lands
   without one, which is the only moment it could still be cheap to fix.
2. **The vacuity is printed on every run**, via `tests/conftest.py`, because a
   check over an empty folder that reports nothing is indistinguishable from a
   check that found nothing. Same reasoning as the credential-scan header.

**When the prompt gains the `id`, `test_the_format_still_lacks_a_key` goes red.**
That is the trigger to come back and build the real grouping -- deliberately, so
the missing matcher cannot be forgotten the way rule 15 itself was.

See OBS-028.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
SNAPSHOT_DIR = REPO / "docs" / "regime-snapshots"
PROMPT = REPO / "docs" / "specs" / "REGIME-PROMPT.md"


def snapshots() -> list[Path]:
    return sorted(p for p in SNAPSHOT_DIR.glob("*.yaml") if p.is_file())


def could_not_do_entries(path: Path) -> list:
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        pytest.fail(f"{path.name} is not valid YAML: {exc}. REGIME-PROMPT rule 4 says a "
                    "malformed snapshot poisons every later query -- this is that.")
    if not isinstance(doc, dict):
        return []
    return doc.get("could_not_do") or []


def snapshot_report() -> list[str]:
    """One line for the pytest header. **A vacuous check must announce itself.**"""
    found = snapshots()
    if not found:
        return ["regime snapshots: 0 present -- rule-15 grouping cannot run (OBS-028); "
                "docs/regime-snapshots/ holds only .gitkeep"]
    keyed = sum(1 for p in found for e in could_not_do_entries(p)
                if isinstance(e, dict) and e.get("id"))
    total = sum(len(could_not_do_entries(p)) for p in found)
    return [f"regime snapshots: {len(found)} present, {total} could_not_do entries, "
            f"{keyed} carrying an id"]


def test_the_snapshot_folder_exists() -> None:
    """If the folder is gone the two tests below pass over an empty list and this
    file silently stops checking anything."""
    assert SNAPSHOT_DIR.is_dir(), (
        f"{SNAPSHOT_DIR} is missing. Every check here iterates it, so its absence "
        "makes them all vacuously green.")


def test_every_could_not_do_entry_carries_a_stable_id() -> None:
    """**The precondition for rule 15, and the only sound half available today.**

    No grouping, no fuzzy matching, no heuristic -- it asks one question of each
    entry: can this be recognised as the same item next session?

    Vacuous while zero snapshots exist. That is stated in the report header on
    every run rather than hidden, and it goes red on the FIRST snapshot that
    lands without an id -- when fixing the format is still cheap, instead of
    after a hundred sessions of unkeyed history.
    """
    unkeyed = []
    for path in snapshots():
        for i, entry in enumerate(could_not_do_entries(path)):
            if not (isinstance(entry, dict) and str(entry.get("id", "")).strip()):
                shown = entry if isinstance(entry, str) else repr(entry)
                unkeyed.append(f"{path.name}[{i}]  {shown!s:.70}")

    assert not unkeyed, (
        "these could_not_do entries carry no stable `id`:\n  " + "\n  ".join(unkeyed) +
        "\n\nRule 15 counts an entry's RECURRENCE across sessions, which needs a key that "
        "does not\nchange when the session's numbers do. Free text cannot supply one: "
        "'HYG 0 shares\nthrough 05:15' and 'HYG 0 shares through 05:20' are the same "
        "finding and different\nstrings.\n\nThis is a requirement on docs/specs/"
        "REGIME-PROMPT.md, not a defect in the snapshot --\nsee OBS-028. Do NOT fix it by "
        "adding a fuzzy matcher here."
    )


def test_the_format_still_lacks_a_key() -> None:
    """**A tripwire that fires on SUCCESS, and it is deliberate.**

    While `REGIME-PROMPT.md` documents `could_not_do` as a bare string list,
    there is nothing to group on and the real rule-15 matcher must not be
    written. **When the prompt is amended to carry an `id`, this test goes red**
    -- which is the signal to come back and build the grouping.

    Without it, the amendment lands, the precondition above starts passing
    meaningfully, and the matcher nobody built is forgotten exactly the way rule
    15 itself was for four days.
    """
    assert PROMPT.exists(), f"{PROMPT} is missing"
    text = PROMPT.read_text(encoding="utf-8")

    block = text.split("could_not_do:", 1)
    assert len(block) > 1, (
        "REGIME-PROMPT.md no longer documents a `could_not_do:` block. Either the "
        "schema moved or the prompt was re-supplied without it -- both change what "
        "this file can assert.")

    # The documented example, taken up to the end of its YAML fence.
    example = block[1].split("```", 1)[0]
    documented_entries = [l.strip() for l in example.splitlines() if l.strip().startswith("-")]
    assert documented_entries, "no example entries found under could_not_do:"

    assert not any("id:" in l for l in documented_entries), (
        "REGIME-PROMPT.md now documents an `id` on could_not_do entries.\n\n"
        "**This test failing is the GOOD outcome.** It is the trigger to build the "
        "rule-15\ngrouping that 027 part 2 could not build soundly: entries can now be "
        "matched on a\nstable key instead of on free text.\n\nTo clear it: implement the "
        "recurrence grouping, assert 3+ consecutive sessions with\nno matching "
        "OBSERVATIONS.md row fails, then delete this tripwire and say so in the\ndone-note. "
        "Do not silence it. See OBS-028."
    )
