---
task: 004 (+ 004a)
title: Watchlist ingestion — Deepvue CSV drop, two-folder split
status: DONE
built: 2026-08-09
supersedes: handoff/done/004-watchlist-ingestion-spec.md   (was inbox/004-...)
            handoff/done/004a-ingestion-two-folder-split.md
---

# 004 + 004a — Watchlist ingestion, built

The front door is in. A hand-exported Deepvue CSV dropped into
`D:\watchlists_drop` is validated, parsed, and — only if it passes everything —
copied with its provenance companion into `scanner_watchlists/` inside the
repo, where git records it.

**Read this cold and you know what exists:** one module
(`core/watchlist.py`), one test file (`tests/test_watchlist_ingest.py`, 79
tests, all green), one `.gitignore` change that is load-bearing, and two stale
references cleaned up.

## What changed

| File | Change |
|---|---|
| `core/watchlist.py` | **new** — the whole ingestion contract |
| `tests/test_watchlist_ingest.py` | **new** — 79 tests |
| `.gitignore` | **negation block** for `scanner_watchlists/` — see below, this one matters |
| `live/flag_monitor.py` | two stale references to the retired scanner, removed |
| `handoff/inbox/004a-...md` | drop path corrected to `D:\watchlists_drop`; "Naming note" deleted |
| `scanner_watchlist_handoffs/` | **deleted** — empty, untracked, one letter off the real archive name |

`scanner_watchlists/` was **not** pre-created. Its existence means an ingest
succeeded, and several tests depend on that being true.

## Why it lives in `core/`

Not an arbitrary placement. The dependency rule forbids `harness ↔ live` in
both directions, so anything both sides need must be in `core` or be reachable
from neither. 004a says history resolves from the archive, and research
legitimately wants to know which universe was traded on a date — the same thing
the dashboard wants. `core` is the only tree both may import.
`core/watchlist.py` imports stdlib only, so
`tests/test_import_boundaries.py::test_core_imports_nothing_from_the_repo_at_all`
still passes.

## The API

```python
ingest_drop(csv_path, *, archive_dir, schema=DEEPVUE, now=None) -> WatchlistSnapshot
ingest_latest(drop_dir, *, archive_dir, ...)     # newest validated name in the drop folder
latest_archived(archive_dir)                     # history — reads the ARCHIVE, never the drop
archived_names(archive_dir)                      # every validated name, oldest first
read_archived(csv_path)                          # re-read without copying
parse_filename(name) -> WatchlistName            # raises; never infers a date
```

`WatchlistSnapshot` carries `.provenance` (source filename and path, parsed
date, version, companion filenames, **archive** paths, ingest timestamp, row
count, `csv_sha256`, `content_key`, `columns_seen`, `unrecognised_columns`),
`.rows`, `.duplicate_symbols`, and `.age_days(now=None)`.

## The four refusals

Three from the specs, plus schema drift. **All are evaluated before anything is
written** — that ordering is the whole reason the archive stays untouched, and
it is not incidental.

| Exception | Fires when |
|---|---|
| `MalformedFilename` | name is not `watchlist-YYYY-MM-DD-vN.csv`. `v0` and `v01` refused too — two spellings of one version would defeat the collision refusal, which keys on the name |
| `MissingProvenanceCompanion` | no companion beside the CSV. Another CSV cannot serve as one — that would be the requirement satisfying itself |
| `ArchiveCollision` | same archived name, different content. No overwrite, no skip, no auto-increment |
| `WatchlistSchemaError` | an expected **column** is absent (schema drift), or there is no symbol column |

Plus `WatchlistDataError` for a cell that is present, non-blank, and not a
number.

## What the tests said

**79 passed.** Full suite: **2,600 passed, 5 failed, 5 skipped**. The 5
failures are all `tests/test_incomplete_work.py` — the halted phase-3 work,
pre-existing, untouched, and deliberately not fixed here.

The assertions worth knowing about:

- **A failed drop leaves the archive byte-identical** — asserted for each
  refusal, and each one is *paired with a control* proving a successful drop
  does change the archive. "Untouched" is trivially true if nothing works, and
  this repo has shipped green suites over broken code twice.
- **A failed *first* drop does not even create `scanner_watchlists/`.**
- **A mid-archive I/O failure rolls back completely** (`copy2` fails on the
  second of three files → nothing survives, directory removed). A successful
  ingest that did not archive is a failed ingest, so a half-archive must not
  survive as a half-record.
- **No code path infers a date**: 12 near-miss filenames × 3 entry points.
- **Latest is by name date, not mtime** — the test back-dates the newer file's
  mtime by 10,000 seconds so an mtime implementation fails.
- **`git check-ignore` is asserted directly** against 7 archive paths, with a
  vacuity guard proving `check-ignore` can still detect an ignored path.

## Three things I found

**1. `.gitignore` had the trap 004a predicted, wearing a different extension.**
No `*.csv` and no `watchlists/`. But line 29 is a bare, unanchored `*.jsonl`,
and `*.zst` / `*.parquet` are the same — they match at **any depth**.
`scanner_watchlists/ingest_manifest.jsonl` was ignored, confirmed by
`git check-ignore`. A companion or ledger in any of those formats would have
looked committed right up until someone went looking for one. Closed with an
explicit negation block plus a test, rather than by avoiding those extensions —
a future broad rule now fails a test instead of eating the record. The
`.partial` temp marker is re-ignored after the negation so a crashed copy is
not committable as a watchlist.

**2. Byte comparison for the collision refusal is wrong in this repo.**
`.gitattributes` pins `* text=auto eol=lf`. An archived CSV comes back out of a
fresh clone with LF while the Deepvue drop has CRLF, so byte-identical content
would refuse as a collision on any machine that had re-cloned — turning a
legitimate re-drop into a hard stop. Collision keys on a newline-normalized
hash (`content_key`); the raw `csv_sha256` is still recorded for the audit
trail. There is a test with an explicit control asserting the two files
genuinely differ byte-for-byte first.

**3. `ingest_latest` refuses on a malformed name rather than skipping it.**
This is a decision, and it is the opposite of what "pick the latest valid file"
suggests. Skipping is the dangerous behaviour: `watchlist-2026-08-10.csv` (no
`vN`) passed over silently means yesterday's v1 is ingested in its place and
the dashboard shows a stale universe with nothing raised. The newest file is
the one most likely to be misnamed. So: any CSV in the drop folder that does
not validate stops everything, listing the offenders.

## Design notes from 004, as built

All four accepted, three of them sharpened (user confirmed before build):

1. **`deepvue_` prefix applied by the parser**, not expected of the caller —
   there is no code path that can put a bare `rvol` into a snapshot.
2. **Unknown columns preserved *and segregated*** — `metrics` (recognized,
   prefixed, typed) vs `extra` (verbatim, unparsed), with
   `unrecognised_columns` on the provenance. Preserved, and visibly not
   understood.
3. **Missing column ≠ blank cell.** Absent column → refuse (schema drift).
   Blank cell (`""`, `-`, `N/A`) → `None`, row still ingests. Present but
   unparseable → refuse, naming symbol/column/value. The expected set is
   injected via `DeepvueSchema`, so a Deepvue change is a config edit.
4. **Provenance plus two fields** — `csv_sha256` (content identity must be
   decidable and later-verifiable) and the **archive** path (the drop path is a
   doorway that will not exist tomorrow).

## Open, for whoever picks up the dashboard panel

Not blocking, not a question — a display decision that belongs to the panel,
not to the door:

**`age_days` is calendar days.** A Monday looking at Friday's list reads 3, but
it is 1 trading day stale. `core/us_equity_calendar.py` exists if the panel
wants the trading-day count. Left calendar-only here because the door should
not decide how the room displays. `age_days` may also be **negative** for a
forward-dated export — reported rather than clamped, because a clamped zero is
invisible and this module cannot know whether that is a mistake or a
Sunday-evening preparation.
