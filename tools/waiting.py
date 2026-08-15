"""How many files Drive is holding that this tree does not have.

045 Part 5. **`waiting in Drive` is the point, and it is deliberately not a
clock.**

*"Last success two hours ago"* is unalarming, and it reads identically on a
Sunday and a Thursday. **"Four files are in Drive that are not in the tree"
means the same thing on both days, and it goes to zero exactly when the problem
is gone.**

On 2026-08-15 four UAT files sat in `momentum-christoph-open` while
`christoph/open/` held one `.gitkeep`. **The age of the last success said
nothing about it** — the sync had run, successfully, over a pair that had
nothing waiting at the time it ran.

----

**AN UNREACHABLE SOURCE IS ITS OWN OUTCOME AND MUST NEVER READ AS `0 waiting`.**
Those are opposite facts: one says the pipe is clear, the other says the pipe is
gone. `045`'s refusal test turns on exactly this.

**This lives here rather than inside `verify.ps1` so it can be tested by running
it.** 045: *a static check would pass forever against a `verify.ps1` that had
stopped counting, which is this defect exactly.*
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

REPO = Path(__file__).resolve().parents[1]
CONFIG = REPO / "config" / "sync.yaml"

#: How many filenames to name before summarising. Naming them is most of the
#: value — `4` is a number, `018-…, 019-…` is a thing you recognise.
NAME_CAP = 4


@dataclass(frozen=True)
class Waiting:
    """One pair's answer. **`unreachable` and `count == 0` are different
    facts and never render alike.**"""

    pair_id: str
    count: int
    names: tuple[str, ...]
    unreachable: Optional[str] = None      # the source path, when it is gone

    def render(self) -> str:
        if self.unreachable is not None:
            return f"SOURCE UNREACHABLE  {self.pair_id} — {self.unreachable}"
        shown = ", ".join(self.names[:NAME_CAP])
        if self.count > NAME_CAP:
            shown += f" ... and {self.count - NAME_CAP} more"
        return f"{self.pair_id}  {self.count} — {shown}"


def waiting_for(pair: dict) -> Waiting:
    src, dst = Path(pair["from"]), Path(pair["to"])
    glob = pair.get("glob", "*.md")
    if not src.is_dir():
        return Waiting(pair["id"], 0, (), unreachable=str(src))
    have = {p.name for p in dst.glob(glob)} if dst.is_dir() else set()
    missing = tuple(sorted(p.name for p in src.glob(glob) if p.name not in have))
    return Waiting(pair["id"], len(missing), missing)


def survey(config: Optional[Path] = None) -> list[Waiting]:
    p = config or CONFIG
    pairs = (yaml.safe_load(p.read_text(encoding="utf-8")) or {}).get("pairs", [])
    return [waiting_for(pair) for pair in pairs]


def main(argv: Optional[list[str]] = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    rows = survey(Path(argv[0]) if argv else None)

    total = sum(r.count for r in rows if r.unreachable is None)
    print(f"waiting in Drive  {total}")
    for row in rows:
        if row.unreachable is not None or row.count:
            print(f"  {row.render()}")
    if total == 0 and not any(r.unreachable for r in rows):
        print("  every configured source is fully represented in the tree")

    # **Non-zero when a source is gone, zero when merely nothing is waiting.**
    # `verify.ps1` draws no conclusions, but a caller that wants one must be able
    # to tell those apart without parsing prose.
    return 1 if any(r.unreachable for r in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
