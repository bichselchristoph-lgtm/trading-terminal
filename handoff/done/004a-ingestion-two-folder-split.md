---
task: 004a
title: Watchlist ingestion — ADDENDUM: two-folder drop/archive split
status: READY
written: 2026-08-09
amends: 004-watchlist-ingestion.md
---

# 004a — ADDENDUM to 004: two-folder split

**Read this together with `004-watchlist-ingestion.md`.** It closes that
artifact's "One open item" and changes one part of its structure. Everything
else in 004 stands unchanged.

## The decision

Two folders, not one.

| Folder | Path | In repo? | Committed? |
|---|---|---|---|
| DROP (user exports here) | `D:\watchlists_drop` | No | No — unversioned scratch |
| ARCHIVE (system writes here) | `D:\dev\momentum-harness\scanner_watchlists\` | Yes | Yes — CSV **and** provenance companion |

Flow: the user exports from Deepvue into the drop folder. The system watches the
drop folder, validates, and **only on successful ingestion** copies the CSV and
its provenance companion into the archive folder inside the repo, where git
records them.

## Why, and what it buys

The addendum in the original spec (`1PBDUZqai5rPLDAfDnBkqZczjyvH4GpwdPCGZ_qWFW2E`)
put the drop folder inside the repo so git would record it. That rationale is
preserved here — git still records everything that matters — but the split adds
something the single-folder version could not:

**The git history becomes a record of universes actually ingested, not
everything ever dropped.** Files that failed the verification contract never
reach the archive, so they never enter the provenance record. A malformed
filename or a CSV with no provenance companion stays in the drop folder as
scratch, which is what it is.

The original spec's "commit everything, nothing gitignored" still holds — it now
applies to the archive folder.

## Consequences for the build

These follow from the split and are **not** optional details:

- **The copy is part of ingestion, not a separate housekeeping step.** A
  successful ingest that did not archive is a failed ingest. Do not let the two
  come apart.
- **The provenance companion travels with the CSV.** Archiving the CSV alone
  would defeat the point — the boundary of the universe is in the companion.
- **Filename collision with differing content is a HARD REFUSAL — a third one,
  in addition to the two in 004.** If `watchlist-YYYY-MM-DD-vN.csv` already
  exists in the archive and the incoming file's content differs, stop and alert.
  Do not overwrite, do not silently skip, do not auto-increment the version.
  It means either the list was revised without bumping `vN`, or two different
  universes are wearing the same name. Both need a human.
  Identical content under the same name is a no-op, not an error — re-dropping
  the same file is harmless.
  **Content identity is decided on a newline-NORMALIZED hash, not on raw
  bytes.** `.gitattributes` pins `* text=auto eol=lf`, so an archived CSV comes
  back out of a fresh clone with LF while the Deepvue drop has CRLF; a byte
  comparison would refuse an identical file as a collision on any machine that
  had re-cloned. The raw sha256 is still recorded for the audit trail.
- **Schema drift is a HARD REFUSAL — a fourth one.** Added during the build,
  recorded here so the spec is not behind its own implementation. It is 004's
  design note 3 ("a missing *expected* column is a loud failure, not a `None`")
  promoted to the same standing as the other three, because it has the same
  shape: an absent column read as a column of `None`s is a well-formed table
  that a later reader takes as a finding.
  The distinction that makes it safe: a missing **column** refuses, a blank
  **cell** in a present column does not. Those are different failures, and
  collapsing them means one empty float value takes the whole watchlist down on
  a trading morning. A cell that is present and *unparseable* refuses too
  (`WatchlistDataError`, a sibling of the schema refusal rather than a fifth
  peer) — an unrecognised token in a numeric column means the export is not the
  shape we think it is, and that is not a `None`.
- **Ingestion reads the archive, not the drop folder, for anything historical.**
  The drop folder is a doorway. Nothing downstream should ever resolve a past
  watchlist by looking there.
- **Check `.gitignore`.** A repo assembled from six others tends to carry
  inherited patterns; a bare `*.csv` or `watchlists/` rule would silently defeat
  the whole provenance record. The files would look committed right up until the
  day someone went looking for one.
  **Found, and it was there — wearing a different extension.** No `*.csv` rule
  and no `watchlists/` rule, but `*.jsonl`, `*.zst` and `*.parquet` are all
  unanchored and match at any depth, so an archived companion or ledger in any
  of those formats was ignored. Closed with an explicit negation block for
  `scanner_watchlists/` plus a test asserting `git check-ignore`, so a future
  broad rule fails a test instead of eating the record.

## Definition of done — additions to 004's list

- A valid drop results in CSV **and** companion present in
  `scanner_watchlists\`, and git sees them.
- A drop failing **any** hard refusal leaves the archive folder **untouched** —
  assert this, it is the point of the split. Every refusal must therefore be
  evaluated before anything is written, including before the archive directory
  is created: a failed first-ever drop must not bring `scanner_watchlists\`
  into being.
- Same-name-different-content refuses loudly; same-name-same-content is a no-op.
