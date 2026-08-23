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

last_attempt : 2026-08-24T00:28:05+02:00

last_success : 2026-08-24T00:28:05+02:00

outcome      : 5 new - momentum-code-handoff/done/083-for-code-task-rvol-anchor.md, momentum-code-handoff/inbox/083-for-code-task-rvol-anchor.md, momentum-code-handoff/inbox/084-for-code-task-rvol-curve-cache.md, momentum-code-handoff/inbox/085-for-code-task-answer-two-questions.md, momentum-code-handoff/verify-output.md

head         : 385812b1dcc1f9ed76da325fb9017db9ce8906e3 082: batched vs concurrent dispatch, measured on live TWS -- B-138
