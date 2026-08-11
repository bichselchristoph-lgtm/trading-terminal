"""The `--supersede` path, tested by something other than the task that wanted it.

H10 added `--as` and `--supersede` after refusal 3 blocked a legitimate version
replacement. H10's own instruction was to **stop and say so** if no supersession
path existed; that instruction was not followed. The reason it existed is that
the session needing an exemption is not the one that should grant it.

H11's review asked four questions. Three had no test and two were **defects**:

  Q1  Could --supersede land at a path with no existing adoption?   WAS YES -- fixed
  Q2  Did it verify the superseded row exists and is not already
      superseded?                                                    WAS NO  -- fixed
  Q3  Could the order be reconstructed from ADOPTION-LOG?            WAS NO  -- fixed
  Q4  Do refusals 1, 2 and 4 still fire under --supersede?           YES     -- always did

These tests exercise the gate against a temporary repo, so they never touch the
real ADOPTION-LOG.md or D:\\Dev\\_adopt\\.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
ADOPT_PY = REPO / "tools" / "adopt.py"

LOG_HEADER = (
    "# ADOPTION-LOG\n\n"
    "| date | path in new tree | source path | origin | reason | test that covers it | adopted by |\n"
    "|---|---|---|---|---|---|---|\n"
)

COMPANION = """# Provenance

source: {source}
origin: {origin}
reason: {reason}
depends: something real depends on it
{extra}
"""


def load_gate(tmp_path: Path):
    """Import adopt.py with REPO and ADOPT_DIR pointed at a scratch tree."""
    name = f"adopt_{tmp_path.name}"
    spec = importlib.util.spec_from_file_location(name, ADOPT_PY)
    mod = importlib.util.module_from_spec(spec)
    # Registering BEFORE exec_module is load-bearing: @dataclass resolves field
    # types via sys.modules[cls.__module__], which is None for a module that was
    # created but never registered, and the decorator raises on it.
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    mod.REPO = tmp_path / "repo"
    mod.ADOPT_DIR = tmp_path / "_adopt"
    mod.LOG = mod.REPO / "ADOPTION-LOG.md"
    mod.REPO.mkdir(parents=True, exist_ok=True)
    mod.ADOPT_DIR.mkdir(parents=True, exist_ok=True)
    (mod.REPO / "docs").mkdir(exist_ok=True)
    mod.LOG.write_text(LOG_HEADER, encoding="utf-8")
    return mod


def drop(mod, name: str, body: str, *, origin="authored", reason="a real reason", extra=""):
    (mod.ADOPT_DIR / name).write_text(body, encoding="utf-8")
    (mod.ADOPT_DIR / f"{name}.provenance.md").write_text(
        COMPANION.format(source="somewhere real", origin=origin, reason=reason, extra=extra),
        encoding="utf-8")


def test_q1_supersede_refuses_when_there_is_nothing_to_supersede(tmp_path: Path) -> None:
    """**Q1, and it was a real hole.** The early `if not target.exists(): return`
    fired before the supersede branch, so the flag silently became a create and
    the `supersedes:` line was never validated."""
    mod = load_gate(tmp_path)
    drop(mod, "thing.md", "new content", extra="supersedes: docs/thing.md")
    with pytest.raises(mod.Refusal) as e:
        mod.run_checks("thing.md", mod.REPO / "docs", supersede=True)
    assert e.value.number == 3
    assert "nothing to supersede" in str(e.value)


def test_q1_first_adoption_still_works_without_the_flag(tmp_path: Path) -> None:
    """The fix must not break the ordinary create it sits in front of."""
    mod = load_gate(tmp_path)
    drop(mod, "thing.md", "new content")
    prov, _, _ = mod.run_checks("thing.md", mod.REPO / "docs")
    assert prov.origin == "authored"


def test_q2_refuses_when_no_log_row_exists(tmp_path: Path) -> None:
    """**Q2.** The file is in the tree but was never logged. Marking a row that
    is not there used to write the log back unchanged and say nothing."""
    mod = load_gate(tmp_path)
    (mod.REPO / "docs" / "thing.md").write_text("old content", encoding="utf-8")
    with pytest.raises(mod.Refusal) as e:
        mod.mark_superseded("docs/thing.md", "thing.md")
    assert "no ADOPTION-LOG row" in str(e.value)


def test_q2_refuses_when_the_row_is_already_superseded(tmp_path: Path) -> None:
    """A chain with a gap in it is unreadable, and the gap is invisible exactly
    because nothing complained when it opened."""
    mod = load_gate(tmp_path)
    mod.LOG.write_text(
        LOG_HEADER + "| 2026-08-10 | `docs/thing.md` | `x` | authored | r | `n/a` | "
                     "someone — **SUPERSEDED** 2026-08-10 by the row above |\n",
        encoding="utf-8")
    with pytest.raises(mod.Refusal) as e:
        mod.mark_superseded("docs/thing.md", "thing.md")
    assert "already marked SUPERSEDED" in str(e.value)


def test_q3_the_two_rows_point_at_each_other(tmp_path: Path) -> None:
    """**Q3.** Same path, same date, and only insertion order to tell them apart
    is not a reconstructable sequence once a third version lands."""
    mod = load_gate(tmp_path)
    mod.LOG.write_text(
        LOG_HEADER + "| 2026-08-10 | `docs/thing.md` | `x` | authored | v1 | `n/a` | someone |\n",
        encoding="utf-8")
    (mod.REPO / "docs" / "thing.md").write_text("old content", encoding="utf-8")
    drop(mod, "thing-v2.md", "new content", reason="v2 of the thing",
         extra="supersedes: docs/thing.md")

    prov, tests, _ = mod.run_checks("thing-v2.md", mod.REPO / "docs", "thing.md", supersede=True)
    mod.mark_superseded(prov.supersedes, "thing.md")
    mod.append_log_row("thing-v2.md", mod.REPO / "docs", prov, tests, "someone", "thing.md")

    log = mod.LOG.read_text(encoding="utf-8")
    assert "**SUPERSEDES `docs/thing.md` (the marked row below).**" in log, (
        "the new row does not reference the row it replaces")
    assert "**SUPERSEDED** " in log and "by the row above" in log, (
        "the old row does not reference the row that replaced it")


def test_q4_refusal_1_still_fires_under_supersede(tmp_path: Path) -> None:
    """**Q4.** The flag must not shortcut the other three refusals."""
    mod = load_gate(tmp_path)
    (mod.ADOPT_DIR / "thing.md").write_text("new", encoding="utf-8")   # no companion
    with pytest.raises(mod.Refusal) as e:
        mod.run_checks("thing.md", mod.REPO / "docs", supersede=True)
    assert e.value.number == 1


def test_q4_refusal_4_still_fires_under_supersede(tmp_path: Path) -> None:
    mod = load_gate(tmp_path)
    mod.LOG.write_text(
        LOG_HEADER + "| 2026-08-10 | `docs/thing.md` | `x` | imported | v1 | `n/a` | someone |\n",
        encoding="utf-8")
    (mod.REPO / "docs" / "thing.md").write_text("old", encoding="utf-8")
    drop(mod, "thing-v2.md", "new", origin="imported", extra="supersedes: docs/thing.md")
    with pytest.raises(mod.Refusal) as e:
        mod.run_checks("thing-v2.md", mod.REPO / "docs", "thing.md", supersede=True)
    assert e.value.number == 4, "refusal 4 must still demand a decision for an imported origin"


def test_supersede_still_refuses_without_a_supersedes_line(tmp_path: Path) -> None:
    mod = load_gate(tmp_path)
    (mod.REPO / "docs" / "thing.md").write_text("old", encoding="utf-8")
    drop(mod, "thing-v2.md", "new")                       # no supersedes:
    with pytest.raises(mod.Refusal) as e:
        mod.run_checks("thing-v2.md", mod.REPO / "docs", "thing.md", supersede=True)
    assert "no `supersedes:` line" in str(e.value)


def test_supersede_refuses_when_the_companion_names_a_different_path(tmp_path: Path) -> None:
    mod = load_gate(tmp_path)
    (mod.REPO / "docs" / "thing.md").write_text("old", encoding="utf-8")
    drop(mod, "thing-v2.md", "new", extra="supersedes: docs/something-else.md")
    with pytest.raises(mod.Refusal) as e:
        mod.run_checks("thing-v2.md", mod.REPO / "docs", "thing.md", supersede=True)
    assert "but this adoption targets" in str(e.value)


def test_a_collision_without_the_flag_still_refuses(tmp_path: Path) -> None:
    """The base behaviour the flag sits in front of. If this ever passes, the
    supersession path has become a hole rather than a door."""
    mod = load_gate(tmp_path)
    (mod.REPO / "docs" / "thing.md").write_text("old", encoding="utf-8")
    drop(mod, "thing-v2.md", "new", extra="supersedes: docs/thing.md")
    with pytest.raises(mod.Refusal) as e:
        mod.run_checks("thing-v2.md", mod.REPO / "docs", "thing.md")
    assert e.value.number == 3
    assert "Do NOT delete the existing file" in str(e.value)
