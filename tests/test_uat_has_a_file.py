"""A UAT named in a done-note must exist as a file Christoph will open.

`S009`'s exit table said *"UAT — yours. Write the record to `christoph/`."*
**Nothing wrote it.** Claude Code correctly never writes to `christoph/`, and the
design session had no trigger, so the UAT existed only as a line inside a
done-note already read, in a folder nobody opens again. It surfaced because
Christoph asked where his UAT was.

That is the **seventh** instance of a correct instruction sitting in a file
nobody was directed to open — the pattern that left Layer 0 fully specified and
never built. A convention in prose depends on someone remembering. This one
fails a test instead.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DONE = REPO / "handoff" / "done"
CHRISTOPH = (REPO / "christoph" / "open", REPO / "christoph" / "done")
MANIFEST = REPO / "EVIDENCE-CARRY.md"

#: **Positional, not lexical.** The first cell of a table row must be `UAT` —
#: matching the bare word anywhere would turn every done-note that *discusses*
#: UATs into a false positive, and the exclusion list to suppress those becomes
#: the hiding place. Same discipline as `test_handoff_state_declared`.
UAT_ROW = re.compile(r"^\|\s*\*{0,2}UAT\*{0,2}\s*\|(?P<rest>.+)$", re.M)

#: A declaration that nothing is owed. **Not every task needs a UAT**, and a rule
#: that fires on tasks with nothing to check trains people to ignore it.
NO_UAT = re.compile(r"\bnone\b", re.I)

#: `**Slice** S009` or `**Task** 012`, with or without backticks. The format
#: follows the first real instance — `christoph/open/003` — rather than the
#: other way round.
DECLARES = re.compile(r"\*\*(?:Slice|Task)\*\*\s*`?([A-Za-z]?\d+[a-z]?)`?")

#: Resolution D, REUSED — not a second mechanism. A done-note recorded in
#: EVIDENCE-CARRY.md is carried evidence: it completed in another repository
#: under a convention that did not exist, and its UAT was performed verbally if
#: at all. Derived from the manifest at test time, never a list.
_CARRIED = re.compile(r"^\|\s*\d{4}-\d{2}-\d{2}\s*\|\s*`(?P<rel>[^`]+)`", re.M)


def carried() -> set[str]:
    if not MANIFEST.exists():
        return set()
    return {m.group("rel") for m in _CARRIED.finditer(MANIFEST.read_text(encoding="utf-8"))}


def identifier(note: Path) -> str:
    """`S009-tui-frame….md` -> `S009`; `012a-preopen….md` -> `012a`."""
    return re.split(r"-", note.stem, 1)[0]


def declared_identifiers() -> set[str]:
    """Every task id claimed by a file in christoph/open/ or christoph/done/.

    **Both folders**, because an answered UAT is still a satisfied one.
    """
    out: set[str] = set()
    for d in CHRISTOPH:
        if not d.is_dir():
            continue
        for p in d.glob("*.md"):
            head = "\n".join(p.read_text(encoding="utf-8").splitlines()[:10])
            out |= {m.group(1) for m in DECLARES.finditer(head)}
    return out


def notes_owing_a_uat() -> list[tuple[Path, str]]:
    exempt = carried()
    owing: list[tuple[Path, str]] = []
    for p in sorted(DONE.glob("*.md")):
        if p.relative_to(REPO).as_posix() in exempt:
            continue
        m = UAT_ROW.search(p.read_text(encoding="utf-8"))
        if not m:
            continue
        # Only the first ~80 characters decide: "None" must be the declaration,
        # not a word appearing later in a paragraph about something else.
        if NO_UAT.search(m.group("rest")[:80]):
            continue
        owing.append((p, identifier(p)))
    return owing


def test_every_declared_uat_exists_as_a_file() -> None:
    have = declared_identifiers()
    missing = [(p.name, ident) for p, ident in notes_owing_a_uat() if ident not in have]
    assert not missing, (
        "these done-notes name a UAT in their exit table, but no file in christoph/ "
        "declares it:\n  "
        + "\n  ".join(f"{n}  ->  needs a file declaring **Slice**/**Task** {i}"
                      for n, i in missing)
        + "\n\nA UAT named only inside a done-note is not a UAT: it sits in a folder nobody "
          "opens\nagain. THE FIX IS TO AUTHOR THE FILE — the design session authors it and "
          "Christoph\nsaves it to christoph/open/. See docs/specs/CHRISTOPH-TASKS.md.\n"
          "If the task genuinely owes no UAT, its exit row should read `UAT | ... | None`, "
          "which\nis a valid declaration and passes."
    )


def test_the_rule_is_positional_not_lexical(tmp_path: Path) -> None:
    """A done-note that merely discusses UATs in prose owes nothing."""
    p = tmp_path / "zz-prose.md"
    p.write_text("# t\n\nThis note explains what a UAT is and why UAT rows matter.\n",
                 encoding="utf-8")
    assert UAT_ROW.search(p.read_text(encoding="utf-8")) is None


def test_none_is_a_valid_declaration(tmp_path: Path) -> None:
    p = tmp_path / "zz-none.md"
    p.write_text("| test | who | what |\n|---|---|---|\n| **UAT** | Christoph | None. |\n",
                 encoding="utf-8")
    m = UAT_ROW.search(p.read_text(encoding="utf-8"))
    assert m is not None
    assert NO_UAT.search(m.group("rest")[:80]), "a `None` row must not demand a file"


def test_the_exemption_is_resolution_d_reused_not_a_second_mechanism() -> None:
    """Guard: the exempt set must come from EVIDENCE-CARRY.md and nowhere else."""
    src = Path(__file__).read_text(encoding="utf-8")
    assert "EVIDENCE-CARRY.md" in src
    assert carried(), "the manifest parsed to nothing; the exemption is not derived"
    # Every exempt path must actually be in the manifest — the same guard-1 shape
    # as test_handoff_state_declared, so the rule cannot become a list.
    manifest_text = MANIFEST.read_text(encoding="utf-8")
    for rel in list(carried())[:5]:
        assert f"`{rel}`" in manifest_text


def test_s009s_uat_resolves() -> None:
    """The instance that produced this test."""
    assert "S009" in declared_identifiers(), (
        "christoph/open/003-s009-read-the-empty-screen.md should declare **Slice** S009")
