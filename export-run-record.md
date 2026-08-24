# export-handoff.ps1 -- run record

**Not a report and not a manifest.** It answers one question: *did the export
run, and did it work.* Written on EVERY invocation, before the copy and again
after, so a run killed mid-copy leaves `last_attempt` moved and
`last_success` stale -- which is exactly the signature to look for.

Deliberately outside `handoff/`, `christoph/done/` and the Drive root. A run
record inside the destination cannot report a failure to reach the destination.

`verify.ps1` section 5 prints the age of `last_success`.
`tests/test_export_run_record.py` goes red if this file stops existing or
stops parsing.

The four fields below are at COLUMN ZERO and must stay there. Indenting them to
render as a markdown code block is what broke `Read-LastSuccess` on the first
cut of this file.

last_attempt : 2026-08-24T08:54:50+02:00

last_success : 2026-08-24T08:54:52+02:00

outcome      : 2 new - momentum-code-handoff/done/084-for-code-task-rvol-curve-cache.md, momentum-code-handoff/verify-output.md

head         : be8a232d86ce9ab2ca545a392c0c7d661c6cd23d 083: RVOL's anchor becomes a configured choice, defaults to RTH, and renders (B-049)
