"""`claude/NOW.md` — what is runnable, what is blocked, and on whom.

045 Part 3. **Specified in the project instructions §4 and never built.**

----

**IT IS COMPUTED, NEVER STORED, AND THAT IS THE WHOLE DESIGN.**

Three sessions write to this tree and each sees a snapshot. A hand-maintained
status file would be wrong within the hour and would be *believed*, because it
reads exactly like a correct one. **Anything that cannot be derived from the
tree does not go in it.**

The consequence, stated so nobody tries: **a hand edit to `NOW.md` does not
survive the next `verify.ps1` run.** `tests/test_now_is_derived.py` asserts it.

----

**Every rule here is mechanical, and that is the point.**

    done          a file exists in handoff/done/
    ready         in handoff/inbox/, not done, every `depends:` done
    blocked       in handoff/inbox/, not done, with an unmet dependency NAMED
    on christoph  in christoph/open/, not in christoph/done/
    admin         counted from `class:` in frontmatter, per rule 16
    naming a
      product task admin tasks above whose `unblocks:` names a product/spec task
    product       counted from `class:` in frontmatter, per rule 16
    days since
      last product the newest git commit date among handoff/done/ notes whose
                    OWN `class:` is product/spec — printed with its reason
                    instead of a number when it cannot be derived

**`depends:` is optional and its absence means "depends on nothing".** 045 is
explicit that task files already in the tree must not be edited to add it —
`handoff/` is copy-and-keep.

**A dependency cycle is REFUSED and named.** Two tasks depending on each other
would otherwise render as `blocked` forever with no explanation, which is the
shape of a status line that is technically true and useless.

**069 Part B.** Every rendered id carries its sequence — `h` for `handoff/`,
`c` for `christoph/` — because the two id spaces collide: a real
`handoff/inbox/033-...` and a real `christoph/open/033-...` have both existed
in this tree at once, and a bare `033` on two adjacent lines does not say
which is which. **A rendering change only** — nothing on disk is renumbered,
and every bit of matching logic (the dependency graph, `unmet`, `superseded`)
still runs on bare ids; the tag is applied once, last, by which folder actually
holds each id, never guessed from which report line is asking.

**069 Part C.** `admin:product this stretch N:M` fused two numbers that rule 16
asks for separately into a bare ratio and lost the two that carry the signal —
how many of the admin count actually name a product task, and how long it has
been since one landed. Both are rendered now, derived rather than guessed.
"""
from __future__ import annotations

import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

REPO = Path(__file__).resolve().parents[1]
NOW = REPO / "claude" / "NOW.md"

#: `NNN` at the start of a filename. Task ids are three digits; `035a` and the
#: like carry a suffix, and the suffix is part of the id.
_ID = re.compile(r"^(?P<id>\d{3}[a-z]?)\b")

#: A frontmatter scalar or inline list: `depends: 045` / `depends: 037, 043` /
#: `depends: [037, 043]`.
_FIELD = re.compile(r"^(?P<key>\w+)\s*:\s*(?P<value>.*?)\s*$")


class CycleError(ValueError):
    """A `depends:` cycle. **Named, never rendered as `blocked`.**"""


def task_id(path: Path) -> Optional[str]:
    m = _ID.match(path.name)
    return m.group("id") if m else None


def frontmatter(path: Path) -> dict[str, str]:
    """The `---` block at the top of a markdown file, as flat strings.

    **Deliberately not a YAML parse.** These files are written by hand in a
    design session and one malformed colon should not take the status board
    down — a `NOW.md` that refuses to render because a task file has a stray
    quote is less useful than one that reads what it can.
    """
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    if not text.startswith("---"):
        return {}
    out: dict[str, str] = {}
    for line in text.splitlines()[1:]:
        if line.strip() == "---":
            break
        m = _FIELD.match(line)
        if m:
            out[m.group("key")] = m.group("value")
    return out


def depends_on(path: Path) -> list[str]:
    """The ids this task waits for. **Absent means nothing, and so does the
    literal value `none`** -- 056: five task files write `depends: none` as
    the established convention for "no dependency", and the parser must read
    it the same way it reads an absent key, not as a phantom dependency on a
    task literally named "none"."""
    raw = frontmatter(path).get("depends", "")
    raw = raw.strip().strip("[]")
    if not raw or raw.lower() == "none":
        return []
    return [p.strip() for p in raw.split(",") if p.strip()]


#: 069 Part B. `h` for `handoff/`, `c` for `christoph/`. **Measured, not
#: assumed, that the two id spaces collide**: `handoff/inbox/033-for-code-...`
#: and `christoph/open/033-for-christoph-task-...` both exist in this tree at
#: once, which is the exact case this task was written for. A first cut of
#: this function guessed the namespace from which folders hold the bare id --
#: `033 in inbox or done -> h`, else `033 in c_open or c_done -> c` -- and
#: mistagged the real `c033` as `h033`, because it checked handoff membership
#: first regardless of which section was asking. **The fix is to never guess:
#: every call site below already knows which folder its own id came from**
#: (`ready`/`blocked`/`superseded`/`done` are built by iterating `inbox`, `done`
#: or `graph`, all handoff-space; `on_christoph` is built by iterating
#: `c_open`, christoph-space), so the tag is applied AT that iteration, not
#: recovered afterward from an ambiguous lookup.
H = "h"
C = "c"


#: 069 Part C. `unblocks:` on an admin task counts toward the SECOND number
#: only when it names a task file whose OWN `class:` is one of these -- the
#: same bucketing rule 16's admin:product ratio already uses for the two
#: numbers it fuses (`class: spec` counts as product-shaped work).
_PRODUCT_CLASSES = {"product", "spec"}


#: An `unblocks:` value is not always a clean id list -- `054`'s reads *"049,
#: 050 and 051 -- all three are held only by the isolation ruling..."*. Every
#: id-shaped token in the raw text is a candidate, not only the first one a
#: comma-split would find, so a prose `unblocks:` line is read the same way
#: `_ID` reads a filename.
_UNBLOCKS_ID = re.compile(r"\b(\d{3}[a-z]?)\b")


def _names_a_product_task(p: Path, inbox: dict[str, Path], done: dict[str, Path]) -> bool:
    """Does `p`'s `unblocks:` line name AT LEAST ONE task file whose own
    `class:` is product-shaped? `unblocks: NOTHING`, a blank line, a missing
    line, and an `unblocks:` naming only admin tasks all answer `False` here
    -- they still count toward the FIRST number (`compute()`'s `admin`
    count), just not this one."""
    raw = frontmatter(p).get("unblocks", "").strip()
    if not raw or raw.upper() == "NOTHING":
        return False
    for target_id in _UNBLOCKS_ID.findall(raw):
        target = inbox.get(target_id) or done.get(target_id)
        if target is None:
            continue
        if frontmatter(target).get("class", "").strip().lower() in _PRODUCT_CLASSES:
            return True
    return False


def _days_since_last_product_task(repo: Path, done: dict[str, Path]) -> tuple[Optional[int], Optional[str]]:
    """`(days, reason)` -- exactly one is `None`. Derived from the tree: the
    most recent `handoff/done/` note for a task file declaring `class:
    product` (or `spec`, the same bucketing as everywhere else in this rule).

    **The date is the file's OLDEST commit**, not its latest -- a done-note
    is copy-and-keep, so a later commit touching it is a paperwork fix
    (`bugs: []` added retroactively, a typo caught) rather than a new product
    task landing. Using the latest commit would report "0 days" the moment
    anyone touches an old note for an unrelated reason.
    """
    product_notes = [p for p in done.values()
                     if frontmatter(p).get("class", "").strip().lower() in _PRODUCT_CLASSES]
    if not product_notes:
        return None, "no handoff/done/ note in the tree declares class: product (or spec)"

    newest: Optional[datetime] = None
    unresolved: list[str] = []
    for p in product_notes:
        try:
            out = subprocess.run(
                ["git", "-C", str(repo), "log", "--format=%aI", "--", str(p)],
                capture_output=True, text=True, check=True, timeout=10)
        except (OSError, subprocess.SubprocessError) as exc:
            unresolved.append(f"{p.name}: git log failed ({exc})")
            continue
        dates = [d for d in out.stdout.splitlines() if d.strip()]
        if not dates:
            unresolved.append(f"{p.name}: not in git history")
            continue
        # OLDEST commit for THIS file -- the last line, since git log lists
        # newest-first.
        try:
            first = datetime.fromisoformat(dates[-1].strip())
        except ValueError:
            unresolved.append(f"{p.name}: unparseable git date {dates[-1]!r}")
            continue
        if newest is None or first > newest:
            newest = first

    if newest is None:
        return None, ("every product-class done-note failed to resolve a git "
                      "date: " + "; ".join(unresolved))
    now = datetime.now(timezone.utc)
    return (now - newest).days, None


def _ids_in(folder: Path) -> dict[str, Path]:
    out: dict[str, Path] = {}
    if not folder.is_dir():
        return out
    for p in sorted(folder.glob("*.md")):
        tid = task_id(p)
        if tid:
            out.setdefault(tid, p)
    return out


def find_cycle(graph: dict[str, list[str]]) -> Optional[list[str]]:
    """The first cycle found, as the path around it. `None` if acyclic.

    Iterative depth-first with an explicit stack — a recursive walk would blow
    up on a long chain and report a `RecursionError` instead of the cycle,
    which is the wrong finding entirely.
    """
    WHITE, GREY, BLACK = 0, 1, 2
    colour = {n: WHITE for n in graph}
    for start in sorted(graph):
        if colour[start] != WHITE:
            continue
        stack: list[tuple[str, Iterable[str]]] = [(start, iter(graph[start]))]
        path = [start]
        colour[start] = GREY
        while stack:
            node, children = stack[-1]
            advanced = False
            for child in children:
                if child not in graph:
                    continue                       # depends on something absent
                if colour[child] == GREY:
                    return path[path.index(child):] + [child]
                if colour[child] == WHITE:
                    colour[child] = GREY
                    path.append(child)
                    stack.append((child, iter(graph[child])))
                    advanced = True
                    break
            if not advanced:
                colour[node] = BLACK
                stack.pop()
                path.pop()
    return None


def compute(repo: Path = REPO) -> dict[str, object]:
    """Everything `NOW.md` renders, as data. **Pure — reads, never writes.**"""
    inbox = _ids_in(repo / "handoff" / "inbox")
    done = _ids_in(repo / "handoff" / "done")
    c_open = _ids_in(repo / "christoph" / "open")
    c_done = _ids_in(repo / "christoph" / "done")

    # **Superseded is DERIVED, from `supersedes:` in the frontmatter of any task
    # file in the tree.** Not in 045's list of categories, and added because
    # leaving it out is actively harmful rather than merely incomplete: `035`
    # and `036` are superseded by `038` and would otherwise render as **ready
    # now**, which is an invitation to run them. **A session did exactly that on
    # 2026-08-15** — it read `035`, found two files under one number saying
    # opposite things about PDL, and stopped only because the ambiguity was
    # visible. A status board that says `ready` is a stronger signal than the
    # ambiguity was.
    superseded: dict[str, str] = {}
    for tid, path in sorted(inbox.items()):
        raw = frontmatter(path).get("supersedes", "").strip().strip("[]")
        for dead in (x.strip() for x in raw.split(",") if x.strip()):
            superseded.setdefault(dead, tid)

    graph = {tid: depends_on(p) for tid, p in inbox.items()}
    cycle = find_cycle(graph)
    if cycle:
        raise CycleError(
            "a `depends:` cycle: " + " -> ".join(cycle) + ". Two tasks waiting "
            "on each other render as `blocked` forever with no explanation, so "
            "this refuses rather than reporting a status that is true and "
            "useless.")

    ready, blocked = [], []
    for tid in sorted(inbox):
        if tid in done or tid in superseded:
            continue
        # A dependency satisfied by supersession is satisfied: `035a` waits on
        # `035`, and `035` is not going to be done -- `038` replaced it.
        unmet = [d for d in graph[tid] if d not in done and d not in superseded]
        if unmet:
            blocked.append((tid, unmet))
        else:
            ready.append(tid)

    # Rule 16's tax, counted from `class:` across every task file that declares
    # one. **Autonomy buys no exemption from the count** (045 Part 4 guardrail 3).
    classes: dict[str, int] = {}
    admin_naming_product = 0
    for tid, p in sorted(inbox.items()):
        cls = frontmatter(p).get("class", "").strip().lower()
        if cls:
            classes[cls] = classes.get(cls, 0) + 1
        if cls == "admin" and _names_a_product_task(p, inbox, done):
            admin_naming_product += 1

    days_since_product, days_since_product_reason = _days_since_last_product_task(repo, done)

    # 069 Part B. Tagged HERE, as the LAST step -- every bit of matching logic
    # above (the dependency graph, `unmet`, `superseded`) runs on bare ids, so
    # a `depends:`/`supersedes:` cross-reference cannot fail to resolve
    # because one side gained a prefix the other side does not have.
    #
    # **Applied by PROVENANCE, not by looking the id up afterward.** `ready`,
    # `blocked` (its own id and every `unmet` dependency), `superseded` and
    # `done` are all built above by iterating `inbox`/`done`/`graph` -- every
    # id in them is handoff-space by construction, because `unmet` itself only
    # ever checks membership in `done`/`superseded` (both handoff dicts), never
    # `c_done`. `on_christoph` is built by iterating `c_open` and is
    # christoph-space by the same construction. See `H`/`C`'s own comment for
    # why this is not a lookup: `033` names a real task in BOTH spaces at
    # once, and a lookup keyed on the bare id alone cannot tell them apart.
    return {
        "ready": [f"{H}{t}" for t in ready],
        "blocked": [(f"{H}{t}", [f"{H}{u}" for u in unmet]) for t, unmet in blocked],
        "superseded": [(f"{H}{d}", f"{H}{b}") for d, b in sorted(superseded.items())],
        "on_christoph": [f"{C}{t}" for t in sorted(c_open) if t not in c_done],
        "done": [f"{H}{t}" for t in sorted(done)],
        "admin": classes.get("admin", 0),
        "admin_naming_product": admin_naming_product,
        "product": classes.get("product", 0) + classes.get("spec", 0),
        "days_since_product": days_since_product,
        "days_since_product_reason": days_since_product_reason,
    }


def render(state: dict[str, object]) -> str:
    """`NOW.md`'s text. **No timestamp anywhere in it, deliberately.**

    A generated-at line would change on every run, so two runs over an unchanged
    tree would differ — and `test_now_is_derived.py` asserts they do not. More
    importantly it would make the file *look* fresh when the tree behind it was
    stale, which is the class of defect 045 exists to close.
    """
    blocked = state["blocked"]              # type: ignore[assignment]
    lines = [
        "# NOW — computed from the tree, never edited by hand",
        "",
        "**Rewritten by `verify.ps1` on every run** (045 Part 3). A hand edit does",
        "not survive. Anything not derivable from the tree is not in here — which is",
        "why there is no date on it: three sessions write to this tree and each sees",
        "a snapshot.",
        "",
        "```",
        f"ready now    {' '.join(state['ready']) or '—'}",  # type: ignore[index]
    ]
    if blocked:
        first, *rest = blocked
        lines.append(f"blocked      {first[0]} — needs {' '.join(first[1])}")
        for tid, unmet in rest:
            lines.append(f"             {tid} — needs {' '.join(unmet)}")
    else:
        lines.append("blocked      —")
    # 069 Part C. Four numbers, not a ratio. The middle two carry the signal:
    # the gap between "admin this stretch" and "naming a product task" is what
    # makes an admin chain visible in arithmetic instead of needing a
    # prohibition -- a bare ratio fused two numbers together and lost it.
    days_val = state["days_since_product"]
    days_line = (f"days since last product task  {days_val}" if days_val is not None
                else f"days since last product task  CANNOT COMPUTE: {state['days_since_product_reason']}")

    lines += [
        "running      —",
        f"on christoph {' '.join(state['on_christoph']) or '—'}",  # type: ignore[index]
        f"superseded   {' '.join(f'{d}->{b}' for d, b in state['superseded']) or '—'}",  # type: ignore[index]
        f"done         {' '.join(state['done']) or '—'}",          # type: ignore[index]
        f"admin this stretch           {state['admin']}",
        f"  naming a product task       {state['admin_naming_product']}",
        f"product this stretch         {state['product']}",
        days_line,
        "```",
        "",
        "**`running` is always `—`.** It is the one line that cannot be derived: a",
        "session in flight leaves nothing in the tree that says so, and a stored flag",
        "would be exactly the state this file refuses to keep.",
        "",
    ]
    return "\n".join(lines)


def main(argv: Optional[list[str]] = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    repo = Path(argv[0]).resolve() if argv else REPO
    out = repo / "claude" / "NOW.md"
    try:
        text = render(compute(repo))
    except CycleError as exc:
        print(f"NOW.md NOT WRITTEN: {exc}", file=sys.stderr)
        return 1
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"NOW.md rewritten from the tree: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
