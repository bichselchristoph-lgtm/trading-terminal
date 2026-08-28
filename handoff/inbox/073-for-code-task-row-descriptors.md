---
task: 073
class: admin
unblocks: NOTHING
depends: 071
touches: the ATTACHED renderer, the row grammar, the panel snapshot fixtures
---

# 073 — a row becomes a declaration, not four edits

**If `handoff/inbox/073-for-code-task-row-descriptors.md` exists in your tree and `handoff/done/073-*.md` does not, this task is for you. Otherwise stop reading and ignore this message.**

---

## 0. The problem, stated as a cost

**Removing six rows from one panel is a task.** It should be six deletions from a list.

**Christoph, 2026-08-23:** *"Why does removing or adding information to a panel need so much coding time? It should be basic — rather than a full code rewrite."*

**He is right about the cost and the answer is not a config file.** His follow-on ruling settles the shape: **"I don't want changes in runtime. Only when defining."**

**So: declarative at definition time, in code, resolved at import. Not a YAML anyone edits. Not a toggle.**

---

## 1. What this must not become

**`config/layout.yaml` stays exactly as it is** — panel-level, `id` · `slot` · `visible` · a required `reason` on any change, with the standing test that a hidden component still computes and still writes to the day record. **Do not extend it to rows.**

**Three reasons, and the third is the one that matters:**

- **A runtime toggle makes what the terminal shows a choice.** *A setting is a choice; a basis is a fact.* The row set is closer to a basis.
- **The snapshot suite would have to cover combinations** rather than states.
- **A hideable row is a hideable refusal.** SPEC calls scrolling *"the sixth version of a correct warning nobody was instructed to read."* **A row toggle is the seventh.**

**Nothing in this task changes what renders.** If the screen differs before and after, the refactor is wrong.

---

## 2. Part 0 — read how a row is defined today, and report it

**The design session has read the dev specs and not the code. Everything below §2 is a proposal against an unread implementation.** **If Part 0 finds it wrong, say so and stop — a task built on a misread of the tree is worse than no task.**

**Report, with file and function names:**

1. **Where the ATTACHED panel's rows are constructed.** One function, several, a template?
2. **Where a value becomes a string.** `grammar.py` is documented as the only such place — confirm or correct.
3. **Where the basis string is attached** — with the value, at render, or hardcoded per row?
4. **Where a refusal reason is attached.**
5. **How a row's field reaches the day record**, and whether removing a row today also removes the field.
6. **How many places a single row change touches, counted.** That number is the thing this task exists to reduce, and it should be measured before and after.

---

## 3. Part 1 — the descriptor

**One declarative entry per row. Resolved at import. Immutable after.**

**Each entry carries, at minimum:**

| | |
|---|---|
| **key** | the field it reads from the day record |
| **label** | what renders on the left |
| **format** | how the value becomes a string — **delegating to the existing grammar, not reimplementing it** |
| **basis** | what it was computed over, rendered inline |
| **refusal** | what renders when the value is absent, and why |

**The panel renders the list. It does not know the rows individually.**

**Two properties are the whole point and both are testable:**

- **A row not in the table cannot render.**
- **A field not in the table is absent from the record.** **That is B-028 generalised** — the ADR dollar value kept reaching the renderer after its row was deleted, and this makes that class impossible rather than caught.

**`renderer(record)` stays a pure function.** No descriptor computes anything; it reads a field and formats it. **If a descriptor needs to calculate, it has reached around the record and the property is gone.**

---

## 4. Part 2 — convert ATTACHED only

**One panel. Not six.**

**And convert it after `071` has reduced it to four rows** — that is why this task depends on `071`. **Converting a thirteen-row panel and then deleting nine of them is the expensive order.** Four rows is the smallest surface on which the shape can be proven.

**Leave every other panel alone.** WATCHLIST, TAPE, SIZING, RISK, HEALTH and PIPELINE keep whatever they do now. **If the descriptor is right, they follow later at a cost this task will have measured. If it is wrong, one panel is the loss.**

---

## 5. Part 3 — the tests that make it hold

1. **Removing an entry removes the row.** Delete one descriptor, snapshot goes red, row is gone. **Seen red first.**
2. **Removing an entry removes the field from the record.** Asserted at the record, not the screen.
3. **A row whose value is absent renders its refusal**, not a blank and not a zero.
4. **The four ATTACHED snapshot fixtures are byte-identical before and after the refactor.** **This is the acceptance test for the whole task** — a refactor that changes output is not a refactor.
5. **No descriptor computes.** A test that the render path reads fields and does not derive them.

**Test 4 depends on `071`'s fixtures existing.** If they do not, write them first from the mockup and see them red — `PROCESS §9`, and the step that gets skipped.

---

## 6. Not in this task

- **Any change to what renders.** §1.
- **Any other panel.** §4.
- **`config/layout.yaml`.** Untouched.
- **The attach path.** That is `072`.
- **A runtime or file-based row toggle.** Ruled out by Christoph, 2026-08-23.

---

## 7. Exit tests

**Green.**
- **Part 0's reading is in the done-note**, including the counted number of places a row change touches today.
- **The ATTACHED panel renders from a descriptor list.**
- **The four snapshot fixtures are byte-identical to before.**
- **All five tests in §5, each seen red first.**
- **The done-note states the new count** — how many places a row change touches after. **If it is not materially lower, the refactor did not pay and should be said so plainly rather than defended.**

**Refusal.**
- **If Part 0 finds the render path is already declarative**, stop. Report it and change nothing. **The task was written against a spec, not against the code.**
- **If the four fixtures cannot be made byte-identical**, stop and report the difference. **Do not update the fixture to match the new output** — that is a test agreeing with whatever the code does, which is `B-029`.

**UAT (Christoph).**
- **None needed.** Nothing on screen changes. **The measure is the next panel change: it should be a list edit and a fixture.**

---

## 8. The closing sequence

Per `CLAUDE.md`, from the main checkout. One commit.

**The done-note carries the before and after counts from §2 item 6.** **That number is the only evidence this task produced anything** — the screen is identical by design, so the cost reduction is the deliverable and it has to be stated as a number rather than claimed.

---

**This note needs to be pasted to chat.**
