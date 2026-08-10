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
"""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

CANONICAL = "docs/regime-snapshots/"
FORBIDDEN = "claude/regime-snapshots/"

SUFFIXES = (".md", ".py", ".yaml", ".yml", ".ps1", ".json")
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "venv", "node_modules"}

#: Two exemptions, both deliberate, both narrow.
#:
#: DRIVE-ARCHIVE-LIST.md records the five competing naming conventions as
#: history -- it must keep saying what they were, or the audit stops being an
#: audit. handoff/ is the same: task files and done-notes record what the
#: convention was at the time they were written, and rewriting them would be
#: falsifying the record this project keeps.
EXEMPT_PREFIXES = ("docs/specs/DRIVE-ARCHIVE-LIST.md", "handoff/")


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
        if rel.startswith(EXEMPT_PREFIXES):
            continue
        # This file DEFINES the forbidden string, so it necessarily contains it.
        # Same precedent as tests/test_no_secrets.py, which skips itself for
        # holding the credential patterns. Excluding the definition is not
        # widening an exemption over content.
        if p.name == Path(__file__).name:
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if FORBIDDEN in line:
                hits.append(f"{rel}:{i}  {line.strip()[:70]}")
    assert not hits, (
        f"the legacy path {FORBIDDEN!r} still appears:\n  " + "\n  ".join(hits)
        + f"\n\nThe canonical path is {CANONICAL!r}. There is ONE path -- do not add a "
          f"symlink\nor alias for compatibility, and do not widen the exemption list; it "
          "covers only\nthe archive audit and handoff/, both of which record history "
          "deliberately."
    )


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
