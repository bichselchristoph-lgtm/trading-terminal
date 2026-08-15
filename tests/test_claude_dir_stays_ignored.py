"""`.claude/` is ignored, except four `.md` files. 024.

**This is the first time anything under `.claude/` has been trackable in this
tree, and the exception exists under protest.** M001 §6 says *"Do not copy
`.claude/` in any form"*, and it says that because the predecessor's
`.claude/settings.local.json` held a **live Databento key**. Nothing about that
has become less true.

What changed is that `024` needs a subagent roster whose restrictions are
committed — *a roster whose restrictions are not asserted is a roster of
suggestions*, and a roster that is not tracked is not even that, because the next
clone does not have it. **Claude Code reads agent definitions from
`.claude/agents/` and nowhere else**, so the location is forced by the tool
rather than chosen, and moving it is not available.

----

**The exceptions are `.claude/agents/*.md` and — since `046` — the single file
`.claude/settings.json`. Everything else stays ignored**, and this file is what
makes that a fact rather than an intention:

* **no `settings.local.json`** — the shape that held the key, and the near-miss
  here, because it differs from the one permitted filename by a single word
* no `.json` under `agents/`, at any depth
* no subdirectory under `agents/`
* no `worktrees/`, no `.credentials`, nothing else at the top level

**`046` opened the second exception and narrowed the guard rather than removing
it.** The shared permission policy has to be committed for the same reason the
roster does: a rule that is not in the repository is not inherited by a clone.
It is negated **by exact filename, never by pattern** — `!.claude/settings*.json`
would have readmitted the local file — and the ordering assertion below was
restated rather than deleted, so a widened negation appended after the blanket
rule still goes red. **Both of those were seen red before this was accepted.**

**Seen red before it was accepted**, against a real
`.claude/agents/settings.local.json` planted in the working tree. A test that has
never failed is a claim, not a guard.

**`git check-ignore` is the oracle, deliberately.** Re-implementing gitignore
precedence in Python would test this file's *model* of git rather than git — and
the whole defect class here is a rule that reads correctly and behaves
otherwise. The four-line negation depends on subtle ordering (a directory-form
ignore stops git descending, so no negation inside it can rescue anything), which
is exactly the kind of rule nobody should assert from memory.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

#: The ONLY shapes that may be tracked under `.claude/`. **Two, since 046**, and
#: the second is one exact filename rather than a pattern.
PERMITTED = ".claude/agents/*.md and the single file .claude/settings.json"

#: 046. The shared permission policy, and the one `.json` that may be committed.
#:
#: **Why the exception was opened at all**: a permission policy that is not in
#: the repository is not inherited by a clone — the same argument that opened the
#: `agents/` exception under `024`, where a reviewer's restrictions were useless
#: if the next clone did not have them.
#:
#: **Why it is a filename and not a pattern.** `settings.local.json` is where the
#: predecessor's live Databento key sat, and it is what a developer writes a
#: secret into precisely because it is the local one. A pattern such as
#: `!.claude/settings*.json` would admit it. This does not, and
#: `MUST_STAY_IGNORED` asserts it below.
TRACKED_POLICY = ".claude/settings.json"

#: Paths that MUST stay ignored. **Written as paths that do not exist**, because
#: `git check-ignore` answers about a path, not about a file — so this asserts
#: the rule rather than the current contents of the disk, and it keeps working on
#: a clone where none of these has ever existed.
#:
#: `settings.local.json` appears twice on purpose: at the top level, where the
#: predecessor's key actually sat, and **inside `agents/`**, which is the one an
#: over-broad negation would let through and the one this file was seen red
#: against.
MUST_STAY_IGNORED = [
    # `.claude/settings.json` was HERE until 046 and has moved to
    # MUST_BE_TRACKABLE. **`settings.local.json` did not move and must not.**
    # That is the near-miss: the two filenames differ by one word, one is the
    # shared policy and the other is where a machine-local secret goes, and the
    # predecessor's live Databento key was in the second.
    ".claude/settings.local.json",
    ".claude/agents/settings.local.json",
    ".claude/agents/settings.json",
    ".claude/agents/anything.json",
    ".claude/agents/nested/deeper.json",
    ".claude/agents/nested/roster.md",
    ".claude/worktrees/029-entry-point/live/tui/app.py",
    ".claude/mcp.json",
    ".claude/.credentials.json",
    ".claude/agents/roster.yaml",
    ".claude/agents/notes.txt",
]

#: Paths that must be TRACKABLE. The four `.md` names are 024's roster; the
#: fifth is 046's shared permission policy.
MUST_BE_TRACKABLE = [
    TRACKED_POLICY,                                        # 046
    ".claude/agents/architect.md",
    ".claude/agents/implementer.md",
    ".claude/agents/reviewer.md",
    ".claude/agents/test-author.md",
]


def is_ignored(rel: str) -> bool:
    """Ask git, never a reimplementation of git.

    `--no-index` matters: without it git answers about the index for a tracked
    path, so a file that slipped in before the rule tightened would report as
    *not ignored* and the test would agree with the mistake.
    """
    proc = subprocess.run(
        ["git", "check-ignore", "--no-index", "-q", "--", rel],
        cwd=REPO, capture_output=True, text=True)
    if proc.returncode not in (0, 1):
        raise AssertionError(
            f"git check-ignore failed on {rel!r} (exit {proc.returncode}): "
            f"{proc.stderr.strip()}")
    return proc.returncode == 0


@pytest.mark.parametrize("rel", MUST_STAY_IGNORED)
def test_the_exception_admits_nothing_but_markdown_under_agents(rel: str) -> None:
    """**The whole security surface of `024`, one path per case.**

    A key in any of these would be committed and pushed to `trading-terminal`,
    where removing it is no longer a local operation.
    """
    assert is_ignored(rel), (
        f"{rel} is NOT ignored.\n\n"
        f"The only permitted exception under .claude/ is {PERMITTED}. This path is "
        "outside it,\nso the negation in .gitignore is wider than it is meant to be "
        "— and the file it\nadmits is the shape that held a live Databento key in the "
        "predecessor tree.\n\n"
        "Narrow the negation. Do not add an exception for this path.")


@pytest.mark.parametrize("rel", MUST_BE_TRACKABLE)
def test_the_roster_itself_is_trackable(rel: str) -> None:
    """The other half, and without it the test above passes on a rule that
    ignores everything — which would leave the roster untracked and the
    restrictions absent from every clone, silently."""
    assert not is_ignored(rel), (
        f"{rel} IS ignored, so the roster cannot be committed.\n"
        "A restriction that is not in the repository is not a restriction — the "
        "next clone\nhas no roster at all, and nothing goes red to say so.")


def test_a_json_under_agents_is_ignored_even_if_the_negation_widens() -> None:
    """**The belt-and-braces line, asserted as its own case.**

    `.claude/**/*.json` is the LAST rule in the block, and later rules win in git.
    So a future edit that widens the exception — `!.claude/agents/**` is the
    obvious one somebody reaches for — still cannot admit a JSON config without
    also deleting a line whose comment says why it exists.

    This is the same construction `024` asks for everywhere else: **make the
    defect unrepresentable rather than forbidden in prose.**
    """
    text = (REPO / ".gitignore").read_text(encoding="utf-8")
    lines = [l.strip() for l in text.splitlines() if l.strip() and not l.startswith("#")]
    claude = [l for l in lines if l.lstrip("!").startswith(".claude/")]
    assert claude, ".gitignore no longer has a .claude/ block at all"

    # **046 CHANGED THIS ASSERTION AND DELIBERATELY DID NOT DROP IT.**
    #
    # Until 046 the blanket rule was LAST and the test said so. Committing the
    # shared permission policy needs exactly one negation after it, because that
    # is the only position git honours. So the invariant is restated rather than
    # deleted: the blanket rule must be second-to-last, and the ONE thing allowed
    # after it is the single exact path.
    #
    # The protection is intact. A widened negation — `!.claude/agents/**`, or the
    # `!.claude/settings*` that would readmit settings.local.json — still has to
    # be placed after the blanket rule to have any effect, and placing it there
    # fails this test. **Deleting the assertion instead would have removed the
    # protection while leaving a file that looked guarded.**
    assert claude[-2:] == [".claude/**/*.json", "!" + TRACKED_POLICY], (
        f"the last two .claude/ rules are {claude[-2:]!r}, not "
        f"['.claude/**/*.json', '!{TRACKED_POLICY}'].\n\n"
        "That ORDER is the protection: later rules win in git, so the blanket "
        "JSON rule\nmust sit directly above the one exact negation 046 opened. "
        "Anything else after it\nwins over it — which is how "
        "`!.claude/settings*` would readmit settings.local.json,\nthe shape that "
        "held a live Databento key in the predecessor tree.\n\n"
        "Add the one path you need to MUST_BE_TRACKABLE and negate it by exact "
        "name, or\nnarrow the rule. Do not append a pattern here.")


def test_the_directory_form_is_gone_and_that_is_load_bearing() -> None:
    """`.claude/` as a bare directory rule would make the exception impossible.

    Git does not descend into an ignored directory, so **no negation inside one
    can rescue anything** — the roster would be silently untracked while
    `.gitignore` appeared to permit it. Recorded as a test because the bare form
    is what was there before and is what someone restoring "the original rule"
    would write.
    """
    text = (REPO / ".gitignore").read_text(encoding="utf-8")
    lines = [l.strip() for l in text.splitlines() if l.strip() and not l.startswith("#")]
    assert ".claude/" not in lines, (
        "the bare directory rule `.claude/` is back. Git does not descend into an "
        "ignored\ndirectory, so the agents/ negation below it can rescue nothing and "
        "the roster\nbecomes untracked WITHOUT ANY TEST GOING RED except this one.")


def test_only_the_roster_is_tracked_under_claude() -> None:
    """What is actually in the index right now, as opposed to what the rules
    permit. The two can disagree: a file added before the rule tightened stays
    tracked forever, and `.gitignore` has no effect on it at all."""
    tracked = subprocess.run(
        ["git", "ls-files", "--", ".claude"], cwd=REPO,
        capture_output=True, text=True, check=True).stdout.split()
    offenders = [p for p in tracked
                 if p != TRACKED_POLICY
                 and not (p.startswith(".claude/agents/") and p.endswith(".md")
                          and p.count("/") == 2)]
    assert not offenders, (
        f"tracked under .claude/ but outside {PERMITTED}: {offenders}\n\n"
        ".gitignore does not untrack a file that is already in the index. Remove it "
        "with\n`git rm --cached`, and if it ever held a credential, rotate that "
        "credential —\nit is in the history and on the remote.")
