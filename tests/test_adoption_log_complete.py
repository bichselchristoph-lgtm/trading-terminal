"""Every tracked file arrived through the gate, the evidence carry, or bootstrap.

This is the test that makes M001 stick. Without it the adoption gate is prose,
and a convention that lives in prose depends on someone remembering -- which is
exactly how the predecessor tree came to hold a README describing another
repository.

With it, wholesale import is not discouraged. It is impossible without a visible
failing test.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

#: The M001 §2 bootstrap. These files were WRITTEN for this tree, not carried,
#: so they have no source path and no adoption row. Everything else must be
#: accounted for. Keep this list short -- every entry is a hole in the gate.
BOOTSTRAP_ALLOWLIST = {
    ".gitignore",
    # Not in M001 §2's list. Added because without it git normalises line endings
    # on checkout, which rewrites the bytes of hash-verified carried evidence and
    # turns test_evidence_carry_intact red on a fresh clone -- automated tidying
    # of exactly the kind §4 forbids.
    ".gitattributes",
    "pytest.ini",
    "requirements.txt",
    "CLAUDE.md",
    "README.md",
    "ADOPTION-LOG.md",
    "EVIDENCE-CARRY.md",
    "tools/adopt.py",
    "tests/test_adoption_log_complete.py",
    "tests/test_no_secrets.py",
    "tests/test_pytest_collection.py",
    "tests/test_evidence_carry_intact.py",
    # Authored here under H9, not adopted. Caught by this very test when
    # docs/specs/ lost its native-prefix carve-out, which is the gate working
    # as designed on its own author.
    "tests/test_spec_pointers.py",
    "tests/test_regime_snapshot_path.py",
    "tests/test_regime_prompt_invariants.py",
    "tests/test_resupplied_docs_are_repaired.py",
    "tests/test_adopt_supersession.py",
    # Authored here under H11, not supplied from outside. It is the one file
    # in docs/specs/ that documents the tree rather than specifying the system.
    "docs/specs/RE-SUPPLY.md",
    "tests/test_handoff_state_declared.py",
    # Authored here under task 012, not adopted from anywhere. tools/ is a code
    # tree and deliberately has no native-prefix carve-out, so the gate demanded
    # this entry -- correctly, and it surfaced on 013's full-suite run rather
    # than 012's, which only ran the tool.
    "tools/capture_tape.py",

    # ---- S009: the first slice to author NEW CODE in this tree -------------
    # The gate has three routes in: adoption, evidence carry, and this list.
    # None of them is "code written fresh here for a slice", because M001 built
    # the gate for a migration and every file until now either came from the
    # predecessor or was scaffolding.
    #
    # These are natively authored, in a CODE TREE, which deliberately has no
    # native-prefix carve-out — so they land here. **The allowlist is now doing
    # two jobs**, and the second one will grow by roughly this many entries per
    # slice. That is the "list that becomes a hiding place" this project keeps
    # naming, and it needs a proper fourth route rather than more entries.
    # Flagged in S009's done-note as a decision, not taken here.
    "config/layout.yaml",
    "live/__init__.py",
    "live/tui/__init__.py",
    "live/tui/grammar.py",
    "live/tui/day_record.py",
    "live/tui/layout.py",
    "live/tui/app.py",
    "live/tests/__init__.py",
    "live/tests/test_tui_grammar.py",
    "live/tests/test_tui_frame.py",
    "live/tests/snapshots/empty-record.txt",

    # ---- 015, S009a and 016: the growth rate S009 predicted ----------------
    # The block above said this list's second job "will grow by roughly this
    # many entries per slice". **Seven more, across three tasks.** That
    # prediction is now measured rather than expected.
    #
    # It is recorded as OBS-008 in docs/observations/OBSERVATIONS.md with a
    # review-by date, which is the point of the ledger 016 built: acting on the
    # finding no longer depends on somebody rereading S009's done-note.
    #
    # STILL NOT FIXED HERE. A fourth route into the tree is a design decision,
    # and 016 is not the task that takes it.
    "tests/test_uat_has_a_file.py",                        # 015
    "live/tests/test_tui_measured_against_its_tile.py",    # S009a
    "live/tests/snapshots/tile-80x24.txt",                 # S009a - the floor
    "live/tests/snapshots/tile-209x54.txt",                # S009a - the working width
    "live/tests/snapshots/tile-240x70.txt",                # S009a - the ceiling
    "tests/test_observations_ledger.py",                   # 016 part 5c
    # Repo root, not a code tree. The root has no native-prefix carve-out and
    # must not get one -- it is where a stray copied file would be least visible.
    "verify.ps1",                                          # 016 part 1

    # ---- S010: core/ is born, and the count is now 21 ----------------------
    # S009 predicted ~11 allowlist entries per slice. 015/S009a/016 added seven;
    # S010 adds eight and creates a whole tree. **The prediction is holding and
    # the list is now doing its second job more than its first.**
    #
    # OBS-008 in the ledger, with a review-by date. A fourth route into the tree
    # -- "authored here for a slice" -- is still a design decision nobody has
    # taken, and S010 is not the task that takes it.
    "core/__init__.py",
    "core/indicators/__init__.py",
    "core/indicators/context.py",
    "core/tests/__init__.py",
    "core/tests/test_core_imports_nothing_first_party.py",
    "live/attach/__init__.py",
    "live/attach/attach.py",
    "live/tests/test_attach.py",
    "live/attach/ibkr.py",                                 # S010 part 6

    # ---- 020: two more, and the count is now 23 ----------------------------
    # Both authored here. `export-handoff.ps1` is at the repo root, which has no
    # native-prefix carve-out and must not get one -- the root is where a stray
    # copied file would be least visible. `verify.ps1` landed the same way under
    # 016 and is four entries above.
    #
    # OBS-008 in the ledger still stands: a fourth route in -- "authored here for
    # a slice" -- is a design decision nobody has taken, and 020 is not the task
    # that takes it.
    "export-handoff.ps1",                                  # 020 part 2
    "tests/test_export_scope_is_derived.py",               # 020 part 2

    # ---- 022: one more, and the count is now 24 ----------------------------
    # The first conftest.py in this tree. It exists to print the credential
    # scan's root coverage in the pytest report header, because a pytest.skip
    # renders as a bare `s` and invisibility is the failure test_no_secrets.py
    # exists to prevent.
    "tests/conftest.py",                                   # 022 part 2

    # ---- 026: three more, and the count is now 27 --------------------------
    # One copier, two configured pairs -- 026 forbids a second script, so the
    # regime pair in sync.yaml belongs to 025 and is configured but not yet
    # exercised.
    "config/sync.yaml",                                    # 026
    "tools/sync_from_drive.py",                            # 026
    "tests/test_sync_from_drive.py",                       # 026

    # ---- 027: the rule-15 precondition, and the count is now 28 ------------
    # The grouping itself is NOT built -- could_not_do is free text with no key,
    # and a matcher that mis-groups would be worse than none. This file holds
    # the sound half plus the tripwire that fires when the prompt gains an id.
    "tests/test_regime_snapshot_could_not_do.py",          # 027 part 2

    # ---- 023: the verification gate writes a file -------------------------
    "tests/test_verify_output_is_ignored.py",              # 023 part 2

    # ---- 021: three more, and the count is now 31 --------------------------
    # An investigation, not a slice, and it still lands here -- which is the
    # clearest evidence yet for OBS-008. The probe and its analysis are split on
    # purpose: the probe holds five live streams for six hours against a session
    # that cannot be re-recorded, so no arithmetic runs in the same process.
    "tools/probe_keepuptodate_scale.py",                   # 021
    "tools/analyse_keepuptodate_scale.py",                 # 021
    "tests/test_keepuptodate_scale.py",                    # 021

    # ---- 029: two more, and the count is now 33 ----------------------------
    # The app had no entry point. `MomentumApp` was defined and never run, so
    # `python -m live.tui.app` imported the module and exited 0 in silence while
    # 236 tests passed -- every one of them driving the app through Textual's
    # run_test() pilot, which never needs one.
    #
    # **The test is a subprocess and has to be.** An import-and-assert-it-exists
    # test would pass against an entry point that raises on its first line, and
    # exit 0 is the failure mode being fixed rather than the pass condition.
    "live/tui/__main__.py",                                # 029 part 1
    "live/tests/test_launches_as_a_program.py",            # 029 part 2

    # ---- 032: one more, and the count is now 34 ----------------------------
    # `attach()` was reachable from a test and from nothing else. This file is
    # the key-press test that would have caught it -- `Pilot.press()` through
    # Textual's real dispatch, never `run_action()`, which would pass against a
    # binding no key reaches.
    #
    # **Written by a SECOND session working this tree concurrently on
    # 2026-08-13.** Two independent 032 suites existed for four minutes; this one
    # landed first, imports the existing `Fake` from test_attach.py rather than
    # declaring a second fixture, and survived on Christoph's call. The other was
    # deleted after its one unique case was ported in. Recorded here because the
    # allowlist is where a file's arrival is accounted for, and "arrived from the
    # other terminal" is exactly the provenance this gate exists to make visible.
    "live/tests/test_attach_is_reachable_by_key.py",       # 032

    # ---- 034: one more, and the count is now 41 ----------------------------
    # The connection settings for the first broker this tree has ever dialled.
    # `config/layout.yaml` landed the same way under S009 and is the precedent:
    # config/ is not a code tree, but it has no native-prefix carve-out and must
    # not get one -- a config file is where a value arrives with no provenance
    # and is then read as a decision somebody took.
    #
    # **Only ONE entry for a task that wired a broker into the launcher**, and
    # that is not the list getting better. Everything else 034 touched was an
    # edit to a file already accounted for. OBS-008 still stands.
    "config/ibkr.yaml",                                    # 034 part 1

    # ---- 024: six more, and the count is now 40 ----------------------------
    # **The first tracked files under `.claude/` in this tree's history.** M001
    # §6 says "do not copy .claude/ in any form" and the predecessor's
    # .claude/settings.local.json held a live Databento key -- so the .gitignore
    # exception is four markdown files wide and nothing else, fenced by
    # test_claude_dir_stays_ignored.py and seen red against a planted
    # .claude/agents/settings.local.json.
    #
    # The roster has to be COMMITTED or it does not exist: an agent definition
    # that is not in the repository is absent from every clone, and a restriction
    # nobody has is not a restriction. That is the whole reason the exception was
    # opened rather than the roster kept local.
    #
    # OBS-008 again: six more allowlist entries, and this task is not a slice at
    # all -- it is infrastructure. **The second job this list is doing has now
    # outgrown the first by a wide margin**, and a fourth route into the tree is
    # still a design decision nobody has taken.
    # ---- 037: two more, and the count is now 42 ----------------------------
    # `export-run-record.md` is at the repo root, alongside `verify.ps1` and
    # `export-handoff.ps1`, and for the same reason those are: the root has no
    # native-prefix carve-out and must not get one.
    #
    # It is the one entry here that is WRITTEN BY A PROGRAM rather than by a
    # person. That is deliberate and is the whole mechanism -- the export leaves
    # a record of every attempt outside both destinations, because a record
    # inside the destination cannot report a failure to reach the destination.
    # Tracked rather than gitignored so test_export_run_record.py has a subject
    # on a fresh clone; the cost is that an export run after a commit leaves the
    # tree dirty until the next commit picks it up.
    #
    # OBS-008 again, unchanged: a fourth route in -- "authored here for a slice"
    # -- is still a design decision nobody has taken, and 037 is a bug fix.
    "export-run-record.md",                                # 037 part 2a
    "tests/test_export_run_record.py",                     # 037 part 2c

    ".claude/agents/architect.md",                         # 024
    ".claude/agents/implementer.md",                       # 024
    ".claude/agents/reviewer.md",                          # 024
    ".claude/agents/test-author.md",                       # 024
    "tests/test_subagent_roster.py",                       # 024
    "tests/test_claude_dir_stays_ignored.py",              # 024

    # ---- 039: five more -----------------------------------------------------
    # `core/risk/` is the second tree under core/ and it is born the same way
    # `core/indicators/` was under S010 -- authored here, no adoption row, an
    # allowlist entry each. That is five entries for one slice, against S009's
    # prediction of ~11, and the prediction has now held across six slices.
    #
    # `config/risk.yaml` lands like `config/ibkr.yaml` did under 034 and
    # `config/layout.yaml` under S009: config/ is not a code tree, but it has no
    # native-prefix carve-out and MUST NOT GET ONE -- a config file is where a
    # value arrives with no provenance and is then read as a decision somebody
    # took. That risk is live here rather than theoretical: `risk_usd_per_trade`
    # is the number every position size will be computed from and NOTHING READS
    # THE FILE YET (OBS-057).
    #
    # OBS-008 still stands and is now the longest-open row in the ledger.
    "core/risk/__init__.py",                               # 039 Part 2
    "core/risk/classify.py",                               # 039 Part 2
    "core/tests/test_trade_classification.py",             # 039 Part 2
    "config/risk.yaml",                                    # 039 Part 1
    "tests/test_risk_config_matches_core.py",              # 039 Part 1
}


def tracked_files() -> list[str]:
    """`-z` is load-bearing. Without it git quotes and octal-escapes any path
    containing non-ASCII bytes -- a task file whose name holds an em-dash comes
    back as `"handoff/inbox/H9 \\342\\200\\224 ...md"` and never matches the real
    name in the log, so a correctly-carried file reports as an orphan."""
    out = subprocess.run(
        ["git", "ls-files", "-z"], cwd=REPO, capture_output=True, check=True
    ).stdout.decode("utf-8")
    return [p for p in out.split("\0") if p]


def logged_paths(filename: str, column: int) -> set[str]:
    """Pull the backticked path out of the given column of a markdown table."""
    path = REPO / filename
    if not path.exists():
        return set()
    found = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or line.startswith("|---") or " date " in line[:10]:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) <= column:
            continue
        m = re.match(r"^`(.+?)`$", cells[column])
        if m:
            found.add(m.group(1))
    return found


#: Surfaces where files are AUTHORED in this tree rather than arriving from
#: anywhere. A done-note written here is native work: it was neither adopted nor
#: carried, and demanding a log row for it would make the log meaningless.
#:
#: The trade-off, stated rather than left implicit: a file could be copied
#: wholesale into handoff/ or docs/observations/ without tripping the gate. That
#: is accepted because these hold prose, not behaviour -- nothing here is
#: imported and then silently relied on, which is the failure the gate exists to
#: stop. NO CODE TREE gets this carve-out; core/, live/, harness/ and tools/
#: always need a row.
#: `docs/specs/` was here until H9 and has been REMOVED. The specs turned out to
#: be adopted, not authored, and all thirteen carry ADOPTION-LOG rows -- so the
#: carve-out was buying nothing and costing the gate its reach over a directory
#: that now holds the system's most load-bearing documents.
NATIVE_PREFIXES = ("handoff/", "docs/observations/", "docs/regime-snapshots/",
                   "christoph/")


def is_native(path: str) -> bool:
    return path.startswith(NATIVE_PREFIXES)


def accounted_for() -> set[str]:
    return (
        BOOTSTRAP_ALLOWLIST
        | logged_paths("ADOPTION-LOG.md", 1)
        | logged_paths("EVIDENCE-CARRY.md", 1)
    )


def test_every_tracked_file_is_accounted_for() -> None:
    """The rule. A file in git that nobody logged arrived by copying."""
    known = accounted_for()
    orphans = sorted(f for f in tracked_files() if f not in known and not is_native(f))
    assert not orphans, (
        "these tracked files arrived by neither adoption nor evidence carry:\n  "
        + "\n  ".join(orphans)
        + "\n\nEvery file in this tree enters through tools/adopt.py (logged in "
        "ADOPTION-LOG.md)\nor the evidence carry (logged in EVIDENCE-CARRY.md). "
        "Copying a file in directly is\nthe failure mode this repository was created to "
        "prevent -- see CLAUDE.md.\nIf one of these is genuinely bootstrap, it belongs in "
        "BOOTSTRAP_ALLOWLIST, and\nadding it there should feel like a decision."
    )


def test_the_allowlist_does_not_rot() -> None:
    """An allowlist entry for a file that no longer exists is a hole nobody can
    see. It would silently re-admit a future file of the same name."""
    stale = sorted(e for e in BOOTSTRAP_ALLOWLIST if not (REPO / e).exists())
    assert not stale, (
        f"BOOTSTRAP_ALLOWLIST names files that do not exist: {stale}. "
        "Remove them -- a stale entry silently pre-authorises any future file with that name."
    )


def test_no_code_tree_is_native() -> None:
    """The carve-out must never reach a directory that holds behaviour. If
    NATIVE_PREFIXES ever grows to include one, every file in it stops needing an
    adoption row and the gate quietly stops applying to code."""
    for tree in ("core/", "live/", "harness/", "tools/"):
        assert not is_native(tree + "anything.py"), (
            f"NATIVE_PREFIXES now exempts {tree} -- that is a code tree, and exempting it "
            "means files with behaviour can arrive with no provenance and no test."
        )


def test_the_check_can_actually_fail() -> None:
    """A test that cannot fail proves nothing. Confirm an unlogged path would be
    caught, so a future refactor that quietly widens `accounted_for` is visible."""
    assert "core/definitely_not_adopted.py" not in accounted_for()


@pytest.mark.parametrize("required", ["ADOPTION-LOG.md", "EVIDENCE-CARRY.md"])
def test_the_logs_exist(required: str) -> None:
    """If a log is deleted, `logged_paths` returns an empty set and this test
    would pass vacuously while the gate silently stopped accounting for anything."""
    assert (REPO / required).exists(), (
        f"{required} is missing. Without it the completeness check above still passes, "
        "but accounts for nothing -- the same 'deleting the file is the cheapest route to "
        "green' failure the open-questions gate was rewritten to close."
    )
