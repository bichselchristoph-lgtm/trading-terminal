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

The three fields below are at COLUMN ZERO. **The reader below also tolerates
leading whitespace, and BOTH halves are deliberate** -- see `_FIELD`.

last_attempt : 2026-08-15T11:46:20+02:00

last_success : 2026-08-15T11:46:20+02:00

outcome      : christoph_open: 0 new · up to date (4 unchanged)
