# ADOPTION-LOG

One row per file adopted into this tree through the gate (`tools/adopt.py`).

`tests/test_adoption_log_complete.py` asserts every tracked file outside the bootstrap
allowlist appears here or in `EVIDENCE-CARRY.md`. A file that arrives by any other route
turns the suite red — that is the mechanism, and it is why this table is not documentation.

Evidence does **not** appear here. It is carried, not adopted, and lives in
`EVIDENCE-CARRY.md`.

| date | path in new tree | source path | origin | reason | test that covers it | adopted by |
|---|---|---|---|---|---|---|

**The table is empty, and that is the correct state as of 2026-08-10.**

Nothing has been adopted because M001's input — H9a's file inventory, which classifies every
candidate as `authored`, `imported` or `unknown` — does not exist. Refusal 4 keys directly
on that classification, so every candidate in `momentum-harness` currently refuses at the
same gate, for the same reason, and adopting anything would mean inventing the origin value
the refusal exists to demand.

An empty table here is not work outstanding. It is the gate holding.
