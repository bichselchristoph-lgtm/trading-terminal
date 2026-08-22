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

last_attempt : 2026-08-22T22:37:37+02:00

last_success : 2026-08-22T22:37:37+02:00

outcome      : 3 new - momentum-code-handoff/inbox/061-for-code-task-permission-policy-test.md, momentum-christoph-done/035-for-christoph-task-claude-permissions-and-databento-history.md, momentum-christoph-done/036-for-christoph-task-uat-060-panels-render-once.md

head         : 8d0d46b8f68b0241c8139d181d34c712390c4b3c 060: B-001 fixed -- async check-then-act race in _apply_fit
