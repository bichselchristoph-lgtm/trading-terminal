---
task: 007
title: Watchlist ingestion — minimum schema, absence display contract, companion requirement removed
status: READY
written: 2026-08-09
written_for: a clean session with no prior context
amends: handoff/done/004-watchlist-ingestion.md (built), handoff/done/004a-ingestion-two-folder-split.md
depends_on: 004 (done). Nothing else.
blocks: 006 — it consumes WatchlistSnapshot and inherits the absence semantics changed here
---

# 007 — Watchlist ingestion amendments

004 built the front door and it works. Three decisions taken since have made
parts of it wrong. This task corrects them and re-draws the blueprint that
describes them.

**You do not need any other context to do this task.** Do NOT go looking for
the research/phase-3 work in this repo — it is unrelated and HALTED by user
instruction. `tests/test_incomplete_work.py` has 5 pre-existing failures
belonging to it. Leave them failing; do not fix them. If a file points you
there, report and stop.

**Numbering note.** 005 and 006 already exist in `handoff/inbox/`. This is 007.

## Scope

`core/watchlist.py`, `tests/test_watchlist_ingest.py`, and
`docs/specs/mockups/mockup-01-ingest.html`. Nothing else. No panel work — 006
owns the display; this task defines what the display is given.

## What does NOT change

Stated because most of 004 stands and a reader could over-correct:

- Drop folder `D:\watchlists_drop`, unversioned. Archive
  `D:\dev\momentum-harness\scanner_watchlists\`, committed.
- Filename convention `watchlist-YYYY-MM-DD-vN.csv`. Still refused if malformed.
  Still never inferred.
- Latest by validated-name date, never mtime.
- `ArchiveCollision` on same name / different content, keyed on the
  newline-normalized `content_key`.
- All checks evaluated before anything is written; failed drop leaves the
  archive byte-identical; mid-archive I/O failure rolls back completely.
- `ingest_latest` refuses on a malformed name rather than skipping it.
- The `deepvue_` prefix applied by the parser. `metrics` vs `extra`
  segregation. `unrecognised_columns` on the provenance.
- The system never scans. There is no fallback scanner.

## Change 1 — the schema requires SYMBOL and nothing else

**Current behaviour, and why it is wrong.** `WatchlistSchemaError` fires when
any *expected* column is absent. The expected set was written from the spec,
not from a real export. So a Deepvue header rename shuts the door on a trading
morning, and the column that shut it is one nothing reads.

**Nothing downstream depends on any Deepvue field except the symbol.** Verified
against the blueprints: `gap%`, `deepvue_rvol`, `adr%` and `float` appear in
the mockup-03 ranked table as *display* columns beside the fit score, not as
inputs to it. `deepvue_rvol` is structurally barred from computation anyway —
unknown baseline, and `comparable_to()` refuses it against `rvol_vs_curve` and
`rvol_vs_trailing`. Sizing takes an entry reference and an invalidation; its
ATR mode reads bars, not Deepvue's ADR.

**Required:**

- A missing **symbol column** remains a hard refusal. Keep
  `WatchlistSchemaError` for exactly this, or rename it if the narrower meaning
  reads better — your call, but say which in the done artifact.
- Every other column becomes optional. Absent → the column is simply not
  present in the snapshot. Not an error, not a column of `None`s.
- A cell that is present, non-blank and unparseable still refuses
  (`WatchlistDataError`). Unchanged. An unrecognised token in a numeric column
  still means the export is not the shape we think it is.
- Blank cells (`""`, `-`, `N/A`) still parse to `None` with the row ingesting.
  Unchanged.
- `DeepvueSchema` stops being a requirement list and becomes a *recognition*
  list: the columns we know how to type and prefix. Keep it injected, so a
  Deepvue change stays a config edit.

## Change 2 — two kinds of absence, and they must not print the same

This is the reason not to simply delete the check, and it is the part most
likely to be dropped on the way to a passing test suite.

If Deepvue silently stops exporting ADR, every row reads `n/a` and the panel
looks like thin data rather than a changed export. Those are different facts
and the user acts differently on each.

**Required:** the snapshot must let a reader distinguish, per column:

| State | Meaning |
|---|---|
| column absent from this export | Deepvue did not ship it. A property of the file |
| column present, cell empty | Deepvue shipped the column and had no value for this symbol |

`columns_seen` already records the first. Make it a first-class, documented
part of the provenance contract rather than an incidental field, and make sure
a consumer can ask the question without string-matching. 006 will render this
as *not in this export* for the column versus *no value* for the cell — that
wording belongs to the panel, but the distinction must survive the door.

This is the house rule the mockups are built around: absence shown as absence,
with its reason, never a zero and never an undifferentiated blank.

## Change 3 — the provenance companion is no longer required

**Decided by the user 2026-08-09.** See
`handoff/questions/scanner-provenance-requirement-dropped.md`, which is the
authoritative record of the decision and the reasoning. Read it before doing
this part.

Short version: the requirement assumed one watchlist maps to one scan. It does
not — a list may be the union of several Deepvue scans, so one dated screenshot
cannot describe the boundary even in principle. A check that gets satisfied
incorrectly is worse than no check.

**Required:**

- `MissingProvenanceCompanion` no longer fires. Ingestion proceeds with no
  companion present.
- **If a companion IS present, still archive it.** Losing the optional record
  was not part of the decision. Copy it alongside the CSV exactly as now.
- Record on the provenance whether a companion was found, and its filenames if
  so. A later reader must be able to tell "no companion existed" from "nobody
  recorded whether one existed".
- The refusal set is now **two**: malformed filename, archive collision. Plus
  `WatchlistDataError` for an unparseable cell and the symbol-column refusal.
  State the count plainly in the done artifact; it has now changed twice and
  the blueprint drifted the first time.

**Do not** edit `handoff/done/004-watchlist-ingestion.md` or
`004a-ingestion-two-folder-split.md`. Those are historical records of what was
built. This file is the later state.

## Change 4 — re-draw `mockup-01-ingest.html`

The sheet is stale in three ways, and `mockup-README.md` is explicit that a
sheet describing changed behaviour is wrong and must be updated in the same
pass or deleted.

| In the sheet now | Should read |
|---|---|
| Header path `D:\tradesignals\watchlists` | The two-folder split: drop `D:\watchlists_drop`, archive `scanner_watchlists\` |
| Margin note 1: "Two hard errors only" — filename and provenance | Two hard errors: **malformed filename** and **archive collision**. Provenance is no longer one of them |
| The `STOP … no filter screenshot for this date` refusal panel | Remove. Replace with the collision refusal, which has never been drawn and is the one a user will actually meet |

Also add, because the sheet currently cannot show them:

- the **column-absent** state from Change 2, distinct from a blank cell
- the companion line rendered as *present* or *none* rather than as a gate

Keep everything else: the age flag shown-never-enforced, "the system never
scans", git as the provenance record, the prior-drops block.

The sheet is a blueprint of PowerShell console output. It is not a web app and
nothing imports it.

## Tests

`tests/test_watchlist_ingest.py` is 79 tests and green. Expect to rewrite, not
delete.

- The schema-drift refusal tests invert: an export missing an optional column
  now **succeeds**, and the resulting snapshot reports that column as absent.
  Keep at least one that still refuses — the missing symbol column.
- The companion refusal tests invert the same way. Add one asserting a present
  companion is still archived, and one asserting the provenance distinguishes
  "no companion" from "not recorded".
- **Keep every paired control.** 004's assertions that a failed drop leaves the
  archive byte-identical are each paired with a control proving a successful
  drop does change it. Untouched-ness is trivially true if nothing works, and
  this repo has shipped green suites over broken code twice. Do not let the
  rewrite drop the controls.
- Add a test distinguishing the two absences at the API level, so Change 2
  cannot be quietly collapsed by a later refactor.
- Full suite before and after. The 5 `test_incomplete_work.py` failures are
  expected and are not yours.

## Ordering against 006

007 changes what `WatchlistSnapshot` guarantees. 006 renders it and its
"missing is missing" rule now has two cases instead of one. **Land 007 first**,
or land them together — do not build 006's absence rendering against the old
contract.

## Raise, do not choose

If the build wants a different answer on any settled item above, that is a
question for `handoff/questions/`, not a decision to make in code.
