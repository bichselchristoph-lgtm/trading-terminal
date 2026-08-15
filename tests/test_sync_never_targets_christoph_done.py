"""043 part 1 — **no configured pair may write into `christoph/done/`.**

`043` amends the rule that no Claude writes to `christoph/` **narrowly, and only
for `christoph/open/`.** That half holds files the design session authors — its
task files for Christoph — so there was never an authorship conflict there, only
a placement convention that cost a manual copy on every UAT.

**`christoph/done/` is the other half and it does not change.** Those are
Christoph's own answers. It is copy-verify-retire and **he** performs it:
nothing writes into it, by any channel, ever.

**Why this is a test and not a sentence.** The lock lived in `CLAUDE.md` and in
`docs/specs/HANDOFF-PROTOCOL.md`, and prose locks depend on the next person
having read them. Adding a fourth pair is three lines of YAML, and the obvious
symmetry — *`christoph/open/` syncs in, so why not `christoph/done/`* — is
exactly the change that would destroy a UAT answer by overwriting it with a
Drive copy. **The symmetry is the trap.**

Scoped positionally to `config/sync.yaml`, which is the only place a pair can be
declared: `tools/sync_from_drive.py` has no pair-specific branches and reads
every destination from that file.
"""
from __future__ import annotations

import pathlib
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

CONFIG = REPO / "config" / "sync.yaml"

#: The one destination no pair may target, in any spelling.
#:
#: **Matched on the path's SHAPE, not against this checkout's own path.**
#: `config/sync.yaml` carries absolute paths into the main checkout, so a test
#: running from a git worktree resolves `REPO` to the worktree and would compare
#: two different trees — and would therefore MISS a pair aimed at the main
#: checkout's `christoph/done`, which is the one holding the real answers.
#: The first version of this guard had exactly that hole.
FORBIDDEN_TAIL = ("christoph", "done")


def configured_pairs() -> list[dict]:
    data = yaml.safe_load(CONFIG.read_text(encoding="utf-8")) or {}
    pairs = data.get("pairs")
    assert isinstance(pairs, list) and pairs, f"{CONFIG}: no `pairs:` list"
    return pairs


def _targets_forbidden(dest: str) -> bool:
    """**Resolved, not string-matched.** `christoph/done`, `christoph\\done`,
    a trailing slash and a `..` detour are the same destination, and a
    substring check would miss at least one of them."""
    parts = tuple(Path(dest).resolve().parts)
    n = len(FORBIDDEN_TAIL)
    return any(parts[i:i + n] == FORBIDDEN_TAIL for i in range(len(parts) - n + 1))


def test_no_pair_writes_into_christoph_done() -> None:
    offenders = [p["id"] for p in configured_pairs() if _targets_forbidden(p["to"])]
    assert not offenders, (
        f"these configured pairs write into christoph/done/: {offenders}.\n"
        "**That folder holds Christoph's own answers and nothing writes into "
        "it, by any channel, ever.** 043 amended the christoph/ rule for "
        "christoph/open/ only — the design session authors those, so there was "
        "never an authorship conflict there. A UAT answer overwritten by a "
        "Drive copy is not recoverable from this repository.")


def test_the_guard_catches_a_forbidden_pair() -> None:
    """**The refusal, executed.** 043: *seen red by adding one.*

    Without this the test above passes on a config that has no pairs at all, or
    on a `_targets_forbidden` that always returns False — and a guard that
    cannot be shown to fire is a guard nobody has checked.
    """
    here = REPO / "christoph" / "done"
    assert _targets_forbidden(str(here)), (
        "the guard does not recognise christoph/done/ as forbidden")
    assert _targets_forbidden(str(here / "NNN-a-uat.md")), (
        "the guard does not recognise a path INSIDE christoph/done/")
    # **The case the first version of this guard missed: ANOTHER checkout.**
    # config/sync.yaml holds absolute paths into the main tree, so a guard
    # resolved against a worktree would wave through a pair aimed at the real
    # answers.
    assert _targets_forbidden(str(pathlib.PurePath("D:/Dev/momentum/christoph/done"))), (
        "the guard only recognises THIS checkout's christoph/done")


@pytest.mark.parametrize("allowed", [
    "christoph/open",
    "handoff/inbox",
    "docs/regime-snapshots",
])
def test_the_guard_does_not_overreach(allowed: str) -> None:
    """The three destinations that ARE legal must not trip it.

    **`christoph/open/` is the one that matters here** — it is a sibling of the
    forbidden folder, and a guard written as a substring check on `christoph`
    would refuse the very pair 043 exists to add.
    """
    assert not _targets_forbidden(str(REPO / allowed))


def test_christoph_open_is_actually_configured() -> None:
    """043 part 1 landed, and this is what makes the guard above meaningful.

    A test asserting an absence passes against a feature that does not exist —
    `OBS-037`. If pair 3 were never added, every assertion in this file would
    still be green while the task had not been done.
    """
    dests = {p["id"]: Path(p["to"]).resolve() for p in configured_pairs()}
    assert "christoph_open" in dests, (
        f"no `christoph_open` pair in {CONFIG}. Configured: {sorted(dests)}")
    # Compared on shape, for the same reason `_targets_forbidden` is: the
    # configured paths are absolute into the main checkout and this test may be
    # running from a worktree.
    assert dests["christoph_open"].parts[-2:] == ("christoph", "open"), (
        f"the christoph_open pair points at {dests['christoph_open']}")
