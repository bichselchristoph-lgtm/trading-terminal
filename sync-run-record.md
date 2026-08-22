# tools/sync_from_drive.py -- run record

**Not a report and not a manifest.** It answers one question: *did the inbound
sync run, and did it work.* Written on EVERY invocation, before the copy and
again after, so a run killed mid-copy leaves `last_attempt` moved and
`last_success` stale -- which is exactly the signature to look for.

Deliberately at the repository root, outside every configured source and
destination. A run record inside the destination cannot report a failure to
reach the destination.

The companion for the OUTBOUND direction is `export-run-record.md`. They are
two files on purpose -- see `RUN_RECORD` in `tools/sync_from_drive.py`.

`tests/test_sync_run_record.py` goes red if this file stops existing or stops
parsing.

**056: `refused` is a MACHINE-READABLE count, per pair, not a sentence.** The
`outcome` line below stays exactly as it is -- it is prose for Christoph and
for `verify.ps1` section 6, and the two zero-cases (`up to date` vs `REFUSED`)
must keep reading differently. `refused` exists because `outcome` prints the
same "files refused" condition two different ways depending on whether
anything else copied in the same run, and a test that matches one wording is
one rewording away from going false-green again -- `tests/test_inbound_run_
record_has_no_conflicts.py` reads THIS field and ignores the prose entirely.
Zero is written explicitly, per pair -- an absent field is never read as zero.

The four fields below are at COLUMN ZERO. **The reader below also tolerates
leading whitespace, and BOTH halves are deliberate** -- see `_FIELD`.

last_attempt : 2026-08-22T14:19:42+02:00

last_success : 2026-08-15T11:46:20+02:00

outcome      : regime_snapshots: 0 new · up to date (2 unchanged) | handoff_inbox: 0 new · 3 REFUSED · 24 unchanged | christoph_open: 11 new · 018-for-christoph-task-check-atr14-and-pdl.md, 021-for-christoph-task-52-week-basis.md, 023-for-christoph-task-third-drive-pair.md, 024-for-christoph-decision-read-only-api.md, 025-for-christoph-decision-percent-loss-limits.md, 026-for-christoph-decision-trades-max-day.md, 027-for-christoph-decision-52wl.md, 028-for-christoph-decision-type-dollar.md, 029-for-christoph-decision-006-007-visual-contract.md, 031-for-christoph-decision-ledger-persistence.md, 032-for-christoph-decision-gapped-over.md · 1 differing

refused      : regime_snapshots: 0 | handoff_inbox: 3 | christoph_open: 1
