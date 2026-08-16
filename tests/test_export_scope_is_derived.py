"""The export's scope is derived from its sources, never from a forbidden-list.

020 part 2. The prohibition -- no ``docs/specs/``, no ``records/``, no
``christoph/open/``, no code -- is STRUCTURAL: it holds because those folders are
not named as sources, not because anything checks for them by name.

A forbidden-list is the alternative and it is worse. It grows into a hiding
place: every folder nobody thought to add is implicitly permitted, and the list
looks more thorough the longer it gets. This project has ruled that three times.
So these tests ask one question only -- *does each destination contain anything
that is not in its source?* -- and derive the answer from the source itself.

``docs/specs/`` is the one that matters. Drive held the specs once and Layer 0
was fully specified and never built because of it.

These tests are SKIPPED when the Drive root is absent rather than failed. The
export cannot have leaked into a folder that does not exist, and this suite must
stay green on a machine that is not Christoph's.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "export-handoff.ps1"
DRIVE_ROOT = Path("D:/claude-googledrive-sync")

#: Parsed from the script rather than restated here. A second copy of the source
#: list would drift from the first, and the drift would be invisible -- the tests
#: would keep passing against a table the script no longer uses.
_EXPORT_ROW = re.compile(
    r"@\{\s*Src\s*=\s*Join-Path\s+\$repo\s+'(?P<src>[^']+)'\s*;"
    r"\s*Dst\s*=\s*Join-Path\s+\$driveRoot\s+'(?P<dst>[^']+)'\s*;"
    r"\s*Recurse\s*=\s*\$(?P<recurse>true|false)"
)


def exports() -> list[tuple[Path, Path, bool]]:
    text = SCRIPT.read_text(encoding="utf-8")
    rows = [
        (REPO / m.group("src").replace("\\", "/"),
         DRIVE_ROOT / m.group("dst"),
         m.group("recurse") == "true")
        for m in _EXPORT_ROW.finditer(text)
    ]
    assert rows, (
        "no export rows parsed out of export-handoff.ps1. Either the $exports "
        "table was reformatted or it is gone. Either way these tests are now "
        "checking nothing, which is the failure mode they exist to prevent."
    )
    return rows


def source_relpaths(src: Path, recurse: bool) -> set[str]:
    if not src.exists():
        return set()
    it = src.rglob("*.md") if recurse else src.glob("*.md")
    return {p.relative_to(src).as_posix() for p in it if p.is_file()}


def test_the_export_script_exists() -> None:
    assert SCRIPT.exists(), (
        "export-handoff.ps1 is missing. Without it these tests pass vacuously "
        "while nothing is exported at all."
    )


def test_exactly_three_destinations() -> None:
    """Widening the export must be a visible edit, not a quiet one. A fourth
    destination here means somebody added a source, and that is a decision.

    054 Part 3 / 043 Part 2 widened this deliberately from two to three:
    handoff/questions/ -> momentum-code-questions, joining the recursive
    handoff/ pair rather than replacing it. The two overlap ON PURPOSE --
    043 asked for the questions folder by name, so a question file now
    travels twice, once inside momentum-code-handoff/questions/ and once at
    momentum-code-questions/ directly."""
    rows = exports()
    assert len(rows) == 3, f"expected 3 export rows, parsed {len(rows)}: {rows}"
    leaves = sorted(dst.name for _, dst, _ in rows)
    assert leaves == [
        "momentum-christoph-done", "momentum-code-handoff", "momentum-code-questions",
    ], leaves


def test_sources_are_the_two_folders_and_nothing_else() -> None:
    """The structural prohibition, stated as an assertion about the sources
    rather than as a list of what is banned."""
    srcs = sorted(str(src.relative_to(REPO)).replace("\\", "/") for src, _, _ in exports())
    assert srcs == ["christoph/done", "handoff", "handoff/questions"], (
        f"the export's sources are now {srcs}. Every folder not in this list is "
        "excluded BECAUSE it is not in this list -- there is no forbidden-list "
        "backing this up, deliberately."
    )


def test_christoph_open_is_not_a_source() -> None:
    """Its own test because it is the obvious 'improvement'.

    ``christoph/open/`` answers *what is still outstanding* by being empty. An
    additive export cannot represent empty, so a retired file would sit in the
    mirror forever saying the exact opposite of what the folder exists to say --
    and it would say it convincingly. Putting it in Drive needs a mirroring
    export that deletes. That is a separate decision, not a fix to this one.
    """
    for src, _, _ in exports():
        assert src.name != "open", (
            "christoph/open/ has become an export source. An additive export "
            "cannot represent an empty folder, and empty is the only answer that "
            "folder ever gives."
        )


@pytest.mark.parametrize("index", [0, 1])
def test_destination_contains_nothing_outside_its_source(index: int) -> None:
    """The rule, derived from the source rather than from a ban-list.

    The one permitted extra is the manifest this export writes, which exists only
    in the destination by design. It is exempted by NAME, computed from the
    destination folder, so a second stray file cannot hide behind the exemption.
    """
    src, dst, recurse = exports()[index]
    if not DRIVE_ROOT.exists():
        pytest.skip(f"{DRIVE_ROOT} not present -- nothing can have leaked into it")
    if not dst.exists():
        pytest.skip(f"{dst} not present -- export has not run on this machine")

    permitted = source_relpaths(src, recurse) | {f"MANIFEST-{dst.name}.md"}
    found = {p.relative_to(dst).as_posix() for p in dst.rglob("*") if p.is_file()}
    extra = sorted(found - permitted)
    assert not extra, (
        f"{dst} holds files that are not in {src}:\n  " + "\n  ".join(extra) +
        "\n\nThe export is additive and never deletes, so this is either a file "
        "that arrived by another route or a source file that was renamed. "
        "Neither is fixed by widening this test."
    )


def test_no_drive_path_is_tracked_by_git() -> None:
    """Nothing enters the tree except through the adoption gate.

    The export is one-way. If a Drive path ever appears in git, the mirror has
    become an input -- which is how a stale v1.0 spec walks back into the tree
    wearing the shape of current work.
    """
    out = subprocess.run(
        ["git", "ls-files", "-z"], cwd=REPO, capture_output=True, check=True
    ).stdout.decode("utf-8")
    tracked = [p for p in out.split("\0") if p]

    named = sorted(p for p in tracked if "claude-googledrive-sync" in p.lower())
    assert not named, f"tracked paths name the Drive mirror: {named}"

    # A symlink or junction under the repo could put a tracked path physically
    # inside the mirror without the string appearing in it. resolve() catches it.
    drive = DRIVE_ROOT.resolve() if DRIVE_ROOT.exists() else DRIVE_ROOT
    inside = sorted(
        p for p in tracked if drive in (REPO / p).resolve().parents
    )
    assert not inside, (
        f"these tracked paths resolve to somewhere under {drive}: {inside}. "
        "The export is one-way; a tracked file inside the mirror makes Drive an "
        "input to this repository."
    )


def test_the_script_never_deletes() -> None:
    """It deletes nothing, anywhere, ever -- in the tree or in Drive.

    Checked as text because there is no safe way to test the alternative
    empirically: a test that proves deletion works has already deleted something.
    """
    text = SCRIPT.read_text(encoding="utf-8")
    code = "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("#")
    )
    for verb in ("Remove-Item", "Clear-Content", "del ", "rmdir", "Remove-ItemProperty"):
        assert verb not in code, (
            f"export-handoff.ps1 contains {verb!r}. The export is additive: it "
            "never deletes, in either location. A deletion here reaches Drive, "
            "and a Drive deletion reaches every mirrored machine."
        )


def test_the_check_can_actually_fail() -> None:
    """A test that cannot fail proves nothing."""
    src, dst, recurse = exports()[0]
    permitted = source_relpaths(src, recurse) | {f"MANIFEST-{dst.name}.md"}
    assert "docs/specs/SPEC.md" not in permitted
    assert "MANIFEST.md" not in permitted, (
        "a bare MANIFEST.md is permitted. The manifests carry distinct names "
        "because the design session finds Drive files by searching filenames "
        "across the whole account."
    )
