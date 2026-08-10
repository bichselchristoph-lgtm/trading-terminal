---
task: 004
title: Watchlist ingestion — Deepvue CSV drop
status: READY
written: 2026-08-09
written_for: a clean session with no prior context
depends_on: nothing
blocks: every dashboard panel downstream of the watchlist
---

# 004 — Watchlist ingestion

This is the first build task of the trading-signal dashboard project. It is the
front door: everything the dashboard displays enters the system through here.

**You do not need any other context to do this task.** Read this file and the
two source specs it cites. Do not go looking for the research/phase-3 work in
this repo — it is unrelated, it is currently halted, and nothing in it bears on
this build.

## Scope

Build the ingestion of a Deepvue watchlist CSV into the framework, with its
verification contract and provenance record.

**Not in scope:** the dashboard panels themselves, ranking, live quotes, regime
layers. Those consume what this produces. Build the door, not the rooms.

## Source specs (both settled, both already agreed)

| Doc | ID |
|---|---|
| Watchlist Ingestion — CSV Drop, Naming Convention, Verification Contract | `1BsZcBSzSEJ1WOMz83_9uUGk0T0p_oVjE5P22h_xR6C8` |
| Watchlist Ingestion — ADDENDUM: Folder Path & Git Commit Decision | `1PBDUZqai5rPLDAfDnBkqZczjyvH4GpwdPCGZ_qWFW2E` |
| mockup-01-ingest.html — what this looks like on screen, incl. both refusals | `1yxUMpafpd7SdFsb8TORpg26KOoMY0M_J` |

## Settled — do not reopen

These were decided deliberately. If the build seems to want a different answer,
that is a signal to raise a question in `handoff/questions/`, not to choose.

| Decision | Detail |
|---|---|
| The system does **not** scan | The user exports from Deepvue by hand. No `reqScannerData`, no re-derivation, no "fallback scanner". See below. |
| Filename convention | `watchlist-YYYY-MM-DD-vN.csv`. Year-first so files sort chronologically unaided. `vN` tracks **real revisions** — it increments when the list actually changes. |
| Latest file wins | Chosen by the date in the **validated** filename, never by filesystem mtime. |
| Provenance companion required | The CSV does not carry the scan filter settings — those define the universe *boundary*. The user drops a dated screenshot or note alongside it. |
| Git commits everything | CSVs **and** provenance screenshots/notes are committed, nothing gitignored. Git becomes a dated immutable record of exactly which universe was traded each day, for free. |
| Staleness is shown, never enforced | A watchlist that does not change is a legitimate state (stable universe). Display age; do not alarm, do not force a rename, do not treat unchanged as error. |

### The two hard refusals

Ingestion **stops and alerts** — does not ingest, does not guess — on exactly two
conditions:

1. **Filename does not match the convention.** Never infer the date. A file
   named nearly-right is the case this refusal exists for.
2. **Provenance companion missing.** Ingesting a universe with no record of how
   it was built is the thing being prevented.

Everything else surfaces as information the user judges.

### Why there is no fallback scanner

`watchlist_builder.py` (which called `ib.reqScannerData`) was **retired**
2026-08-07 — see `docs/observations/watchlist-builder-contradicts-ingestion.md`.
Confirm it is actually gone from the tree; the decision is recorded but verify
the code followed.

The reasoning matters here because it will come up again: a labelled fallback is
how a deliberate decision gets quietly reversed on the morning the export fails.
That is exactly the moment nobody is checking labels, and a fallback producing a
*different population* would enter the sample without anyone deciding it should.
An RVOL mismatch shows up as a number; a population mismatch does not.

## One open item — ask before building

**The drop-folder path in the addendum predates the repo consolidation.**

The addendum says `D:\tradesignals\watchlists`, described as "inside the project
repo". The repo is now `D:\dev\momentum-harness`. That path either no longer
exists or is no longer inside the repo, and the addendum's stated *rationale*
(alongside the code that consumes it; committed to git) only holds if it sits
inside the current repo.

Do not guess. Ask the user to confirm the path. Everything else in this task is
decided; this one line is not.

## Design notes — proposed, confirm before committing to them

Marked separately from the settled block above because these are my reading, not
prior decisions.

- **Deepvue's metadata columns must carry their source in the name.** The export
  includes gap %, relative volume, ADR, float, market cap — real per-symbol
  values the dashboard can use immediately. But a Deepvue RVOL is not either of
  the two RVOLs this codebase computes. Name it `deepvue_rvol` (and likewise for
  the others) so it cannot silently stand in for a computed value. This repo has
  an established pattern for exactly this: a value carries its basis and refuses
  to compare across bases.
- **Unknown columns are preserved, not dropped.** Deepvue can change its export
  without telling anyone. Keep what you do not recognise rather than discarding
  it silently.
- **A missing *expected* column is a loud failure, not a `None`.** An absent
  column read as an empty value is the defect shape this codebase keeps hitting:
  a well-formed default that a later reader takes as a finding.
- **Ingestion produces a snapshot object carrying its own provenance** — source
  filename, parsed date, version, path to the provenance companion, ingest
  timestamp, row count. Anything downstream that displays watchlist data should
  be able to say where it came from without re-reading the file.

## Definition of done

- A valid CSV plus companion ingests, and the resulting snapshot carries full
  provenance.
- Each of the two hard refusals has a test that asserts the system **refuses**,
  and refuses visibly — not a silent skip, not a partial ingest.
- Staleness is computed and exposed as an age, with a test that it never raises
  or blocks.
- A malformed filename never results in an inferred date under any code path.
- `watchlist_builder.py` confirmed absent.

## Tenets this leans on

1 (distrust the data — including our own ingestion), 8 (fail loud, degrade
gracefully), 11 (a changed source lowers confidence, never discards).
