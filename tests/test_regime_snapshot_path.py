"""One path for the regime snapshot, and the legacy one appears nowhere.

Two faults produced this. Five naming conventions were in use for one artifact
(`DRIVE-ARCHIVE-LIST.md` lists them), and the convention that won pointed at a
folder that has never existed: `SPEC.md` §3.2, §5.1 and `REGIME-PROMPT.md` all
named a `claude/`-rooted directory, checked against disk on 2026-08-10 and found
absent. Every snapshot written so far went to a cloud session's own filesystem.

**Why `docs/` and not the original root.** The old name sorted adjacent to
`.claude/`, differed by one character, and one of the two was untracked config
that held a plaintext Databento key. Two directories that look identical in a
listing, with opposite tracking rules, is a trap worth three path edits to
avoid.

**The snapshots are tracked.** They are the record that makes the §5.5a join to
the trade log possible, and an untracked record is not a record.

**016 part 3 -- the exemption is DERIVED, not listed.**

`EXEMPT_PREFIXES` was `("docs/specs/DRIVE-ARCHIVE-LIST.md", "handoff/")`, and it
failed on `christoph/done/006-h8-snapshot-path-fills.md`, which cites the legacy
path **while describing the change H8 made.** The docstring's own reason for
exempting `handoff/` -- *task files and done-notes record what the convention was
at the time they were written, and rewriting them would falsify the record* --
describes `christoph/` word for word. The list simply predated that tree.

**A prefix list will need widening at the next tree, and a list that grows is
the hiding place this project keeps naming.** So the property is derived
instead: *this file is a dated record of a past state rather than a live
pointer*, established two ways and no other:

1. **It declares one of the five handoff states in its header region.** That is
   what makes a document a record by construction -- `WRITTEN · HANDED OFF ·
   RUNNING · REVIEWED · DONE`. **`CURRENT` is deliberately not among them**, so
   `SPEC.md`, `BUILD-PLAN.md` and `REGIME-PROMPT.md` are never exempt -- and
   those are exactly the files where a reintroduced live pointer would matter,
   since all three named a `claude/`-rooted directory before H8.
2. **It is recorded in `EVIDENCE-CARRY.md`.** Resolution D, reused rather than
   re-invented. Two carried predecessor task files predate the five-state
   vocabulary entirely -- one says `**Status** OPEN`, the other has no header --
   and they may not be edited, because carried evidence is byte-identical or it
   is not evidence.

`docs/specs/DRIVE-ARCHIVE-LIST.md` stays **explicitly named**, because it is a
genuinely different case the derivation should not reach: a `STATUS CURRENT`
spec that inventories the five competing naming conventions as history. Reaching
it by rule would mean a rule that also reaches every other live spec.

**Three guards, on the Resolution D pattern.** `test_guard_1` refuses to exempt
anything but prose; `test_guard_2` proves a file with neither property is not
exempt; `test_guard_3` pins the three live specs as never-exempt by name.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

CANONICAL = "docs/regime-snapshots/"
FORBIDDEN = "claude/regime-snapshots/"

SUFFIXES = (".md", ".py", ".yaml", ".yml", ".ps1", ".json")
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "venv", "node_modules"}

#: The ONE named exception. See the module docstring for why it cannot be derived.
EXEMPT_NAMED = ("docs/specs/DRIVE-ARCHIVE-LIST.md",)

#: The five states, and nothing else. `OPEN` and `CURRENT` are not among them.
STATES = ("WRITTEN", "HANDED OFF", "RUNNING", "REVIEWED", "DONE")

#: Same header region and same pattern as `tests/test_handoff_state_declared.py`.
#: **Positional, not lexical** -- a state word appearing in body prose is a
#: citation, not a declaration, and matching it anywhere would let any document
#: exempt itself by discussing handoff states.
HEADER_LINES = 20
STATUS_RE = re.compile(r"\*\*Status\*\*[:\s]*([A-Za-z][A-Za-z ]*?)\s*(?:·|\||—|$)", re.M)

MANIFEST = REPO / "EVIDENCE-CARRY.md"
_CARRIED = re.compile(r"^\|\s*\d{4}-\d{2}-\d{2}\s*\|\s*`(?P<rel>[^`]+)`", re.M)

#: Only prose can be a record. A live pointer lives in code or config, so the
#: exemption may never reach one -- that is guard 1, and it is the property that
#: makes this derivation safe where a bare date header would not be.
PROSE_SUFFIX = ".md"


def carried() -> set[str]:
    if not MANIFEST.exists():
        return set()
    return {m.group("rel") for m in _CARRIED.finditer(MANIFEST.read_text(encoding="utf-8"))}


def declares_a_handoff_state(text: str) -> bool:
    head = "\n".join(text.splitlines()[:HEADER_LINES])
    m = STATUS_RE.search(head)
    return bool(m) and m.group(1).strip().upper() in STATES


def is_a_record(rel: str, text: str) -> bool:
    """The derived property: a dated record of a past state, not a live pointer."""
    if rel in EXEMPT_NAMED:
        return True
    if not rel.lower().endswith(PROSE_SUFFIX):
        return False
    return declares_a_handoff_state(text) or rel in carried()


def candidate_files() -> list[Path]:
    return [
        p for p in REPO.rglob("*")
        if p.is_file()
        and p.suffix.lower() in SUFFIXES
        and not any(part in SKIP_DIRS for part in p.parts)
    ]


def test_no_legacy_regime_snapshot_path() -> None:
    """The old path appears nowhere outside the two exemptions."""
    hits = []
    for p in candidate_files():
        rel = p.relative_to(REPO).as_posix()
        # This file DEFINES the forbidden string, so it necessarily contains it.
        # Same precedent as tests/test_no_secrets.py, which skips itself for
        # holding the credential patterns. Excluding the definition is not
        # widening an exemption over content.
        if p.name == Path(__file__).name:
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        if is_a_record(rel, text):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if FORBIDDEN in line:
                hits.append(f"{rel}:{i}  {line.strip()[:70]}")
    assert not hits, (
        f"the legacy path {FORBIDDEN!r} still appears:\n  " + "\n  ".join(hits)
        + f"\n\nThe canonical path is {CANONICAL!r}. There is ONE path -- do not add a "
          "symlink\nor alias for compatibility.\n\n"
          "DO NOT ADD A PREFIX TO AN EXEMPTION LIST. The exemption is DERIVED: a .md "
          "file\nis exempt when it declares one of the five handoff states in its first "
          f"{HEADER_LINES}\nlines, or when EVIDENCE-CARRY.md records it. If this file is "
          "genuinely a record\nof a past state, give it a state header; if it is not, the "
          "path is live and\nwrong."
    )


# ---- the three guards, on the Resolution D pattern -------------------------
#
# An exemption with no guard is a hole. These fail if the derivation ever starts
# covering a live pointer, which is the only way it could do damage.


def exempted_paths() -> list[str]:
    out = []
    for p in candidate_files():
        rel = p.relative_to(REPO).as_posix()
        if p.name == Path(__file__).name:
            continue
        if is_a_record(rel, p.read_text(encoding="utf-8", errors="ignore")):
            out.append(rel)
    return out


def test_guard_1_the_exemption_reaches_prose_and_nothing_else() -> None:
    """**A live pointer lives in code or config, never in prose.**

    This is the guard that makes the derivation safe. A bare date-header rule
    would have exempted `SPEC.md`, `.yaml` config and `.py` modules -- every
    place the path could actually be live -- which is why that candidate was
    rejected rather than merely disliked.
    """
    wrong = [r for r in exempted_paths() if not r.lower().endswith(PROSE_SUFFIX)]
    assert not wrong, (
        f"the exemption reached non-prose files: {wrong}. A live pointer lives "
        "in code or config; if one of those is exempt, the test is no longer "
        "checking the thing it exists to check.")


def test_guard_2_a_file_with_neither_property_is_never_exempt(tmp_path: Path) -> None:
    """Derived, not listed -- proven by construction.

    Three fixtures: no header at all, a header whose value is outside the five,
    and a state word in body prose rather than the header region. **None may be
    exempt.** The third is the positional rule: a document that merely discusses
    handoff states must not be able to exempt itself by mentioning one.
    """
    assert not is_a_record("x/none.md", "# t\n\nno header at all\n")
    assert not is_a_record("x/current.md", "**Status** CURRENT\n\n# t\n"), (
        "CURRENT was accepted as a handoff state. It is not one, and accepting "
        "it would exempt every live spec in docs/specs/.")
    assert not is_a_record("x/open.md", "**Status** OPEN\n\n# t\n")
    body = "# t\n" + "\n" * HEADER_LINES + "**Status** DONE\n"
    assert not is_a_record("x/late.md", body), (
        "a state declared below the header region was accepted -- the rule must "
        "stay positional, or any document exempts itself by discussing states.")
    # And the positive case, so the guard cannot pass by exempting nothing.
    assert is_a_record("x/real.md", "**Status** REVIEWED · **Date** 2026-08-11\n\n# t\n")


def test_guard_3_the_live_specs_are_never_exempt() -> None:
    """The three documents that actually named a `claude/`-rooted directory
    before H8. If a re-supply reintroduces the legacy path into any of them,
    this test must still fail -- so none of them may ever be a record."""
    for name in ("SPEC.md", "BUILD-PLAN.md", "REGIME-PROMPT.md"):
        p = REPO / "docs" / "specs" / name
        if not p.exists():
            continue
        rel = p.relative_to(REPO).as_posix()
        assert not is_a_record(rel, p.read_text(encoding="utf-8", errors="ignore")), (
            f"{rel} is exempt from the legacy-path check. It is a live spec, and "
            "it is one of the three that carried the wrong path before H8.")


def test_the_derivation_actually_exempts_the_case_it_was_built_for() -> None:
    """`christoph/done/006` is why part 3 exists. If it is not exempt, the
    derivation did not do its job; if `christoph/` were hardcoded, this would
    pass for the wrong reason -- so guard 2 pins that it is derived."""
    p = REPO / "christoph" / "done" / "006-h8-snapshot-path-fills.md"
    if not p.exists():
        return
    rel = p.relative_to(REPO).as_posix()
    assert is_a_record(rel, p.read_text(encoding="utf-8", errors="ignore"))
    # Checked against the DECIDING FUNCTION and the named list, not the whole
    # file -- an earlier version searched the module and failed on its own
    # explanation. Positional, same as every other rule in this suite.
    import inspect
    tree_name = "chr" + "istoph"
    assert tree_name not in inspect.getsource(is_a_record), (
        f"{tree_name}/ was hardcoded into the deciding function. The whole point "
        "of part 3 is that the next tree must not need an edit here.")
    assert not any(tree_name in e for e in EXEMPT_NAMED), (
        f"{tree_name}/ was added to the named list instead of being derived.")


def test_snapshot_directory_exists() -> None:
    d = REPO / CANONICAL
    assert d.exists() and d.is_dir(), (
        f"{CANONICAL} does not exist. The scheduled task writes here, and a missing "
        "directory\nis indistinguishable from a task that never ran."
    )


def test_snapshots_are_not_gitignored() -> None:
    """An untracked record is not a record. `SPEC.md` §5.5a's join to the trade
    log on `session_date` only works if the snapshots are in history."""
    import subprocess
    probe = CANONICAL + "2026-01-01.md"
    r = subprocess.run(["git", "check-ignore", "-v", probe],
                       cwd=REPO, capture_output=True, text=True)
    assert r.returncode != 0, (
        f"{probe} is gitignored by: {r.stdout.strip()}\n"
        "The .md and .yaml snapshots must be tracked -- they are the record that makes the "
        "§5.5a join possible."
    )
