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

last_attempt : 2026-08-22T12:55:30+02:00

last_success : 2026-08-22T12:55:31+02:00

outcome      : 5 new - momentum-code-handoff/done/056-two-false-guards.md, momentum-code-handoff/inbox/056-for-code-task-two-false-guards.md, momentum-code-handoff/verify-output.md, momentum-christoph-done/018-for-christoph-task-check-atr14-and-pdl.md, momentum-christoph-done/021-for-christoph-task-52-week-basis.md

head         : ccfdb589f4ad01a12f1c2eff3e99da328263e507 Closing sync run: reappeared 021 template, OBS-077 second instance
