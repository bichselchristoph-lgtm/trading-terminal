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

import pytest

REPO = Path(__file__).resolve().parents[1]
OUTPUT = "verify-output.txt"


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
    """Unanchored rules match at any depth. `verify-output.txt` is written to the
    root and nowhere else, and an unanchored rule would silently swallow a file
    of that name inside `handoff/` or `docs/` — the failure the whole `.gitignore`
    was rewritten to avoid under M001."""
    assert not check_ignore(f"docs/{OUTPUT}"), (
        f"a nested docs/{OUTPUT} is also ignored, so the rule is unanchored. "
        "Write it as `/verify-output.txt`.")


def test_verify_ps1_writes_the_path_this_test_guards() -> None:
    """The two must not drift. If the script is changed to write somewhere else,
    this file keeps asserting an ignore rule for a path nothing produces, and the
    real output becomes committable."""
    script = (REPO / "verify.ps1").read_text(encoding="utf-8")
    assert f"'{OUTPUT}'" in script or f'"{OUTPUT}"' in script, (
        f"verify.ps1 no longer names {OUTPUT}. Either it writes elsewhere -- in "
        "which case that path is not ignored -- or it stopped writing a file at all.")


@pytest.mark.parametrize("forbidden", ["git add", "git commit", "New-Item", "Remove-Item"])
def test_verify_ps1_still_modifies_nothing_else(forbidden: str) -> None:
    """023's standing constraint: the output file is the ONE exemption to
    `verify.ps1` never modifying the tree, and it must stay the only one."""
    script = (REPO / "verify.ps1").read_text(encoding="utf-8")
    code = "\n".join(l for l in script.splitlines() if not l.lstrip().startswith("#"))
    if forbidden == "Remove-Item":
        # The section-4 temp file is removed from the SYSTEM temp directory, not
        # from the tree. Allowed, and pinned to that one call so a second one
        # cannot hide behind this exemption.
        assert code.count("Remove-Item") == 1, (
            "more than one Remove-Item in verify.ps1. The only permitted one clears "
            "the section-4 rehash script from the system temp directory.")
        assert "Remove-Item $tmp" in code
        return
    assert forbidden not in code, (
        f"verify.ps1 contains {forbidden!r}. It reports on the tree and must not "
        "change it -- writing verify-output.txt is the single exemption.")
