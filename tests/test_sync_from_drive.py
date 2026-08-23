"""The copier's rules, each proved in isolation against real folders.

026. Every test here builds its own source and destination under `tmp_path` and
runs the real `sync_pair`. Nothing is mocked: the whole value of this tool is
what it does to files on disk, and a mocked copy proves nothing about that.

**The rule under test, in one line: it never overwrites, and it never writes to
the source.** Everything else is reporting.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from tools.sync_from_drive import (  # noqa: E402
    CONFIG, CONVENTION, folder_digest, main, sync_pair,
)


def make_pair(tmp_path: Path, checks: list[str] | None = None) -> dict:
    src, dst = tmp_path / "drive", tmp_path / "inbox"
    src.mkdir(parents=True, exist_ok=True)
    dst.mkdir(parents=True, exist_ok=True)
    return {"id": "t", "from": str(src), "to": str(dst), "glob": "*.md",
            "checks": checks if checks is not None else
            ["filename_convention", "number_collision"]}


def write(p: Path, name: str, text: str) -> Path:
    f = p / name
    f.write_text(text, encoding="utf-8")
    return f


# --------------------------------------------------------------- the three rows
def test_a_new_file_is_copied_and_named(tmp_path: Path) -> None:
    pair = make_pair(tmp_path)
    write(Path(pair["from"]), "031-for-code-thing.md", "body")

    r = sync_pair(pair)

    assert r.copied == ["031-for-code-thing.md"]
    assert (Path(pair["to"]) / "031-for-code-thing.md").read_text(encoding="utf-8") == "body"
    assert "031-for-code-thing.md" in r.headline()  # naming it is the point
    assert not r.blocked


def test_an_identical_file_is_left_alone(tmp_path: Path) -> None:
    """The normal case on a re-run, and it must be silent about the file."""
    pair = make_pair(tmp_path)
    write(Path(pair["from"]), "031-for-code-thing.md", "body")
    write(Path(pair["to"]), "031-for-code-thing.md", "body")

    r = sync_pair(pair)

    assert r.copied == []
    assert r.unchanged == ["031-for-code-thing.md"]
    assert "up to date" in r.headline()
    assert not r.blocked


def test_a_differing_file_is_reported_and_never_overwritten(tmp_path: Path) -> None:
    """**The row this tool exists for.**

    A handed-off task file that changes breaks a reference another party already
    holds, and Claude Code may have read the old one. Two parties acting on two
    different documents while both believe they have the same one is strictly
    worse than a stale copy somebody notices."""
    pair = make_pair(tmp_path)
    write(Path(pair["from"]), "031-for-code-thing.md", "NEW BODY")
    dest_file = write(Path(pair["to"]), "031-for-code-thing.md", "ORIGINAL BODY")

    r = sync_pair(pair)

    assert r.copied == []
    assert len(r.differing) == 1
    name, src_hash, dst_hash = r.differing[0]
    assert name == "031-for-code-thing.md"
    assert src_hash != dst_hash
    assert dest_file.read_text(encoding="utf-8") == "ORIGINAL BODY", "the repo copy was overwritten"
    assert r.blocked, "a differing file must make the run non-zero"


def test_comparison_is_on_content_not_mtime(tmp_path: Path) -> None:
    """Drive rewrites mtimes on files whose bytes never changed -- a re-sync or a
    client reinstall is enough. An mtime comparison would report a change every
    time Drive touched the folder and the real changes would drown in it."""
    pair = make_pair(tmp_path)
    src = write(Path(pair["from"]), "031-for-code-thing.md", "same bytes")
    dst = write(Path(pair["to"]), "031-for-code-thing.md", "same bytes")
    import os
    os.utime(src, (10_000_000, 10_000_000))
    os.utime(dst, (2_000_000_000, 2_000_000_000))
    assert src.stat().st_mtime != dst.stat().st_mtime

    r = sync_pair(pair)

    assert r.unchanged == ["031-for-code-thing.md"]
    assert r.differing == []


# ------------------------------------------------------------------- one way
def test_the_source_folder_is_never_written_to(tmp_path: Path) -> None:
    pair = make_pair(tmp_path)
    src = Path(pair["from"])
    write(src, "031-for-code-a.md", "a")
    write(src, "032-for-code-b.md", "b")
    before = folder_digest(src, "*.md")

    sync_pair(pair)

    assert folder_digest(src, "*.md") == before
    assert sorted(p.name for p in src.iterdir()) == ["031-for-code-a.md", "032-for-code-b.md"]


def test_source_mutation_during_the_run_is_reported(tmp_path: Path) -> None:
    """The before/after digest is not decoration. If the source changes mid-run
    the copy that just landed may not match what is now there, and a silent
    success would be a lie about which bytes were taken."""
    pair = make_pair(tmp_path)
    src = Path(pair["from"])
    write(src, "031-for-code-a.md", "a")
    r = sync_pair(pair)
    assert not r.source_mutated

    # Simulate: hash the folder, mutate it, and confirm the digest notices.
    before = folder_digest(src, "*.md")
    write(src, "031-for-code-a.md", "MUTATED")
    assert folder_digest(src, "*.md") != before


def test_nothing_is_copied_in_dry_run(tmp_path: Path) -> None:
    pair = make_pair(tmp_path)
    write(Path(pair["from"]), "031-for-code-thing.md", "body")

    r = sync_pair(pair, dry_run=True)

    assert r.copied == ["031-for-code-thing.md"]
    assert not (Path(pair["to"]) / "031-for-code-thing.md").exists()


# ------------------------------------------------------- the two 026-only checks
def test_an_off_convention_name_is_copied_AND_flagged(tmp_path: Path) -> None:
    """**Copied, not refused.** The design session may have had a reason, and a
    refused task file is a task nobody sees. The flag is so the anomaly is
    visible before anyone opens it."""
    pair = make_pair(tmp_path)
    write(Path(pair["from"]), "notes-about-something.md", "body")

    r = sync_pair(pair)

    assert r.copied == ["notes-about-something.md"]
    assert (Path(pair["to"]) / "notes-about-something.md").exists()
    assert r.off_convention == ["notes-about-something.md"]
    assert not r.blocked, "an off-convention name is a flag, not a block"


def test_a_number_collision_copies_neither(tmp_path: Path) -> None:
    """Numbers have collided three times in this project. The design session
    reads the folder before assigning, but it reads it at a moment, and Drive
    introduces a gap between reading and landing."""
    pair = make_pair(tmp_path)
    write(Path(pair["from"]), "031-for-code-second-thing.md", "arriving")
    existing = write(Path(pair["to"]), "031-for-code-first-thing.md", "already here")

    r = sync_pair(pair)

    assert r.copied == []
    assert r.collisions == [
        ("031-for-code-second-thing.md", "031-for-code-first-thing.md",
         "already in destination")]
    assert not (Path(pair["to"]) / "031-for-code-second-thing.md").exists()
    assert existing.read_text(encoding="utf-8") == "already here"
    assert r.blocked


def test_two_ARRIVING_files_with_the_same_number_collide(tmp_path: Path) -> None:
    """027 part 3. **The gap the first version could not see.**

    `by_number` was seeded from the destination and never updated, so two
    arriving files sharing a number -- neither in the destination -- were both
    copied silently. That was faithful to 026's text, which describes the check
    against *an existing inbox file*, and it is the likelier collision: the
    design session assigns numbers by reading the inbox at a moment, Drive
    introduces a gap between reading and landing, and two files written in one
    sitting land together.

    **The first file stays.** It is already placed by the time the second is
    seen, and nothing this tool has written is removed by this tool.
    """
    pair = make_pair(tmp_path)
    write(Path(pair["from"]), "031-for-code-alpha.md", "first")
    write(Path(pair["from"]), "031-for-code-beta.md", "second")

    r = sync_pair(pair)

    assert r.copied == ["031-for-code-alpha.md"], "the first arrival is placed"
    assert (Path(pair["to"]) / "031-for-code-alpha.md").read_text(encoding="utf-8") == "first"
    assert not (Path(pair["to"]) / "031-for-code-beta.md").exists()
    assert r.collisions == [
        ("031-for-code-beta.md", "031-for-code-alpha.md", "copied by this run")]
    assert r.blocked

    # The report must SAY which case it is -- the two need different responses.
    from tools.sync_from_drive import render
    text = "\n".join(render([r]))
    assert "copied by this run" in text
    assert "nothing this tool wrote is removed by it" in text


def test_the_arriving_collision_is_caught_in_dry_run_too(tmp_path: Path) -> None:
    """A dry run that misses a collision would green-light a real run that hits
    it -- the report is the whole point of --dry-run."""
    pair = make_pair(tmp_path)
    write(Path(pair["from"]), "031-for-code-alpha.md", "first")
    write(Path(pair["from"]), "031-for-code-beta.md", "second")

    r = sync_pair(pair, dry_run=True)

    assert len(r.collisions) == 1
    assert not any(Path(pair["to"]).iterdir())


def test_the_checks_are_configured_not_hardcoded(tmp_path: Path) -> None:
    """With `checks: []` the same inputs produce no flag and no collision --
    proving the two 026 checks belong to a pair's CONFIG and not to the copier.
    If they were hardcoded, 025's pair would silently inherit them."""
    pair = make_pair(tmp_path, checks=[])
    write(Path(pair["from"]), "notes-about-something.md", "body")
    write(Path(pair["from"]), "031-for-code-second.md", "arriving")
    write(Path(pair["to"]), "031-for-code-first.md", "already here")

    r = sync_pair(pair)

    assert r.off_convention == []
    assert r.collisions == []
    assert sorted(r.copied) == ["031-for-code-second.md", "notes-about-something.md"]


# --------------------------------------------- 069 Part A: retire means retired
def _pair_with_done(tmp_path: Path, checks=("suppress_retired",)) -> tuple[dict, Path]:
    """Like `make_pair`, but the destination has a SIBLING `done/` directory,
    matching `christoph/open/` and `christoph/done/` -- the shape
    `suppress_retired` reads."""
    src, dst, done = tmp_path / "drive", tmp_path / "open", tmp_path / "done"
    src.mkdir(parents=True, exist_ok=True)
    dst.mkdir(parents=True, exist_ok=True)
    done.mkdir(parents=True, exist_ok=True)
    return ({"id": "christoph_open", "from": str(src), "to": str(dst),
             "glob": "*.md", "checks": list(checks)}, done)


def test_a_retired_item_is_suppressed_and_a_live_one_still_copies(tmp_path: Path) -> None:
    pair, done = _pair_with_done(tmp_path)
    write(done, "032-for-christoph-decision-gapped-over.md", "answer")
    write(Path(pair["from"]), "032-for-christoph-decision-gapped-over.md", "template")
    write(Path(pair["from"]), "033-for-christoph-task-live-item.md", "still open")

    r = sync_pair(pair)

    assert r.suppressed == ["032"]
    assert r.copied == ["033-for-christoph-task-live-item.md"]
    assert "1 suppressed (032)" in r.headline()


def test_035a_in_done_does_not_suppress_035(tmp_path: Path) -> None:
    """The id token is taken WHOLE, letter suffix included -- `035` and `035a`
    are different tasks, and a suppression keyed on the bare digits would let
    one retire the other."""
    pair, done = _pair_with_done(tmp_path)
    write(done, "035a-for-christoph-task-something-else.md", "answer")
    write(Path(pair["from"]), "035-for-christoph-task-live.md", "still open")

    r = sync_pair(pair)

    assert r.suppressed == []
    assert r.copied == ["035-for-christoph-task-live.md"]


def test_an_unreadable_done_directory_suppresses_nothing(tmp_path: Path) -> None:
    """**Refusal.** Fail CLOSED toward copying: a `done/` that cannot be read
    -- here, missing entirely -- must not be read as "nothing is retired,
    forever", which would suppress correctly by luck today and wrongly the
    day something is actually retired. It suppresses NOTHING and says so by
    name.

    **Seen red first, against the code before this task's patch.** The old
    `sync_pair` has no `suppress_retired` handling at all, so
    `r.retirement_check_unreadable` did not exist as an attribute and this
    assertion raised `AttributeError` rather than failing cleanly -- confirmed
    by running this test against a `git stash` of the patch, recorded in the
    done-note rather than reproduced here, since this file cannot regress to
    the pre-patch module inline.
    """
    pair, done = _pair_with_done(tmp_path)
    import shutil as _shutil
    _shutil.rmtree(done)
    write(Path(pair["from"]), "032-for-christoph-decision-gapped-over.md", "template")

    r = sync_pair(pair)

    assert r.suppressed == []
    assert r.copied == ["032-for-christoph-decision-gapped-over.md"]
    assert r.retirement_check_unreadable is not None
    assert "not readable" in r.headline()
    assert "nothing suppressed" in r.headline()


def test_the_four_retirement_report_lines_are_distinguishable(tmp_path: Path) -> None:
    """§4a: silence must be meaningful. Normal, N-suppressed, done/-unreadable
    and source-unreachable must not read alike."""
    pair, done = _pair_with_done(tmp_path)
    normal = sync_pair(pair).headline()

    write(done, "032-for-christoph-decision-gapped-over.md", "answer")
    write(Path(pair["from"]), "032-for-christoph-decision-gapped-over.md", "template")
    suppressing = sync_pair(pair).headline()

    import shutil as _shutil
    _shutil.rmtree(done)
    unreadable = sync_pair(pair).headline()

    gone = dict(pair, **{"from": str(tmp_path / "does-not-exist")})
    unreachable = sync_pair(gone).headline()

    lines = {normal, suppressing, unreadable, unreachable}
    assert len(lines) == 4, "two report lines read alike:\n" + "\n".join(sorted(lines))


def test_pairs_without_the_check_are_unaffected_by_a_done_sibling(tmp_path: Path) -> None:
    """`suppress_retired` is opt-in per pair. A pair that never asked for it
    must behave exactly as before even if a `done/` sibling happens to exist
    beside its destination."""
    pair = make_pair(tmp_path)  # checks default to the two 026 checks, not this one
    done = tmp_path / "done"
    done.mkdir()
    write(done, "031-for-code-thing.md", "irrelevant")
    write(Path(pair["from"]), "031-for-code-thing.md", "body")

    r = sync_pair(pair)

    assert r.suppressed == []
    assert r.retirement_check_unreadable is None
    assert r.copied == ["031-for-code-thing.md"]


# ------------------------------------------------------ silence must be meaningful
def test_empty_and_unreachable_do_not_read_alike(tmp_path: Path) -> None:
    """`A task that prints nothing when it succeeds prints nothing when it
    fails.` An empty folder is a working pipeline with nothing to send; a
    missing one is a broken path or an unmounted Drive."""
    empty = make_pair(tmp_path / "a")
    (tmp_path / "a").mkdir(exist_ok=True)
    r_empty = sync_pair(empty)

    gone = dict(empty, **{"from": str(tmp_path / "does-not-exist")})
    r_gone = sync_pair(gone)

    assert "EMPTY" in r_empty.headline()
    assert "UNREACHABLE" in r_gone.headline()
    assert r_empty.headline() != r_gone.headline()
    assert not r_empty.blocked, "an empty source is idle, not broken"
    assert r_gone.blocked, "an unreachable source means the pipeline is broken"


def test_the_three_outcomes_are_distinguishable(tmp_path: Path) -> None:
    pair = make_pair(tmp_path)
    write(Path(pair["from"]), "031-for-code-thing.md", "body")
    new = sync_pair(pair).headline()
    uptodate = sync_pair(pair).headline()

    assert "1 new" in new and "031-for-code-thing.md" in new
    assert "up to date" in uptodate
    assert new != uptodate


# ------------------------------------------------------------------ the config
def test_the_shipped_config_has_both_pairs() -> None:
    """026: one copier, N configured pairs. A second script is the thing the
    task exists to prevent, and a config with one pair is how that starts.

    **Three pairs since 043**, which added `christoph_open`. The name of this
    test still says "both" and is deliberately not renamed: `043` cites it and a
    test that moves out from under a citation breaks the reference, which is the
    same argument `handoff/` is copy-and-keep for.
    """
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    ids = [p["id"] for p in cfg["pairs"]]
    assert ids == ["regime_snapshots", "handoff_inbox", "christoph_open"], ids
    for p in cfg["pairs"]:
        assert Path(p["to"]).is_absolute() and Path(p["from"]).is_absolute()


def test_the_copier_has_no_pair_specific_branches() -> None:
    """Every difference between the two pairs must be a value in sync.yaml.

    A branch on `id == "handoff_inbox"` is how one copier becomes two."""
    # CODE ONLY -- docstrings and comments stripped via ast. The first version
    # read the raw source and failed on the copier's own usage example,
    # `--pair handoff_inbox`, in its module docstring. **A guard that forbids
    # naming a pair in documentation pushes the documentation out of the file to
    # stay green**, which is a worse trade than the guard is worth. Same
    # correction as 022's root-derivation guard, for the same reason.
    import ast

    tree = ast.parse((REPO / "tools" / "sync_from_drive.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if (isinstance(body, list) and body and isinstance(body[0], ast.Expr)
                and isinstance(getattr(body[0], "value", None), ast.Constant)
                and isinstance(body[0].value.value, str)):
            node.body = body[1:] or [ast.Pass()]
    code = ast.unparse(tree)

    for pair_id in ("handoff_inbox", "regime_snapshots"):
        assert pair_id not in code, (
            f"{pair_id!r} appears in the copier's code. Pair-specific behaviour "
            "belongs in config/sync.yaml -- a branch here is a second script "
            "wearing one file's name.")


def test_the_destination_paths_are_inside_the_repo() -> None:
    """A misconfigured `to:` would copy Drive content somewhere no test covers."""
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    for p in cfg["pairs"]:
        assert REPO.resolve() in Path(p["to"]).resolve().parents or \
            Path(p["to"]).resolve() == REPO.resolve(), p


def test_no_source_folder_is_inside_the_repo() -> None:
    """The reverse, and it is the one that would be silently destructive: a
    `from:` inside the tree would make the repo its own sync source."""
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    for p in cfg["pairs"]:
        src = Path(p["from"])
        assert REPO.resolve() not in src.resolve().parents, p


@pytest.mark.parametrize("name,ok", [
    ("026-for-code-inbox-sync-from-drive.md", True),
    ("020-for-code-drive-export.md", True),
    ("notes.md", False),
    ("26-for-code-short-number.md", False),
    ("026-regime-context.md", False),
])
def test_the_convention_pattern(name: str, ok: bool) -> None:
    assert bool(CONVENTION.match(name)) is ok


def test_main_returns_nonzero_when_a_person_must_look(tmp_path: Path) -> None:
    """A scheduled run that reports a collision and exits 0 is a report nobody
    reads.

    **`--record` is passed, and OBS-064 is why.** `043` gave `main()` a run
    record defaulting to the tracked `sync-run-record.md` at the repo root.
    These two `main()` calls had no `--record`, so **every pytest run overwrote
    the real record with this fixture's filename** -- `sync-run-record.md` was
    found reading `outcome : t: 1 new - 031-for-code-thing.md`, a copy into a
    temp directory, in the one artifact whose job is saying when the real sync
    last worked. It also left the tree dirty after every suite run.

    Nothing could see it until `verify.ps1` section 6 existed to print it, which
    is `043`'s own subject arriving inside `043`.
    """
    pair = make_pair(tmp_path)
    write(Path(pair["from"]), "031-for-code-thing.md", "NEW")
    write(Path(pair["to"]), "031-for-code-thing.md", "OLD")
    cfg = tmp_path / "sync.yaml"
    cfg.write_text(yaml.safe_dump({"pairs": [pair]}), encoding="utf-8")
    rec = tmp_path / "run-record.md"

    assert main(["--config", str(cfg), "--record", str(rec)]) == 1

    pair2 = make_pair(tmp_path / "clean")
    (tmp_path / "clean").mkdir(exist_ok=True)
    write(Path(pair2["from"]), "031-for-code-thing.md", "body")
    cfg2 = tmp_path / "sync2.yaml"
    cfg2.write_text(yaml.safe_dump({"pairs": [pair2]}), encoding="utf-8")
    assert main(["--config", str(cfg2), "--record", str(rec)]) == 0


def test_an_unknown_pair_id_is_an_error_not_a_silent_no_op(tmp_path: Path) -> None:
    """`--pair typo` matching nothing would run zero pairs and exit 0, which
    reads exactly like a healthy up-to-date run.

    `--record` for OBS-064's reason, though this path returns before writing:
    **the guard belongs on the call, not on the current control flow.** A later
    edit that moves the record write earlier must not silently re-arm the bug.
    """
    assert main(["--pair", "no-such-pair", "--record", str(tmp_path / "r.md")]) == 2


def test_no_test_in_this_file_writes_the_tracked_run_record() -> None:
    """**OBS-064, made structural.** Reviewing every `main()` call by eye is how
    this was missed the first time.

    Positional and scoped to this file: every `main([...])` literal here must
    carry `--record`. The real record is a TRACKED artifact at the repo root and
    a test that overwrites it is a test that forges the evidence.
    """
    src = Path(__file__).read_text(encoding="utf-8")
    calls = re.findall(r"main\(\[[^\]]*\]", src)
    # The regex above matches its own source line; drop anything without a
    # string literal in it.
    calls = [c for c in calls if '"' in c]
    naked = [c for c in calls if "--record" not in c]
    assert not naked, (
        "these main() calls write the tracked sync-run-record.md:\n  "
        + "\n  ".join(naked)
        + "\n\nPass --record with a tmp_path. OBS-064: the real record was found "
          "carrying a fixture filename, and the suite left the tree dirty every run.")
