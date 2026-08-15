---
id: 044
title: Colour links, a boundary is not a float, and three (not five) duplicate ledger ids
type: spec
class: admin
owner: claude-code
answers: OBS-059, OBS-054, OBS-062
---

**Status** RUNNING

# 044 — three parts done, and Part 3 stopped on `044`'s own instruction

**Part 3 is not done, and stopping was the instruction rather than a judgement call.**
`044` Part 3 rests on a premise git contradicts, and once corrected, its **rule** and the
**reason given for the rule** point in opposite directions. `044` closes that Part with an
unconditional clause covering exactly this case, and it fires. **`handoff/questions/044-duplicate-ledger-ids.md`
holds the fork. Nothing was renumbered.**

Parts 1, 2 and 4 are complete.

---

## Part 3 first, because it is the one that needs a decision

### What `044` assumes

> **Why that way round.** `037` allocated `044`–`047` first, and `041` and `043` cite them in
> done-notes **already exported to Drive** … **Moving the earlier findings would break three
> documents; moving the later ones breaks none.**

### What git says

**`021`'s rows were allocated first, not `037`'s.** Established by `git log -S` on distinctive
text from each row, which is `044`'s own suggested method:

| commit | when | rows |
|---|---|---|
| `e625df3` | **2026-08-13 22:12** | `021`'s — `keepUpToDate` dies silently · the ~5 s beat · `survived_window` |
| `eba938d` | **2026-08-14 14:01** | `037`'s — inbound copier has no record · export cannot run from a worktree · worktrees outlived their tasks |

`git merge-base --is-ancestor e625df3 eba938d` succeeds. The dates on the rows agree.

**And it is `037`'s meanings that everything cites** — the reverse of what `044` assumed:

| id | files under `handoff/` citing it | meaning intended |
|---|---|---|
| `OBS-044` | 3 | the inbound copier |
| `OBS-045` | 8 | export cannot run from a worktree |
| `OBS-046` | 9 | worktrees outlived their tasks |

**`021`'s done-note cites none of the three.**

### Why that stops the work

Applying the rule as written — *earlier keeps the number* — reallocates **`037`'s** rows, and
retargets nine files under `handoff/`, several already on Drive. Every existing citation of
`OBS-046` would silently come to mean *"a probe reported `survived_window: true`"* instead of
*"worktrees outlived their tasks."*

`044`'s closing clause:

> **If any reallocation would change what an exported done-note appears to have said, stop and
> report instead.**

**It fires, so I stopped.** `044` also says *do not guess, and do not use "which one seems more
important."*

**My recommendation, recorded and not acted on:** the reason is the durable half — it names a
concrete harm, while *"earlier keeps the number"* was a means to that end chosen under a false
belief about which set was earlier. **Moving `021`'s three rows to `OBS-065`–`067` breaks
nothing.** That is a ruling, not a deduction.

### Two corrections to Part 3's own text

**There are three duplicated ids, not five.** `044` names `OBS-044`, `045`, `046`, `047`, `053`.
**Measured today, `047` and `053` are unique.** Either they were already resolved or the count
was taken from a state the ledger no longer reflects.

**`tests/test_observation_ids_are_unique.py` is RED and is meant to be.** It names the question
in its failure message. **It is deliberately not `xfail`** — that removes it from the failure
count, which is the cheap route to green the ledger convention exists to forbid: *deleting a row
does not clear it.*

---

## Part 1 — link colour

**`SPEC.md` §4.1a added.** §4.1 unchanged; nothing is bound to `gapped over`, `clear for`, or any
other state.

**The argument that makes it safe, and it is load-bearing rather than rhetorical:** a verdict is
a claim about **one** thing; a link is a claim about **two**, and it cannot be read as a judgment
**because it never appears alone**. Remove that and the argument collapses — a lone violet token
is an emphasised token, and emphasis is a verdict. **So the invariant is enforced in code**:
`live/tui/links.py` refuses a render containing an orphaned link.

**The spec's own notation collided with the tree, and the guard found it on its first run.**
§4.1a illustrates links as `[PML]` and says the brackets are not rendered. Taking them literally
as the marker made `Cell.not_built`'s existing `[ NOT BUILT ]` parse as a linked token — the
first run of the live-panel check reported `{' NOT BUILT ': 1}`, **the grammar's own refusal
marker read as an orphaned link.** Banning spaces inside a token would have hidden that one case
and broken §4.1a's own `[at level]` example, so the internal marker is `U+27E6`/`U+27E7` and the
brackets in the spec stay illustrative. Recorded in §4.1a as a note.

**Nothing renders a link yet** — `S012` builds the rail, and `044` puts panel layout out of
scope. **So the guard is exercised against constructed lines**, not only against live panels: a
check that has only ever run over zero linked tokens has not been shown to fire, which is
`OBS-037`'s shape. The live-panel test asserts zero and says in its own message that the day it
sees one is the day it starts doing real work.

**Violet, and `c024` is the check.** If it is not legible that is a finding and a question, **not
a licence to reuse green.**

---

## Part 2 — a boundary is not a float

**`R_closed` is computed in `Decimal` and quantised to four places with `ROUND_HALF_EVEN` before
anything compares it.** The same rounded number classifies, is stored and is rendered.

**What was there before was a tolerance, and the shape was wrong.** `_EDGE = 1e-9` widened every
comparison so the *class* came out right — but the value **stored on the record** was still the
raw float, so a record could read `−0.05000000000000071` beside a class of `BE`. **044 forbids
that pair explicitly**, and a tolerance cannot deliver it: the float has to be removed at the
source. `_EDGE` is gone.

`Decimal(str(x))` rather than `Decimal(x)`, deliberately — the latter faithfully preserves the
binary artefact being removed.

### The five cases, and the red

Built **from prices**, never from a literal `R_closed`. 044's reason is exactly why the original
survived 35 tests: the defect lives in the **division**, so the division must happen inside the
test's subject.

Against the pre-`044` float path:

```
AssertionError: exit 9.95 gave R_closed=-0.05000000000000071, expected exactly -0.0500.
AssertionError: exit 10.05 gave R_closed=0.05000000000000071, expected exactly 0.0500.
AssertionError: exit 10.9999 gave R_closed=0.9999000000000002, expected exactly 0.9999.
AssertionError: exit 9.9499 gave R_closed=-0.05010000000000048, expected exactly -0.0501.
AssertionError: assert -0.05000000000000071 == Decimal('-0.0500')
AssertionError: assert -0.04999999999999929 == Decimal('-0.0500')
```

**Three existing tests had to change, and one of them had asserted the defect as a fact.**
`test_an_exact_edge_scratch_is_not_a_loser` read:

```python
assert r_closed(scratch) < -0.05      # the raw arithmetic IS outside the band
```

That comment was true only because the arithmetic was float. **The test encoded the symptom as a
standing property of the system**, which is the same failure `044` Part 4 is about, in a
different file.

### Every threshold comparison in the risk path

| comparison | where | exact now? |
|---|---|---|
| `r >= winner_min_r` | `classify` | **yes** — both sides `Decimal` |
| `r > breakeven_band_r` | `classify` | **yes** |
| `r >= -breakeven_band_r` | `classify` | **yes** |
| `risk == 0` | `r_closed` | **yes** — exact zero test on a `Decimal` |
| `0.0 <= breakeven_band_r < winner_min_r` | `ClassificationThresholds.__post_init__` | **float, and left so** — an ordering assertion on config values, not a classification boundary. No trade lands on it |
| `r_lost` / `r_net` sums | `classify` | **yes** — seeded with `Decimal("0")` |

**A claim I nearly put in this note and withdrew.** The red output showed `-0.04999999999999929`
beside `-0.05000000000000071`, and I read it as long-versus-short classifying differently. **It
is not**: both sides give the same value, and the other figure came from the *commissions* case,
where the artefact lands the other way. Checked before writing rather than after.

---

## Part 4 — does `038`'s units test assert the rule or the output?

**It asserts the rule. Established by mutation, not by reading it.**

`UNIT_MARKS` no longer contains the space — it reads `"ADR"`, not `" ADR"` — so the coupling
`044` describes is already gone. **How I know the difference:**

| mutation to `config/formatting.yaml` | `test_every_rendered_number_carries_a_unit` | `test_the_formatter_matches_spec_4_0a` |
|---|---|---|
| `"ADR"` → `" ADR"` | **passes** | fails |
| `"ADR"` → `" ADRs"` | **passes** | fails |
| `"ADR"` → `""` | **fails** — *"rows render a bare number with no unit"* | fails |

**The rule test survives spacing and fires only when the unit disappears. That is the
discriminator.** The exact-format test fails on any change including spacing — **by design**,
because §4.0a's table is an exact-output contract. Two tests, two jobs; the 038 defect was that
one test was doing both.

**A methodological note, because it nearly produced a false report.** My first attempt mutated
`' ADR'` — which no longer exists in the file — so all three "mutations" were no-ops and all
three runs passed. **I nearly reported "the test survives unit removal", which would have been
exactly backwards.** The fix was asserting that the replacement actually changed the file.

---

## What I could not do

1. **Reallocate the duplicate ids.** Part 3 above. **The one instruction in `044` left
   unexecuted, and `044` is what says to leave it.**
2. **Confirm violet is legible.** `c024`, and it needs Christoph's palette at 209×54.
3. **Render a link.** `S012` owns the rail. The primitive and its guard are in; nothing emits a
   linked token, and the live-panel test says so rather than implying coverage.
4. **Exercise the boundary fix against a real trade.** Every case is a fixture — no broker, no
   fills. The arithmetic is exact; that it matches IBKR's own fill and commission reporting is
   unverified.

---

## The tests

**`verify.ps1` ran from the main checkout at the time in `verify-output.txt`.** No count quoted —
`044`'s last action forbids it.

**One new failure, and it is deliberate**: `test_observation_ids_are_unique::test_every_observation_id_is_allocated_once`.
It reports three genuinely duplicated ids and names the question. **No previously-passing test
was made to fail.**

The export ran from the main checkout, not from a worktree.

---

**This note and the question file both need to be pasted to chat.**
