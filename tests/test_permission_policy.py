"""The permission policy must be carried by a test, not by memory. `061`.

On 2026-08-22 a session added four `permissions.allow` entries and acted on
them in the same session, calling it `class: admin`. It was not: the file
that decides what a session may do is itself a security control, and the
control was resting on a written rule -- CLAUDE.md prose -- that a session
can misread or a future edit can erode without anyone noticing. Rule 14: a
role is separated by its tools, never by its instructions. This is that
separation made structural for one control: `.claude/settings.json` may not
be written by the session it governs.

**Asserts the property, not the current text.** `B-029` is what pinning
Christoph's exact two pasted strings would produce -- a test that goes red
the moment the wording changes even though the control still holds. This
checks: does `permissions.deny` contain a `Write` or `Edit` entry (the tool
names this policy file actually uses for file mutation -- see the `allow`
and `ask` sections) whose pattern covers `.claude/settings.json` itself.

**Refusal states, not crashes.** A malformed policy file enforces nothing,
silently -- Claude Code does not error on it, it just stops applying every
setting in the file. That failure must be visible from outside a session,
so it is named (`PolicyError`) rather than left to surface as whatever
exception `json.loads` happens to raise. A deny entry naming a verb that is
not a real tool (`WriteAccess`, `FileWrite`, ...) matches no tool and
enforces nothing either, and is the whole reason `covers_settings_json`
checks the tool name at all rather than doing a plain substring search.
"""
from __future__ import annotations

import fnmatch
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
POLICY = REPO / ".claude" / "settings.json"

#: The tool names this policy file uses for file mutation -- confirmed by
#: reading `.claude/settings.json` itself (`Edit(//d/Dev/momentum/**)`,
#: `Write(//d/Dev/momentum/**)` in `allow`; the same pair in `ask` and
#: `deny`). A verb outside this pair is not a real mutating tool for this
#: policy and an entry naming one is inert -- see the refusal case below.
MUTATING_TOOLS = ("Write", "Edit")

#: Forms this project's own policy already uses to name its own settings
#: file: relative (the `deny` entries added under `061`) and the absolute
#: POSIX-slash style the rest of the file uses for repo paths (the `ask`
#: entries added earlier). A pattern only counts as a control on the
#: settings file if it would glob-match one of these.
SETTINGS_JSON_PATHS = (
    ".claude/settings.json",
    "//d/Dev/momentum/.claude/settings.json",
)


class PolicyError(Exception):
    """The policy file could not be read as a policy. Raised with a message
    naming what failed, so a caller sees a refusal by name rather than a
    bare `json.JSONDecodeError` or `KeyError` traceback."""


def load_deny(policy_path: Path) -> list:
    try:
        text = policy_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PolicyError(f"{policy_path} could not be read: {exc}") from exc
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise PolicyError(f"{policy_path} is not valid JSON: {exc}") from exc
    try:
        deny = data["permissions"]["deny"]
    except (KeyError, TypeError) as exc:
        raise PolicyError(
            f"{policy_path} has no permissions.deny list") from exc
    if not isinstance(deny, list):
        raise PolicyError(f"{policy_path}: permissions.deny is not a list")
    return deny


def parse_rule(rule: str):
    """`\"Tool(pattern)\"` -> `(tool, pattern)`, or `None` if the entry is
    not shaped like a tool rule at all."""
    if not isinstance(rule, str) or "(" not in rule or not rule.endswith(")"):
        return None
    tool, _, rest = rule.partition("(")
    return tool, rest[:-1]


def covers_settings_json(pattern: str) -> bool:
    norm = pattern.replace("\\", "/")
    return any(fnmatch.fnmatchcase(target, norm) for target in SETTINGS_JSON_PATHS)


def settings_json_write_is_denied(policy_path: Path) -> bool:
    """True iff `deny` contains a real mutating-tool entry whose pattern
    covers the settings file itself."""
    for rule in load_deny(policy_path):
        parsed = parse_rule(rule)
        if parsed is None:
            continue
        tool, pattern = parsed
        if tool not in MUTATING_TOOLS:
            continue
        if covers_settings_json(pattern):
            return True
    return False


# ---------------------------------------------------------------------------
# The real policy


def test_the_real_policy_parses_and_has_a_deny_list() -> None:
    """Cheap and worth having on its own: a malformed policy file is a
    policy file enforcing nothing, and it would otherwise fail silently."""
    deny = load_deny(POLICY)
    assert isinstance(deny, list)


def test_settings_json_writes_are_denied() -> None:
    """The control this task exists for. If this is red, the deny entries
    from `christoph/open/035-*` are not applied yet -- that is a correct
    red reporting a real gap, not a bug in this test. Do not add the
    entries here to make it pass; that would be the denied party editing
    its own deny list."""
    assert settings_json_write_is_denied(POLICY), (
        "permissions.deny has no Write/Edit entry covering "
        ".claude/settings.json. See christoph/open/035-*.")


# ---------------------------------------------------------------------------
# The detector, proven against scratch copies -- never the real file


@pytest.fixture
def scratch(tmp_path: Path):
    """Write a minimal settings.json-shaped file under pytest's own tmp_path
    (already outside the repo) and return its path. Never touches
    `.claude/settings.json`."""
    def _make(deny_entries: list) -> Path:
        data = {"permissions": {"deny": deny_entries}}
        path = tmp_path / "settings.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path
    return _make


def test_control_present_is_detected(scratch) -> None:
    path = scratch(["Write(.claude/settings.json)", "Edit(.claude/settings.json)"])
    assert settings_json_write_is_denied(path)


def test_control_present_via_absolute_form_is_detected(scratch) -> None:
    """The other form this repo's own policy uses (see the `ask` entries
    added before `061`). The check must not be married to one spelling."""
    path = scratch(["Write(//d/Dev/momentum/.claude/settings.json)"])
    assert settings_json_write_is_denied(path)


def test_control_absent_is_detected_as_absent(scratch) -> None:
    """Seen red: this is `test_control_present_is_detected` with the two
    lines removed. If this ever passes, the detector is vacuous and every
    green above it means nothing."""
    path = scratch(["Bash(git clean:*)", "Edit(//d/Dev/momentum/christoph/done/**)"])
    assert not settings_json_write_is_denied(path)


def test_a_verb_that_is_not_a_real_tool_name_does_not_count(scratch) -> None:
    """The whole reason `covers_settings_json` checks the tool name rather
    than doing a plain substring search over the deny list: an entry naming
    a plausible-looking but non-existent tool matches no tool at runtime and
    enforces nothing, and a test that accepted it would report a control
    that is not there."""
    path = scratch(["WriteAccess(.claude/settings.json)"])
    assert not settings_json_write_is_denied(path)


def test_malformed_json_is_a_named_refusal_not_a_crash(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(PolicyError, match="not valid JSON"):
        settings_json_write_is_denied(path)


def test_missing_deny_list_is_a_named_refusal_not_a_crash(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"permissions": {}}), encoding="utf-8")
    with pytest.raises(PolicyError, match="no permissions.deny list"):
        settings_json_write_is_denied(path)
