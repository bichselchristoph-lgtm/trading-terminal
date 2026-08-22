"""057. `verify.ps1` named its own output artifact under two different
strings — `.md` at the one place it is actually written (line 73 as of
20058f9), `.txt` in three of its own comments. **The cost was not cosmetic and
was already paid**: the design session searched for `verify-output.txt`, did
not find it, and concluded the verification gate had never been reachable and
that no task had ever truly been REVIEWED. The file existed, under the other
name, the whole time.

**The fix is positional: one definition, everything else derived from it.**
The literal string `verify-output` must occur exactly once in `verify.ps1` —
at the line that actually names the file — and nowhere else, in prose or in
a stale second name.

**This test asserts the RULE, not the current output.** It does not read the
file and pin the count it happens to find (that is B-029's shape, and how the
`038` units test came to agree with whatever the code did); the expected
count is the literal `1`, independent of the file's content.
"""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "verify.ps1"

_LITERAL = "verify-output"


def occurrences(text: str) -> int:
    return text.count(_LITERAL)


def test_verify_output_is_named_in_exactly_one_place() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    n = occurrences(text)
    assert n == 1, (
        f"the literal `{_LITERAL}` occurs {n} times in {SCRIPT.name}, not "
        "exactly once. An artifact documented under more than one name is how "
        "a reader who searches for the wrong one concludes it was never "
        "written — see 057.")


def test_the_check_can_actually_fail() -> None:
    """**Demonstrated red before being trusted green** — 057's own
    instruction, and `test_no_secrets.py`'s lesson: *a test never seen
    failing is a test whose green means nothing.*

    A second occurrence, planted into the REAL file's text (never written to
    the repo — this stays in memory), must make `occurrences()` disagree
    with the rule this file asserts. If it did not, `test_verify_output_is_
    named_in_exactly_one_place` above would be green for a reason that has
    nothing to do with the file actually satisfying the rule.
    """
    text = SCRIPT.read_text(encoding="utf-8")
    assert occurrences(text) == 1, (
        "the real file is not at the expected count; plant against a false "
        "premise and this test proves nothing")

    planted = text + "\n# a second verify-output mention, planted for this test only\n"
    assert occurrences(planted) == 2, (
        "planting a second literal did not change the count — the counting "
        "logic itself cannot see the condition it is meant to catch")
