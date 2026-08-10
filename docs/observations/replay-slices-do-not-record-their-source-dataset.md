---
recorded: 2026-08-10
recorded_by: Claude Code, during task 008a while looking for an independent volume source
status: OBSERVATION_OPEN
review_trigger: replay_slice_provenance_companion_specified
review_trigger_kind: gate
review_trigger_note: >
  Comes due when someone next needs a replay slice to answer a question about
  volume or venue scope, which is when the missing provenance actually bites.
  A calendar date would be theatre -- the slices sit unread for weeks at a
  time and the gap costs nothing until one is used as evidence.
---

# A replay slice on disk cannot be traced to the venue it came from

## What was seen

`replay/AMZN-2026-08-03-open.json` carries `publisher_id: 2` on every message and nothing
else identifying its origin. No dataset name, no schema name, no download manifest, no
companion file. The only provenance the slice has is an integer that means nothing without
the Databento publisher map, and that map is not in this repo.

The consequence was hit directly in task 008a. The capture was the only independent volume
source available for Test 5, and **the finding had to be written without naming a venue**,
because naming one would have been a guess. A 330 MB dataset that was paid for could only be
described as "a single publisher, identity not established".

## What produced it

`tools/make_replay_slice.py`. Two things combine:

- Line 72 sets `publisher_id = 2` as a **default before the loop**, then overwrites it from
  the first record. A slice built from a source that never populated `hd.publisher_id`
  therefore emits `2` — indistinguishable from a slice genuinely captured from publisher 2.
- The synthetic snapshot rows written at the slice boundary (lines 93–102) reconstruct `hd`
  from that variable rather than carrying a source record through.

Neither is wrong alone. Together they mean the output's most identifying field may never
have come from the data, and the `src` path the operator typed — which *does* identify the
dataset — is discarded at exit.

## Why this is more than untidiness

Databento is billed per byte, and `harness/spend.py` exists so every paid pull is estimated,
approved and ledgered. That ledger records **what was bought**. This gap means the artefact
on disk cannot be matched back to the purchase: a capture and its receipt cannot be
reconciled without remembering which command produced which file. The spend controls
themselves are intact — this is the provenance chain downstream of them.

It also silently limits reuse. A venue-scoped capture and a consolidated one answer
completely different questions about volume, and a reader six months out has no way to tell
which one they are holding. In 008a that turned a potentially decisive comparison into a
labelled lower bound.

## What would settle it

Have `make_replay_slice.py` write a companion `*.provenance.json` beside every slice
recording: the `src` path, the resolved `publisher_id` **and whether it was observed in the
data or defaulted**, the `instrument_id`, the symbol, the requested `--start`/`--end`, the
message count, and the source file's size and mtime. Then assert in a test that a slice
without its companion fails.

One trap to clear on the way. `scanner_watchlists/` already solves this same problem the
same way, and `tests/test_watchlist_ingest.py` pins it with `git check-ignore` — including
the detail that `.gitignore`'s unanchored `*.json`-family rules would otherwise swallow the
companion silently. Any fix here must clear that same trap, or the provenance file will
appear committed right up until someone goes looking for it.

## Route out of this folder

Not a hypothesis: it changes no measurement, so it does not belong in
`preregistration.yaml`. It becomes a `docs/specs/` entry once the companion format is
decided, and this file is then dropped with that decision recorded.
