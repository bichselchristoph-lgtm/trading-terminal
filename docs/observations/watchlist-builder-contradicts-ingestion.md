---
recorded: 2026-08-07
status: OBSERVATION_RESOLVED
review_trigger: none_resolved
review_trigger_kind: gate
review_trigger_note: >
  Resolved 2026-08-07 by decision: retired. Kept as a record of why, because
  the reasoning matters more than the file did.
---

# RESOLVED — watchlist_builder retired

Overlap 6 from the consolidation plan. **Decision: retire.** Taken 2026-08-07.

## What it did

`watchlist_builder.py` called `ib.reqScannerData` with `TOP_PERC_GAIN` and
`HOT_BY_VOLUME`, deduped, applied liquidity/gap/ADR filters, and wrote
`watchlist_YYYYMMDD_HHMM.csv`. It built a watchlist **by scanning**.

## Why it is gone

The system ingests the Deepvue CSV export and does **not** re-scan. That was a
deliberate decision about source drift (Tenet 11): two scanners run at
different moments against different universes return different candidates, and
a system that re-derives its own watchlist cannot be compared against the one a
human actually traded.

## Why "keep it as a labelled fallback" was rejected

It was the option I leaned toward — it is the only thing in the tree that could
produce a watchlist without a Deepvue subscription. The argument against is
better: **a labelled fallback is how a deliberate decision gets quietly
reversed on the morning the export fails.** That is precisely the moment nobody
is checking labels, and a fallback that produces a *different population* would
enter the sample without anyone deciding it should.

The same reasoning that keeps `deepvue_rvol` from ever mixing with the two
computed RVOLs applies here, and more strongly: an RVOL mismatch shows up as a
number, a population mismatch does not.

## Recoverable

Not lost. It is in the archived `orb_tools` repo, read-only and permanent at
`github.com/bichselchristoph-lgtm/orb_tools`, and in this repo's history up to
commit `1e6c893`.
