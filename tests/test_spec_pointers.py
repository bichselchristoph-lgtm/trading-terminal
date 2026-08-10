"""The canonical specs are in the tree, and CLAUDE.md's pointers resolve.

H9's defect: SPEC.md, BUILD-PLAN.md and REGIME-PROMPT.md existed only in Google
Drive and in a Claude project. Discovered 2026-08-10 when a path named in
SPEC.md §5.1 -- `claude/regime-snapshots/` -- was checked against the repo and
found never to have existed. Nobody had looked.

Why this is the expensive kind of missing: BUILD-PLAN.md §2a states the
asymmetry -- Claude Code sees the repo, and sees only what a task file quotes of
the spec. **A spec that is not in the tree is invisible to the side that
builds.** Layer 0 is the priced instance: fully specified, never built, because
the spec lived only in Drive.

This is the third application of "the read is the implementation". A pointer
that lives in prose depends on someone remembering. A pointer with a test behind
it does not.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

CANONICAL_SPECS = [
    "docs/specs/SPEC.md",
    "docs/specs/BUILD-PLAN.md",
    "docs/specs/REGIME-PROMPT.md",
]

#: A line mentioning any of these is talking about something that is GONE or
#: lives elsewhere, so its pointer is not expected to resolve.
OBSOLETE_MARKERS = ("obsolete", "deleted", "archived", "do not use", "not yet supplied",
                    "never existed", "no longer")

#: Backtick-quoted tokens that look like repo-relative paths: contain a
#: separator, and end in a file extension or a trailing separator.
PATH_TOKEN = re.compile(r"`([^`\n]*[\\/][^`\n]*)`")


@pytest.mark.parametrize("rel", CANONICAL_SPECS)
def test_canonical_specs_present(rel: str) -> None:
    """Every canonical spec exists and is non-empty. The failure message names
    the missing path -- a generic assertion error would not say which pointer
    broke, and that is the whole value of the test."""
    p = REPO / rel
    assert p.exists(), (
        f"canonical spec missing: {rel}. It is not in the tree, which means it is invisible "
        "to the side that builds. See docs/specs/ in CLAUDE.md."
    )
    assert p.stat().st_size > 0, f"canonical spec is empty: {rel}"


def _looks_external(token: str) -> bool:
    """Absolute Windows paths, URLs and other repos are not this tree's to resolve."""
    t = token.strip()
    return (
        bool(re.match(r"^[A-Za-z]:[\\/]", t))
        or t.startswith(("http://", "https://", "//", "~"))
        or t.startswith(("momentum-harness/", "tws_order/", "tradesignals/",
                         "trading-scripts/", "orb_tools/", "ibkr_tape_tools/",
                         "D:\\", "D:/"))
    )


def claude_md_tokens() -> tuple[list[tuple[int, str]], list[tuple[int, str]]]:
    """Returns (resolvable_tokens, unclassifiable_tokens).

    A token containing a wildcard is a NAMING CONVENTION, not a pointer --
    `handoff/done/NNN-*.md` describes a shape, and no single path can satisfy it.
    Those go to the unclassifiable bucket and are reported rather than silently
    dropped. This is not an exclusion widened to reach green: the test below is
    still red on the genuine unresolved pointers, and H9 requires this bucket to
    be listed in the done-note precisely so it cannot become a hiding place.
    """
    text = (REPO / "CLAUDE.md").read_text(encoding="utf-8")
    resolvable: list[tuple[int, str]] = []
    unclassifiable: list[tuple[int, str]] = []
    for i, line in enumerate(text.splitlines(), 1):
        low = line.lower()
        if any(m in low for m in OBSOLETE_MARKERS):
            continue
        for m in PATH_TOKEN.finditer(line):
            tok = m.group(1).strip()
            if _looks_external(tok):
                continue
            if not (re.search(r"\.\w{1,6}$", tok) or tok.endswith(("/", "\\"))):
                continue
            (unclassifiable if any(c in tok for c in "*?[") else resolvable).append((i, tok))
    return resolvable, unclassifiable


def test_claude_md_pointers_resolve() -> None:
    """Every repo-relative path CLAUDE.md names actually exists.

    If this is red, DO NOT widen the exclusions until it goes green. Record the
    unresolved pointers and fix the thing they point at, or the pointer. An
    exclusion list quietly grown to reach green hides real breakage, and that is
    strictly worse than a red test somebody reads.
    """
    resolvable, _ = claude_md_tokens()
    unresolved = [
        f"CLAUDE.md:{ln}  `{tok}`"
        for ln, tok in resolvable
        if not (REPO / tok.replace("\\", "/")).exists()
    ]
    assert not unresolved, (
        "CLAUDE.md names paths that do not exist:\n  " + "\n  ".join(unresolved)
        + "\n\nEither the path is wrong or the thing is missing. Do not silence this by "
        "widening\nthe exclusion list -- that hides real breakage behind a green run."
    )


def test_the_extractor_finds_something() -> None:
    """An extractor matching nothing would make the test above pass vacuously --
    which is exactly the shape of the defect this file exists for."""
    resolvable, unclassifiable = claude_md_tokens()
    assert len(resolvable) >= 5, (
        f"the path extractor found only {len(resolvable)} resolvable tokens in CLAUDE.md. It is "
        "almost certainly broken, and test_claude_md_pointers_resolve is passing by checking nothing."
    )
    # Not an assertion about the count -- the bucket is allowed to be empty. It
    # is printed so the done-note can list it, because H9 treats an unexamined
    # "could not classify" pile as the place real breakage goes to hide.
    print(f"unclassifiable (wildcard) tokens: {unclassifiable}")


def test_regime_prompt_is_v1_1_not_v1_0() -> None:
    """H9 §1: v1.1 carries `PART E — the three outputs` and an `E0` subsection.
    A copy saying "the two outputs" is v1.0 and must not be committed. Pinned
    here so a later re-supply cannot silently downgrade it."""
    p = REPO / "docs/specs/REGIME-PROMPT.md"
    if not p.exists():
        pytest.skip("REGIME-PROMPT.md not present; test_canonical_specs_present owns that")
    text = p.read_text(encoding="utf-8")
    assert "the two outputs" not in text.lower(), (
        "REGIME-PROMPT.md says 'the two outputs' — that is v1.0, and H9 says to stop rather "
        "than commit it."
    )
    assert "PART E" in text and "the three outputs" in text, (
        "REGIME-PROMPT.md is missing the 'PART E — the three outputs' heading that identifies v1.1."
    )
    assert "E0" in text, "REGIME-PROMPT.md is missing the 'E0 — the chat body' subsection."
