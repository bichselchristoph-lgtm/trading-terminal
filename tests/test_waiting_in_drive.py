"""045 Part 5 — `waiting in Drive`, exercised rather than inspected.

**045 is explicit about why this is behavioural**: *a static check would pass
forever against a `verify.ps1` that had stopped counting, which is this defect
exactly.* So every test here builds a real source folder, a real destination,
and runs the counter over them.

**The defect it measures.** On 2026-08-15 four UAT files sat in
`momentum-christoph-open` while `christoph/open/` held one `.gitkeep`. The
inbound sync's *last success* was recent and truthful — it had run, over a pair
with nothing waiting at the time — and said nothing at all about the four files.
**An age cannot report a backlog.**
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tools.waiting import NAME_CAP, survey, waiting_for

TOOL = REPO / "tools" / "waiting.py"


def pair(src: Path, dst: Path, pair_id: str = "p") -> dict:
    return {"id": pair_id, "from": str(src), "to": str(dst), "glob": "*.md"}


def config(tmp_path: Path, *pairs: dict) -> Path:
    import yaml
    p = tmp_path / "sync.yaml"
    p.write_text(yaml.safe_dump({"pairs": list(pairs)}), encoding="utf-8")
    return p


def test_a_file_in_the_source_and_not_the_destination_is_counted(tmp_path: Path) -> None:
    src, dst = tmp_path / "drive", tmp_path / "tree"
    src.mkdir(); dst.mkdir()
    (src / "018-for-christoph-task.md").write_text("x", encoding="utf-8")

    w = waiting_for(pair(src, dst))
    assert w.count == 1
    assert w.names == ("018-for-christoph-task.md",)
    assert w.unreachable is None
    assert "018-for-christoph-task.md" in w.render()


def test_the_count_goes_to_zero_when_the_file_lands(tmp_path: Path) -> None:
    """**It goes to zero exactly when the problem is gone.** That is the whole
    argument for counting rather than timing."""
    src, dst = tmp_path / "drive", tmp_path / "tree"
    src.mkdir(); dst.mkdir()
    (src / "018-a.md").write_text("x", encoding="utf-8")
    assert waiting_for(pair(src, dst)).count == 1

    (dst / "018-a.md").write_text("x", encoding="utf-8")
    assert waiting_for(pair(src, dst)).count == 0


def test_an_unreachable_source_is_its_own_outcome_and_never_reads_as_zero(
        tmp_path: Path) -> None:
    """**045's refusal test.** *An unreachable source is its own line and must
    never read as `0 waiting`.*

    They are opposite facts: `0` says the pipe is clear, unreachable says the
    pipe is gone. Collapsing them would make a disconnected Drive the most
    reassuring reading on the panel.
    """
    dst = tmp_path / "tree"
    dst.mkdir()
    w = waiting_for(pair(tmp_path / "not-there", dst))

    assert w.unreachable is not None
    assert "UNREACHABLE" in w.render()
    assert w.render() != "p  0 — "
    assert "0 —" not in w.render()


def test_the_program_exits_non_zero_only_for_an_unreachable_source(
        tmp_path: Path) -> None:
    """**Run as a program**, because that is how `verify.ps1` reaches it."""
    src, dst = tmp_path / "drive", tmp_path / "tree"
    src.mkdir(); dst.mkdir()
    (src / "018-a.md").write_text("x", encoding="utf-8")

    ok = subprocess.run([sys.executable, str(TOOL), str(config(tmp_path, pair(src, dst)))],
                        capture_output=True, text=True)
    assert ok.returncode == 0, ok.stderr
    assert "waiting in Drive  1" in ok.stdout, ok.stdout

    gone = subprocess.run(
        [sys.executable, str(TOOL),
         str(config(tmp_path, pair(tmp_path / "not-there", dst, "q")))],
        capture_output=True, text=True)
    assert gone.returncode != 0, gone.stdout
    assert "UNREACHABLE" in gone.stdout


def test_the_list_is_capped_and_says_how_many_it_dropped(tmp_path: Path) -> None:
    """**A silent truncation reads as `that is all of them`.** The tail is named
    as a count rather than left off."""
    src, dst = tmp_path / "drive", tmp_path / "tree"
    src.mkdir(); dst.mkdir()
    for i in range(NAME_CAP + 3):
        (src / f"{100 + i:03d}-x.md").write_text("x", encoding="utf-8")

    rendered = waiting_for(pair(src, dst)).render()
    assert f"and {3} more" in rendered, rendered
    assert rendered.count(".md") == NAME_CAP


def test_verify_ps1_actually_invokes_the_counter() -> None:
    """**The half a behavioural test cannot cover.**

    Every test above proves the counter works. **None of them proves
    `verify.ps1` still calls it** — and a `verify.ps1` that quietly stopped
    invoking it would leave all of them green while the panel reported nothing,
    which is precisely 045's complaint about static checks, inverted.
    """
    script = (REPO / "verify.ps1").read_text(encoding="utf-8")
    code = "\n".join(l for l in script.splitlines() if not l.lstrip().startswith("#"))
    assert "waiting.py" in code, (
        "verify.ps1 no longer invokes tools/waiting.py, so the `waiting in "
        "Drive` line cannot be printed however well the counter works.")


def test_the_shipped_config_surveys_every_configured_pair() -> None:
    """Against the real `config/sync.yaml`. **Asserts shape, never a count** —
    a live count is a moving target and a test that pinned it would go red every
    time Drive received a file, which is the time-based failure 045 forbids."""
    rows = survey()
    assert {r.pair_id for r in rows} == {"regime_snapshots", "handoff_inbox",
                                         "christoph_open"}
    for row in rows:
        assert row.count >= 0
        assert row.render()
