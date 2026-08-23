---
id: 069
title: The inbound copier suppresses what is retired; NOW.md tags its ids and renders rule 16's four numbers
type: task
class: admin
owner: claude-code
unblocks: NOTHING
depends: none
touches: tools/sync_from_drive.py config/sync.yaml tools/now.py
bugs:
  - id: NEW
    action: raise
    status: pair 3 (christoph_open) resurrected every retired christoph/open/ item, forever, because the copier's one rule ("not in the destination -> copy it") has no concept of copy-verify-retire; three confirmed live occurrences (c032, c035, c036) before Christoph worked around it by hand
---

**Status** RUNNING

# 069 — done. All three parts landed; Part A's fix is measured against the real collision, not a synthetic one.

**Part 0's file map.** Parts A (`tools/sync_from_drive.py`, `config/sync.yaml`,
`tests/test_sync_from_drive.py`) and B+C (`tools/now.py`, `tests/test_now_is_derived.py`)
are fully disjoint — done sequentially in one session rather than as two subagents, since
neither needed the other's file and there was nothing to serialise or partition beyond
that observation itself.

---

## Part A — pair 3 suppresses what is already done

`checks: [suppress_retired]`, opt-in per pair (`config/sync.yaml`, `christoph_open` only —
pairs 1 and 2 are copy-and-keep and must not gain this). In `sync_pair()`
(`tools/sync_from_drive.py`), a pair with the check reads the leading id tokens present in
its destination's SIBLING `done/` directory before copying; a source file whose token is
already there is not copied, counted, and named in the report.

**The id token is the leading run of characters before the first hyphen, whole** —
`LEADING_ID`, deliberately distinct from the existing `LEADING_NUM` (three digits only).
Confirmed: `035` in the Drive source with `035a` (not `035`) in `christoph/done/` still
copies `035` — the two are different tasks and a bare-digit match would have let one
retire the other.

**Fails closed toward copying.** `christoph/done/` missing or unreadable for any reason →
`retirement_check_unreadable` is set, nothing is suppressed, every source file copies, and
the headline says `christoph/done not readable — nothing suppressed`. **"Empty" is not
"unreadable"**: an existing, readable, empty `done/` directory produces a genuinely empty
suppression set and reports as the ordinary case — the task's own four illustrative report
lines require this distinction to hold, and it does. Flagged rather than silently resolved,
since the task's prose lists "missing, empty, permission error" together as reasons
`christoph/done/` "cannot be read," which its own four examples do not support.

**The four report shapes, confirmed distinct**, via
`test_the_four_retirement_report_lines_are_distinguishable`:
```
t: 0 new · up to date (0 unchanged)
t: 0 new · 1 suppressed (032) · up to date (0 unchanged)
t: 0 new · christoph/done not readable — nothing suppressed · up to date (0 unchanged)
t: 0 new · source folder UNREACHABLE · <path>
```

**Seen red before green, against the real pre-patch module — not inline in the test
suite.** `git stash push -- tools/sync_from_drive.py config/sync.yaml` reverted both files
to `HEAD` while keeping this task's new tests; four of five new tests failed with
`AttributeError: 'PairResult' object has no attribute 'suppressed'`, confirming the
suppression behaviour did not exist before this patch. `git stash pop` restored the fix;
all 31 tests in `tests/test_sync_from_drive.py` pass.

**No pair-specific branch was added.** `checks: [suppress_retired]` gates the behaviour the
same way `filename_convention`/`number_collision` already gate theirs;
`test_the_copier_has_no_pair_specific_branches` (unmodified) still passes.

## Part B — `NOW.md` tags every rendered id with its sequence

`h` for `handoff/`, `c` for `christoph/`, applied to every line that renders an id (`ready
now`, `blocked`, `on christoph`, `superseded`, `done`). **A rendering change only** — every
bit of matching logic (`depends_on`, the dependency graph, `find_cycle`, `unmet`,
`superseded`) still runs on bare ids; the tag is the last thing `compute()` does before
returning.

**The first cut of this was wrong, and it was wrong in exactly the way the task exists to
prevent.** A generic `_tag(bare_id)` helper looked the id up against `inbox`/`done` first
and `c_open`/`c_done` second — so for the real, currently-live collision
(`handoff/inbox/033-for-code-the-admin-tax-has-a-test.md` and
`christoph/open/033-for-christoph-task-auction-imbalance-ten-sessions.md`, both genuinely
in this tree right now), it tagged the christoph item `h033`, reproducing the exact bug
under a different disguise. **Found by running it against the real tree, not by reasoning
about the code** — `on christoph h033` where `c033` was expected. Fixed by tagging at the
point of construction (provenance, not lookup): `ready`/`blocked`/`superseded`/`done` are
built by iterating `inbox`/`done`/`graph`, which are handoff-space by construction (`unmet`
never checks `c_done`); `on_christoph` is built by iterating `c_open`, christoph-space by
construction. Neither needs to guess.

`test_the_same_bare_id_in_both_spaces_is_not_confused` pins the real scenario directly
(`033` in both `handoff/inbox/` and `christoph/open/` in one fixture) so this cannot
regress silently. Confirmed against the live tree: `NOW.md` now reads
`ready now ... h033 ...` and `on christoph c033` on separate, correctly-tagged lines.

**`S` for build slices, per the task's own wording, has nothing to apply to today.**
`_ID` only matches filenames starting with three digits; `S009`-, `H8`-, `M001`-style
filenames were already invisible to `_ids_in()` before this task and remain so — a
pre-existing scope gap, not touched, since widening what `NOW.md` tracks is a different
change than tagging what it already renders.

## Part C — four numbers, not a ratio

```
admin this stretch           21
  naming a product task       3
product this stretch         11
days since last product task  0
```

`admin`/`product` are unchanged (still counted from `class:` across `handoff/inbox/`).
**`naming a product task`** counts admin task files whose `unblocks:` names at least one
task file (in `handoff/inbox/` or `handoff/done/`) whose own `class:` is `product` or
`spec` — `unblocks: NOTHING`, a blank or missing line, and an `unblocks:` naming only
admin tasks all count toward `admin` and not toward this number.

**A real `unblocks:` line is prose, not a clean id list** — `054`'s reads *"049, 050 and
051 — all three are held only by..."* — and the first cut of this checked only the first
comma-separated token. That happened to be correct for `054`/`055` (both list a
product-class id first) but is fragile in general: `test_an_unblocks_line_that_is_prose_is_still_read_for_ids`
constructs a case where the FIRST id named is admin-class and a LATER one is product-class,
confirming the naive first-token version would have undercounted. Fixed to scan every
id-shaped token in the raw text (`_UNBLOCKS_ID`) and count if any resolves to a
product/spec-class file — measured against the real tree, this moved the real count from
2 to 3.

**`days since last product task`** is the newest git commit date among
`handoff/done/*.md` notes whose OWN `class:` is `product`/`spec`, converted to days before
now. **The OLDEST commit per file, not the latest** — a done-note is copy-and-keep, so a
later commit touching it is a paperwork fix (`bugs: []` retrofitted, a typo caught), not a
new product task landing; using the latest commit would report `0` the moment anyone
touches an old note for an unrelated reason. **Prints why, not a number, when it cannot be
derived** — no product-class note in the tree, or every one of them fails to resolve a git
date.

**Not time-based in the sense `tests/test_now_is_derived.py`'s own docstring forbids.**
`test_days_since_last_product_task_prefers_the_newest_and_ignores_admin` asserts only the
RELATION — a 2020 commit reports over a thousand days regardless of which day this runs, a
more recent product-class note shortens the count, and a recently-committed ADMIN-class
note does not move it at all — never an exact day count tied to today's date.

**`064` Part A refused this change, correctly, because it was scoped to `verify.ps1` and
this lives in `tools/now.py`.** Landed here, in the file the refusal named.

---

## Not done

- **`056`'s frontmatter, the `040`/`043`/`052` divergences.** Not this task's.
- **Renumbering anything on disk.** Part B is a rendering change only, per its own
  instruction.
- **Widening `_ids_in()` to see `S`/`H`/`M`-prefixed files.** Noted above, not attempted.

---

## A note on `verify-failures.txt` (068), as asked, not a change

**The main-checkout ruling holds, and no task in this session has ever run `verify.ps1`
from a worktree.** Every closing sequence across `061`–`069` ran `sync.ps1`/`verify.ps1`/
`export-handoff.ps1` directly from `D:\Dev\momentum`, never from `.claude/worktrees/` or
`D:\Dev\_worktrees\`. Under that practice, `verify-failures.txt`'s delta is real: each
task's closing `verify.ps1` run has compared against the previous task's, not started cold.
**If a future session runs `verify.ps1` inside a per-task worktree, this stops being true**
— the gitignored state file would not exist there, every such run would report `no
previous run recorded`, and the delta this task's Part A and `068` both built would
silently stop meaning anything. Nothing changed here to address that; stated because the
task asked which is true, not because it is fixed.

---

## Exit tests

| test | result |
|---|---|
| Green: a retired id is suppressed, a live one still copies, `035a` in `done/` does not suppress `035` | **true** — `test_a_retired_item_is_suppressed_and_a_live_one_still_copies`, `test_035a_in_done_does_not_suppress_035` |
| Refusal: `christoph/done/` unreadable → suppresses nothing, reports why, seen red before green | **true** — `test_an_unreadable_done_directory_suppresses_nothing`; red/green demonstrated via `git stash`, above |
| UAT | **Christoph's** — run a sync with a retired item still in Drive and confirm it does not reappear, and that a new item still arrives. Not performed here. |

---

## The closing sequence

Per `CLAUDE.md`, from the main checkout. One commit.

`verify.ps1` is the last action, and is not the file this task changed (that was `069`'s
own targets — `tools/sync_from_drive.py`, `config/sync.yaml`, `tools/now.py` — none of
which is `verify.ps1` itself, so this run **is** independent evidence, unlike `064`'s and
`068`'s own closing runs). It ran and its output is not pasted or summarised here beyond
what is already quoted above for the specific exit-test evidence.

---

**This note needs to be pasted to chat.**
