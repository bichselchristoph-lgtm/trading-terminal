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

last_attempt : 2026-08-22T17:18:19+02:00

last_success : 2026-08-22T17:18:20+02:00

outcome      : 2 new - momentum-code-handoff/verify-output.md, momentum-christoph-done/034-for-christoph-decision-the-rolling-window-unit.md

head         : 278d6a73c3e305d3833c8c5d986bbd4b45d5eec1 Closing sync run: 034 template reappeared (OBS-077 pattern), routine record update
