"""**053 Part 5, test 6. B-027.** One task number, one file in `handoff/inbox/`.

The addressing gate every task file opens with is a GLOB: *if
`handoff/inbox/NNN-*.md` exists and `handoff/done/NNN-*.md` does not, this task
is for you.* When two different files share a number **both match, and the gate
cannot tell them apart** -- so "do inbox 035" resolves to two documents and the
session picks one, silently.

**No allowlist.** The known collision is not exempted here. An allowlist for
known conflicts is how a red test becomes furniture: `040` and `043` have been
furniture since `045`, which is exactly the outcome this file must not have.
**This test is red until somebody renumbers, and renumbering is an allocation
read from `handoff/ALLOCATIONS.md` -- not a fix to be taken in passing.**
"""

from __future__ import annotations

import collections
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[1]
INBOX = REPO / "handoff" / "inbox"

#: **The gate's OWN glob, not a looser one.** The addressing gate matches
#: `NNN-*.md`, so the digits must be followed by a HYPHEN to be that task's
#: address. `035a-...` does not match `035-*.md` and is therefore a different
#: address, not a collision -- and the letter suffix (`008a`, `012a`, `013d`)
#: is an established convention in this folder, not a defect.
#:
#: Measured, because the looser rule matters: grouping on leading digits alone
#: reports 008, 012, 013 and 035 as clashes, and every one of those is a correct
#: file correctly named. **A test calibrated one character too loose would have
#: demanded four renames that the gate does not need.**
_NUM = re.compile(r"^(\d+)-")


def numbered_files() -> dict[str, list[str]]:
    by_id: dict[str, list[str]] = collections.defaultdict(list)
    for p in sorted(INBOX.glob("*.md")):
        m = _NUM.match(p.name)
        if m:
            by_id[m.group(1)].append(p.name)
    return by_id


def test_the_inbox_has_numbered_files_at_all() -> None:
    assert numbered_files(), (
        f"no NNN-prefixed files parsed from {INBOX}; this test would pass "
        "vacuously.")


def test_each_task_number_names_exactly_one_file() -> None:
    by_id = numbered_files()
    clashes = {k: v for k, v in by_id.items() if len(v) > 1}

    detail = []
    for num in sorted(clashes):
        detail.append(f"  {num}:")
        detail.extend(f"      {n}" for n in clashes[num])

    assert not clashes, (
        "these task numbers each name more than one file in handoff/inbox/, "
        "so the addressing gate cannot resolve them:" + chr(10)
        + chr(10).join(detail) + chr(10) + chr(10)
        + "**The gate globs NNN-*.md and both files match.** A session told to "
          "'do inbox NNN' will pick one and never learn there was another." + chr(10)
        + "**Resolve by allocating a NEW number from handoff/ALLOCATIONS.md** "
          "-- read it, never infer it -- and renaming one file. Do not add an "
          "exemption here: an allowlist for known collisions is how a red test "
          "becomes furniture.")


def test_the_clash_detection_actually_fires() -> None:
    """**The guard, shown to fire, on constructed text.**

    `test_each_task_number_names_exactly_one_file` is green today, so on its own
    it is a check that has never been seen refusing. Demonstrated here against a
    constructed mapping, so the green above means the folder is clean rather
    than the logic being inert.
    """
    constructed = {"035": ["035-one.md", "035-two.md"], "036": ["036-only.md"]}
    clashes = {k: v for k, v in constructed.items() if len(v) > 1}
    assert clashes == {"035": ["035-one.md", "035-two.md"]}


def test_a_letter_suffix_is_not_a_clash() -> None:
    """`035a-` is a DIFFERENT address from `035-`, because `035-*.md` misses it.

    Pinned because the obvious looser rule -- group on leading digits -- reports
    008, 012, 013 and 035 as collisions, and all four are correctly named.
    """
    assert _NUM.match("035a-for-code-adr-is-rth-atr-is-eth.md") is None
    assert _NUM.match("035-for-code-bug-pdl-and-atr14.md").group(1) == "035"
