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
def _path_module():
    """Loaded BY PATH, not imported. `tests/` has no `__init__.py` — deliberately —
    so `from tests.test_regime_snapshot_path import ...` raises ModuleNotFoundError.
    Written that way first and caught immediately.

    `tests/test_regime_snapshot_path.py` is the single definition of the legacy
    string, the consumer-suffix set and the docstring stripper. **A second literal
    here would be a second occurrence of the very string this asserts is absent.**"""
    import importlib.util, sys
    src = Path(__file__).with_name("test_regime_snapshot_path.py")
    spec = importlib.util.spec_from_file_location("_legacy_src", src)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_legacy_src"] = mod
    spec.loader.exec_module(mod)
    return mod


def _legacy_path() -> str:
    return _path_module().FORBIDDEN


def _pointers_module():
    """Loaded BY PATH, for the same reason as `_path_module` above: `tests/` has
    no `__init__.py`. `test_spec_pointers.py` owns the definition of *how far
    into a file the STATUS header may be*; a second copy of that rule here would
    be a second place for it to drift."""
    import importlib.util, sys
    src = Path(__file__).with_name("test_spec_pointers.py")
    spec = importlib.util.spec_from_file_location("_pointers_src", src)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_pointers_src"] = mod
    spec.loader.exec_module(mod)
    return mod


EXEMPT_FROM_LEGACY_PATH = ("docs/specs/DRIVE-ARCHIVE-LIST.md",)
BANNERED_SHEETS = ("mockup-02-regime.html", "mockup-04-size-stage.html",
                   "mockup-05-live-context.html")

#: Invariant 5. The dev specs carrying 052's product-spec ruling. Each is a DEV
#: spec: `REGIME-PROMPT.md` (an instruction to a scheduled run) and
#: `HANDOFF-PROTOCOL.md` (protocol) are deliberately excluded, per 052.
DEV_SPECS_WITH_RULING = ("SPEC.md", "BUILD-PLAN.md", "RE-SUPPLY.md")

#: The load-bearing first line of that comment, not the whole block: a re-supply
#: that drops the ruling drops this line, while matching the whole block would go
#: red on a faithful copy that had merely been reflowed.
RULING_MARK = "DEV SPEC — authoritative for implementation."


def spec_docs() -> list[Path]:
    return sorted(SPECS.rglob("*.md"))


def test_invariant_1_every_spec_still_declares_a_status() -> None:
    """**The window skips a leading HTML comment, and nothing else.** 052 put a
    21-line ruling comment above the title of three dev specs; it renders as
    nothing, so the STATUS header is still the first thing on screen. See
    `test_spec_pointers.head`, which owns that rule and pins it."""
    head = _pointers_module().head
    missing = []
    for p in spec_docs():
        m = re.search(r"\*\*STATUS\*\*\s+(\w+)", head(p.read_text(encoding="utf-8")))
        if not m or m.group(1) not in VALID_STATUSES:
            missing.append(p.relative_to(REPO).as_posix())
    assert not missing, (
        "docs/specs files with no valid STATUS header in their first 10 lines:\n  "
        + "\n  ".join(missing) + CAUSE
    )


def test_invariant_5_dev_specs_keep_the_product_spec_ruling() -> None:
    """**The newest tree-side repair, and the one most likely to be dropped.**

    Ruled 2026-08-16 under 052: product behaviour is owned by the product spec
    set in Drive, and these documents are dev specs derived from it. The ruling
    lives in an HTML comment at the very top of each -- invisible when rendered,
    and therefore invisible to an author re-supplying the document from outside
    this tree, who will hand back a file that silently un-rules it.

    Without this assertion nothing in the tree would notice.
    """
    missing = []
    for name in DEV_SPECS_WITH_RULING:
        p = SPECS / name
        if not p.exists():
            missing.append(f"{name}: file is absent")
        elif RULING_MARK not in p.read_text(encoding="utf-8"):
            missing.append(f"docs/specs/{name}: no product-spec ruling comment")
    assert not missing, (
        "dev specs that have lost 052's product-spec ruling:\n  "
        + "\n  ".join(missing)
        + "\n\nThe comment is invisible when rendered, so an author re-supplying the "
          "document\ncannot see it and will not carry it. Re-apply the block from "
          "handoff/inbox/052-for-code-task-product-spec-pointer.md, Part 1." + CAUSE
    )


def test_invariant_2_no_legacy_snapshot_path_survives() -> None:
    """**RE-SCOPED TO THE CONSUMER, ratified 2026-08-13. The invariant was wrong,
    not the document.**

    It scanned every `.md` under `docs/specs/` for the legacy string. v1.8 of
    `REGIME-PROMPT.md` uses it six times **and is right to**: it instructs a
    scheduled cloud run that has no repo access, permanently, so
    `claude/regime-snapshots/` is that run's canonical write location
    (Christoph, 2026-08-13).

    Re-applying the old rule would have rewritten a live task's instructions to
    write somewhere it cannot reach — **a behaviour change to a running system,
    dressed as a mechanical repair.**

    **The question is now who READS the path, not whether the string appears.**
    Specs are prose: they instruct people and external runs, and read nothing.
    The consumer-side assertion — no repo-side code or config may point at the
    legacy path — lives in `tests/test_regime_snapshot_path.py`
    (`test_no_consumer_reads_the_legacy_snapshot_path`), which has no exemptions
    at all.

    **This test is kept and inverted rather than deleted**, for the same reason
    as the three flipped prompt invariants: the risk is a later supply putting
    the path somewhere a consumer reads it.
    """
    mod = _path_module()
    CONSUMER_SUFFIXES, code_only = mod.CONSUMER_SUFFIXES, mod.code_only

    legacy = _legacy_path()
    hits = [
        f"{p.relative_to(REPO).as_posix()}:{i}"
        for p in spec_docs()
        if p.suffix.lower() in CONSUMER_SUFFIXES
        for i, line in enumerate(code_only(p, p.read_text(encoding="utf-8")).splitlines(), 1)
        if legacy in line
    ]
    assert not hits, (
        f"the legacy path {legacy!r} appears in a CONSUMER under docs/specs/:\n  "
        + "\n  ".join(hits)
        + "\n\nProse may carry it — it instructs a run with no repo access. Code and config "
          "may not.\nThe canonical path for anything in this tree is `docs/regime-snapshots/`."
        + CAUSE
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
