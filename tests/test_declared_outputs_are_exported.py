"""Every artifact the protocol OWES to the design session must sit inside a path
the export actually carries.

**053 Part 5, test 1.** The defect that produced this file: `verify.ps1` wrote
`verify-output.txt` to the repository root, and the export carries `handoff/`
and `christoph/done/` and nothing else. So the artifact `HANDOFF-PROTOCOL.md`
names as the evidence for `REVIEWED` was written where nothing could carry it,
and **`REVIEWED` was unreachable by its own definition** for every run between
`023` and `053`.

**This test is deliberately the GENERAL form of that defect.** A one-line path
change fixes the instance; a declared list plus this check fixes the class, and
answers *how many more of these are there* every time it runs.

**The export scope is DERIVED, never restated.** It is parsed out of
`export-handoff.ps1`, so a pair added or removed there changes what this test
allows without anybody remembering to update it. A second copy of the scope is
a copy that will diverge -- the same reasoning `config/sync.yaml` records for
having one copier and N configured pairs.
"""

from __future__ import annotations

import pathlib
import re

import pytest

yaml = pytest.importorskip("yaml")

REPO = pathlib.Path(__file__).resolve().parents[1]
OUTPUTS = REPO / "config" / "outputs.yaml"
EXPORT_SCRIPT = REPO / "export-handoff.ps1"

#: A `@{ Src = Join-Path $repo 'handoff'; ... }` row in the export script.
_SRC = re.compile(r"Src\s*=\s*Join-Path\s+\$repo\s+'([^']+)'")


def exported_roots() -> list[str]:
    """Repo-relative source folders the export carries, read from the script."""
    raw = _SRC.findall(EXPORT_SCRIPT.read_text(encoding="utf-8"))
    return [r.replace(chr(92), "/").strip("/") for r in raw]


def declared() -> list[dict]:
    return yaml.safe_load(OUTPUTS.read_text(encoding="utf-8"))["outputs"]


def test_the_export_script_yields_sources_at_all() -> None:
    """Guards every assertion below from passing on a parse that found nothing.

    A containment check against an empty list of roots fails loudly, but a
    containment check where the *declared* list came back empty passes silently
    -- and this file's whole subject is a check that was absent.
    """
    roots = exported_roots()
    assert roots, (
        f"no Src entries parsed out of {EXPORT_SCRIPT.name}; the regex has "
        "drifted from the script and this test is no longer checking anything.")
    assert declared(), f"no outputs declared in {OUTPUTS}"


def test_every_declared_output_is_inside_an_exported_path() -> None:
    roots = exported_roots()
    bad = []
    for entry in declared():
        path = entry["path"].replace(chr(92), "/").strip("/")
        if not any(path == r or path.startswith(r + "/") for r in roots):
            bad.append(f"  {entry['id']:<18} {entry['path']}")

    assert not bad, (
        "these artifacts are declared as owed to the design session but sit "
        "outside every exported path, so nothing carries them:" + chr(10)
        + chr(10).join(bad) + chr(10) + chr(10)
        + "exported roots, read from " + EXPORT_SCRIPT.name + ": "
        + ", ".join(roots) + chr(10)
        + "**This FAILS, it does not warn.** An artifact the protocol owes and "
          "the export cannot carry is a silent hole: the file is written, the "
          "script exits 0, and the gap shows only if somebody compares two "
          "documents nobody reads together. That is exactly how "
          "verify-output.txt sat at the repository root from 023 to 053 while "
          "REVIEWED was unreachable by its own definition." + chr(10)
        + "Fix by moving the artifact inside an exported path, or by moving it "
          "to `exclusions:` WITH A REASON -- never by deleting the entry.")


def test_exclusions_all_carry_a_reason() -> None:
    """An exclusion without a reason is an allowlist entry wearing a disguise."""
    data = yaml.safe_load(OUTPUTS.read_text(encoding="utf-8"))
    for entry in data.get("exclusions", []):
        assert entry.get("reason", "").strip(), (
            f"{entry.get('path')} is excluded from the export with no reason "
            "recorded. **The reason is the whole value of the exclusion** -- "
            "without it the next reader cannot tell a considered decision from "
            "an oversight, and will 'fix' it.")
