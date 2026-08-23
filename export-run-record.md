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

last_attempt : 2026-08-23T17:39:50+02:00

last_success : 2026-08-23T17:39:51+02:00

outcome      : 5 new - momentum-code-handoff/done/075-attach-still-slow-measured.md, momentum-code-handoff/inbox/075-for-code-task-attach-still-slow.md, momentum-code-handoff/inbox/076-for-code-task-tws-order-latency.md, momentum-code-handoff/inbox/077-for-code-task-levels-rail.md, momentum-code-handoff/verify-output.md

head         : 11309f6c9dc04f297df777b1456c14c5c45e5065 072: attaching a second symbol accumulated instead of replacing the first -- and the first fix broke SPEC.md 4.2 before it landed
