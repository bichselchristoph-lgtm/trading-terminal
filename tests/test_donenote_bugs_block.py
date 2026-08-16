"""**053 Part 5, test 2.** A done-note carries its findings as DATA.

There is no path from a bug found here to the tracker the design session keeps.
This session writes prose; somebody then retypes it into a sheet. **All 88 rows
in that sheet exist because they were typed**, and a finding that is not retyped
is a finding that did not happen.

`bugs:` in done-note frontmatter closes that. It is **present and possibly
empty, never absent** -- `bugs: []` says *I looked and found none*, a missing
block says *nobody knows whether I looked*, and those must not look alike.

**Ids are never allocated here.** `id: NEW` for a row that does not exist yet;
the design session holds the sheet and allocates on rebuild. Allocating from
this side would be a number inferred rather than read -- the exact defect that
put four duplicate ids in the observations ledger.

**WATERMARK, not an allowlist.** The rule begins at `053`, the task that
introduced it. Retrofitting `bugs:` onto forty historical done-notes would mean
inventing findings nobody recorded, which is fabricated evidence in the one
folder whose whole value is being a true record of what happened. Notes below
the line are left exactly as written.
"""

from __future__ import annotations

import pathlib
import re

import pytest

yaml = pytest.importorskip("yaml")

REPO = pathlib.Path(__file__).resolve().parents[1]
DONE = REPO / "handoff" / "done"

#: The task this rule starts at. See WATERMARK note in the module docstring.
FROM_TASK = 53

_NUM = re.compile(r"^(\d+)")
_FM = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.S)
_ID = re.compile(r"\A(B-\d{3,}|NEW)\Z")

ACTIONS = {"raise", "correct", "close", "confirm"}


def notes_in_scope() -> list[pathlib.Path]:
    out = []
    for p in sorted(DONE.glob("*.md")):
        m = _NUM.match(p.name)
        if m and int(m.group(1)) >= FROM_TASK:
            out.append(p)
    return out


def test_the_scope_is_not_empty() -> None:
    """A rule that matches no files is green for the wrong reason."""
    assert notes_in_scope(), (
        f"no done-notes numbered {FROM_TASK} or higher found in {DONE}. "
        "This test would pass vacuously; that is the shape of the defect it "
        "exists to prevent.")


def test_every_done_note_in_scope_carries_a_bugs_block() -> None:
    for path in notes_in_scope():
        fm = _FM.match(path.read_text(encoding="utf-8"))
        assert fm, f"{path.name}: no YAML frontmatter block found."
        data = yaml.safe_load(fm.group(1)) or {}
        assert "bugs" in data, (
            f"{path.name}: frontmatter has no `bugs:` key. **Use `bugs: []` "
            "when there are none.** An empty block and a missing block must "
            "not look alike -- one says nothing was found, the other says "
            "nobody knows whether anyone looked.")
        entries = data["bugs"] or []
        for i, e in enumerate(entries):
            where = f"{path.name} bugs[{i}]"
            for key in ("id", "action", "status"):
                assert key in e, f"{where}: missing `{key}`."
            assert _ID.match(str(e["id"])), (
                f"{where}: id is {e['id']!r}; expected `B-NNN` for an existing "
                "row or the literal `NEW` for one that does not exist yet. "
                "**Do not allocate a B number from this side** -- the design "
                "session holds the sheet and allocates on rebuild.")
            assert e["action"] in ACTIONS, (
                f"{where}: action is {e['action']!r}; expected one of "
                + ", ".join(sorted(ACTIONS)))
