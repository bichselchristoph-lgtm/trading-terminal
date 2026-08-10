"""The canonical specs are in the tree, and CLAUDE.md's pointers resolve.

H9's defect: SPEC.md, BUILD-PLAN.md and REGIME-PROMPT.md existed only in Google
Drive and in a Claude project. Discovered 2026-08-10 when a path named in
SPEC.md §5.1 -- the old `claude/`-rooted regime-snapshots directory -- was checked
against the repo and found never to have existed. Nobody had looked.

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

#: Three values, not four. `PROVENANCE.md` shows every docs/specs/ file
#: `authored` here, so every supersession has a real decision behind it and
#: every `by` resolves to a document in this project. An `INHERITED` status
#: would have been a place to put files nobody had decided about.
VALID_STATUSES = ("CURRENT", "SUPERSEDED", "HISTORICAL")

STATUS_LINE = re.compile(r"\*\*STATUS\*\*\s+(\w+)")
BY_LINE = re.compile(r"\*\*by\*\*\s+`([^`]+)`")


def spec_docs() -> list[Path]:
    return sorted((REPO / "docs" / "specs").rglob("*.md"))

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


def test_every_spec_declares_status() -> None:
    """Every `.md` under docs/specs/ says what it is, in its first 10 lines.

    **This is the test that makes the convention survive.** The old repo held
    current and superseded documents side by side with nothing declaring which
    was which, so a reader who opened the wrong one got a confident, well-formed
    answer to a question no longer being asked. A spec dropped in without a
    header goes red, which is what stops the next person quietly redoing what
    was just fixed.
    """
    missing, bad = [], []
    for p in spec_docs():
        rel = p.relative_to(REPO).as_posix()
        head = "\n".join(p.read_text(encoding="utf-8").splitlines()[:10])
        m = STATUS_LINE.search(head)
        if not m:
            missing.append(rel)
        elif m.group(1) not in VALID_STATUSES:
            bad.append(f"{rel}: STATUS {m.group(1)!r} is not one of {VALID_STATUSES}")
    assert not missing and not bad, (
        ("these docs/specs files declare no STATUS in their first 10 lines:\n  "
         + "\n  ".join(missing) if missing else "")
        + ("\n" if missing and bad else "")
        + ("\n  ".join(bad) if bad else "")
        + "\n\nAdd a header as the first non-heading block, e.g.\n"
          "  > **STATUS** CURRENT · **date** YYYY-MM-DD\n"
          "  > **STATUS** SUPERSEDED · **by** `docs/specs/SPEC.md` §5.1 · **date** YYYY-MM-DD"
    )


def test_every_superseded_spec_names_a_resolving_by() -> None:
    """`SUPERSEDED` requires `by`, and the `by` must resolve. A supersession
    pointing at nothing is indistinguishable from an unexplained deletion."""
    problems = []
    for p in spec_docs():
        rel = p.relative_to(REPO).as_posix()
        head = "\n".join(p.read_text(encoding="utf-8").splitlines()[:10])
        m = STATUS_LINE.search(head)
        if not m or m.group(1) != "SUPERSEDED":
            continue
        b = BY_LINE.search(head)
        if not b:
            problems.append(f"{rel}: SUPERSEDED with no **by**")
        elif not (REPO / b.group(1)).exists():
            problems.append(f"{rel}: **by** names `{b.group(1)}`, which does not exist")
    assert not problems, "\n  ".join(["superseded specs with a broken `by`:"] + problems)


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


# The REGIME-PROMPT version pin moved to tests/test_regime_prompt_invariants.py
# under H10, with the floor raised to v1.2 and the PART E / E0 assertions carried
# forward intact. Kept in one place so the two cannot drift apart.
