# 030 — done — v1.8 landed byte-identical, and eight invariants now disagree with it

**Status** RUNNING · **Date** 2026-08-13 · **Type** re-supply · **Tree** `D:\Dev\momentum`

> **Read §2 before acting on this.** The copy is correct and the pin is green. **Eight other tests
> are red against the new text**, and they are not all the same kind of red — one is a real defect
> in v1.8, four are invariants v1.8 deliberately supersedes, one is a good outcome, and two are a
> conflict `030` said would not arise.

---

## 1. The replacement is byte-identical to the payload

| | bytes | sha256 |
|---|---|---|
| **Payload** between the sentinels in `handoff/inbox/030-*.md` | 38,611 | `4ca164b21e9a5a1d85c4e52a9ea1f5d361b38d3861e2de893d1e6ca50cb3d16b` |
| **`docs/specs/REGIME-PROMPT.md` as written** | 38,611 | `4ca164b21e9a5a1d85c4e52a9ea1f5d361b38d3861e2de893d1e6ca50cb3d16b` |
| *(the v1.2 file it replaced)* | 20,663 | `a30395a2ba47b956eb09a6bb9759aeaedf3a70df0918325544388b12c25ef64a` |

**Extracted by line index between the two sentinel lines, written with `newline=""` so nothing was
translated.** Not re-typed, not reflowed, not re-wrapped. 480 lines. **The payload's first and last
lines are blank** — the blank lines that sit inside the sentinels — and they were kept, because
"everything below this line, up to the END line" says so and *"do not fix what looks like a typo"*
covers whitespace too.

### One deliberate edit after the byte check, and why it is not a violation

| after RE-SUPPLY invariant 1 | 38,630 | `50e8505e49937b6c05c02c6453f8b75d5f4ae8faca10486cb5053c88fc35bd02` |

**+19 bytes: a `**STATUS** CURRENT` line above the version line.** `docs/specs/RE-SUPPLY.md`
invariant 1 requires every `.md` under `docs/specs/` to carry one within its first 10 lines, and
`tests/test_spec_pointers.py::test_every_spec_declares_status` enforces it.

**`030` says the re-supply hazard does not apply — *"there is nothing in the tree copy to undo."*
That is true of the tree copy and false of the invariants.** They are repairs the *tree* requires
of any document living in `docs/specs/`, not marks left in the old file. A plain re-supply drops
them whether or not the predecessor showed traces, which is exactly what `RE-SUPPLY.md` says will
happen and why the test *"fails loudly and names re-supply as the likely cause."*

**Re-applied, not re-authored.** Both hashes are above so the delivered bytes remain recoverable.

---

## 2. The pin is green. Eight other tests are red, and they are four different things

```
tests/test_regime_prompt_invariants.py ... 9 passed, 5 failed
  test_version_is_1_8_or_higher  PASSED     <- the pin 030 asked for
```

`**Version** 1.8` is on line 4 of the new file; `(1, 8) >= (1, 8)`.

**`030` says: "It should go green immediately. If it does not, the copy is wrong — say so and
stop."** **The copy is not wrong — §1 proves byte-identity — so that branch does not apply, and
stopping without diagnosing would waste the only reading anyone will do of these failures.** I
diagnosed and stopped short of changing any test or any content.

### 2a. One is a REAL DEFECT in v1.8

**`test_no_bare_six_of_nine` / `..._anywhere_in_specs`** — line 368 of the new text:

```yaml
  health:       "6/9 fresh"
```

**This is the Amendment 1 §A1.5 anti-pattern, reintroduced in the authored document.** The
invariant's rule is that a count must name its exclusions; `6/9` is legal if three of nine Layer I
rows are unavailable **and** is exactly what a reader gets by miscounting a card.

**Mitigating, and stated because it changes the severity rather than the verdict:** PART D is
headed *"Layer I, institutional context (9 rows)"*, so unlike the original defect the denominator
here is arithmetically real. **The form is still ambiguous and the test is still right.**

**Not fixed. Editing it would be re-authoring the document**, which `RE-SUPPLY.md` forbids in the
same breath as it mandates re-applying invariants. **This one is the design session's to correct
at source**, and it should be, because the tree copy will be overwritten by the next supply.

### 2b. Four are invariants v1.8 DELIBERATELY supersedes

| Test | What it asserts | What v1.8 says |
|---|---|---|
| `test_schema_version_is_2` | `schema_version: 2` | **`schema_version: 3`**, line 318, commented *"bumped in v1.7 — row 2 retired, layer_i row 1 replaced"*, with a paragraph at line 382 explaining the break |
| `test_part_e_is_the_three_outputs_not_two` | heading contains `PART E` **and** `the three outputs` | `### PART E — the outputs`. **`PART E` is present**; the word *three* moved to line 36, *"Produce three outputs, in this order"* |
| `test_ratification_bands_are_present_and_sourced` | ≥3 occurrences of `regime_read_template_2026-08` | **2.** One band block went with the cut row |
| `test_regime_snapshot_path` / `resupplied invariant 2` | no `claude/`-rooted snapshot path | **six occurrences**, and see 2d |

**None of these is a broken copy and none is a defect.** Each is a test pinned to v1.2's content,
which v1.8 changed on purpose and documents in its own version history.

**I did not update them.** *"Do not weaken a test to make it pass"* is unconditional, and the fact
that I believe the change is intended is not the same as it being ratified. **Each needs a
one-line decision from the design session**, and then they are one-line edits. The `schema_version`
one is the clearest: `RE-SUPPLY.md` itself lists *"states `schema_version: 2`"* as an adjacent
invariant, so **that document needs amending too**, or the next re-supply will be checked against
a superseded list.

### 2c. One is the GOOD outcome, and it is `027`'s tripwire

**`test_regime_snapshot_could_not_do.py::test_the_format_still_lacks_a_key` is red.** That test was
written under `027` to fire **on success**:

> **This test failing is the GOOD outcome.** It is the trigger to build the rule-15 grouping that
> `027` part 2 could not build soundly.

v1.8 line 391 delivers exactly what it was waiting for:

```yaml
could_not_do:
  - id:     gap_breadth_no_source
    detail: "Row 10: no market-wide pre-market gap scanner ..."
```

**The declared key exists, so rule-15 recurrence grouping is now buildable.** `027` is held at
Christoph's instruction, so **I did not build it** — but the mechanism worked exactly as designed:
the amendment landed and something went red rather than the missing matcher being forgotten.

**`028`'s note said the first keyed snapshot is 2026-08-14**, so any grouping must treat 08-10
through 08-13 as un-keyed and say so rather than guessing.

### 2d. Two are a conflict `030` could not have known about

`RE-SUPPLY.md` invariant 2: *"No `claude/`-rooted regime-snapshots path anywhere. The canonical
path is `docs/regime-snapshots/`."* Applied under H8.

**v1.8 uses `claude/regime-snapshots/` six times, and it is right to.** The Drive folder's own
README — **a decision recorded by Christoph on 2026-08-13** — says:

> The canonical write location for a scheduled cloud run is the Claude project at
> `claude/regime-snapshots/YYYY-MM-DD.{md,yaml}` — **that run has no repo access, permanently.**

**Re-applying invariant 2 would rewrite a live scheduled task's instructions to write somewhere it
cannot reach.** That is not a mechanical repair; it is a behaviour change to a running system, and
it is not mine to make.

**So invariant 2 is superseded and `RE-SUPPLY.md` does not know it.** The two paths answer
different questions — where the *cloud run* writes, and where the *tree* keeps copies (`025`'s
job). **The invariant should be narrowed to the tree's own references rather than "anywhere", and
that is a decision.**

---

## 3. The OBS-030 line

Added to the OBS-030 row:

> **Added by `030`: the tree copy sat at v1.2 through six versions and nothing went red, because
> the pin compares the file against a version number a human typed into the test, and reads the
> file's own claim about itself for the other half — a pin that asks its subject what version it
> is cannot notice that the subject is stale. That is the self-reference trap (§7), and it is why
> six versions were invisible.**

---

## 4. What I could not do

1. **Get the suite green.** Eight tests disagree with v1.8; §2 sorts them into four kinds. **None
   is fixable without either re-authoring the delivered document or weakening a test**, and both
   are forbidden.
2. **Fix the `6/9`.** Design session's, at source. A tree-side fix is overwritten by the next supply.
3. **Decide the four superseded invariants**, or amend `RE-SUPPLY.md`'s adjacent-invariant list,
   which now contains at least two claims v1.8 contradicts.
4. **Build rule-15 grouping**, now unblocked. `027` is held.
5. **Three failures are not mine and predate or postdate this task:** `test_handoff_state_declared`
   and `test_uat_has_a_file` (both attributed in `028`), plus **two new ones I did not cause** —
   `test_every_retired_uat_has_a_register_row` and its refusal-B pair, which went red because
   **Christoph retired `014-for-christoph-account-parameters.md` into `christoph/done/`** and the
   UAT review register has no row for it. That row is mine to write — *the test says so explicitly*
   — but it needs the UAT read, and it is not `030`'s scope. **Named so it is not inherited
   silently.** `test_pytest_collection` is also red and is the concurrent session's.

## The suite

**Not quoting a count**, for the reason `028` recorded: another session is committing to this tree
while I work. The figure at this task's `HEAD` is in `verify-output.txt`.

**What matters is the composition, not the number**: of the failures, **five are v1.8's arrival**
(four superseded invariants + the real `6/9` defect), **one is `027`'s tripwire firing as
designed**, and the rest are pre-existing or another party's.

## 5. `verify.ps1`

Run at 2026-08-13 15:35 +02:00. Output not quoted, per HANDOFF-PROTOCOL v1.2.
