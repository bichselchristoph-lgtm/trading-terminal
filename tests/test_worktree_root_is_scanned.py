"""Worktrees left `.claude/worktrees/` on 2026-08-16, and the instrument moved with them.

**The defect that forced the move.** `.claude/settings.json` denies `Edit` and
`Write` on `.claude/worktrees/**`. `EnterWorktree` creates a worktree there and
**has no parameter to create anywhere else** -- its only creation input is a
`name`. So every task carrying *"work in a worktree"* had two instructions that
could not both be obeyed: enter the worktree, then be unable to write a byte in
it. **Mutually exclusive, blocking every such task identically, and never
exercised** -- the sessions that were told to use a worktree reached for
`git worktree add` with an explicit path instead and never met the deny.

**The move is the easy half. This file guards the hard half.**

A scanner left pointing at the old root reports `on-disk orphans 0` forever --
not because there are none, but because it is looking where they no longer
appear. **That is strictly worse than the defect it replaces**: the old failure
was visible in section 1 as a red test with a confusing cause, and this one reads
as success. It is OBS-034's shape with a green light on top.

So the condition on the move was that `verify.ps1`'s orphan scan point at the new
location **in the same change**, and these are the assertions that keep it there.

**Seen red before it was accepted.** The scan was demonstrated against a real
worktree and a real orphan directory at the new root, both reported by name, both
then removed. A test that has never failed is a claim, not a guard.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
VERIFY = REPO / "verify.ps1"
POLICY = REPO / ".claude" / "settings.json"
SYNC_CFG = REPO / "config" / "sync.yaml"

#: The current root, as a bare name. **Asserted as a name, not a full path**,
#: because `verify.ps1` derives the path from its own location -- the sibling of
#: the checkout -- and a test that hardcoded `D:\Dev\_worktrees` would be the
#: second place the path lives, which is what the derivation exists to avoid.
CURRENT_ROOT_NAME = "_worktrees"

#: The former root. Still scanned, because three orphan directories are in it
#: today and history does not relocate itself.
FORMER_ROOT = r".claude\worktrees"


def verify_text() -> str:
    return VERIFY.read_text(encoding="utf-8")


def policy() -> dict:
    return json.loads(POLICY.read_text(encoding="utf-8"))


def test_the_orphan_scan_names_the_current_root() -> None:
    """**The condition the move was granted on.**

    Without this the relocation is a blinding: worktrees appear somewhere the
    scanner does not look, and it goes on printing zero.
    """
    assert CURRENT_ROOT_NAME in verify_text(), (
        f"verify.ps1 does not mention {CURRENT_ROOT_NAME!r} anywhere.\n\n"
        "Worktrees are created outside the repository since 2026-08-16. A scan that "
        "still\npoints only at .claude/worktrees/ reports `on-disk orphans 0` forever — "
        "not because\nthere are none, but because it is looking in the wrong place. "
        "AN INSTRUMENT THAT\nGOES DARK WHEN THE THING IT MEASURES MOVES IS WORSE THAN NO "
        "INSTRUMENT: this one\nreads as success."
    )


def test_the_former_root_is_still_scanned() -> None:
    """**Dropping it would strand the orphans already in it.**

    Three directories sat under `.claude/worktrees/` on the day of the move.
    They do not relocate themselves, and a scan that stops looking at them has
    lost exactly the finding OBS-046 is about.
    """
    text = verify_text()
    assert FORMER_ROOT in text or ".claude/worktrees" in text, (
        "verify.ps1 no longer scans the FORMER worktree root.\n\n"
        "Orphan directories from before 2026-08-16 are still on disk there. The root "
        "stops\nbeing worth scanning when it stops existing — which the per-root "
        "Test-Path already\nhandles — not when worktrees stop being created in it."
    )


def test_a_missing_root_still_prints() -> None:
    """Silence and zero must not look alike.

    Until this change the whole orphan block sat inside one `if (Test-Path)`, so a
    missing root printed **nothing at all** — indistinguishable in the output from
    a scan that ran and found nothing. This script's only job is to state facts a
    reader can act on, and an absent line states nothing.
    """
    assert re.search(r"on-disk orphans\s+n/a", verify_text()), (
        "verify.ps1 has no `on-disk orphans n/a` branch.\n\n"
        "A root that does not exist must SAY so. If the block is skipped silently, a "
        "reader\ncannot tell 'scanned, found none' from 'never looked'."
    )


def test_the_new_root_is_writable_by_policy() -> None:
    """**The move accomplishes nothing if the new location is not writable.**

    This is the whole point: the old root was denied, so the worktree was useless.
    A new root with no matching allow reproduces the defect one directory over.
    """
    allow = policy()["permissions"]["allow"]
    for verb in ("Edit", "Write"):
        assert any(v.startswith(f"{verb}(") and CURRENT_ROOT_NAME in v for v in allow), (
            f"no `{verb}` allow rule covers the worktree root.\n\n"
            "EnterWorktree's own root is DENIED, which is why worktrees moved. A new root "
            "that\nis merely not-denied still prompts on every edit, and a task cannot run "
            "that way."
        )


def test_the_deny_on_the_former_root_is_untouched() -> None:
    """**Explicitly ruled 2026-08-16: the deny stays as written, do not narrow it.**

    The tempting fix was to carve `.claude/worktrees/**` out of `deny` instead of
    moving the worktrees. That was rejected — it weakens a security control, and
    the reasoning originally offered for it was itself wrong: it leaned on B-036,
    which measured path-scoped **deletion** rules. `Edit`/`Write` path rules DO
    bind, as probed. **The ruling survived its own bad argument, and this test is
    what stops the argument being retried.**
    """
    deny = policy()["permissions"]["deny"]
    for verb in ("Edit", "Write"):
        assert any(v == f"{verb}(//d/Dev/momentum/.claude/worktrees/**)" for v in deny), (
            f"the `{verb}` deny on .claude/worktrees/** is gone or has been narrowed.\n\n"
            "Moving the worktrees is the fix. Weakening this rule is not, and was ruled "
            "against\non 2026-08-16 — including against the reasoning first offered FOR "
            "the ruling."
        )


def test_the_root_is_outside_the_repo_and_every_sync_path() -> None:
    """**Outside the repo, outside Drive, outside every configured pair.**

    Three distinct failures, one assertion each:

    * **inside the repo** — `test_every_directory_holding_tests_is_declared` walks
      the filesystem with `rglob` and collects the worktree's own `tests/`, which
      is the red that started all of this;
    * **inside a sync `to`** — the copier would carry worktree files into the
      tree, or refuse the pair as differing;
    * **inside Drive** — the export mirrors it, and `handoff/` appears twice in a
      folder the design session reads.
    """
    root = (REPO.parent / CURRENT_ROOT_NAME).resolve()

    assert REPO.resolve() not in root.parents and root != REPO.resolve(), (
        f"the worktree root {root} is INSIDE the repository.\n\n"
        "A worktree there carries its own tests/ directory, which pytest collects from "
        "the\nMAIN checkout — the failure whose cause is invisible in every other section "
        "of\nverify.ps1."
    )

    cfg = yaml.safe_load(SYNC_CFG.read_text(encoding="utf-8"))
    paths = [Path(p["from"]) for p in cfg["pairs"]] + [Path(p["to"]) for p in cfg["pairs"]]
    paths.append(Path(r"D:\claude-googledrive-sync"))

    for p in paths:
        try:
            resolved = p.resolve()
        except OSError:                     # a Drive folder may be absent on a clone
            continue
        assert resolved != root and resolved not in root.parents, (
            f"the worktree root {root} is inside a synced path: {resolved}\n\n"
            "Worktrees must sit outside the repository AND outside every sync pair and "
            "Drive\nmirror. A worktree inside a mirror is exported; a worktree inside a "
            "`to` is\ncopied over or reported as differing on every run."
        )
