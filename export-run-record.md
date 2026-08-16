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

last_attempt : 2026-08-16T11:34:05+02:00

last_success : 2026-08-16T11:34:06+02:00

outcome      : 5 new - momentum-code-handoff/done/052-product-spec-pointer.md, momentum-code-handoff/inbox/049-for-code-task-validate-the-owned-corpus.md, momentum-code-handoff/inbox/050-for-code-task-the-tape-window.md, momentum-code-handoff/inbox/051-for-code-task-the-basis-audit.md, momentum-code-handoff/inbox/052-for-code-task-product-spec-pointer.md

head         : dc4697bbb8cea778b384e8cacc969575e15f86a5 052: NOW.md offers 006 and 007 as ready, which is OBS-071 measured
