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


def _load_frontmatter(p: pathlib.Path, problems: list[str]) -> dict | None:
    """Parse `p`'s frontmatter, or record a named problem and return None.

    **OBS-080.** The three checks below used to call `yaml.safe_load` directly
    inside their loop with no per-file guard. `056` has an unquoted colon in a
    prose value ("Rule 16: this counts...") -- invalid YAML -- and
    `yaml.safe_load` raised `yaml.scanner.ScannerError` on it. With no
    try/except, that exception propagated out of the loop entirely: every file
    sorting after `056` was never reached, so class/unblocks/destination went
    unverified for the whole tail of the inbox without any test going red for
    the right reason (they went red for `056` alone, then stopped).

    A malformed file is a violation to report by name, not a reason to abort
    checking every file after it. Catching `yaml.YAMLError` here -- the common
    base of `ScannerError` and `ParserError` -- keeps that failure mode local
    to the one file that caused it.
    """
    fm = _FM.match(p.read_text(encoding="utf-8"))
    if not fm:
        problems.append(f"{p.name}: no frontmatter.")
        return None
    try:
        return yaml.safe_load(fm.group(1)) or {}
    except yaml.YAMLError as exc:
        problems.append(
            f"{p.name}: frontmatter is not valid YAML ({exc}) -- cannot "
            "check class/unblocks/destination for this file")
        return None


def _check_declares_a_class(paths: list[pathlib.Path]) -> list[str]:
    problems: list[str] = []
    for p in paths:
        data = _load_frontmatter(p, problems)
        if data is None:
            continue
        if data.get("class") not in {"admin", "product", "spec"}:
            problems.append(
                f"{p.name}: class is {data.get('class')!r}; expected admin, "
                "product or spec.")
    return problems


def _check_admin_names_what_it_unblocks(paths: list[pathlib.Path]) -> list[str]:
    problems: list[str] = []
    for p in paths:
        data = _load_frontmatter(p, problems)
        if data is None:
            continue
        if data.get("class") != "admin":
            continue
        if not str(data.get("unblocks", "")).strip():
            problems.append(
                f"{p.name}: class is admin with no `unblocks:`. **Admin "
                "exists to unblock product.** An admin task that unblocks "
                "nothing, or that unblocks only more admin, is the failure "
                "rule 16 was written to make visible.")
    return problems


def _check_names_no_destination(paths: list[pathlib.Path]) -> list[str]:
    problems: list[str] = []
    for p in paths:
        data = _load_frontmatter(p, problems)
        if data is None:
            continue
        found = ROUTING_KEYS & set(data)
        if found:
            problems.append(
                f"{p.name}: frontmatter names a destination "
                f"({', '.join(sorted(found))}). **ROUTING IS PROTOCOL, NOT "
                "TASK CONTENT.** Destinations come from config/sync.yaml and "
                "the handoff protocol. A task file is authoritative about "
                "its own work and is not authoritative about the channel -- "
                "the channel is shared state it cannot see.")
    return problems


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
    problems = _check_declares_a_class(task_files())
    assert not problems, "\n".join(problems)


def test_admin_tasks_name_what_they_unblock() -> None:
    problems = _check_admin_names_what_it_unblocks(task_files())
    assert not problems, "\n".join(problems)


def test_no_task_file_names_a_destination() -> None:
    problems = _check_names_no_destination(task_files())
    assert not problems, "\n".join(problems)


def test_malformed_frontmatter_is_a_named_violation_not_an_abort(
    tmp_path: pathlib.Path,
) -> None:
    """**OBS-080, demonstrated directly.** Two scratch files -- one with `056`'s
    unquoted-colon shape, one with syntactically valid YAML that fails a real
    rule -- must both be reported from a single run of the per-file checker.
    Before the fix, the first file's `yaml.scanner.ScannerError` propagated out
    of the loop and the second file was never reached.
    """
    bad_yaml = tmp_path / "100-scratch-bad-yaml.md"
    bad_yaml.write_text(
        "---\n"
        "class: admin\n"
        "unblocks: something\n"
        "reason: Rule 16: this counts against you\n"
        "---\n"
        "handoff/inbox/ handoff/done/\n",
        encoding="utf-8",
    )
    bad_class = tmp_path / "101-scratch-bad-class.md"
    bad_class.write_text(
        "---\n"
        "class: nonsense\n"
        "---\n"
        "handoff/inbox/ handoff/done/\n",
        encoding="utf-8",
    )

    paths = [bad_yaml, bad_class]
    problems = _check_declares_a_class(paths)

    assert len(problems) == 2, (
        "expected one violation per scratch file, in one run; got: "
        f"{problems!r}")
    assert any("not valid YAML" in msg and bad_yaml.name in msg
                for msg in problems), problems
    assert any("class is" in msg and bad_class.name in msg
                for msg in problems), problems
