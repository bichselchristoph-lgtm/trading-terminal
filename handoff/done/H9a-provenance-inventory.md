---
id: H9a
title: Origin inventory of momentum-harness — the input M001's refusal 4 needs
status: DONE
type: inventory
owner: claude-code
ran: 2026-08-10
target: D:\Dev\momentum-harness (77 commits, 183 tracked files)
wrote: D:\Dev\momentum-harness\docs\PROVENANCE.md (untracked, deliberately)
---

# H9a — origin inventory of `momentum-harness`

**There was no H9a task file.** Not in either inbox. M001 cites it four times — `H9a's
table`, `H9a §3b`, and twice more — but the task itself was never written. This was built to
the four questions M001 actually asks of it, plus the instruction given directly. **If a real
H9a exists and asks for something else, this is the wrong shape and should be re-run**, not
patched.

## Result

| origin | files | consequence for adoption |
|---|---:|---|
| `authored` | **142** | adoptable on merits |
| `imported` | **37** | needs a recorded decision (refusal 4) |
| `unknown` | **4** | needs a recorded decision (refusal 4) |
| **total** | **183** | |

**`docs/PROVENANCE.md`** in the old repo carries the full 183-row table: path, origin,
reference count, and the specific evidence that decided each one.

**M001's adoption gate is now unblocked.** 142 files can be adopted on their merits; 41 need
a sentence from you first.

## Constraints — all held

| constraint | result |
|---|---|
| Run against the old repo, not the new tree | ran against `D:\Dev\momentum-harness`, 77 commits |
| Write `docs/PROVENANCE.md` there | one file, 313 lines, 32,863 bytes |
| No deletions, no edits outside that file | `git diff --name-only` shows only `CLAUDE.md` and `requirements.txt` — **both pre-existing**, from M001 §1 and your own earlier edit. Nothing edited by this task. |
| No git history changes | **77 commits before and after.** `PROVENANCE.md` is left **untracked** — committing it would itself have been a history change |
| pytest counts match | see below |

```
BEFORE : 8 failed, 2612 passed, 5 skipped, 1 warning
AFTER  : 8 failed, 2612 passed, 5 skipped, 1 warning
```

**They did not match on the first attempt** — the write took it to `9 failed, 2611 passed`.
`docs/` is in scope for `tests/test_deferred_work.py`, and the inventory necessarily lists a
file named `handoff/inbox/condition-codes-config-is-unverified.md`, whose name matches the
deferral scanner's `UNVERIFIED` pattern. I used the repo's own sanctioned `NOT-A-DEFERRAL`
escape marker rather than widening the scanner. My first attempt put the marker in the wrong
table cell — the trigger was in the *path* column, not the *evidence* column — so the check
now runs against the assembled row. **Counts verified equal by differencing the two FAILED
lists, not by eyeballing totals.**

## Method, and the two wrong answers on the way

Three evidence sources, strongest first: byte-identical content against the four sibling
repos still on disk; the commit that first created the file with **renames followed to the
root of the chain**; and a distinctive-filename-plus-path-tail match, which is suggestive
only and therefore yields `unknown` rather than `imported`.

Both wrong passes are recorded in `PROVENANCE.md` because both are traps.

**A commit message is not provenance — this was the serious one.** Commit `7987376`
("Flatten: core/harness/live tree, boundary enforced, tradesignals moved in") does two things
at once: it reorganises this repo's *own* files **and** absorbs `tradesignals`. Classifying
at commit level marked **63** files `imported`. Per-file rename-following brought it to
**37**. The giveaway was `harness/spend.py` ← `data/spend.py` and `core/indicators/rvol.py` ←
`signals/rvol.py` — old paths that are this repo's own initial-commit directories, not
`tradesignals` paths.

**Rename blindness inflates `unknown`.** `git log --diff-filter=A` credits a renamed file's
creation to its old path, so a first pass reported "no adding commit" for ~25 files and
dropped them all to `unknown`.

The two errors were chased in opposite directions on purpose. A false `authored` lets an
import through the gate silently — the exact failure the inventory exists to prevent. A false
`imported`/`unknown` only costs a decision. Thin evidence resolves to the conservative side.

## What the inventory says

**The whole of `live/` is imported.** Every file: `feeds.py`, `engine.py`, `render.py`,
`detectors.py`, `levels.py`, `marketstate.py`, `cache.py`, `cli.py`, `config.py`,
`ep_premarket.py`, `flag_monitor.py`, `run_signals.py`, `tape/`, `regime/`. So is
`tests/orb_validator/`. That is independent corroboration of two things the old `CLAUDE.md`
already warned about — that `live/` has import coverage only, and that the validator runs
against a reference oracle — and it means **the entire live console needs decisions before
any of it moves.**

**`harness/` and `core/` are almost entirely authored**, including `harness/spend.py` (the
sanctioned Databento client, 31 referencing files) and `core/bars.py`.

### §3a — imported and unreferenced

M001 §6 says name these and do not adopt them. Exactly one qualifies —
**`live/tests/test_level_flow.py`** — and **the metric misleads here**: it is a *test*, and
no test is referenced by anything. So the list is effectively empty.

It is worth naming for a different reason. It holds **exactly seven test functions**, it came
from `tradesignals`, and `pytest.ini` sets `testpaths = tests`, so a default run collects
**0** tests from `live/tests/`. **These are precisely the seven behavioural tests M001 §2
cites as the reason two consolidations shipped a broken `live/` while staying green.** They
have never run in this repository. The new tree's `pytest.ini` and
`tests/test_pytest_collection.py` already prevent the recurrence.

### §3b — "step 7" is settled, and `live/_to_merge/` holds nothing to adopt

M001 §6 defers adopting `live/_to_merge/` until this is established. **It is now, and the
answer is that the gate was already discharged.**

"Step 7" is a step of `docs/specs/REPO_CONSOLIDATION_PLAN.md` — folding in `trading-scripts`
and `orb_tools`. Three independent confirmations: the directory's own frontmatter
(`review_trigger: consolidation_step_7`), commit `1e6c893` titled "Step 7: fold in
trading-scripts and orb_tools", and `tests/test_staging.py` enforcing it.

| commit | what |
|---|---|
| `7987376` | added `live/_to_merge/{README.md, core.py, config.py}` |
| `d3174c9` | gave staging a review trigger |
| `1e6c893` | **step 7 itself** |
| `20f1d6d` | **deleted `core.py` and `config.py`** — "Resolve the staged pair; live/ was broken and nothing noticed" |

`live/_to_merge/` now contains **only `README.md`**, which still reads as though the pair is
staged and awaiting review — a resolved gate described by a stale document. The originals are
at `D:\Dev\tradesignals\tradesignals\{core.py,config.py}` if wanted.

### §3c — the four `unknown`

All four are **zero-byte** files: `core/config/.gitkeep`, `handoff/questions/.gitkeep`,
`live/regime/__init__.py`, `live/tape/__init__.py`.

An empty file has no content to have come from anywhere, and git's rename detection matches
every empty file to every other, so `--follow` lands somewhere arbitrary. I kept them
`unknown` rather than inventing a fourth status, because **M001 defines exactly three and a
fourth would let them past refusal 4 without a decision.** The decisions are trivial; they
should still be made rather than assumed.

## One correction to M001 §6

**M001 lists `core/config/condition_codes.yaml` under "do not adopt", grouped with imported
material. The inventory says it is `authored`** — created in this repo's initial commit
`3ce6fc8` as `config/condition_codes.yaml`, and referenced by 10 files.

The prohibition stands, but the reason differs, and the difference matters to whoever
rewrites it. Its own banner records that the delivery carries no condition field at all, so
the codes are a vocabulary **this** codebase invented — not a predecessor's. **There is no
upstream to reconcile against.** M001's instruction that it be "written fresh against the
delivery" is therefore the only available route, not merely the preferred one.

## What this unblocks, and what it does not

**Unblocked:** M001's adoption gate has origin data. 142 files are adoptable on merits.

**Still needs you:** 41 decisions before those files can move — 37 `imported`, 4 `unknown`.
The 37 are effectively one decision repeated, since 24 of them are the `live/` tree; a single
recorded rationale for "adopting the predecessor's live console" would cover most of it, but
**that rationale is yours to write, which is the entire point of refusal 4.**

**Deliberately not done:** `PROVENANCE.md` is untracked in the old repo, because your
instruction forbade history changes there. If it should be committed, that is a one-line
follow-up — but note it would be the first commit to an archived tree, and `ARCHIVED.md` says
files leave only through the gate.

**Still open from before, unchanged:** the four canonical specs have not been supplied, so
`docs/specs/` in the new tree remains empty and H9 has not run.
