# momentum

Intraday momentum research harness and live console. **Born 2026-08-10. Deliberately
near-empty.**

This tree is being populated one file at a time from `D:\Dev\momentum-harness`, which is now
archived reference. Nothing is copied wholesale — that is what produced the predecessor's
state, where the `README.md` you would have read here described a different repository
entirely.

**So: this file describes what is actually in the tree today.** When that stops being true,
it is a defect.

## What is here today

```
docs/specs/       location of record for SPEC.md, BUILD-PLAN.md, REGIME-PROMPT.md,
                  DRIVE-ARCHIVE-LIST.md — NONE YET SUPPLIED (H9 owns this)
handoff/          inbox/ and done/ — tracked, unlike in the predecessor
tests/            four tests, all structural: they police how files arrive
tools/adopt.py    the adoption gate
ADOPTION-LOG.md   one row per adopted file
EVIDENCE-CARRY.md one row per carried evidence file, with hashes
```

No `core/`, no `live/`, no `harness/`. Those directories appear when something is adopted
into them, not before.

## How things get in

Two routes, and only two.

**The adoption gate** — for code. Drop a candidate in `D:\Dev\_adopt\` with a
`<name>.provenance.md`, then:

```powershell
C:\venvs\trading\Scripts\python.exe tools\adopt.py --check <name>
```

It refuses without a provenance companion, without a behavioural test, on a name collision
with different bytes, or when the origin is `imported`/`unknown` and no person has recorded
a decision. Import-smoke is not a test.

**The evidence carry** — for records of what happened. Carried byte-identical and verified
by hash, never cleaned or regenerated.

`tests/test_adoption_log_complete.py` fails if a tracked file appears by any other route.
That is what makes the gate a mechanism rather than a convention.

## Running it

There is no `python` on PATH.

```powershell
C:\venvs\trading\Scripts\python.exe -m pytest
```

A near-empty test run is the expected result.

## Related trees

| directory | status |
|---|---|
| `momentum-harness/` | **archived reference.** Predecessor. Keeps the full git history — this repo starts at commit one. |
| `tws_order/` | **deliberately separate.** The only code that can place a live order. |
| `tradesignals/`, `trading-scripts/`, `orb_tools/`, `ibkr_tape_tools/` | absorbed into the predecessor, remotes archived read-only. Do not edit. |

See `CLAUDE.md` for the handoff convention and the full refusal table.
