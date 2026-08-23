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

**068 Part C.** A note that has since been EXPORTED cannot be retrofitted the
way `061` retrofitted its own — `handoff/` is copy-and-keep, and an edit to an
already-exported note would put the tracked copy and the Drive copy out of
byte-sync on bytes, the exact `040`/`043`/`052` condition the inbound copier
has refused on since 2026-08-15. `058`'s note is in that state. **The guard
yields, the archive does not**: an exported note missing `bugs:` is reported
as a named, counted skip rather than a failure, and "exported" is read from
the export manifest (`tools/exported_notes.py`) rather than inferred from a
number or a date — raising `raising a task-number floor` above `058` would be
`B-029` again, protecting nothing that has not already happened to pass.
"""

from __future__ import annotations

import pathlib
import re
import sys
import warnings

import pytest

yaml = pytest.importorskip("yaml")

REPO = pathlib.Path(__file__).resolve().parents[1]
DONE = REPO / "handoff" / "done"
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tools.exported_notes import (ExportManifestUnreadable,
                                  exported_done_note_basenames, manifest_path)

#: The task this rule starts at. See WATERMARK note in the module docstring.
#: Mirrored in `tools/exported_notes.py` -- imported from there rather than
#: duplicated, so the two cannot check different sets of notes.
from tools.exported_notes import FROM_TASK

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
    # 068 Part C. Read BEFORE the loop and let a failure here abort the test
    # loudly -- "the test refuses by name rather than skipping everything" --
    # never caught and treated as "nothing is exported", which would exempt
    # nothing on a genuine failure and everything on a bug in this except
    # clause. Neither is acceptable, so neither is attempted.
    try:
        exported = exported_done_note_basenames()
    except ExportManifestUnreadable as exc:
        pytest.fail(
            f"the export manifest could not be read, so which done-notes are "
            f"already exported and out of scope for this guard cannot be "
            f"determined: {exc}\n\nThis test refuses rather than silently "
            f"treating every note as not-yet-exported (which would fail "
            f"correctly here, by luck) or as already-exported (which would "
            f"exempt everything). See tools/exported_notes.py.")

    for path in notes_in_scope():
        fm = _FM.match(path.read_text(encoding="utf-8"))
        assert fm, f"{path.name}: no YAML frontmatter block found."
        data = yaml.safe_load(fm.group(1)) or {}
        if "bugs" not in data and path.name in exported:
            # **The guard yields, the archive does not.** `handoff/` is
            # copy-and-keep; this note left the tree via the export before
            # `bugs:` existed on it, and editing it now would put the tracked
            # copy and the Drive copy out of byte-sync -- the exact
            # `040`/`043`/`052` condition. Reported, never silent: a skip
            # nobody sees is the guard quietly shrinking.
            warnings.warn(
                f"{path.name}: exempt from the `bugs:` requirement -- "
                f"already exported (see the manifest at "
                f"{manifest_path()}) before this rule reached it. Not "
                f"edited: handoff/ is copy-and-keep.",
                stacklevel=1)
            continue
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


def test_an_unreadable_manifest_refuses_by_name_rather_than_exempting_everyone(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """**068 Refusal.** Force `manifest_path()` to point nowhere and confirm
    `exported_done_note_basenames()` raises rather than returning an empty
    set. An empty set here would silently pass through to `path.name in
    exported` as always-`False` -- every in-scope note failing correctly by
    luck today, and every note silently exempted the day something else about
    the manifest breaks. Both are worse than a named, loud refusal."""
    import tools.exported_notes as exported_notes_module

    monkeypatch.setattr(
        exported_notes_module, "manifest_path",
        lambda: pathlib.Path(r"D:\does-not-exist\MANIFEST-nope.md"))
    with pytest.raises(ExportManifestUnreadable, match="does not exist"):
        exported_notes_module.exported_done_note_basenames()


def test_058_is_actually_exported_and_that_is_what_makes_the_exemption_real(
) -> None:
    """**Not a synthetic stand-in.** The exemption logic is only worth having
    if it reads a REAL manifest naming a REAL exported note -- a test that
    only ever exercised a fabricated basename set would pass even if
    `manifest_path()` pointed at the wrong file entirely."""
    exported = exported_done_note_basenames()
    assert "058-attach-latency-and-attaching-state.md" in exported, (
        "the real export manifest no longer names 058's done-note. Either "
        "the export has not run on this machine, or the manifest table "
        "shape changed and tools/exported_notes.py's parser was not updated "
        "with it -- either way, the exemption this test guards is not what "
        "it claims to be right now.")
