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

last_attempt : 2026-08-15T10:06:59+02:00

last_success : 2026-08-15T10:07:00+02:00

outcome      : 4 new - momentum-code-handoff/done/041-thirteen-levels-are-rth.md, momentum-code-handoff/inbox/039-for-code-spec-risk-and-trade-classification.md, momentum-code-handoff/inbox/040-for-code-task-readonly-stop-and-accounting-probe.md, momentum-code-handoff/inbox/041-for-code-spec-thirteen-levels-are-rth.md

head         : be76a43cb56644ef905f7a65cfecb6cf90efb10d 041 done-note, and 041's task file
