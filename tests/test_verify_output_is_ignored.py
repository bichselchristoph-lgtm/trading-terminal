"""`verify-output.txt` is generated and must never be committed.

023 part 2. It is per-machine, describes a single moment, and would become a
second source of truth about the tree that ages badly and diffs noisily.

**Asserted with `git check-ignore`, not by reading `.gitignore` for a string.**
A substring match proves the line is present; it does not prove the line has
effect. `.gitignore` in this repo has swallowed an intended path before, and the
negation blocks are load-bearing — the only reliable check is to ask git.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import re

import pytest

REPO = Path(__file__).resolve().parents[1]
#: 053 Part 2 moved this out of the repository root and into `handoff/`, which
#: IS an export source. At the root it was unreachable by the export, so the
#: REVIEWED gate that depends on it could never be satisfied from the file.
OUTPUT = "handoff/verify-output.txt"


def check_ignore(rel: str) -> bool:
    """Exit 0 = ignored, 1 = not ignored. `--no-index` so the answer is about the
    rules, not about whether the file happens to exist right now."""
    r = subprocess.run(["git", "check-ignore", "--no-index", "-q", rel],
                       cwd=REPO, capture_output=True)
    return r.returncode == 0


def test_verify_output_is_ignored() -> None:
    assert check_ignore(OUTPUT), (
        f"`git check-ignore` says {OUTPUT} is NOT ignored. verify.ps1 writes it on "
        "every run, so an unignored file means the next `git add -A` commits a "
        "machine-local snapshot of one moment as though it described the tree."
    )


def test_it_is_ignored_even_before_it_exists() -> None:
    """The rule must not depend on the file being present -- a fresh clone has no
    `verify-output.txt`, and that is exactly when someone runs the script and
    commits the result by accident."""
    assert check_ignore(OUTPUT)


def test_the_check_can_actually_fail() -> None:
    """A `check_ignore` that returned True for everything would make the tests
    above pass while proving nothing."""
    assert not check_ignore("README.md"), (
        "git check-ignore reports README.md as ignored. The helper is broken or "
        "the ignore rules are far wider than intended.")
    assert not check_ignore("verify.ps1"), (
        "verify.ps1 itself is ignored -- the rule is matching the script, not its "
        "output.")


def test_the_rule_is_anchored_to_the_repo_root() -> None:
    """Unanchored rules match at any depth. `verify-output.txt` is written to
    `handoff/` and nowhere else, and an unanchored rule would silently swallow a file
    of that name inside `handoff/` or `docs/` — the failure the whole `.gitignore`
    was rewritten to avoid under M001."""
    assert not check_ignore("docs/verify-output.txt"), (
        "a nested docs/verify-output.txt is also ignored, so the rule is "
        "unanchored. Write it as `/handoff/verify-output.txt`.")


def test_verify_ps1_writes_the_path_this_test_guards() -> None:
    """The two must not drift. If the script is changed to write somewhere else,
    this file keeps asserting an ignore rule for a path nothing produces, and the
    real output becomes committable."""
    script = (REPO / "verify.ps1").read_text(encoding="utf-8")
    needle = OUTPUT.replace("/", chr(92))
    assert needle in script or OUTPUT in script, (
        f"verify.ps1 no longer names {OUTPUT}. Either it writes elsewhere -- in "
        "which case that path is not ignored -- or it stopped writing a file at all.")


@pytest.mark.parametrize("forbidden", ["git add", "git commit", "New-Item", "Remove-Item"])
def test_verify_ps1_still_modifies_nothing_else(forbidden: str) -> None:
    """023's standing constraint: the output file is the ONE exemption to
    `verify.ps1` never modifying the tree, and it must stay the only one."""
    script = (REPO / "verify.ps1").read_text(encoding="utf-8")
    code = "\n".join(l for l in script.splitlines() if not l.lstrip().startswith("#"))
    if forbidden == "Remove-Item":
        # Temp scripts are removed from the SYSTEM temp directory, not from the
        # tree. Allowed — **and asserted by SHAPE rather than by count.**
        #
        # This used to read `code.count("Remove-Item") == 1`, pinned to the
        # section-4 rehash cleanup. 045 added a second temp script for the
        # `waiting in Drive` count and the test went red on a change that broke
        # nothing it exists to protect. **A count is the wrong assertion twice
        # over**: it blocks a legitimate second temp cleanup, and it would happily
        # permit a single `Remove-Item` pointed at a repo path.
        #
        # What matters is the TARGET. Every removal must name a `$tmp*` variable,
        # which is only ever assigned from `[System.IO.Path]::GetTempPath()`.
        removals = [l.strip() for l in code.splitlines() if "Remove-Item" in l]
        assert removals, "the temp-file cleanup has gone missing"
        for line in removals:
            assert re.search(r"Remove-Item \$tmp\w*", line), (
                f"verify.ps1 removes something that is not a temp script: "
                f"{line!r}. The exemption is for files this script wrote to the "
                f"SYSTEM temp directory, never for anything in the tree.")
        # And every temp path this script builds comes from the system temp
        # directory. **Asserted over the ASSIGNMENTS that build a temp script
        # path**, matched on `Join-Path` so the check cannot be satisfied by an
        # unrelated variable that merely starts with the same three letters —
        # which is what an earlier cut of this check did, reporting a false
        # failure against a correct script.
        builds = [l.strip() for l in code.splitlines()
                  if re.search(r"\$tmp\w*\s*=", l)]
        assert builds, "no temp script path is built; the removals above have no source"
        for line in builds:
            assert "GetTempPath" in line, (
                f"a temp path is built outside the system temp directory: "
                f"{line!r}")
        return
    assert forbidden not in code, (
        f"verify.ps1 contains {forbidden!r}. It reports on the tree and must not "
        "change it -- writing verify-output.txt is the single exemption.")
