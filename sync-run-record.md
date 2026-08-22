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

last_attempt : 2026-08-22T18:33:12+02:00

last_success : 2026-08-15T11:46:20+02:00

outcome      : regime_snapshots: 0 new · up to date (2 unchanged) | handoff_inbox: 1 new · 060-for-code-bug-panel-duplication-at-real-sizes.md · 3 differing | christoph_open: 0 new · up to date (3 unchanged)

refused      : regime_snapshots: 0 | handoff_inbox: 3 | christoph_open: 0
