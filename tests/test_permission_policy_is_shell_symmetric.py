"""Every `git` restriction binds under BOTH shell tools, or it binds under none.

**046 part 2, and it was found by nearly shipping the hole.**

`046` built the permission policy against the Bash tool, because that is the
tool the session happened to be using. All eleven `deny` rules read
`Bash(git ...)`. Then one line arrived:

    [Environment]::SetEnvironmentVariable('CLAUDE_CODE_USE_POWERSHELL_TOOL','1','User')

**That variable switches Claude Code to the PowerShell tool, at which point
`PowerShell(git worktree remove ...)` matches nothing in `deny` and every
protection `046` had just built and verified stops applying.** Not loosened —
absent. The policy file would still read exactly as it did when it was reviewed.

----

**Why `git` and not every rule.** The two shells have genuinely different
vocabularies: `find` and `rm` are Bash's, `Remove-Item` and `Set-Content` are
PowerShell's, and demanding a twin for each would force meaningless entries.
**`git` is the one case where the command is the same executable, spelled the
same way, doing the same thing under both.** So a `git` rule that exists for one
tool and not the other is always an oversight, never a design choice.

**Only `ask` and `deny` are asserted. `allow` asymmetry is deliberately
permitted**, because it fails safe: a `git status` allowed under Bash and not
under PowerShell costs a prompt. A `git reset --hard` denied under Bash and not
under PowerShell costs the work.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
POLICY = REPO / ".claude" / "settings.json"

#: The two shell tools whose rules must agree about `git`.
TOOLS = ("Bash", "PowerShell")

#: Asserted classes. `allow` is excluded and the docstring says why.
GUARDED = ("ask", "deny")

RULE = re.compile(r"^(?P<tool>Bash|PowerShell)\((?P<cmd>.*)\)$", re.S)


def permissions() -> dict:
    assert POLICY.is_file(), (
        f"{POLICY.relative_to(REPO)} is missing. It is the committed permission "
        "policy and is\ntracked deliberately — a policy that is not in the "
        "repository is not inherited by\na clone. See tests/test_claude_dir_stays_ignored.py.")
    return json.loads(POLICY.read_text(encoding="utf-8"))["permissions"]


def shell_rules(section: str) -> list[tuple[str, str]]:
    """`(tool, command)` for every Bash/PowerShell rule in a section."""
    out = []
    for rule in permissions().get(section, []):
        m = RULE.match(rule)
        if m:
            out.append((m.group("tool"), m.group("cmd")))
    return out


def git_commands(section: str, tool: str) -> set[str]:
    return {cmd for t, cmd in shell_rules(section) if t == tool and cmd.startswith("git ")}


def test_the_policy_is_valid_json() -> None:
    """A malformed settings.json silently disables EVERY setting in the file —
    it does not error, it just stops applying. That failure is invisible from
    inside a session, so it is asserted from outside one."""
    permissions()


@pytest.mark.parametrize("section", GUARDED)
def test_every_git_restriction_binds_under_both_shells(section: str) -> None:
    """**The invariant.** A `git` rule under one tool and not the other is a
    protection that a single environment variable turns off."""
    bash = git_commands(section, "Bash")
    powershell = git_commands(section, "PowerShell")

    only_bash = sorted(bash - powershell)
    only_ps = sorted(powershell - bash)

    assert not (only_bash or only_ps), (
        f"`{section}` rules for git do not agree across the two shell tools.\n\n"
        + ("  Bash only:       " + ", ".join(only_bash) + "\n" if only_bash else "")
        + ("  PowerShell only: " + ", ".join(only_ps) + "\n" if only_ps else "")
        + "\n`git` is the same executable under both tools, so a rule for one and "
          "not the other\nis an oversight. Add the twin.\n\n"
          "THIS IS NOT COSMETIC. Claude Code switches shell tool on the "
          "CLAUDE_CODE_USE_POWERSHELL_TOOL\nenvironment variable, and a "
          "Bash-only deny stops applying entirely the moment it is\nset — while "
          "the policy file still reads exactly as it did when it was reviewed.")


def test_the_worktree_and_uncommitted_work_guards_are_present_under_both() -> None:
    """**The specific set this policy exists for, named rather than inferred.**

    `test_every_git_restriction_binds_under_both_shells` passes vacuously on a
    policy with no git rules at all — `OBS-037`, a test asserting an absence
    passing against a feature that does not exist. This names what must be there.

    Every entry below destroys either another session's worktree or uncommitted
    work, and none of them has an undo.
    """
    required = {
        "git worktree remove:*",
        "git worktree prune:*",
        "git reset --hard:*",
        "git checkout --:*",
        "git restore:*",
        "git stash drop:*",
        "git stash clear:*",
        "git clean:*",
    }
    for tool in TOOLS:
        missing = sorted(required - git_commands("deny", tool))
        assert not missing, (
            f"these are not denied for the {tool} tool: {missing}\n\n"
            "Each one removes a worktree or destroys uncommitted work and cannot "
            "be undone.\nThey are `deny` rather than `ask` because ask was "
            "MEASURED not to bind under auto\nmode: `git push --dry-run origin "
            "main` matched an ask rule and ran unprompted,\nwhile a deny rule on "
            "`git clean` blocked. See 046's commit message.")


def test_the_force_push_denials_hold_under_both() -> None:
    """`CLAUDE.md`: never force-push, and never push to the archive. The second
    half is not expressible as a permission rule — rules match command strings,
    not git remotes — so only this half is enforced here, and saying so is the
    point rather than leaving a reader to assume both are covered."""
    for tool in TOOLS:
        denied = git_commands("deny", tool)
        for form in ("git push --force:*", "git push -f:*",
                     "git push --force-with-lease:*"):
            assert form in denied, f"{form} is not denied for the {tool} tool"
