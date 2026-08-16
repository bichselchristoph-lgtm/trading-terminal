"""Every task file declares its state, so the repo is never the ambiguous party.

`docs/specs/HANDOFF-PROTOCOL.md` governs a conversation between Christoph and
the design session, and **no test in this repo can enforce a conversation.**
Christoph holds the state; neither Claude can observe it. What a test *can*
enforce is that the file says which state it is in.

That is the whole claim, and the protocol document makes it in those terms:
*"The untested half remains untested, and this document says so plainly."*

This mirrors `test_every_spec_declares_status` and exists for the same reason —
a convention that fails a test does not depend on anyone remembering it. Note
the two conventions differ on purpose: `docs/specs/` uses `**STATUS**` for a
document's lifecycle, task files use `**Status**` for a handoff state. They are
different questions about different things.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TASK_DIRS = (REPO / "handoff" / "inbox", REPO / "handoff" / "done")

#: The five states, in order. No sixth, and no aliases — 013 is explicit that
#: nothing beyond these is added.
STATES = ("WRITTEN", "HANDED OFF", "RUNNING", "REVIEWED", "DONE")

#: **Header region only — the first 20 lines.** A task file that discusses these
#: words in prose must not accidentally satisfy the test. This is a positional
#: rule rather than an exclusion list, for the same reason the `6 of 9`
#: normalisation ended up positional: a list of things to ignore grows until it
#: is a hiding place, and a rule about WHERE the claim must appear does not.
HEADER_LINES = 20

#: A leading YAML frontmatter block, skipped before the window is measured.
#: See `declared_state`. 053 Part 4 made frontmatter length variable by design.
_FRONTMATTER = re.compile(r"\A---\r?\n.*?\r?\n---\r?\n", re.S)

#: `**Status**` followed by the value. Captures greedily to the end of the
#: state-ish token so `IN PROGRESS` is captured whole and reported, rather than
#: matching `IN` and reporting something the file does not say.
STATUS_RE = re.compile(r"\*\*Status\*\*[:\s]*([A-Za-z][A-Za-z ]*?)\s*(?:·|\||$)", re.M)


#: RESOLUTION D. A file recorded in EVIDENCE-CARRY.md is carried evidence, not a
#: live handoff, and is exempt from the state-header requirement.
#:
#: Not because of who wrote it -- that would be scoping by authorship, which is
#: arbitrary and would exempt the files most likely to go stale. It is scoped by
#: a property **already recorded and hash-enforced** elsewhere in the suite.
#:
#: The absence of a header on a pre-convention file is not a defect. It is a true
#: statement about when the file was written: these tasks completed in another
#: repository, under a convention that did not exist yet. Backfilling them would
#: assert a handoff state that nobody ever declared -- and a fabricated state is
#: precisely what this test exists to catch.
#:
#: **Derived at test time, never a hardcoded list.** A literal list is a hiding
#: place that grows; a derived rule is not. Two guards below stop the exemption
#: widening quietly.
MANIFEST = REPO / "EVIDENCE-CARRY.md"
CARRIED_SOURCE_ROOT = "D:/Dev/momentum-harness/"

_ROW = re.compile(
    r"^\|\s*\d{4}-\d{2}-\d{2}\s*\|\s*`(?P<rel>[^`]+)`\s*\|\s*`(?P<src>[^`]+)`\s*\|", re.M)


def carried() -> dict[str, str]:
    """path-in-tree -> source path, from EVIDENCE-CARRY.md."""
    if not MANIFEST.exists():
        return {}
    return {m.group("rel"): m.group("src")
            for m in _ROW.finditer(MANIFEST.read_text(encoding="utf-8"))}


def all_task_files() -> list[Path]:
    out: list[Path] = []
    for d in TASK_DIRS:
        if d.is_dir():                      # empty or absent directories pass
            out += sorted(d.glob("*.md"))
        # An empty handoff/done/ is a true statement about a project where
        # nothing has completed yet. Emptiness is not a failure.
    return out


def exempt_paths() -> set[str]:
    c = carried()
    return {p.relative_to(REPO).as_posix() for p in all_task_files()
            if p.relative_to(REPO).as_posix() in c}


def task_files() -> list[Path]:
    """Live handoffs only — carried evidence is exempt under resolution D."""
    ex = exempt_paths()
    return [p for p in all_task_files() if p.relative_to(REPO).as_posix() not in ex]


def test_guard_1_every_exempted_path_is_in_the_manifest() -> None:
    """The exemption may only ever come from EVIDENCE-CARRY.md.

    If this test ever skips a file that is not in the manifest, the rule has
    stopped being derived and has become a list.
    """
    c = carried()
    ungrounded = sorted(p for p in exempt_paths() if p not in c)
    assert not ungrounded, (
        "these task files are exempt from the state-header rule but are NOT in "
        f"{MANIFEST.name}:\n  " + "\n  ".join(ungrounded)
        + "\n\nThe exemption is derived from the manifest and from nothing else. A file "
          "skipped\nwithout a manifest row means the rule has become a hardcoded list."
    )


def test_guard_2_no_natively_authored_file_is_exempt() -> None:
    """A file authored in THIS tree can never qualify for the exemption.

    It was written after the convention existed, so it has a state and must
    declare one. The check is the manifest's own `source path` column: a
    genuinely carried file was copied from the archived predecessor, and a live
    task file authored here cannot have come from there.

    This is the guard that fails if someone adds a live task file to the
    manifest to silence the header test.
    """
    c = carried()
    native = sorted(
        f"{p}  (source recorded as `{c[p]}`)"
        for p in exempt_paths()
        if not c[p].replace("\\", "/").startswith(CARRIED_SOURCE_ROOT)
    )
    assert not native, (
        "these exempt task files were NOT carried from the archived predecessor:\n  "
        + "\n  ".join(native)
        + f"\n\nA carried file's source is under {CARRIED_SOURCE_ROOT}. Anything else was "
          "authored\nhere, after the convention existed, and must declare a state like every "
          "other live\ntask. Adding a live task file to EVIDENCE-CARRY.md does not make it "
          "evidence."
    )


#: **053: from this task number on, the state header is read from the BODY.**
#:
#: Two things forced this, and the second is the interesting one.
#:
#: 1. Part 4 requires every done-note to carry a `bugs:` block in frontmatter. A
#:    note reporting six findings has ~100 lines of it, which pushes `**Status**`
#:    past line 20. Counting from the top of the FILE would make the header rule
#:    depend on how many bugs a task happened to find.
#:
#: 2. **Measured while fixing (1): this test was being satisfied by the
#:    frontmatter `status:` KEY, not by the `**Status**` header at all.**
#:    `handoff/inbox/021-...md` carries `status: READY` in frontmatter and has no
#:    body header whatsoever, and it passed. CLAUDE.md is explicit that these are
#:    different things -- *"A done-note's frontmatter is a separate thing and may
#:    say what it likes: it describes the work, while the header describes the
#:    handoff."* The check had been conflating them.
#:
#: **A WATERMARK, not an allowlist.** Files below it keep the old behaviour:
#: they are pre-convention documents the other half of the loop authored and has
#: already read, and editing them now would rewrite a record rather than fix a
#: defect. Files at or after it must carry a real body header. **The exemption
#: cannot grow, because a new task file is always numbered above the line.**
STATE_HEADER_FROM = 49

_TASK_NUM = re.compile(r"(?:^|/)(\d+)")


def _at_or_after_watermark(path: Path) -> bool:
    m = _TASK_NUM.search(path.name)
    return bool(m) and int(m.group(1)) >= STATE_HEADER_FROM


def declared_state(path: Path) -> str | None:
    """The state header, read from the first HEADER_LINES lines OF THE BODY.

    **053: the frontmatter is skipped before the window is measured.** Part 4
    requires every done-note to carry a `bugs:` block in frontmatter, and a note
    reporting six findings has a hundred lines of it -- which pushed `**Status**`
    past line 20 and turned this test red on a file that declares its state
    correctly.

    Counting from the top of the FILE would make the header rule depend on how
    many bugs a task happened to find. **The rule is "near the top of what a
    reader reads", and frontmatter is not that.** The window itself is unchanged.
    """
    text = path.read_text(encoding="utf-8")
    if _at_or_after_watermark(path):
        # 053: the BODY header only. See STATE_HEADER_FROM note above.
        text = _FRONTMATTER.sub("", text, count=1) if _FRONTMATTER.match(text) else text
    head = chr(10).join(text.splitlines()[:HEADER_LINES])
    m = STATUS_RE.search(head)
    return m.group(1).strip() if m else None


def test_every_task_file_declares_a_state() -> None:
    """Condition 1: no state header at all."""
    missing = [p.relative_to(REPO).as_posix() for p in task_files() if declared_state(p) is None]
    assert not missing, (
        "these task files declare no handoff state in their first "
        f"{HEADER_LINES} lines:\n  " + "\n  ".join(missing)
        + "\n\nAdd a header line, e.g. `**Status** RUNNING`. One of: "
        + " · ".join(STATES)
        + "\nChristoph holds the state — if it is not known, ask rather than assume. "
          "See docs/specs/HANDOFF-PROTOCOL.md."
    )


def test_no_task_file_declares_a_state_outside_the_five() -> None:
    """Condition 2, and it is a DIFFERENT defect from condition 1.

    An unrecognised state is not the same as an absent one, and a reader needs
    to know which they have: a missing header means nobody said, an invalid one
    means somebody said something the protocol does not define.
    """
    bad = []
    for p in task_files():
        state = declared_state(p)
        if state is not None and state.upper() not in STATES:
            bad.append(f"{p.relative_to(REPO).as_posix()}: declares {state!r}")
    assert not bad, (
        "these task files declare a state outside the five:\n  " + "\n  ".join(bad)
        + "\n\nThe five states are: " + " · ".join(STATES)
        + "\nThis is not a missing header — the file says something, and what it says is not "
          "a state.\nDo not add a sixth state; see docs/specs/HANDOFF-PROTOCOL.md."
    )


def test_the_header_region_rule_is_positional_not_lexical() -> None:
    """A file mentioning a state word deep in its body must not satisfy the
    check. The protocol document itself is the natural counter-example: it
    tabulates all five states in prose."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "t.md"
        p.write_text("# t\n" + "\n" * 40 + "**Status** DONE\n", encoding="utf-8")
        assert declared_state(p) is None, (
            "a state declared past the header region was accepted; the rule has stopped "
            "being positional")


def test_the_five_states_match_the_protocol_document() -> None:
    """If the document ever gains or loses a state, this test must not keep
    enforcing the old set silently."""
    doc = REPO / "docs" / "specs" / "HANDOFF-PROTOCOL.md"
    if not doc.exists():
        return
    text = doc.read_text(encoding="utf-8")
    for s in STATES:
        assert s in text, f"state {s!r} is enforced here but absent from {doc.name}"
