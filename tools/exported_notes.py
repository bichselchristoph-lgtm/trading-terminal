"""Which `handoff/done/` notes are already exported — read from the export
manifest, never inferred from a number or a date. 068 Part C.

**Extracted here, not embedded in the test or in `verify.ps1`, so the SAME
answer decides "exported" in both places** — a test that skips a note the
count does not know about, or a count that includes one the test still fails
on, is a well-formed value answering a different question. Same reasoning as
`tools/waiting.py` and `tools/now.py`: logic that both a test and `verify.ps1`
need lives in one importable place, run directly by the test and invoked as a
subprocess by the shell script.

----

**Why a note that has been exported cannot simply be fixed.** `handoff/` is
copy-and-keep: nothing there is edited, because an edit puts the tracked copy
and the Drive copy out of byte-sync on bytes — the `040`/`043`/`052` condition
the inbound copier has refused on since 2026-08-15. `061` could add `bugs: []`
to its own note only because that note had not been exported yet; `058`'s has.

**So the guard yields instead of the archive.** A note already carried to
Drive is a record of what was true when it was written, and records are not
corrected. `exported_done_note_basenames()` answers *has this note left the
tree*, from the one place that answer is actually recorded — the export
manifest — so the exemption cannot be widened by anything short of an export
actually having happened.

**Fails closed.** If the manifest cannot be located or read,
`ExportManifestUnreadable` is raised rather than an empty set returned — an
empty set here would silently exempt nothing, but a scope check that reads a
gap as "nobody is exempt" **when it cannot see the exemption list at all**
would, on a future export failure, instead read as "everybody is exempt".
Refusing by name is the only shape that cannot decay into the second one.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EXPORT_SCRIPT = REPO / "export-handoff.ps1"
DONE = REPO / "handoff" / "done"

#: Mirrors `tests/test_donenote_bugs_block.py`'s own watermark. Defined once
#: here and imported there, so the two cannot drift into checking different
#: sets of notes.
FROM_TASK = 53

_NUM = re.compile(r"^(\d+)")
_FM = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.S)

#: `export-handoff.ps1`'s own `$driveRoot = '...'` line. Parsed rather than
#: restated, matching `verify.ps1` section 5's own approach to the same
#: script — a second hardcoded copy of a Drive path is how one goes stale.
_ROOT_RE = re.compile(r"\$driveRoot\s*=\s*'([^']+)'")
#: One `$exports` table entry: `Src = Join-Path $repo '<src>'; Dst = Join-Path
#: $driveRoot '<dst>'`. Only the `handoff` row is needed here.
_ROW_RE = re.compile(
    r"@\{\s*Src\s*=\s*Join-Path\s+\$repo\s+'([^']+)'\s*;\s*Dst\s*=\s*Join-Path\s+\$driveRoot\s+'([^']+)'"
)
#: A manifest table row: `` | `rel\path.md` | HASH | BYTES | ``.
_MANIFEST_ROW_RE = re.compile(r"^\|\s*`(?P<rel>[^`]+)`\s*\|", re.M)


class ExportManifestUnreadable(Exception):
    """Named, so a caller refuses rather than silently treating every note as
    not-yet-exported. 068: *"a scope check that fails open is worse than no
    scope check."*"""


def manifest_path() -> Path:
    if not EXPORT_SCRIPT.exists():
        raise ExportManifestUnreadable(f"{EXPORT_SCRIPT} does not exist")
    src = EXPORT_SCRIPT.read_text(encoding="utf-8")
    root_m = _ROOT_RE.search(src)
    if not root_m:
        raise ExportManifestUnreadable(
            f"could not find $driveRoot in {EXPORT_SCRIPT} -- the script was "
            "reformatted and this parser was not")
    drive_root = root_m.group(1)
    dest = next((m.group(2) for m in _ROW_RE.finditer(src)
                if m.group(1) == "handoff"), None)
    if dest is None:
        raise ExportManifestUnreadable(
            f"could not find the `handoff` export pair in {EXPORT_SCRIPT} -- "
            "the $exports table was reformatted and this parser was not")
    return Path(drive_root) / dest / f"MANIFEST-{dest}.md"


def exported_done_note_basenames() -> set[str]:
    """Basenames (e.g. `058-attach-latency-and-attaching-state.md`) of every
    `handoff/done/*.md` file the export manifest names — i.e. carried to
    Drive at least once. Raises `ExportManifestUnreadable` rather than
    returning an empty set on any failure to locate or parse the manifest."""
    manifest = manifest_path()
    if not manifest.exists():
        raise ExportManifestUnreadable(
            f"{manifest} does not exist -- the export has not run against "
            "this destination on this machine, or the mirror is absent")
    try:
        text = manifest.read_text(encoding="utf-8")
    except OSError as exc:
        raise ExportManifestUnreadable(f"{manifest}: {exc}") from exc
    out: set[str] = set()
    for m in _MANIFEST_ROW_RE.finditer(text):
        rel = m.group("rel").replace("\\", "/")
        if rel.startswith("done/"):
            out.add(rel.split("/")[-1])
    if not out:
        raise ExportManifestUnreadable(
            f"{manifest} parsed but named no `done/*.md` row -- the table "
            "shape changed and this parser was not updated with it")
    return out


def notes_in_scope() -> list[Path]:
    out = []
    for p in sorted(DONE.glob("*.md")):
        m = _NUM.match(p.name)
        if m and int(m.group(1)) >= FROM_TASK:
            out.append(p)
    return out


def skipped_for_export(yaml_module) -> list[tuple[Path, str]]:
    """Notes in scope, missing `bugs:`, and already exported — the exact set
    `test_donenote_bugs_block.py` treats as a named skip rather than a
    failure. `yaml_module` is passed in rather than imported here so this
    module has no hard dependency of its own on PyYAML being installed
    beyond what the caller already requires."""
    exported = exported_done_note_basenames()
    out: list[tuple[Path, str]] = []
    for p in notes_in_scope():
        if p.name not in exported:
            continue
        fm = _FM.match(p.read_text(encoding="utf-8"))
        if not fm:
            continue
        data = yaml_module.safe_load(fm.group(1)) or {}
        if "bugs" not in data:
            out.append((p, "exported before `bugs:` existed on this note; "
                            "handoff/ is copy-and-keep, so it is reported "
                            "here rather than edited"))
    return out


def main(argv: list[str] | None = None) -> int:
    """`verify.ps1`'s content signal. **Never a CANNOT-COMPUTE crash past this
    point** — a refusal here is still printed as one line, the same shape as
    every other section's failure-to-compute case."""
    try:
        import yaml
    except ImportError:
        print("CANNOT COMPUTE: PyYAML not installed")
        return 1
    try:
        skipped = skipped_for_export(yaml)
    except ExportManifestUnreadable as exc:
        print(f"CANNOT COMPUTE: {exc}")
        return 1
    print(f"done-notes exempted (already exported, missing bugs:)  {len(skipped)}")
    for p, reason in skipped:
        print(f"  {p.name} -- {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
