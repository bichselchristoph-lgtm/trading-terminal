"""Copy files from a Drive-sync folder into the repo. One way, additive, never overwrites.

026 (and 025's pair, configured but not yet exercised).

THE ONE RULE THAT MATTERS is the third row:

    not in the destination      -> copy it, and NAME it in the report
    present and byte-identical  -> do nothing. The normal case on a re-run
    present and DIFFERENT       -> do not overwrite. Report and stop

**Why immutability, for a task file as much as for a snapshot.** `Do inbox 012`
resolves a path by name and done-notes cite paths, so a task file that changes
after it was handed off breaks a reference another party is already holding --
and Claude Code may have already read the old one. Silently replacing it would
mean two parties acting on two different documents while both believed they had
the same one.

**Compared on CONTENT, never on mtime.** Drive rewrites modification times on
files whose bytes never changed; a re-sync or a client reinstall is enough. An
mtime comparison would report a change every time Drive touched the folder, and
the real changes would drown in it.

**One way.** Nothing is written to, deleted from or renamed in the source. The
tool hashes the whole source folder before and after its run and says so.

Usage:
    python tools/sync_from_drive.py               # every configured pair
    python tools/sync_from_drive.py --pair handoff_inbox
"""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import sys
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

REPO = Path(__file__).resolve().parents[1]
CONFIG = REPO / "config" / "sync.yaml"

#: 043 part 2, and it is `037`'s mechanism rather than a parallel one.
#:
#: **At the repository ROOT, outside every source and every destination.** A run
#: record that only exists where the copy lands cannot report a failure to reach
#: there -- which is precisely the failure this file is for.
#:
#: **Two record files, not one shared with the export, and that was a judgement
#: call 043 left open.** The reasons, in order of weight:
#:
#: 1. **The writers are in two languages.** `export-handoff.ps1` is PowerShell
#:    and this is Python. One file means two independent implementations of the
#:    same write-and-parse contract, which is the argument `config/sync.yaml`'s
#:    own header makes about copiers: two copies WILL diverge.
#: 2. **A shared file is a shared failure mode.** The export writes its record
#:    whole, with `Set-Content`. A Python writer would have to read-modify-write
#:    around it, and a crash mid-write would destroy the OTHER copier's record --
#:    in the one artifact whose entire job is surviving a crash.
#: 3. `verify.ps1` reading two files instead of one is cheap; it already reads
#:    two Drive manifests side by side.
RUN_RECORD = REPO / "sync-run-record.md"

#: The fields are at COLUMN ZERO and must stay there. **`037` indented its own
#: fields into a markdown code block, so `^last_success` never matched and every
#: failed run silently reset it to `never`** -- a fix that reintroduced its own
#: bug inside itself, found by executing the refusal rather than by reading it.
_RECORD_TEMPLATE = """# tools/sync_from_drive.py -- run record

**Not a report and not a manifest.** It answers one question: *did the inbound
sync run, and did it work.* Written on EVERY invocation, before the copy and
again after, so a run killed mid-copy leaves `last_attempt` moved and
`last_success` stale -- which is exactly the signature to look for.

Deliberately at the repository root, outside every configured source and
destination. A run record inside the destination cannot report a failure to
reach the destination.

The companion for the OUTBOUND direction is `export-run-record.md`. They are
two files on purpose -- see `RUN_RECORD` in `tools/sync_from_drive.py`.

`tests/test_sync_run_record.py` goes red if this file stops existing or stops
parsing.

**056: `refused` is a MACHINE-READABLE count, per pair, not a sentence.** The
`outcome` line below stays exactly as it is -- it is prose for Christoph and
for `verify.ps1` section 6, and the two zero-cases (`up to date` vs `REFUSED`)
must keep reading differently. `refused` exists because `outcome` prints the
same "files refused" condition two different ways depending on whether
anything else copied in the same run, and a test that matches one wording is
one rewording away from going false-green again -- `tests/test_inbound_run_
record_has_no_conflicts.py` reads THIS field and ignores the prose entirely.
Zero is written explicitly, per pair -- an absent field is never read as zero.

The four fields below are at COLUMN ZERO. **The reader below also tolerates
leading whitespace, and BOTH halves are deliberate** -- see `_FIELD`.

last_attempt : {attempt}

last_success : {success}

outcome      : {outcome}

refused      : {refused}
"""

#: **`^\s*`, not `^`. This is `037`'s remedy, copied deliberately rather than
#: re-derived.**
#:
#: `037` indented these fields four spaces so they would render as a markdown
#: code block, while its reader anchored on a bare `^` -- so `last_success`
#: never matched, and every failed run read the previous success as `never` and
#: wrote that back. **The record silently forgot every success it had ever had,
#: and it looked perfectly fine to a reader.**
#:
#: `037` fixed it with BELT AND BRACES and said so in as many words: *"The
#: fields are now at column zero AND the anchor tolerates whitespace; either
#: alone would be enough, which is the point."* This file keeps both halves for
#: the same reason. **The first cut of 043 kept only the column-zero half and
#: pinned the intolerance as a test** -- which would have left the inbound
#: record one reformat away from the outbound record's original bug, with a
#: green suite, and with the two records' parsers disagreeing about the same
#: format. Two implementations of one contract that differ in their strictness
#: is the divergence `config/sync.yaml`'s own header warns about.
_FIELD = r"(?m)^\s*{name}\s*:\s*(.+?)\s*$"


def read_field(name: str, path: Optional[Path] = None) -> str:
    """One field out of the record. `never` when the file or the field is absent.

    **Absent and unparsable deliberately answer the same way**, because both
    mean *no evidence this ever succeeded*. What must NOT reach that branch is a
    field that is present and merely indented -- that is `037`'s defect, and
    `_FIELD` tolerates it rather than treating it as absence.
    """
    p = path or RUN_RECORD
    if not p.is_file():
        return "never"
    m = re.search(_FIELD.format(name=name), p.read_text(encoding="utf-8"))
    return m.group(1).strip() if m else "never"


def write_record(*, attempt: str, success: str, outcome: str, refused: str,
                 path: Optional[Path] = None) -> None:
    p = path or RUN_RECORD
    p.write_text(_RECORD_TEMPLATE.format(attempt=attempt, success=success,
                                         outcome=outcome, refused=refused),
                 encoding="utf-8")


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


#: `NNN-for-code-*.md`. The convention exists so the AUDIENCE is visible before
#: the file is opened.
CONVENTION = re.compile(r"^(?P<num>\d{3})-for-code-.+\.md$")
#: Leading number, for collision detection. Deliberately looser than CONVENTION:
#: a file that breaks the convention still has a number that can collide.
LEADING_NUM = re.compile(r"^(?P<num>\d{3})\b")

#: 069 Part A. The leading id TOKEN, whole -- everything before the first
#: hyphen, letter suffix included. Deliberately not `LEADING_NUM`: `035` and
#: `035a` are different tasks (`NOW.md`'s own `superseded` line lists them
#: separately), so a suppression keyed on the bare digits would let `035a`
#: in `christoph/done/` wrongly suppress a live `035` still in Drive.
LEADING_ID = re.compile(r"^([^-]+)-")


def _leading_id(name: str) -> Optional[str]:
    m = LEADING_ID.match(name)
    return m.group(1) if m else None


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def folder_digest(folder: Path, pattern: str) -> dict[str, str]:
    """Every file's hash, for the before/after comparison that proves one-way."""
    if not folder.is_dir():
        return {}
    return {p.name: sha256(p) for p in sorted(folder.glob(pattern)) if p.is_file()}


@dataclass
class PairResult:
    pair_id: str
    source: Path
    dest: Path
    reachable: bool = True
    #: 043 part 2. **A destination that cannot be created is a DIFFERENT failure
    #: from a source that is not there** -- one is a broken Drive mount, the
    #: other a broken repo path -- and before 043 it was not a failure at all:
    #: `dest.mkdir()` raised `FileNotFoundError` and the tool died with a
    #: traceback. It exited non-zero only because an unhandled exception happens
    #: to exit 1, which is luck rather than a contract.
    dest_reachable: bool = True
    copied: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    differing: list[tuple[str, str, str]] = field(default_factory=list)
    off_convention: list[str] = field(default_factory=list)
    #: (arriving, other, origin) -- origin distinguishes a clash with a file
    #: that was already in the destination from one with a file THIS RUN copied.
    collisions: list[tuple[str, str, str]] = field(default_factory=list)
    source_mutated: list[str] = field(default_factory=list)
    considered: int = 0
    #: 069 Part A. `checks: [suppress_retired]` only. Id tokens of source files
    #: NOT copied because that token is already present in the pair's sibling
    #: `done/` directory -- i.e. genuinely retired, not merely missing.
    suppressed: list[str] = field(default_factory=list)
    #: Set instead of `suppressed` being empty, when the sibling `done/`
    #: directory could not be read at all (missing, permission error, any
    #: reason) -- fail CLOSED toward copying everything rather than silently
    #: reading "cannot tell" as "nothing is retired". Distinct from `suppressed
    #: == []`, which means "read fine, nothing retired yet".
    retirement_check_unreadable: Optional[str] = None

    @property
    def refused_differing(self) -> bool:
        """A file present under the same name with different bytes. Refused,
        never overwritten -- a handed-off file that changes breaks a reference
        another party already holds."""
        return bool(self.differing)

    @property
    def refused_count(self) -> int:
        """056: the same count `headline()` computes inline for its `N REFUSED`
        wording (line ~225), exposed here so the run record can carry it as a
        MACHINE-READABLE field instead of only as prose. Two refusal shapes,
        one count: a same-name file with different bytes, and a number
        collision -- neither is ever copied."""
        return len(self.collisions) + len(self.differing)

    @property
    def blocked(self) -> bool:
        """Anything a person must look at before this pair is trustworthy."""
        return bool(self.differing or self.collisions or self.source_mutated
                    or not self.reachable or not self.dest_reachable)

    def headline(self) -> str:
        """Three outcomes that MUST NOT read alike.

        `A task that prints nothing when it succeeds prints nothing when it
        fails.` The two zero-cases are different facts and get different words.

        **Refinement on the task text, stated rather than slipped in:** 026
        writes the failure line as `source folder empty or unreachable`. Those
        are also two different facts -- an empty folder is a working pipeline
        with nothing to send, a missing one is a broken path or an unmounted
        Drive -- so they are printed separately, on the task's own principle.
        """
        if not self.reachable:
            return f"{self.pair_id}: 0 new · source folder UNREACHABLE · {self.source}"
        if not self.dest_reachable:
            return f"{self.pair_id}: 0 new · destination UNREACHABLE · {self.dest}"
        if self.considered == 0:
            return f"{self.pair_id}: 0 new · source folder EMPTY · {self.source}"

        # 069 Part A. Composed once, prefixed onto every shape below, so the
        # four report lines this exists for -- normal, N suppressed, sibling
        # done/ unreadable, source unreachable (already its own branch above)
        # -- cannot drift out of sync with each other by being written twice.
        if self.retirement_check_unreadable is not None:
            suppression = f"{self.retirement_check_unreadable} — nothing suppressed · "
        elif self.suppressed:
            suppression = (f"{len(self.suppressed)} suppressed "
                          f"({' '.join(sorted(self.suppressed))}) · ")
        else:
            suppression = ""

        if not self.copied and (self.collisions or self.differing):
            # **043: a refused file is its own outcome and must NOT read as `up
            # to date`.** Before this, a run whose only event was a refusal
            # printed the same headline as a run where everything was already in
            # place -- and the `035` collision made the copier exit 1 on every
            # run for two days under a headline that said nothing was wrong.
            n = len(self.collisions) + len(self.differing)
            return (f"{self.pair_id}: 0 new · {suppression}{n} REFUSED · "
                    f"{len(self.unchanged)} unchanged")
        if not self.copied and not self.differing:
            return (f"{self.pair_id}: 0 new · {suppression}up to date "
                    f"({len(self.unchanged)} unchanged)")
        new = ", ".join(sorted(self.copied)) if self.copied else "-"
        return (f"{self.pair_id}: {len(self.copied)} new · {suppression}{new} · "
                f"{len(self.differing)} differing")


def sync_pair(pair: dict, dry_run: bool = False) -> PairResult:
    source = Path(pair["from"])
    dest = Path(pair["to"])
    pattern = pair.get("glob", "*.md")
    checks = set(pair.get("checks") or [])

    r = PairResult(pair_id=pair["id"], source=source, dest=dest)

    if not source.is_dir():
        r.reachable = False
        return r

    before = folder_digest(source, pattern)

    try:
        dest.mkdir(parents=True, exist_ok=True)
    except OSError:
        # **A named outcome, not a traceback** (043 part 2). The record is still
        # written by the caller, which is the whole point: a copier that dies
        # before recording anything is indistinguishable from one that never ran.
        r.dest_reachable = False
        return r
    existing = {p.name: p for p in dest.glob(pattern) if p.is_file()}

    # 069 Part A. `christoph/open/` is copy-verify-retire: the file leaves the
    # DESTINATION when it is done, and the Drive SOURCE still holds it -- so
    # `not in the destination -> copy it` resurrects every retired item,
    # forever. `checks: [suppress_retired]` (config/sync.yaml, this pair only)
    # opts a pair into reading its sibling `done/` directory and refusing to
    # copy a source file whose leading id token is already retired there.
    #
    # FAIL CLOSED TOWARD COPYING. `done_ids is None` means "could not
    # determine what is retired" -- missing directory, permission error, any
    # reason -- and the loop below suppresses nothing in that case. A
    # resurrected retired item is annoying and visible; a suppressed live one
    # is invisible, and this project fails toward the annoying one.
    done_ids: Optional[set[str]] = None
    if "suppress_retired" in checks:
        done_dir = dest.parent / "done"
        try:
            done_names = [p.name for p in done_dir.iterdir() if p.is_file()]
        except OSError:
            r.retirement_check_unreadable = f"{done_dir} not readable"
        else:
            done_ids = {tok for tok in (_leading_id(n) for n in done_names)
                       if tok is not None}

    # Number -> (filename, origin), for the collision check. Seeded from the
    # DESTINATION, because that is where a reference someone holds points, and
    # then UPDATED AS FILES ARE COPIED.
    #
    # 027 part 3. Seeding it once and never updating it was faithful to 026's
    # text -- which describes the check against "an existing inbox file" -- and
    # left a reachable gap: two ARRIVING files sharing a number, neither in the
    # destination, were both copied silently. That is the same failure the check
    # exists to catch, and it is the likelier one: the design session assigns
    # numbers by reading the inbox at a moment, Drive introduces a gap between
    # reading and landing, and two files written in one sitting land together.
    by_number: dict[str, tuple[str, str]] = {}
    for name in existing:
        m = LEADING_NUM.match(name)
        if m:
            by_number.setdefault(m.group("num"), (name, "already in destination"))

    for src in sorted(source.glob(pattern)):
        if not src.is_file():
            continue
        r.considered += 1
        name = src.name

        if done_ids is not None:
            token = _leading_id(name)
            if token is not None and token in done_ids:
                # Genuinely retired, not merely missing from the destination --
                # a distinct fact from "not in the destination" and reported as
                # one. Never copied, and not counted as `off_convention` or any
                # other flag below; it is suppressed, full stop.
                r.suppressed.append(token)
                continue

        if "filename_convention" in checks and not CONVENTION.match(name):
            # COPIED ANYWAY. The design session may have had a reason, and a
            # refused task file is a task nobody sees. Flagged, not blocked.
            r.off_convention.append(name)

        if name in existing:
            if sha256(src) == sha256(existing[name]):
                r.unchanged.append(name)
            else:
                r.differing.append((name, sha256(src), sha256(existing[name])))
            continue

        number = None
        if "number_collision" in checks:
            m = LEADING_NUM.match(name)
            number = m.group("num") if m else None
            if number and number in by_number:
                # Copy NEITHER of the ones still to come. Numbers have collided
                # three times here.
                #
                # When the clash is with a file THIS RUN copied, that first file
                # is already placed -- and it stays. **Nothing this tool has
                # written is removed by this tool.** The report says which case
                # it is, in those words, because "already in destination" and
                # "copied by this run" need different responses from a person.
                other, origin = by_number[number]
                r.collisions.append((name, other, origin))
                continue

        if not dry_run:
            shutil.copy2(src, dest / name)
        r.copied.append(name)
        if number:
            by_number.setdefault(number, (name, "copied by this run"))

    after = folder_digest(source, pattern)
    if before != after:
        changed = sorted(set(before) ^ set(after)) or [
            k for k in before if after.get(k) != before[k]]
        r.source_mutated = changed

    return r


def render(results: list[PairResult]) -> list[str]:
    out: list[str] = []
    for r in results:
        out.append(r.headline())

        for name, src_hash, dst_hash in r.differing:
            out.append(f"  !! DIFFERS, NOT OVERWRITTEN: {name}")
            out.append(f"       source {src_hash}")
            out.append(f"       repo   {dst_hash}")
            out.append("       The repo copy is untouched. A handed-off file that changes "
                       "breaks a reference")
            out.append("       another party holds, and may already have been read. "
                       "Resolve by hand.")

        for arriving, other, origin in r.collisions:
            out.append(f"  !! NUMBER COLLISION, NOT COPIED: {arriving}")
            out.append(f"       clashes with {other} ({origin})")
            if origin == "copied by this run":
                out.append("       That first file IS placed and stays -- nothing this tool "
                           "wrote is removed by it.")

        if r.off_convention:
            out.append(f"  ~  off-convention names (copied anyway): "
                       f"{', '.join(sorted(r.off_convention))}")
            out.append("       expected NNN-for-code-*.md")

        if r.source_mutated:
            out.append(f"  !! SOURCE FOLDER CHANGED DURING THE RUN: "
                       f"{', '.join(r.source_mutated)}")
            out.append("       This tool never writes to the source. Something else did, "
                       "or Drive synced mid-run.")
        elif r.reachable and r.dest_reachable:
            # **Gated on the DESTINATION too.** On a destination failure the
            # source is never hashed, and this line printed
            # `0 files hashed before and after` -- a clean bill of health for a
            # check that did not run. That is the `survived_window: true` shape.
            out.append(f"  ok source folder byte-for-byte unchanged "
                       f"({r.considered} files hashed before and after)")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pair", action="append", help="pair id; repeatable. Default: all")
    ap.add_argument("--config", type=Path, default=CONFIG)
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would be copied and copy nothing")
    ap.add_argument("--record", type=Path, default=None,
                    help="run-record path; defaults to sync-run-record.md at "
                         "the repo root. For tests, never for normal use.")
    args = ap.parse_args(argv)

    # The report format 026 specifies uses `·`, and a Windows console on cp1252
    # renders that as a replacement box -- the same mojibake that made the
    # credential-scan header unreadable under 022. Reconfiguring the stream
    # keeps the SPECIFIED format instead of quietly substituting ASCII for it.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    pairs = config["pairs"]
    if args.pair:
        wanted = set(args.pair)
        unknown = wanted - {p["id"] for p in pairs}
        if unknown:
            print(f"unknown pair id(s): {', '.join(sorted(unknown))}", file=sys.stderr)
            return 2
        pairs = [p for p in pairs if p["id"] in wanted]

    # **Written BEFORE the attempt, and again after** (043 part 2, reusing
    # `037`'s mechanism). A run killed mid-copy leaves `last_attempt` moved and
    # `last_success` stale, which is the signature to look for. The previous
    # success is read first, so a failing run carries it forward instead of
    # resetting it -- that reset is the bug `037` shipped inside its own fix.
    # **A run against a NON-DEFAULT config never touches the repository's
    # record**, and this is a fail-safe rather than a convention the tests have
    # to remember.
    #
    # Found by reading `verify.ps1` section 6 after it went in: the outcome line
    # read `t: 1 new · 031-for-code-thing.md` — **a pytest fixture's filename, in
    # the tracked record, describing a copy into a temp directory.** Every test
    # that drives `main()` with its own config was overwriting the one artifact
    # whose entire job is saying when the real sync last worked.
    #
    # That is this task's own subject: an instrument reporting on everything
    # except itself. Fixing it by passing `--record` from each test would work
    # until somebody wrote the next test.
    if args.record:
        record = args.record
    elif args.config.resolve() != CONFIG.resolve():
        record = args.config.parent / "sync-run-record.md"
    else:
        record = RUN_RECORD
    previous_success = read_field("last_success", record)
    attempt = _now()
    if not args.dry_run:
        # `refused` is deliberately NOT "0" here -- tenet 2, an absent or
        # unknown count must never read as zero, and this write happens before
        # any pair has been examined.
        write_record(attempt=attempt, success=previous_success,
                     outcome="RUNNING - this run has not finished",
                     refused="pending", path=record)

    results = [sync_pair(p, dry_run=args.dry_run) for p in pairs]
    for line in render(results):
        print(line)

    blocked = any(r.blocked for r in results)
    if not args.dry_run:
        # **Both failure paths still write the record.** A copier that dies
        # before recording anything is indistinguishable from one that never
        # ran, and "never ran" is the thing this file exists to make visible.
        write_record(attempt=attempt,
                     success=previous_success if blocked else attempt,
                     outcome=" | ".join(r.headline() for r in results),
                     refused=" | ".join(f"{r.pair_id}: {r.refused_count}"
                                        for r in results),
                     path=record)

    # NON-ZERO when a person must look. A scheduled run that reports a collision
    # and exits 0 is a report nobody reads. An off-convention name alone is NOT
    # blocking -- it is flagged and the file is copied.
    return 1 if blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
