# H10 — `REGIME-PROMPT.md` v1.2, and commit what is staged

**Status** DONE · **Date** 2026-08-10 · **Type** spec + housekeeping
**Runs in** `D:\Dev\momentum`. Closes items 1 and 2 of H8's *Left open*.

> Read this cold. The session that wrote it cannot answer questions.

---

## Why

H8's done-note checked `REGIME-PROMPT.md` PART B against 005's two transferred defects and found a split result. Two things survived, both in the document that is `CURRENT` and running daily:

**1. No ratification bands.** Rows 12–14 are captured as `pending` with no scoring rule anywhere. The template's bands — +2/+3 ratifies, 0/+1 downgrades one step, ≤ −1 forces RED — are absent, so 005's sharpest finding is neither solved nor contradicted: with only two of the three rows available, max becomes +2, "ratifies" requires a perfect score, and **the card can only ever downgrade.** Row 13's availability was never verified, so the two-row case is the expected one.

**2. `6 of 9` survived verbatim.** It is arithmetically legal if two of rows 1–11 are unavailable, and PART B does not say which its example assumes — so it is **indistinguishable from the error 005 identified** and told the builder not to implement. `mockup-02` renders the same figure, inherited from Amendment 1 §A1.5.

**Severity dropped, which is the reason to fix it now rather than later.** `SPEC.md` §5.1 removed the exposure dial, so this arithmetic no longer scales position size — 005's stated reason for blocking. But the read still renders GREEN/AMBER/RED prose a person acts on at 05:00. **A defect that stops being urgent is the kind that gets closed by accident.**

---

## Build

### 1. Adopt `REGIME-PROMPT-v1.2.md`

Christoph supplies it in `D:\Dev\_adopt\`. It goes through the gate as a normal adoption: provenance companion, `ADOPTION-LOG.md` row. **It replaces `docs/specs/REGIME-PROMPT.md` in place** — same path, same `CURRENT` status header, version line `1.2`.

**This trips refusal 3 by design** — same name, different content. That is the refusal working, not a bug. Record in the companion that this is a version supersession of an adopted file, cite the row it replaces, and log both. **If the gate offers no supersession path, stop and say so rather than deleting the old file to get around it** — a gate with a hole in it for the one case that recurs is worse than a gate that blocks.

### 2. Verify the four changes landed

| # | Where | What |
|---|---|---|
| 1 | header | `**Version** 1.2` |
| 2 | PART B, after the GREEN/AMBER/RED table | the ratification band table with `source: regime_read_template_2026-08` on each row |
| 3 | PART B, same block | the reduced-card floor — **fewer than three of rows 12–14 available ⇒ ratification skipped entirely, pre-open read stands.** Carries `source: prompt_decision_2026-08-10` and ships `PROVISIONAL` |
| 4 | PART B, the denominator paragraph | `6 of 9` replaced by a worked block that **names the unavailable rows**, with the reasoning that a count not naming its exclusions cannot be checked |

**The floor is the one new threshold and it must stay marked.** Every other cut point in PART B comes from the template. This one was decided on 2026-08-10 because the template's bands break on a two-row card. If it loses its `PROVISIONAL` tag it becomes indistinguishable from a sourced threshold.

### 3. `schema_version` goes to 2

The YAML `ratification` block gains `rows_available`, `floor_fired`, `bands`, `bands_source`, `floor_source`. **A snapshot written under v1.1 has none of these**, so a reader cannot tell a v1 snapshot with no floor from a v2 snapshot where the floor did not fire. Bumping is what makes that distinguishable.

`SPEC.md` §5.5a already says a `schema_version` mismatch means refuse to parse and say so. **Nothing currently parses the snapshot**, so the bump costs nothing today and is unrecoverable if skipped.

### 4. Add the band test

`tests/test_regime_prompt_invariants.py`. Extend the existing v1.1 version pin rather than replacing it:

- `docs/specs/REGIME-PROMPT.md` states `Version` `1.2` or higher.
- It contains `PART E — the three outputs` and `E0`, and does **not** contain `the two outputs`.
- It contains `schema_version: 2`.
- **It does not contain the bare string `6 of 9`.** Failure message: the figure is indistinguishable from the Amendment 1 §A1.5 error and must name its exclusions.
- The ratification band table is present, and the floor rule carries both `prompt_decision_2026-08-10` and `PROVISIONAL`.

**The `6 of 9` assertion is the one that matters.** The figure has now propagated through three documents — Amendment 1, `mockup-02`, and PART B — and each time it was copied rather than recomputed. A test is what stops a fourth.

### 5. Commit

H8's done-note ends: *"The new tree's work is staged but not committed."* Commit it. Separate commits for H9 v3's corrections, H8 §B, the observations carry, and this task — **four commits, not one.** A migration squashed into a single commit cannot be read back.

`momentum-harness` stays untouched.

---

## Do not

- Do not touch PART A, C, D, or E. No threshold, row count or output rule outside PART B.
- Do not rescale the GREEN/AMBER/RED bands. v1.2 states explicitly they do not rescale.
- Do not fix `mockup-05`'s row-14 arrangement or `mockup-02`'s `6 / 9`. Both are bannered `HISTORICAL`; the mockup redraw owns them.
- Do not push either repo.

---

## Exit tests

| Test | Who | What |
|---|---|---|
| **Green** | Claude Code | `pytest` passes. Report the count before and after. |
| **Refusal** | Claude Code | Write a scratch `docs/specs/scratch-regime.md` containing `6 of 9` and a `Version 1.1` line; confirm the new tests fail naming the file and the reason. Remove it. |
| **UAT** | Christoph | Paste v1.2 into the cloud scheduled task and run it once. **Before reading the output, write down whether you expect the ratification floor to fire.** Row 13's availability has never been verified, so it probably will — and if it does not, that is the finding. |

## Done-note must state

- Whether the gate had a supersession path for refusal 3, or whether it had to be worked around — and if worked around, exactly how.
- The four commit SHAs and what each contains.
- The result of the `6 of 9` test, and whether the string appears anywhere else in the new tree.
- Anything in v1.2 that reads as inconsistent with `SPEC.md` §5.5a now that `schema_version` is 2.
