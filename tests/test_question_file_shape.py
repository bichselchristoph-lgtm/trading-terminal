"""**054 Part 3 / 043 Part 2.** A question file is a channel, not a habit.

`handoff/questions/NNN-<short-name>.md`, and every file carries, at minimum, a
frontmatter `status:` (the question's own OPEN/ANSWERED vocabulary) and two
body fields: `**Raised by**` and `**Blocks**`.

**Deliberately distinct from the `**Status**` body line.** CLAUDE.md's handoff
convention already reserves a bold `**Status**` line for the five-state
vocabulary -- WRITTEN, HANDED OFF, RUNNING, REVIEWED, DONE -- tracking the
handoff of the TASK that raised a question, not the question's own OPEN /
ANSWERED state. 043's Part 2 example text writes `**Status** OPEN` as if that
were a third body line; adding it verbatim would have put two different
vocabularies behind the same bold word in the same file. **This test checks
the frontmatter `status:` key instead, and does not require a body
`**Status**` line at all** -- the substance (is this question open) is
present either way, and nothing here forces a collision that 043 did not
anticipate.
"""

from __future__ import annotations

import pathlib
import re

import pytest

yaml = pytest.importorskip("yaml")

REPO = pathlib.Path(__file__).resolve().parents[1]
QUESTIONS = REPO / "handoff" / "questions"

_FM = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.S)
_RAISED_BY = re.compile(r"(?m)^\*\*Raised by\*\*\s+\S+")
_BLOCKS = re.compile(r"(?m)^\*\*Blocks\*\*\s+(yes|no)\b")

VALID_STATUSES = {"OPEN", "ANSWERED"}


def question_files() -> list[pathlib.Path]:
    if not QUESTIONS.exists():
        return []
    return sorted(QUESTIONS.glob("*.md"))


def test_the_folder_has_files_to_check() -> None:
    """Guards every assertion below from passing on an empty folder."""
    assert question_files(), (
        f"no .md files in {QUESTIONS}. If the folder is genuinely empty this "
        "test is vacuous by design; if files were expected, the glob or path "
        "has drifted.")


def test_every_question_file_declares_a_valid_status() -> None:
    for p in question_files():
        fm = _FM.match(p.read_text(encoding="utf-8"))
        assert fm, f"{p.name}: no YAML frontmatter block found."
        data = yaml.safe_load(fm.group(1)) or {}
        status = data.get("status")
        assert status in VALID_STATUSES, (
            f"{p.name}: frontmatter status is {status!r}; expected one of "
            + ", ".join(sorted(VALID_STATUSES)))


def test_every_question_file_names_what_it_blocks() -> None:
    for p in question_files():
        text = p.read_text(encoding="utf-8")
        assert _RAISED_BY.search(text), (
            f"{p.name}: no `**Raised by** NNN` line. A question with no task "
            "number attached cannot be traced back to what raised it.")
        assert _BLOCKS.search(text), (
            f"{p.name}: no `**Blocks** yes` or `**Blocks** no` line. "
            "**A question that does not say whether it blocks is a question "
            "nobody can safely ignore.**")
