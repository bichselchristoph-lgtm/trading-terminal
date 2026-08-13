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
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
CONFIG = REPO / "config" / "sync.yaml"

#: `NNN-for-code-*.md`. The convention exists so the AUDIENCE is visible before
#: the file is opened.
CONVENTION = re.compile(r"^(?P<num>\d{3})-for-code-.+\.md$")
#: Leading number, for collision detection. Deliberately looser than CONVENTION:
#: a file that breaks the convention still has a number that can collide.
LEADING_NUM = re.compile(r"^(?P<num>\d{3})\b")


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
    copied: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    differing: list[tuple[str, str, str]] = field(default_factory=list)
    off_convention: list[str] = field(default_factory=list)
    collisions: list[tuple[str, str]] = field(default_factory=list)
    source_mutated: list[str] = field(default_factory=list)
    considered: int = 0

    @property
    def blocked(self) -> bool:
        """Anything a person must look at before this pair is trustworthy."""
        return bool(self.differing or self.collisions or self.source_mutated
                    or not self.reachable)

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
        if self.considered == 0:
            return f"{self.pair_id}: 0 new · source folder EMPTY · {self.source}"
        if not self.copied and not self.differing:
            return f"{self.pair_id}: 0 new · up to date ({len(self.unchanged)} unchanged)"
        new = ", ".join(sorted(self.copied)) if self.copied else "-"
        return (f"{self.pair_id}: {len(self.copied)} new · {new} · "
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

    dest.mkdir(parents=True, exist_ok=True)
    existing = {p.name: p for p in dest.glob(pattern) if p.is_file()}

    # Number -> existing filename, for the collision check. Built from the
    # DESTINATION, because that is where a reference someone holds points.
    by_number: dict[str, str] = {}
    for name in existing:
        m = LEADING_NUM.match(name)
        if m:
            by_number.setdefault(m.group("num"), name)

    for src in sorted(source.glob(pattern)):
        if not src.is_file():
            continue
        r.considered += 1
        name = src.name

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

        if "number_collision" in checks:
            m = LEADING_NUM.match(name)
            if m and m.group("num") in by_number:
                # Copy NEITHER. Numbers have collided three times here. The
                # design session reads the folder before assigning, but it reads
                # it at a moment, and Drive introduces a gap between reading and
                # landing.
                r.collisions.append((name, by_number[m.group("num")]))
                continue

        if not dry_run:
            shutil.copy2(src, dest / name)
        r.copied.append(name)

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

        for arriving, existing in r.collisions:
            out.append(f"  !! NUMBER COLLISION, NEITHER COPIED: {arriving}")
            out.append(f"       already in destination: {existing}")

        if r.off_convention:
            out.append(f"  ~  off-convention names (copied anyway): "
                       f"{', '.join(sorted(r.off_convention))}")
            out.append("       expected NNN-for-code-*.md")

        if r.source_mutated:
            out.append(f"  !! SOURCE FOLDER CHANGED DURING THE RUN: "
                       f"{', '.join(r.source_mutated)}")
            out.append("       This tool never writes to the source. Something else did, "
                       "or Drive synced mid-run.")
        elif r.reachable:
            out.append(f"  ok source folder byte-for-byte unchanged "
                       f"({r.considered} files hashed before and after)")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pair", action="append", help="pair id; repeatable. Default: all")
    ap.add_argument("--config", type=Path, default=CONFIG)
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would be copied and copy nothing")
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

    results = [sync_pair(p, dry_run=args.dry_run) for p in pairs]
    for line in render(results):
        print(line)

    # NON-ZERO when a person must look. A scheduled run that reports a collision
    # and exits 0 is a report nobody reads. An off-convention name alone is NOT
    # blocking -- it is flagged and the file is copied.
    return 1 if any(r.blocked for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
