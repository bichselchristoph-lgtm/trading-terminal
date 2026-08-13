---
id: 028
title: Correct 027, carry REGIME-PROMPT v1.8 into the tree, and address the two permanently-red tests
type: correction
owner: claude-code
depends: 023, 027
---

**Status** WRITTEN

# 028 — A correction, a sync, and two tests that have never been green

**Run this before `027`.** Part 1 removes two rows from `027`'s Part 1 that would otherwise
record blindnesses that no longer exist.

---

## Part 1 — `027` Part 1 is wrong on two of its five rows

**`027` was written before the design session read the scheduled task's stored prompt.** Two of
the five recurring failures it asks you to enter in the ledger describe rows that were **cut**
from the regime prompt, not rows that are still failing:

| `027` row | Correction |
|---|---|
| **HYG pre-market credit unreadable at 05:00** | **Do not open a live row.** Strip row 2 was cut in prompt v1.7. Open a **closed** row instead: the failure, the four sessions of evidence, and *"resolved by cutting the row, v1.7"*. It is history, not a blindness. |
| **HY OAS at 2 of 3, watch it** | **Delete this instruction entirely.** Layer I row 1 was cut in v1.7 and replaced by *credit, prior session* from IBKR daily bars. There is nothing to watch. |

**The remaining three stand unchanged and are still live blindnesses:** gap breadth, the
VIX-family failure, COR1M dispersion. **Plus the fourth `027` names and this correction does not
touch:** NYSE up/down volume and % above 20DMA.

**Why this happened, recorded rather than absorbed.** `027` took its recurrence counts from the
2026-08-13 snapshot, which was produced under prompt v1.6. **The prompt had already moved and
the snapshot could not know it.** A count read from an artifact is a count as of that artifact's
world, and `027` presented it as current. *This is the project's first pattern — a well-formed
value answering a different question — committed by the design session, in a task file whose own
Part 1 warns about exactly that.*

**`027` Parts 2, 3 and 4 are unaffected.**

---

## Part 2 — The stored prompt is v1.8. Carry it into the tree

**The scheduled task was still holding v1.6.** v1.7 was authored as a project document on
2026-08-13 and **never pushed to the trigger**. It was live nowhere. Discovered by reading the
trigger's stored prompt rather than trusting the document's own §0, which asserted it *was* the
stored prompt. **The task now holds v1.8**, which contains v1.7's changes plus one addition.

**What v1.8 adds — and `027` Part 2 depends on it.** `could_not_do` is now a list of
`{id, detail}` mappings rather than a list of strings, with a stable snake_case `id` per
failure. **This is the declared key `027` Part 2 asks for.** With it, the rule-15 recurrence test
is sound; without it, it could only have been a heuristic. **The first snapshot carrying ids is
2026-08-14** — snapshots 08-10 through 08-13 have none, so the test must treat pre-08-14 files as
un-keyed and say so rather than guessing.

**The eleven live ids**, to be reused verbatim whenever the same failure recurs:

`gap_breadth_no_source` · `vix_family_failure` · `dispersion_cor1m_unavailable` ·
`nyse_breadth_unavailable` · `macro_shock_sd_basis_unavailable` · `slow_frame_not_resourced` ·
`universe_earnings_count_unavailable` · `dxy_no_ibkr_entitlement` ·
`audjpy_no_ibkr_entitlement` · `short_bar_array` · `snapshot_endpoint_degraded`

**Two retired ids that must never reappear:** `hyg_premarket_no_print`, `hy_oas_unreachable`.
**If either shows up in a future snapshot, that is a finding that a cut row came back** — not a
data problem.

**The work:**

1. Replace `docs/specs/REGIME-PROMPT.md` with v1.8. **The design session will deliver the full
   text through the Drive channel as a separate file** — do not reconstruct it from this task,
   and do not edit the v1.7 copy into shape.
2. Update `test_regime_prompt_invariants.py`'s version pin to `1.8`. **Demonstrate it red
   against the v1.7 copy first.**

**And name the gap this episode exposed, in `docs/observations/OBSERVATIONS.md`:** the version
pin watches whether the tree copy matches the authored document. **Nothing watches whether the
authored document reached the scheduled task.** v1.7 passed every check available to it while
never running. **Do not try to build that check here** — this session cannot read the trigger and
the tree cannot either. Record it as an open gap with no owner, which is what it is.

---

## Part 3 — Two tests have been red on every run this project has recorded

`verify-output.txt` at HEAD `1559320` reports `2 failed, 236 passed`, and names them:

```
FAILED tests/test_handoff_state_declared.py::test_every_task_file_declares_a_state
FAILED tests/test_uat_has_a_file.py::test_every_declared_uat_exists_as_a_file
```

**Both are the design session's debt, not yours.** They are reported here so they stop being
described as "the same two people-blocked failures" — a phrase that has now appeared in three
consecutive done-notes and reads more like weather than like work.

**§7: a test that passes is not a test that works. The converse is also true.** A test red on
every run for a week has stopped carrying information: nobody reads a summary line to learn the
count is still 2. **Two permanently-red tests are how a third one arrives unnoticed.**

### 3a. The state header, and the conflict it has with the Drive channel

`test_every_task_file_declares_a_state` requires `**Status** <state>` in the first 20 lines,
where `<state>` is one of the five protocol states. **Task files `021`–`027` carry
`status: READY` in YAML frontmatter instead** — a different vocabulary answering a different
question, authored by the design session in ignorance of the convention. **This file carries the
header correctly; every future one will.**

**Do not backfill `021`–`027`, and the reason is a real conflict rather than caution.** Those
files exist in `handoff/inbox/` and in the Drive folder. Editing the inbox copies makes all seven
differ from their Drive originals, and `026`'s copier would then report seven differing files on
every run, forever — **the `026` conflict multiplied by seven.**

**The deeper problem, stated because it will not go away:** the five states describe a *handoff
that progresses*, and the Drive channel makes a task file *immutable*. **A mutable state cannot
live in an immutable file.** `**Status** WRITTEN` is true when written and wrong within the hour.

**Recommendation, for Christoph, not for you to implement here:** the header declares the state
at authorship and is never updated — it is a provenance stamp, not a status — and the live state
moves to a ledger the protocol document owns. **Do not change the test or the protocol in this
task.** Record the conflict in `OBSERVATIONS.md` with both halves named, and stop.

### 3b. The UAT file is Christoph's to place

`test_every_declared_uat_exists_as_a_file` is red because `020`'s done-note declares a UAT with
no matching file in `christoph/open/`. **The file must be authored by the design session and
placed by Christoph.** No Claude writes to `christoph/`, and rule 12 forbids an exit test that
would require you to. **Take no action.** Named here so it is attributed rather than inherited.

---

## Part 4 — One claim in `023`'s done-note disagrees with the tree

`023`'s note lists `022` as "queued and unstarted". **`handoff/done/022-for-code-secrets-hygiene.md`
exists** and an earlier session reported `022` built, committed and exported. **Observation, not
diagnosis:** two statements disagree; this task does not say which is wrong.

Check it and say plainly which is true. **If `022` is done, the note's outstanding list was
written from memory rather than from the folder** — which is the same failure the verification
gate exists to catch, arriving in the part of the note nobody verifies.

---

## Done when

- `027`'s two corrected rows are reflected in whatever `027` produces — **or `027` has not run
  yet, in which case say so and this Part is a precondition rather than a fix.**
- `docs/specs/REGIME-PROMPT.md` is v1.8 and the version pin test has been seen red, then green.
- `OBSERVATIONS.md` carries: the unwatched prompt-sync gap, and the state-header conflict.
- Part 4 is answered with the folder, not from memory.

---

## Deliverable

`handoff/done/028-for-code-prompt-sync-and-two-red-tests.md`:

1. Whether `027` had already run, and what that means for Part 1.
2. The version pin red, then green.
3. The two `OBSERVATIONS.md` rows, quoted.
4. Part 4's answer, with the evidence you used.
5. **What you could not do**, and why. Empty is suspicious.
6. `verify.ps1` run at `<time>`. **Under HANDOFF-PROTOCOL v1.2, do not quote its output.**
