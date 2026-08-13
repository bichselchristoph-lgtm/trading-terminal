"""What `REGIME-PROMPT.md` must never lose.

This extends the v1.1 version pin that lived in `test_spec_pointers.py` rather
than replacing it — every assertion it made survives here, with the floor raised
to v1.2 and four more added.

The prompt is `CURRENT` and runs daily at 05:00, unattended, and its output is
prose a person acts on. Nothing parses it, so **there is no runtime that would
notice a regression** — a threshold quietly dropped in a re-supply would simply
start producing different reads. These assertions are the only thing standing
between a re-paste and a silent change of meaning.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
PROMPT = REPO / "docs" / "specs" / "REGIME-PROMPT.md"

#: The figure that has now propagated through three documents — Amendment 1
#: §A1.5, `mockup-02`, and PART B — copied each time rather than recomputed.
BARE_COUNT = "6 of 9"

#: A line may cite the figure while naming it as the anti-pattern. That is what
#: v1.2 does, in the passage that forbids it. The test's stated intent is that a
#: count "must name its exclusions", so an occurrence is a violation unless the
#: line marks it as the error being warned against. This is NOT a widened
#: exclusion: a bare worked example still fails, which
#: `test_the_bare_count_check_can_actually_fail` proves.
#:
#: `~~` and "moot" were added under H11 when the normalised check surfaced a
#: FOURTH occurrence the literal check had never seen: SPEC.md §3.1 defect 2,
#: `~~... 02 scores `6/9` out of 11 ...~~ **Moot in the terminal.**` — struck
#: through and recorded as resolved. That line catalogues the defect; it does not
#: assert a count. Strikethrough in this document means "was true, now resolved",
#: which is anti-pattern framing by construction.
ANTI_PATTERN_MARKERS = ("indistinguishable", "error", "must name", "bare", "~~", "moot")


def prompt_text() -> str:
    assert PROMPT.exists(), f"{PROMPT.relative_to(REPO)} is missing"
    return PROMPT.read_text(encoding="utf-8")


def test_version_is_1_8_or_higher() -> None:
    m = re.search(r"\*\*Version\*\*\s*([0-9]+)\.([0-9]+)", prompt_text())
    assert m, "no `**Version** N.N` line found in REGIME-PROMPT.md"
    major, minor = int(m.group(1)), int(m.group(2))
    assert (major, minor) >= (1, 8), (
        f"REGIME-PROMPT.md is v{major}.{minor}. v1.2 added the ratification bands and the "
        "reduced-card floor;\nanything older reintroduces the defects H10 closed."
    )


def test_part_e_is_the_three_outputs_not_two() -> None:
    """Carried forward from the v1.1 pin. A copy saying "the two outputs" is
    v1.0, superseded by Amendment 3, and must not be committed."""
    text = prompt_text()
    assert "the two outputs" not in text.lower(), (
        "REGIME-PROMPT.md says 'the two outputs' — that is v1.0, and it must not be committed."
    )
    assert "PART E" in text and "the three outputs" in text, (
        "REGIME-PROMPT.md is missing the 'PART E — the three outputs' heading."
    )
    assert "E0" in text, "REGIME-PROMPT.md is missing the 'E0 — the chat body' subsection."


def test_schema_version_is_2() -> None:
    """A v1.1 snapshot has no `ratification` block at all, so without the bump a
    reader cannot tell a v1 snapshot from a v2 one where the floor did not fire.
    `SPEC.md` §5.5a makes a mismatch refuse-to-parse, which is what makes the two
    distinguishable."""
    assert "schema_version: 2" in prompt_text(), (
        "REGIME-PROMPT.md does not emit `schema_version: 2`. The ratification block's new "
        "keys\n(rows_available, floor_fired, bands, bands_source, floor_source) are absent "
        "from a v1\nsnapshot, and without the bump the two are indistinguishable."
    )


def test_ratification_bands_are_present_and_sourced() -> None:
    text = prompt_text()
    for band in ("+2 or +3", "0 or +1", "−1 or lower"):
        assert band in text, (
            f"ratification band {band!r} missing from PART B. Without the bands the 05:00 read "
            "is not checkable later — whoever reads the ratification decides after the fact."
        )
    assert text.count("regime_read_template_2026-08") >= 3, (
        "the ratification bands must each carry `source: regime_read_template_2026-08`. "
        "Every cut point in PART B comes from the template except the floor."
    )


def test_the_reduced_card_floor_is_marked_provisional() -> None:
    """The floor is the ONE threshold in PART B not taken from the template. If
    it loses its marking it becomes indistinguishable from a sourced one."""
    text = prompt_text()
    assert "prompt_decision_2026-08-10" in text, (
        "the reduced-card floor must carry `source: prompt_decision_2026-08-10`. It was "
        "decided on 2026-08-10 because the template's bands break on a two-row card."
    )
    assert "PROVISIONAL" in text, (
        "the reduced-card floor must ship `PROVISIONAL`. Unmarked, it reads as sourced."
    )
    assert "fewer than three" in text.lower(), (
        "the floor rule itself is missing: fewer than three of rows 12–14 available ⇒ "
        "ratification skipped entirely, pre-open read stands."
    )


#: Match the DIGIT PAIR, not a literal string. H10 closed `6 of 9` and H11
#: found the spelling gap: `mockup-02` renders `6 / 9`, which the literal check
#: sailed past. The figure has made three document hops already and was spelled
#: differently on at least one of them, so the separator is not the invariant --
#: the unexplained count is.
SIX_NINE = re.compile(r"\b6\s*(?:/|of|\\)\s*9\b", re.I)


def _bare_count_violations(text: str) -> list[str]:
    """A count is a violation unless it is **quoted as a token**.

    The word both documents use is *bare*, and backticks are what "bare" means
    in markdown: `` `6/9` `` is the figure being named, `6 of 9 rows scored` is
    the figure being asserted. This replaced a growing list of marker words —
    H11's normalised check surfaced two further citations (SPEC.md §3.1 defect 2
    and §12.1's revival note) and each would have needed another word added,
    which is how an exclusion list quietly becomes a hiding place.

    The marker words are kept as a secondary allowance for un-backticked prose,
    but the backtick rule is the principled one and does the work.
    """
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        m = SIX_NINE.search(line)
        if not m:
            continue
        quoted = "`" in line[max(0, m.start() - 2):m.start()] and "`" in line[m.end():m.end() + 2]
        if quoted or any(w in line.lower() for w in ANTI_PATTERN_MARKERS):
            continue
        out.append(f"line {i}: {line.strip()[:80]}")
    return out


def test_no_bare_six_of_nine() -> None:
    """**The assertion that matters.**

    `6 of 9` is arithmetically legal if two of rows 1–11 are unavailable, and it
    is also exactly what a reader gets by miscounting an 11-row card as 9. The
    same string means both things, so a count that does not name its exclusions
    cannot be checked. It has propagated through three documents already, copied
    each time. A test is what stops a fourth.
    """
    violations = _bare_count_violations(prompt_text())
    assert not violations, (
        "REGIME-PROMPT.md uses the bare figure `6 of 9`:\n  " + "\n  ".join(violations)
        + "\n\nThe figure is indistinguishable from the Amendment 1 §A1.5 error and must name "
          "its\nexclusions. Report counts as `N of M rows scored` followed by an "
          "`unavailable:` line\nnaming every excluded row."
    )


def test_no_bare_six_of_nine_anywhere_in_specs() -> None:
    """The same rule across every spec, not just this one.

    The figure propagated *between* documents — Amendment 1 to `mockup-02` to
    PART B — so a check scoped to one file would not have caught any of the
    three hops. A fourth would most likely appear somewhere new.
    """
    violations = []
    for p in sorted((REPO / "docs" / "specs").rglob("*")):
        if not p.is_file() or p.suffix.lower() not in (".md", ".html", ".yaml", ".yml"):
            continue
        rel = p.relative_to(REPO).as_posix()
        # `docs/specs/mockups/` is exempt, and the exemption is load-bearing:
        # mockup-02 renders `6 / 9` and H10/H11 both say not to repair it. The
        # sheets are frozen historical artifacts carrying a HISTORICAL banner,
        # not live specification. **This exemption is the only thing standing
        # between that figure and a fourth hop**, so the mockup redraw inherits
        # removing it as a named obligation.
        if rel.startswith("docs/specs/mockups/"):
            continue
        for line in _bare_count_violations(p.read_text(encoding="utf-8", errors="ignore")):
            violations.append(f"{rel}  {line}")
    assert not violations, (
        "an unexplained 6/9 count appears in docs/specs/:\n  " + "\n  ".join(violations)
        + "\n\n**A count that does not name its exclusions cannot be checked, whatever "
          "separator it is\nspelled with.** `6 of 9`, `6 / 9` and `6/9` are the same defect: "
          "each is legal if two of\nrows 1–11 are unavailable, and each is also exactly what a "
          "reader gets by miscounting an\n11-row card as 9. Report counts as `N of M rows "
          "scored` followed by an `unavailable:` line\nnaming every excluded row."
    )


def test_the_bare_count_check_can_actually_fail() -> None:
    """Proves the anti-pattern allowance has not swallowed the rule. A worked
    example carrying the figure with no explanation must still be caught."""
    assert _bare_count_violations("pre-open total +4 · 6 of 9 rows scored")
    assert not _bare_count_violations("A bare `6 of 9` is indistinguishable from an error")
    # H11 §3: every separator spelling, since the figure was spelled two ways
    # across its three hops.
    for spelling in ("6 / 9", "6/9", "6 of 9", "6  /  9", "6 OF 9"):
        assert _bare_count_violations(f"scored {spelling} rows"), f"missed {spelling!r}"


def test_the_denominator_block_names_its_exclusions() -> None:
    """The positive half of the same rule: the worked example must demonstrate
    naming the absent rows, not merely forbid the alternative."""
    text = prompt_text()
    assert "unavailable: row" in text, (
        "PART B's worked denominator block must show an `unavailable: row N (reason)` line. "
        "Forbidding the bare count without demonstrating the correct form leaves the reader "
        "with a prohibition and no pattern."
    )


@pytest.mark.parametrize("part", ["PART A", "PART B", "PART C", "PART D", "PART E"])
def test_all_five_parts_survive(part: str) -> None:
    """H10 changed PART B only. A re-supply that dropped a whole part would
    otherwise pass every assertion above."""
    assert part in prompt_text(), f"{part} is missing from REGIME-PROMPT.md"
