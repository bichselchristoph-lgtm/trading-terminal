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

last_attempt : 2026-08-23T16:17:59+02:00

last_success : 2026-08-23T16:17:59+02:00

outcome      : 3 new - momentum-code-handoff/done/071-context-block-reduced-to-four-rows.md, momentum-code-handoff/inbox/071-for-code-task-attached-context-block.md, momentum-code-handoff/verify-output.md

head         : 73b5caa088bbb80b709477cb262ef0e4bb57a0bf 070: ADR% used lands, ATR/ADR$/room leave the panel and the record, cooldown was never actually gated
