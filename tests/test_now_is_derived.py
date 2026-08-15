"""045 Part 3 — `NOW.md` is derived from the tree, never stored.

**The claim the file makes about itself, asserted.** A status board that can be
hand-edited is worse than none: it reads exactly like a correct one and is wrong
within the hour, because three sessions write to this tree and each sees a
snapshot.

**None of these tests is time-based.** 045 is explicit, and the reason is in this
repo's history: *a test that goes red because nothing ran on a Sunday gets
ignored — there were eight of those a week ago.*
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tools.now import CycleError, compute, find_cycle, main, render


def tree(tmp_path: Path, *, inbox: dict[str, str] | None = None,
         done: tuple[str, ...] = (), c_open: tuple[str, ...] = (),
         c_done: tuple[str, ...] = ()) -> Path:
    """A miniature repo. **Built rather than mocked** — the derivation reads
    directories, so directories are what it must be tested against."""
    for sub in ("handoff/inbox", "handoff/done", "christoph/open", "christoph/done"):
        (tmp_path / sub).mkdir(parents=True, exist_ok=True)
    for name, front in (inbox or {}).items():
        (tmp_path / "handoff/inbox" / f"{name}.md").write_text(front, encoding="utf-8")
    for name in done:
        (tmp_path / "handoff/done" / f"{name}.md").write_text("done", encoding="utf-8")
    for name in c_open:
        (tmp_path / "christoph/open" / f"{name}.md").write_text("open", encoding="utf-8")
    for name in c_done:
        (tmp_path / "christoph/done" / f"{name}.md").write_text("done", encoding="utf-8")
    return tmp_path


def front(**fields: str) -> str:
    body = "\n".join(f"{k}: {v}" for k, v in fields.items())
    return f"---\n{body}\n---\n\nbody\n"


# ---- derived, not stored --------------------------------------------------


def test_two_runs_over_an_unchanged_tree_are_identical(tmp_path: Path) -> None:
    """**045's own test.** Regenerate twice and assert the output is identical.

    This is what forbids a timestamp in the file. A `generated at` line would
    make every run differ — and would make the board *look* fresh while the tree
    behind it was stale, which is the class of defect 045 exists to close.
    """
    repo = tree(tmp_path, inbox={"045-a": front(id="045"), "046-b": front(id="046")},
                done=("045-a",))
    first = render(compute(repo))
    second = render(compute(repo))
    assert first == second


def test_changing_the_tree_moves_the_output(tmp_path: Path) -> None:
    """**The other half, and without it the test above passes on a constant.**

    045 asks for both: *regenerate twice and assert identical, then change one
    thing and assert it moved.* A renderer that returned the same string forever
    would satisfy the first alone.
    """
    repo = tree(tmp_path, inbox={"046-b": front(id="046")})
    before = render(compute(repo))
    (repo / "handoff/done/046-b.md").write_text("done", encoding="utf-8")
    after = render(compute(repo))

    assert before != after
    assert "046" in compute(repo)["done"]          # type: ignore[operator]
    assert "046" not in compute(repo)["ready"]     # type: ignore[operator]


def test_a_hand_edit_does_not_survive(tmp_path: Path) -> None:
    """**The consequence, stated in the module docstring and asserted here.**

    Somebody will edit it — it looks like a document. The next run overwrites it,
    and that must be true rather than merely intended.

    **This goes through `main()`, not `render()`, and the difference was found by
    mutation.** The first cut called `render(compute(repo))` and wrote the result
    itself — asserting only that the *renderer* does not emit "HAND EDIT", never
    reaching the code that decides whether to write at all. Disabling the write
    with `if not out.exists()` — **the exact shape of a file that survives a hand
    edit** — left it green. A test that cannot see the defect it is named after
    is worse than none, because the name says the defect is covered.
    """
    repo = tree(tmp_path, inbox={"046-b": front(id="046")})
    now_file = repo / "claude" / "NOW.md"

    assert main([str(repo)]) == 0
    generated = now_file.read_text(encoding="utf-8")

    now_file.write_text(generated + "\n\nHAND EDIT: 046 is actually finished\n",
                        encoding="utf-8")
    assert "HAND EDIT" in now_file.read_text(encoding="utf-8")

    assert main([str(repo)]) == 0
    assert "HAND EDIT" not in now_file.read_text(encoding="utf-8"), (
        "a hand edit survived a run. NOW.md is derived and nothing in it is "
        "stored — a file that keeps an edit is a status board that can be made "
        "to lie while still looking generated.")
    assert now_file.read_text(encoding="utf-8") == generated


# ---- the categories -------------------------------------------------------


def test_ready_blocked_and_on_christoph(tmp_path: Path) -> None:
    repo = tree(
        tmp_path,
        inbox={"045-a": front(id="045"),
               "044-b": front(id="044", depends="045"),
               "047-c": front(id="047", depends="046")},
        done=(),
        c_open=("c018-x", "c023-y"),
        c_done=("c018-x",),
    )
    state = compute(repo)
    assert state["ready"] == ["045"]
    assert ("044", ["045"]) in state["blocked"]     # type: ignore[operator]
    assert ("047", ["046"]) in state["blocked"]     # type: ignore[operator]


def test_a_task_with_no_depends_is_ready(tmp_path: Path) -> None:
    """**Absence means nothing, not unknown.** 045 forbids retro-fitting
    `depends:` into files already in the tree, so the overwhelming majority of
    task files will never have one — and every one of them must read as ready
    rather than as blocked on something unnameable."""
    repo = tree(tmp_path, inbox={"006-old": "no frontmatter at all\n"})
    assert compute(repo)["ready"] == ["006"]


def test_a_superseded_task_is_not_ready(tmp_path: Path) -> None:
    """**Not in 045's list, and added because leaving it out is harmful.**

    `035` and `036` are superseded by `038` and would otherwise render as
    **ready now** — an invitation to run them. A session did exactly that on
    2026-08-15, found two files numbered `035` saying opposite things about
    `PDL`, and stopped only because the ambiguity happened to be visible. A board
    saying `ready` is a stronger signal than that ambiguity was.

    **Derived from `supersedes:`, which is already in the frontmatter.**
    """
    repo = tree(tmp_path, inbox={"035-old": front(id="035"),
                                 "038-new": front(id="038", supersedes="035")})
    state = compute(repo)
    assert state["ready"] == ["038"]
    assert ("035", "038") in state["superseded"]    # type: ignore[operator]


def test_a_dependency_met_by_supersession_is_met(tmp_path: Path) -> None:
    """`035a` waits on `035`, and `035` will never be done — `038` replaced it.
    Without this it renders as blocked forever, which is the same useless-but-
    true status a cycle produces."""
    repo = tree(tmp_path, inbox={"035-old": front(id="035"),
                                 "035a-b": front(id="035a", depends="035"),
                                 "038-new": front(id="038", supersedes="035")})
    assert "035a" in compute(repo)["ready"]         # type: ignore[operator]


# ---- cycles ---------------------------------------------------------------


def test_a_two_task_cycle_is_refused_and_named(tmp_path: Path) -> None:
    """**045's fourth test.** Two tasks depending on each other must not render
    as `blocked` forever with no explanation."""
    repo = tree(tmp_path, inbox={"050-a": front(id="050", depends="051"),
                                 "051-b": front(id="051", depends="050")})
    with pytest.raises(CycleError) as excinfo:
        compute(repo)
    message = str(excinfo.value)
    assert "050" in message and "051" in message, message
    assert "->" in message, message


def test_a_longer_cycle_is_also_found(tmp_path: Path) -> None:
    repo = tree(tmp_path, inbox={"050-a": front(id="050", depends="051"),
                                 "051-b": front(id="051", depends="052"),
                                 "052-c": front(id="052", depends="050")})
    with pytest.raises(CycleError):
        compute(repo)


def test_a_self_dependency_is_a_cycle(tmp_path: Path) -> None:
    repo = tree(tmp_path, inbox={"050-a": front(id="050", depends="050")})
    with pytest.raises(CycleError):
        compute(repo)


def test_a_long_chain_is_not_a_cycle(tmp_path: Path) -> None:
    """**The guard must not cry wolf on depth.** A recursive walk would raise
    `RecursionError` on a long chain and report the wrong finding entirely,
    which is why `find_cycle` is iterative."""
    inbox = {f"{100 + i:03d}-x": front(id=f"{100 + i:03d}", depends=f"{101 + i:03d}")
             for i in range(400)}
    inbox["500-end"] = front(id="500")
    repo = tree(tmp_path, inbox=inbox)
    assert find_cycle({t: d for t, d in
                       ((k.split("-")[0], [v.split("depends: ")[1].split("\n")[0]]
                         if "depends:" in v else [])
                        for k, v in inbox.items())}) is None
    compute(repo)          # must not raise
