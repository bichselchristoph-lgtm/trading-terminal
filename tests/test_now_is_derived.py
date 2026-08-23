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
    assert "h046" in compute(repo)["done"]          # type: ignore[operator]
    assert "h046" not in compute(repo)["ready"]     # type: ignore[operator]


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
        # **`018`/`023`, not `c018`/`c023`.** `christoph/open/` filenames carry
        # no letter prefix -- `023-for-christoph-task-something.md` -- the `c`
        # is `NOW.md`'s own rendering tag, applied at compute() time, never
        # part of the id on disk. A `c`-prefixed fixture name does not match
        # `_ID` at all, so `on_christoph` was silently empty here before this
        # was noticed -- found while adding the assertion below, not assumed.
        c_open=("018-x", "023-y"),
        c_done=("018-x",),
    )
    state = compute(repo)
    assert state["ready"] == ["h045"]
    assert ("h044", ["h045"]) in state["blocked"]     # type: ignore[operator]
    assert ("h047", ["h046"]) in state["blocked"]     # type: ignore[operator]
    # 069 Part B. christoph-space ids are tagged `c`, never `h` -- checked
    # here because this is the one fixture in the file that builds a
    # christoph/open/ folder at all.
    assert state["on_christoph"] == ["c023"]           # type: ignore[operator]


def test_the_same_bare_id_in_both_spaces_is_not_confused(tmp_path: Path) -> None:
    """**069. Measured, not hypothetical**: `handoff/inbox/033-for-code-...`
    and `christoph/open/033-for-christoph-task-...` both exist in the real
    tree at once. A tag derived by looking `033` up in whichever dict is
    checked first would call the real `c033` an `h033` -- this is the exact
    collision `NOW.md` used to render as one indistinguishable `033` on two
    lines."""
    repo = tree(tmp_path, inbox={"033-h": front(id="033")},
               c_open=("033-c",))
    state = compute(repo)
    assert state["ready"] == ["h033"]
    assert state["on_christoph"] == ["c033"]


def test_a_task_with_no_depends_is_ready(tmp_path: Path) -> None:
    """**Absence means nothing, not unknown.** 045 forbids retro-fitting
    `depends:` into files already in the tree, so the overwhelming majority of
    task files will never have one — and every one of them must read as ready
    rather than as blocked on something unnameable."""
    repo = tree(tmp_path, inbox={"006-old": "no frontmatter at all\n"})
    assert compute(repo)["ready"] == ["h006"]


def test_a_task_with_depends_none_is_ready(tmp_path: Path) -> None:
    """**056 Part B.** The literal string `"none"` written as a VALUE is not
    the same case as an ABSENT key, and `depends_on()` treated only the second
    correctly. `"depends: none"` parsed to `raw="none"` — non-empty, so it
    became a phantom dependency on a task literally named `"none"` that can
    never appear in `done` or `superseded`.

    **This is the project's own established convention, not a hypothetical
    edge case**: `049`, `051`, `052`, `053` and `054` all write `depends:
    none`, and `049`/`051` rendered `blocked — needs none` in `NOW.md` while
    genuinely ready — found by `055`, the two tasks named next after it.
    """
    repo = tree(tmp_path, inbox={"049-x": front(id="049", depends="none")})
    assert compute(repo)["ready"] == ["h049"]


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
    assert state["ready"] == ["h038"]
    assert ("h035", "h038") in state["superseded"]    # type: ignore[operator]


def test_a_dependency_met_by_supersession_is_met(tmp_path: Path) -> None:
    """`035a` waits on `035`, and `035` will never be done — `038` replaced it.
    Without this it renders as blocked forever, which is the same useless-but-
    true status a cycle produces."""
    repo = tree(tmp_path, inbox={"035-old": front(id="035"),
                                 "035a-b": front(id="035a", depends="035"),
                                 "038-new": front(id="038", supersedes="035")})
    assert "h035a" in compute(repo)["ready"]         # type: ignore[operator]


# ---- 069 Part C: the four numbers, not a ratio -----------------------------


def test_admin_naming_a_product_task_is_counted_the_others_are_not(tmp_path: Path) -> None:
    """**The second number, rule 16's whole point.** `unblocks: NOTHING`, a
    missing `unblocks:` line, and `unblocks:` naming another admin task all
    count toward `admin` but not toward `admin_naming_product` -- only an
    admin task naming a task file whose OWN `class:` is `product` (or `spec`)
    does."""
    repo = tree(tmp_path, inbox={
        "060-a": front(id="060", **{"class": "admin"}, unblocks="061"),
        "061-b": front(id="061", **{"class": "product"}),
        "062-c": front(id="062", **{"class": "admin"}, unblocks="NOTHING"),
        "063-d": front(id="063", **{"class": "admin"}),
        "064-e": front(id="064", **{"class": "admin"}, unblocks="060"),
        "065-f": front(id="065", **{"class": "product"}, unblocks="NOTHING"),
    })
    state = compute(repo)
    assert state["admin"] == 4
    assert state["admin_naming_product"] == 1, (
        "only 060 (unblocking 061, class product) should count; 062 unblocks "
        "NOTHING, 063 has no unblocks: at all, and 064 unblocks 060, an admin "
        "task")


def test_an_unblocks_line_that_is_prose_is_still_read_for_ids(tmp_path: Path) -> None:
    """`054`'s real `unblocks:` reads *"049, 050 and 051 -- all three are held
    only by..."* -- prose, not a clean id list, and the FIRST id in it is not
    always the one that matters. Every id-shaped token in the raw text is a
    candidate."""
    repo = tree(tmp_path, inbox={
        "070-a": front(id="070", **{"class": "admin"},
                       unblocks="an admin cleanup with no product effect, see 071"),
        "071-b": front(id="071", **{"class": "admin"}),
        "072-c": front(id="072", **{"class": "admin"},
                       unblocks="071 and, more importantly, 073"),
        "073-d": front(id="073", **{"class": "product"}),
    })
    state = compute(repo)
    assert state["admin_naming_product"] == 1, (
        "070 names only an admin task (071) and must not count; 072 names "
        "071 (admin) AND 073 (product) and must count on the strength of the "
        "second id, not fail on the first")


def _git_commit(repo: Path, rel_path: str, content: str, when: str) -> None:
    import os
    import subprocess
    p = repo / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    subprocess.run(["git", "add", rel_path], cwd=repo, check=True, capture_output=True)
    env = {**os.environ, "GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when}
    subprocess.run(["git", "commit", "-q", "-m", "x"], cwd=repo, check=True,
                   capture_output=True, env=env)


def test_days_since_last_product_task_prefers_the_newest_and_ignores_admin(
    tmp_path: Path,
) -> None:
    """**Not time-based in the sense this file's own docstring forbids** --
    no exact day count is asserted, which would go red on whichever day this
    happens to run. Only the RELATION is: a more recent product-class note
    shortens the count, an admin-class note (however recently committed) is
    ignored entirely, and a repo with no product-class note at all reports
    why, not a number."""
    import subprocess
    repo = tree(tmp_path, inbox={})
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)

    # No product-class note yet: derivation refuses with a reason, not 0.
    assert compute(repo)["days_since_product"] is None
    assert "no handoff/done/ note" in compute(repo)["days_since_product_reason"]

    _git_commit(repo, "handoff/done/040-old-admin.md",
               front(id="040", **{"class": "admin"}), "2020-01-01T00:00:00+00:00")
    _git_commit(repo, "handoff/done/041-old-product.md",
               front(id="041", **{"class": "product"}), "2020-01-01T00:00:00+00:00")

    old_only = compute(repo)["days_since_product"]
    assert old_only is not None and old_only > 1000, (
        "a 2020 commit must report well over a thousand days, whatever day "
        "this test happens to run")

    _git_commit(repo, "handoff/done/042-recent-admin.md",
               front(id="042", **{"class": "admin"}), "2026-01-01T00:00:00+00:00")
    still_old = compute(repo)["days_since_product"]
    assert still_old == old_only, (
        "042 is class: admin and recently committed -- it must not move the "
        "count at all")

    _git_commit(repo, "handoff/done/043-recent-product.md",
               front(id="043", **{"class": "product"}), "2026-01-01T00:00:00+00:00")
    with_recent = compute(repo)["days_since_product"]
    assert with_recent is not None and with_recent < old_only, (
        "043 is a more recent product-class note and must shorten the count")


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
