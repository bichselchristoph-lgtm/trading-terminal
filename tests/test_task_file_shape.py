"""**053 Part 5, test 3.** A task file is well-formed, and names no destination.

Four properties, each of which has failed at least once in this project:

1. **An addressing gate.** Without it a session cannot tell whether the file is
   for it, and `handoff/` is copy-and-keep so completed tasks stay forever.
2. **A `class`.** Rule 16 counts the admin tax and, since CLAUDE.md v1.7, also
   governs who may decide. A file with no class is outside both.
3. **`unblocks:` on an admin task.** Admin exists to unblock product. **Admin
   unblocking admin is forbidden** -- that is what stops this becoming a machine
   for generating its own work.
4. **No destination field.** Routing is protocol, not task content.

**On (4), and why it is a frontmatter check only.** `044` told this session to
paste a question into chat when a questions channel already existed. The
tempting fix is to grep task prose for destinations. **053 forbids that, and is
right**: grepping prose is unbounded, and a check that catches four phrasings
and misses the fifth is worse than none because it would be trusted. A
structured `destination:` key is bounded and decidable, so that is all this
asserts. **The prose half is caught by a human reading, and by CLAUDE.md's
ROUTING IS PROTOCOL rule -- not here.**

**WATERMARK at `049`**, the batch live when the rule was written. Retrofitting
shape onto historical task files would mean editing documents the other half of
the loop authored and has already read.
"""

from __future__ import annotations

import pathlib
import re

import pytest

yaml = pytest.importorskip("yaml")

REPO = pathlib.Path(__file__).resolve().parents[1]
INBOX = REPO / "handoff" / "inbox"

FROM_TASK = 49

_NUM = re.compile(r"^(\d+)-")
_FM = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.S)

#: Any frontmatter key that would route output. Bounded on purpose -- see the
#: module docstring on why prose is not grepped.
ROUTING_KEYS = {"destination", "destinations", "output_to", "report_to",
                "paste_to", "deliver_to", "send_to"}


def task_files() -> list[pathlib.Path]:
    out = []
    for p in sorted(INBOX.glob("*.md")):
        m = _NUM.match(p.name)
        if m and int(m.group(1)) >= FROM_TASK:
            out.append(p)
    return out


def test_the_scope_is_not_empty() -> None:
    assert task_files(), (
        f"no task files numbered {FROM_TASK}+ in {INBOX}; vacuous pass.")


def test_every_task_file_has_an_addressing_gate() -> None:
    for p in task_files():
        text = p.read_text(encoding="utf-8")
        assert "handoff/inbox/" in text and "handoff/done/" in text, (
            f"{p.name}: no addressing gate found. A task file must say which "
            "file's presence means it is for you and which means it is done; "
            "handoff/ is copy-and-keep, so a completed task never disappears.")


def test_every_task_file_declares_a_class() -> None:
    for p in task_files():
        fm = _FM.match(p.read_text(encoding="utf-8"))
        assert fm, f"{p.name}: no frontmatter."
        data = yaml.safe_load(fm.group(1)) or {}
        assert data.get("class") in {"admin", "product", "spec"}, (
            f"{p.name}: class is {data.get('class')!r}; expected admin, "
            "product or spec.")


def test_admin_tasks_name_what_they_unblock() -> None:
    for p in task_files():
        fm = _FM.match(p.read_text(encoding="utf-8"))
        data = yaml.safe_load(fm.group(1)) or {}
        if data.get("class") != "admin":
            continue
        assert str(data.get("unblocks", "")).strip(), (
            f"{p.name}: class is admin with no `unblocks:`. **Admin exists to "
            "unblock product.** An admin task that unblocks nothing, or that "
            "unblocks only more admin, is the failure rule 16 was written to "
            "make visible.")


def test_no_task_file_names_a_destination() -> None:
    for p in task_files():
        fm = _FM.match(p.read_text(encoding="utf-8"))
        data = yaml.safe_load(fm.group(1)) or {}
        found = ROUTING_KEYS & set(data)
        assert not found, (
            f"{p.name}: frontmatter names a destination ({', '.join(sorted(found))}). "
            "**ROUTING IS PROTOCOL, NOT TASK CONTENT.** Destinations come from "
            "config/sync.yaml and the handoff protocol. A task file is "
            "authoritative about its own work and is not authoritative about "
            "the channel -- the channel is shared state it cannot see.")
