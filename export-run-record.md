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

last_attempt : 2026-08-22T14:20:59+02:00

last_success : 2026-08-22T14:21:00+02:00

outcome      : 11 new - momentum-code-handoff/verify-output.md, momentum-christoph-done/018-for-christoph-task-check-atr14-and-pdl.md, momentum-christoph-done/023-for-christoph-task-third-drive-pair.md, momentum-christoph-done/024-for-christoph-decision-read-only-api.md, momentum-christoph-done/025-for-christoph-decision-percent-loss-limits.md, momentum-christoph-done/026-for-christoph-decision-trades-max-day.md, momentum-christoph-done/027-for-christoph-decision-52wl.md, momentum-christoph-done/028-for-christoph-decision-type-dollar.md, momentum-christoph-done/029-for-christoph-decision-006-007-visual-contract.md, momentum-christoph-done/031-for-christoph-decision-ledger-persistence.md, momentum-christoph-done/032-for-christoph-decision-gapped-over.md

head         : 1f71a93c9c205e698855e0673515a7b284ca8448 OBS-077 confirmed a third time, at scale: 11 templates reappeared
