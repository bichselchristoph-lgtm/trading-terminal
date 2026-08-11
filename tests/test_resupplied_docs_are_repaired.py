"""Tree-side repairs survive, and a failure names re-supply as the likely cause.

Specs are authored outside this tree, in a session that cannot see it. Every
repair made here is invisible to the author and is dropped by the next supply of
that document. **The failure is silent**: the file is well-formed, the adoption
gate compares bytes and passes it, and the regression is visible only to someone
who remembers making the edit.

H10 caught exactly this — v1.2 arrived with 5 legacy snapshot paths and no status
header — and only because the same session had made those edits hours earlier.

Several of these invariants are already asserted elsewhere. They are asserted
**again** here on purpose: a failure in this file names the cause, and a reader
who sees `test_no_legacy_regime_snapshot_path` fail in isolation has to work out
why a path that was fixed is back. The duplication is the diagnostic.

`docs/specs/RE-SUPPLY.md` carries the same list in prose, for quoting into task
files so the author can apply them at source.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SPECS = REPO / "docs" / "specs"

CAUSE = (
    "\n\n>>> This invariant was applied in the tree and is absent. The file was probably\n"
    ">>> RE-SUPPLIED from outside and arrived pre-repair. RE-APPLY, DO NOT RE-AUTHOR:\n"
    ">>> the document that arrived is the current content; the invariant is a repair\n"
    ">>> that was made to its predecessor. See docs/specs/RE-SUPPLY.md."
)

VALID_STATUSES = ("CURRENT", "SUPERSEDED", "HISTORICAL")
def _legacy_path() -> str:
    """Imported, not redefined. tests/test_regime_snapshot_path.py is the single
    definition and skips itself when scanning; a second literal here would be a
    second occurrence of the very string this asserts is absent."""
    import importlib.util, sys
    src = Path(__file__).with_name("test_regime_snapshot_path.py")
    spec = importlib.util.spec_from_file_location("_legacy_src", src)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_legacy_src"] = mod
    spec.loader.exec_module(mod)
    return mod.FORBIDDEN
EXEMPT_FROM_LEGACY_PATH = ("docs/specs/DRIVE-ARCHIVE-LIST.md",)
BANNERED_SHEETS = ("mockup-02-regime.html", "mockup-04-size-stage.html",
                   "mockup-05-live-context.html")


def spec_docs() -> list[Path]:
    return sorted(SPECS.rglob("*.md"))


def test_invariant_1_every_spec_still_declares_a_status() -> None:
    missing = []
    for p in spec_docs():
        head = "\n".join(p.read_text(encoding="utf-8").splitlines()[:10])
        m = re.search(r"\*\*STATUS\*\*\s+(\w+)", head)
        if not m or m.group(1) not in VALID_STATUSES:
            missing.append(p.relative_to(REPO).as_posix())
    assert not missing, (
        "docs/specs files with no valid STATUS header in their first 10 lines:\n  "
        + "\n  ".join(missing) + CAUSE
    )


def test_invariant_2_no_legacy_snapshot_path_survives() -> None:
    legacy = _legacy_path()
    hits = []
    for p in spec_docs():
        rel = p.relative_to(REPO).as_posix()
        if rel in EXEMPT_FROM_LEGACY_PATH:
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if legacy in line:
                hits.append(f"{rel}:{i}")
    assert not hits, (
        f"the legacy path {legacy!r} is back in docs/specs/:\n  "
        + "\n  ".join(hits)
        + f"\n\nThe canonical path is `docs/regime-snapshots/`." + CAUSE
    )


def test_invariant_3_spec_section_13_keeps_its_qualification() -> None:
    """The qualification lives in the HEADING, where it is read — not only
    beside each citation. `test_spec_pointers` deliberately excludes external
    paths, so nothing else will ever flag a stale Drive citation."""
    text = (SPECS / "SPEC.md").read_text(encoding="utf-8")
    heading = next((l for l in text.splitlines()
                    if l.startswith("#") and re.search(r"\b13\.\s*Sources", l)), None)
    assert heading, "SPEC.md has no '## 13. Sources' heading at all" + CAUSE
    assert "HUMAN-REACHABLE ONLY" in heading.upper(), (
        f"SPEC.md §13's heading has lost its qualification:\n  {heading}\n\n"
        "The Drive and OneDrive entries resolve for Christoph and for nothing automated. "
        "This is the mechanism that cost Layer 0: a source that reads as live and is "
        "reachable by one person." + CAUSE
    )


def test_invariant_4a_mockups_carry_no_tradesignals_path() -> None:
    hits = []
    for p in sorted((SPECS / "mockups").glob("*.html")):
        if "tradesignals" in p.read_text(encoding="utf-8", errors="ignore"):
            hits.append(p.relative_to(REPO).as_posix())
    assert not hits, (
        "mockup sheets name `tradesignals`, an archived read-only repo:\n  "
        + "\n  ".join(hits)
        + "\n\nPaths should read `D:\\Dev\\momentum\\`. PROVENANCE.md shows these sheets are "
          "`authored`,\nso this is not carried-in wrongness — this project wrote a spec "
          "naming another project's path." + CAUSE
    )


@pytest.mark.parametrize("sheet", BANNERED_SHEETS)
def test_invariant_4b_bannered_sheets_keep_their_banner(sheet: str) -> None:
    """First element inside `<body>`, so it is on screen without scrolling. A
    warning that needs a second file opened is the failure this project has
    already paid for."""
    p = SPECS / "mockups" / sheet
    assert p.exists(), f"{sheet} is missing" + CAUSE
    text = p.read_text(encoding="utf-8")
    assert "NOT THE CURRENT DESIGN" in text, (
        f"{sheet} has lost its banner. It still renders a panel SPEC.md §3.1 resolves by "
        "deletion,\nso anyone opening it as reference gets exactly the artifact the core "
        "design conviction\nexists to prevent." + CAUSE
    )
    m = re.search(r"<body[^>]*>", text, re.I)
    assert m, f"{sheet} has no <body> tag"
    after = text[m.end():m.end() + 400]
    assert "NOT THE CURRENT DESIGN" in after, (
        f"{sheet}'s banner is no longer the first element inside <body>. It must be visible "
        "without scrolling." + CAUSE
    )


def test_the_cause_message_is_actually_attached() -> None:
    """Every assertion in this file must carry the re-supply diagnosis — that is
    the entire reason these checks are duplicated here rather than left to the
    tests that already cover them."""
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split('CAUSE = (', 1)[1].split(')', 1)[1]
    asserts = [l for l in body.splitlines() if l.strip().startswith("assert ")]
    assert len(asserts) >= 6, f"only {len(asserts)} assertions found; the file has lost checks"
    assert body.count("+ CAUSE") >= 6, (
        "an assertion in this file does not append CAUSE. A failure that does not name "
        "re-supply as the likely cause is just a duplicate of a test that already exists."
    )
