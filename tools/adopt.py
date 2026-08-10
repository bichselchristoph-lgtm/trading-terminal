"""The adoption gate (M001 §3).

Nothing enters this tree by copying. A candidate is placed in the drop folder
``D:\\Dev\\_adopt\\`` with a provenance companion and enters the repo only after
passing every check here. **A failed adoption leaves no trace in the tree** --
same rule as a failed watchlist drop.

    python tools/adopt.py --check <name>
    python tools/adopt.py --adopt <name> --into <dest-dir> --by <who>

``--check`` is a dry run: it reports every refusal that fires and writes nothing.
``--adopt`` re-runs every check and copies only if all of them pass.

The four refusals below have **no defaults and no inferred values**. That is the
whole point: the predecessor tree was assembled by carrying folders across
wholesale, and every defect it now has -- a README describing another repo, a
condition-code vocabulary invented by an unidentified codebase, mockups pointing
at D:\\tradesignals\\ -- is a value nobody was ever asked to supply.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ADOPT_DIR = Path("D:/Dev/_adopt")
LOG = REPO / "ADOPTION-LOG.md"

#: Directories whose contents do work, and therefore require a behavioural test.
CODE_TREES = ("core", "live", "harness", "tools")

#: Origins that a person must sign off on. An `authored` file can be adopted on
#: its merits; a predecessor's artifact needs someone to say why this project is
#: adopting it. The `by`-less status exists precisely because that decision was
#: never made last time.
ORIGINS_NEEDING_DECISION = ("imported", "unknown")

REQUIRED_PROVENANCE_FIELDS = ("source", "origin", "reason", "depends")


class Refusal(Exception):
    """One gate check said no. The message is the finding."""

    def __init__(self, number: int, message: str):
        self.number = number
        super().__init__(message)


@dataclass
class Provenance:
    source: str
    origin: str
    reason: str
    depends: str
    decision: str | None
    supersedes: str | None
    raw: str


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_provenance(path: Path) -> Provenance:
    """Read `<name>.provenance.md`. Every required field must be present AND
    non-empty -- a header with nothing under it is not an answer."""
    text = path.read_text(encoding="utf-8")
    fields: dict[str, str] = {}
    for key in REQUIRED_PROVENANCE_FIELDS + ("decision", "supersedes"):
        m = re.search(rf"^\s*{key}\s*:\s*(.+?)\s*$", text, re.I | re.M)
        if m:
            fields[key] = m.group(1).strip()

    missing = [k for k in REQUIRED_PROVENANCE_FIELDS
               if not fields.get(k) or fields[k].lower() in ("", "tbd", "unknown", "n/a", "-")]
    if missing:
        raise Refusal(
            1,
            f"provenance companion {path.name} is missing or empty for: {', '.join(missing)}.\n"
            f"       Every field needs a real value. There is no default and nothing is inferred --\n"
            f"       an inferred origin is exactly the value this gate exists to demand.",
        )
    return Provenance(
        source=fields["source"], origin=fields["origin"].lower(),
        reason=fields["reason"], depends=fields["depends"],
        decision=fields.get("decision"), supersedes=fields.get("supersedes"), raw=text,
    )


def check_1_provenance(name: str) -> Provenance:
    companion = ADOPT_DIR / f"{name}.provenance.md"
    if not companion.exists():
        raise Refusal(
            1,
            f"no provenance companion. Expected {companion}.\n"
            f"       It must name: source (path in the old repo), origin (from H9a's table),\n"
            f"       reason (why this project is adopting it), depends (what needs it).",
        )
    return parse_provenance(companion)


def check_2_behavioural_test(name: str, dest: Path) -> list[Path]:
    """A test that merely imports the module does not count. `regime_pull.py`
    passed import coverage while raising NameError on its first call."""
    top = dest.relative_to(REPO).parts[0] if dest != REPO else ""
    if top not in CODE_TREES:
        return []

    stem = Path(name).stem
    hits = [p for p in REPO.rglob("test_*.py") if stem in p.read_text(encoding="utf-8", errors="ignore")]
    if not hits:
        raise Refusal(
            2,
            f"no test references {stem!r}. Nothing enters {top}/ without at least one\n"
            f"       BEHAVIOURAL test -- one that fails if the file's behaviour changes.\n"
            f"       Import-smoke does not count: regime_pull.py passed import coverage\n"
            f"       while raising NameError on the first call.",
        )

    substantive = [p for p in hits if _has_behavioural_assertion(p, stem)]
    if not substantive:
        raise Refusal(
            2,
            f"the only tests referencing {stem!r} look like import-smoke:\n"
            f"       {', '.join(str(p.relative_to(REPO)) for p in hits)}\n"
            f"       A behavioural test asserts on a RESULT, not on the import succeeding.",
        )
    return substantive


def _has_behavioural_assertion(path: Path, stem: str) -> bool:
    """Crude but honest: a behavioural test asserts something other than that an
    import worked. We look for an assert that is not `assert <module>` and not a
    bare importlib check."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("assert "):
            continue
        body = s[len("assert "):].strip()
        if body in (stem, f"{stem} is not None") or body.startswith("importlib"):
            continue
        return True
    return False


def check_3_name_collision(name: str, dest: Path, candidate: Path, prov: "Provenance",
                           as_name: str | None = None, supersede: bool = False) -> None:
    target = dest / (as_name or Path(name).name)
    if not target.exists():
        return
    if sha256(target) == sha256(candidate):
        raise Refusal(
            3,
            f"{target.relative_to(REPO)} already exists with IDENTICAL bytes.\n"
            f"       Nothing to do. Not an overwrite, not an error -- just already adopted.",
        )

    rel = target.relative_to(REPO).as_posix()
    if supersede:
        # The one legitimate collision: a NEW VERSION of a file already adopted.
        # It is not a hole in refusal 3 -- it still refuses unless the operator
        # asks for it explicitly AND the companion names the exact path being
        # replaced. What it removes is the incentive to delete the old file to
        # get past the gate, which is how a gate acquires a real hole.
        if not prov.supersedes:
            raise Refusal(
                3,
                f"--supersede was passed but {candidate.name}.provenance.md has no `supersedes:` line.\n"
                f"       Add `supersedes: {rel}` naming the exact file this replaces.\n"
                f"       A supersession that does not say what it supersedes is an overwrite.",
            )
        if prov.supersedes.strip().strip("`") != rel:
            raise Refusal(
                3,
                f"companion says `supersedes: {prov.supersedes}` but this adoption targets `{rel}`.\n"
                f"       Refusing on the mismatch rather than trusting the flag.",
            )
        return
    raise Refusal(
        3,
        f"{target.relative_to(REPO)} already exists with DIFFERENT bytes.\n"
        f"       existing sha256 {sha256(target)[:16]}...\n"
        f"       candidate sha256 {sha256(candidate)[:16]}...\n"
        f"       Refusing. Never silently overwrite; never auto-rename.\n"
        f"       If this is a NEW VERSION of an adopted file, that is a supersession:\n"
        f"       add `supersedes: {rel}` to the companion and re-run with --supersede.\n"
        f"       Do NOT delete the existing file to get past this.",
    )


def check_4_origin_decision(prov: Provenance) -> None:
    if prov.origin not in ORIGINS_NEEDING_DECISION:
        return
    if prov.decision and len(prov.decision) > 20:
        return
    raise Refusal(
        4,
        f"origin is {prov.origin!r}, which needs an explicit adoption decision.\n"
        f"       Add a `decision:` line to the provenance companion saying, in Christoph's\n"
        f"       words, why this project is adopting a predecessor's artifact.\n"
        f"       An `authored` file can be adopted on its merits. This one cannot.",
    )


def run_checks(name: str, dest: Path, as_name: str | None = None,
               supersede: bool = False) -> tuple[Provenance, list[Path], Path]:
    candidate = ADOPT_DIR / name
    if not candidate.exists():
        raise Refusal(0, f"candidate {candidate} does not exist. Drop it in {ADOPT_DIR} first.")
    prov = check_1_provenance(name)
    check_4_origin_decision(prov)
    tests = check_2_behavioural_test(name, dest)
    check_3_name_collision(name, dest, candidate, prov, as_name, supersede)
    return prov, tests, candidate


def mark_superseded(old_rel: str, new_name: str) -> None:
    """Annotate the row being replaced. Both rows stay: the log is a history
    of what was adopted, and deleting the old row would erase the fact that a
    different version was once in the tree."""
    text = LOG.read_text(encoding="utf-8")
    out = []
    for line in text.splitlines():
        if line.startswith("| ") and f"`{old_rel}`" in line and "SUPERSEDED" not in line:
            line = line.rstrip()[:-1].rstrip() + f" — **SUPERSEDED** {date.today().isoformat()} |"
        out.append(line)
    LOG.write_text("\n".join(out) + "\n", encoding="utf-8")


def append_log_row(name: str, dest: Path, prov: Provenance, tests: list[Path], by: str,
                   landed: str | None = None) -> None:
    rel = (dest / (landed or Path(name).name)).relative_to(REPO).as_posix()
    test_col = ", ".join(t.relative_to(REPO).as_posix() for t in tests) or "n/a (not a code tree)"
    row = (f"| {date.today().isoformat()} | `{rel}` | `{prov.source}` | {prov.origin} | "
           f"{prov.reason} | `{test_col}` | {by} |\n")
    text = LOG.read_text(encoding="utf-8")
    marker = "| date | path in new tree | source path | origin | reason | test that covers it | adopted by |\n"
    sep = "|---|---|---|---|---|---|---|\n"
    if marker not in text:
        raise SystemExit("ADOPTION-LOG.md has no header row -- refusing to guess where to write.")
    text = text.replace(sep, sep + row, 1)
    LOG.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", metavar="NAME", help="dry run: report refusals, write nothing")
    g.add_argument("--adopt", metavar="NAME", help="run every check, then copy if all pass")
    p.add_argument("--into", help="destination directory, relative to the repo root")
    p.add_argument("--by", help="who is adopting this (required for --adopt)")
    p.add_argument("--as", dest="as_name", metavar="FILENAME",
                   help="land under this name instead of the candidate's own")
    p.add_argument("--supersede", action="store_true",
                   help="this is a NEW VERSION of an already-adopted file. Still refuses "
                        "unless the companion carries a matching `supersedes:` line.")
    args = p.parse_args(argv)

    name = args.check or args.adopt
    dest = (REPO / args.into).resolve() if args.into else REPO
    if args.adopt and not args.by:
        p.error("--adopt requires --by: an adoption with no name attached is how the last one happened")

    try:
        prov, tests, candidate = run_checks(name, dest, args.as_name, args.supersede)
    except Refusal as r:
        print(f"REFUSED (refusal {r.number}): {r}", file=sys.stderr)
        print("\nNothing was written. A failed adoption leaves no trace in the tree.", file=sys.stderr)
        return 1

    print(f"PASSES all four refusals: {name}")
    print(f"  source  : {prov.source}")
    print(f"  origin  : {prov.origin}")
    print(f"  reason  : {prov.reason}")
    print(f"  depends : {prov.depends}")
    print(f"  tests   : {', '.join(str(t.relative_to(REPO)) for t in tests) or '(not a code tree)'}")

    if args.check:
        print("\n--check: dry run, nothing written.")
        return 0

    dest.mkdir(parents=True, exist_ok=True)
    landed = args.as_name or Path(name).name
    if args.supersede:
        mark_superseded(prov.supersedes, landed)
    shutil.copy2(candidate, dest / landed)
    append_log_row(name, dest, prov, tests, args.by, landed)
    # `landed`, not the candidate's own name -- with --as those differ, and a
    # confirmation naming the wrong file is worse than none.
    print(f"\nADOPTED -> {(dest / landed).relative_to(REPO)}")
    print("ADOPTION-LOG.md updated. Commit the file and the log row together.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
