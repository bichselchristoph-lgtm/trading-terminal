"""`core` depends on NEITHER side, and that is enforced rather than intended.

`CLAUDE.md` and `BUILD-PLAN.md` both state the rule; the predecessor enforced it
with `tests/test_import_boundaries.py`, **which has not been carried into this
tree.** So `core/` arrived under S010 with the rule written down and nothing
checking it — which is the shape of every defect this project has found.

This is the narrow half: **`core` imports no first-party module at all.** The
full boundary test — no edge between `harness` and `live`, and `harness`/`live`
importing `core` being permitted rather than required — is owed when those trees
exist. Recorded in S010's done-note rather than left implicit.

**Checked by parsing the AST, not by importing.** An import-time check would
pass on a module that reaches across lazily inside a function, and that is
exactly how the rule gets broken in practice.
"""
from __future__ import annotations

import ast
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CORE = REPO / "core"

#: The first-party trees. A `core` module naming any of these has crossed the
#: boundary, wherever in the file the import sits.
FIRST_PARTY = ("live", "harness", "tools", "core")


def core_modules() -> list[Path]:
    return [p for p in CORE.rglob("*.py") if "__pycache__" not in p.parts]


def imported_roots(tree: ast.AST) -> set[str]:
    """Every module root named by an import, **including inside functions.**"""
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            if node.level:                      # a relative import
                roots.add("core")
            elif node.module:
                roots.add(node.module.split(".")[0])
    return roots


def test_core_imports_no_first_party_module() -> None:
    offenders = []
    for p in core_modules():
        if p.parent.name == "tests":
            continue                            # tests may import what they test
        rel = p.relative_to(REPO).as_posix()
        roots = imported_roots(ast.parse(p.read_text(encoding="utf-8")))
        crossed = sorted(r for r in roots if r in FIRST_PARTY and r != "core")
        if crossed:
            offenders.append(f"{rel} imports {crossed}")
    assert not offenders, (
        "core reached into another tree:\n  " + "\n  ".join(offenders)
        + "\n\ncore depends on NEITHER side. A core that knows about live/ "
          "cannot be\nreused off the screen, and the dependency is one-way by "
          "design.")


def test_core_does_not_reach_sideways_within_itself_by_absolute_path() -> None:
    """A `core` module importing `core.x` absolutely still works, but it makes
    the package non-relocatable and hides the shape of the graph. Relative
    imports inside a package are the convention here."""
    offenders = []
    for p in core_modules():
        if p.parent.name == "tests":
            continue
        src = p.read_text(encoding="utf-8")
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, ast.ImportFrom) and node.module and \
                    node.module.split(".")[0] == "core" and not node.level:
                offenders.append(f"{p.relative_to(REPO).as_posix()}: from {node.module}")
    assert not offenders, "absolute intra-core imports:\n  " + "\n  ".join(offenders)


def test_the_full_boundary_test_is_owed_and_named() -> None:
    """**Guard against this file being mistaken for the whole rule.**

    The predecessor's `tests/test_import_boundaries.py` also forbade any edge
    between `harness` and `live`, and pinned that the harness takes core objects
    as parameters rather than importing them. Neither tree exists here yet, so
    that half cannot be written — and a test asserting it now would pass because
    its subject is absent, which is the vacuous pass S010 part 5 names.
    """
    assert not (REPO / "harness").exists(), (
        "harness/ now exists, so the harness<->live half of the boundary test "
        "is no longer vacuous. Write it — see momentum-harness/tests/"
        "test_import_boundaries.py for the shape it had.")
