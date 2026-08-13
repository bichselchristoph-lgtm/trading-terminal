---
id: 027
title: The recurring scheduled-run failures become ledger rows, and the copier gains the one collision it cannot see
status: READY
blocks: []
type: correction
owner: claude-code
depends: 016, 026
---

# 027 — Rule 15, applied for the first time

**This file is also the end-to-end proof of the Drive channel.** It was authored into Google
Drive `momentum-inbox-handoff` by the design session and placed by nothing else. **If it
appears in `handoff/inbox/` and is named in the copier's report, the copy path is proven on
the real channel** — which `026`'s done-note correctly recorded as inferred rather than
demonstrated. **Say so explicitly in the done-note: quote the line that names this file.**

---

## Part 1 — Five recurring `could_not_do` entries become rows in the ledger

**Project instructions rule 15:** any `could_not_do` entry that recurs on three consecutive
snapshots becomes a row in `docs/observations/OBSERVATIONS.md`, with the ledger test that goes
red. **This is the first time it is applied, and it is four days late.**

**Observation, not inference:** the counts below are quoted from the 2026-08-13 snapshot's own
text, which states its own recurrence count per row. **I did not recount them across files.**
Where you can cheaply verify a count against `docs/regime-snapshots/`, do — **a disagreement
is a finding about the snapshot, not a reason to skip the row.**

| Ledger row | Recurrence stated in the 08-13 snapshot | What it disables |
|---|---|---|
| **HYG pre-market credit unreadable at 05:00** — 0 shares traded through 05:15 ET, below the 25,000-share floor | 4th consecutive session | Strip row 2, **and veto 2** |
| **No market-wide pre-market gap-breadth source** at any hour in this toolset; the 07:00–09:30 window is also not open at read time | 4th consecutive session | Strip row 10, **and veto 4** |
| **VIX-family failure, a different mode each session** — snapshot empty, history errored, `is_close` flag | 4th consecutive session | Strip row 1's ±3% legs |
| **COR1M 6-month percentile unavailable** — dispersion | 5th consecutive session | **State-machine rule 2, every session** |
| **NYSE up/down volume and % of S&P 500 above 20DMA unavailable** | 4th consecutive session | Layer I breadth row is half-unsourced |

**One more, below the threshold and recorded as a watch rather than a row:** HY OAS
unreachable at FRED — **twice, not three times.** Do not open a row for it. **Do record in the
done-note that it is at 2 of 3**, because the thing rule 15 exists to prevent is a count
nobody is holding.

**Each row states the disabled consumer, not just the missing input.** "Dispersion
unavailable" is a supply fact; "state-machine rule 2 cannot be exercised" is what it costs.
**A ledger of missing inputs gets skimmed; a ledger of disabled consumers does not.**

**Do not fix any of them here.** Four are external supply problems and one is an entitlement.
**This task makes them visible and countable. It does not source them.**

---

## Part 2 — Make rule 15 mechanical, because prose is what failed

**These five sat in a daily file for four days and nothing broke.** That is §7's *the read is
the implementation*, and the fix is the same one this project uses everywhere: **something has
to fail.**

Add a test over `docs/regime-snapshots/`:

- Parse `could_not_do` from every snapshot `.yaml`.
- Group entries into recurring items. **Exact string matching will not work** — the 08-13
  entries carry that session's numbers inside the text. **Match on a declared key, and if the
  snapshots do not carry one, say so plainly rather than inventing a fuzzy matcher whose
  false-negative rate nobody knows.**
- **Any group at 3+ consecutive sessions with no matching row in `OBSERVATIONS.md` fails the
  test.**

**If a reliable key cannot be extracted from the current snapshot format, do not build a
heuristic.** Stop, and say in the done-note what the snapshot format would have to carry — a
stable `id` per `could_not_do` entry — for the test to be sound. **That is a finding about
`REGIME-PROMPT.md`, and I will amend the prompt.** A matcher that silently mis-groups is worse
than no test, because its green would mean nothing (§7).

**Demonstrate the test red before accepting green** — delete one of Part 1's rows, watch it
fail, restore it.

---

## Part 3 — The collision the copier cannot currently see

**Observation, from reading `tools/sync_from_drive.py`:** `by_number` is built once from the
*destination* before the loop, and is not updated as files are copied. So:

- arriving file vs **existing inbox file**, same `NNN`, different name → **caught.** Correct.
- arriving file vs **another arriving file**, same `NNN`, different name, neither in the inbox
  → **both copied, silently.**

**This is faithful to `026`'s text**, which describes the check against "an existing inbox
file". **It is not a defect against the task.** It is a gap in the mechanism the task exists to
provide, and it is reachable: the design session assigns numbers by reading the inbox at a
moment, and Drive introduces a gap between reading and landing — **which is precisely the
argument `026` makes for having the check at all.** Two files written in one sitting land
together.

**Fix:** register each copied file's number in `by_number` as it is copied, so a second
arrival with the same number collides with the first. **The first one is already placed by
then** — so report it as a collision against a file this run copied, and say so in those words.
**Do not delete the first.** Nothing this tool has written is removed by this tool.

Add the test. **Two source files, same `NNN`, different names, empty destination.**

---

## Part 4 — The regime pair stays unexercised, and that was the right call

**No work here.** `026`'s done-note declined to run the `regime_snapshots` pair because `025`
owns the gap analysis, the `check-ignore` assertion and the daily wiring, and running the copy
would make `025` look partly done. **That reasoning is correct and is recorded here so it is
not re-litigated.** `025` remains unstarted and owns that pair entirely.

---

## Done when

- Five rows exist in `docs/observations/OBSERVATIONS.md`, each naming its disabled consumer.
- The rule-15 test exists **and has been seen red**, or the done-note states precisely why a
  sound one cannot be built against the current snapshot format.
- The arriving-vs-arriving collision is caught, with a test.
- This file's arrival is quoted from the copier's report.

---

## Deliverable

`handoff/done/027-for-code-observations-ledger-catchup.md`:

1. The five ledger rows, quoted. Any recurrence count that disagreed with the snapshot text.
2. HY OAS confirmed at 2 of 3, or corrected.
3. The rule-15 test red, then green — **or the reason it cannot be sound**, stated as a
   requirement on `REGIME-PROMPT.md`.
4. The arriving-vs-arriving collision test, and its report line.
5. **The copier's report line naming this file**, proving the Drive copy path end to end.
6. **What you could not do**, and why. Empty is suspicious.
7. `verify.ps1` run at `<time>`.
