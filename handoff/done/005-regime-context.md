---
id: 005
title: Regime context — Layer 0 / Layer 1 / Layer 2, hard vetoes, exposure grid
status: SUPERSEDED
superseded_by: docs/specs/SPEC.md §3.2, §5.1, §7b.1
closed: 2026-08-10
built: nothing
---

# 005 — Regime context, closed as SUPERSEDED

**Nothing was built. No code, no tests, no config.** 005 was `BLOCKED ON ONE ANSWER` from
2026-08-09 and never unblocked; the answer arrived as a design decision that removed the
thing it was blocking.

**Two defects it found are TRANSFERRED, not closed.** They were never defects *of* 005 — 005
was the reader that caught them in the source documents, and those documents still exist and
are still `CURRENT`. Closing 005 must not close them. Both are re-stated below with what
`REGIME-PROMPT.md` PART B now does about each.

## Why superseded

Three sections, and they compose into one decision rather than three:

| section | what it does |
|---|---|
| `SPEC.md` §3.2 — *The regime surface is deleted* | "**Decided: no regime surface in the terminal.** Not a thin one, not a band. The whole read — Layer 0, the overnight macro strip, Layer I, **and the Layer 1 index read** — is produced by the Claude scheduled task and consumed there… **It is not worth a screen.**" |
| `SPEC.md` §5.1 — *Layer 0 — deliberately not in the terminal* | The terminal links to the morning's file and renders `[ NOT BUILT ]` if absent. "It does not parse it into rows, does not score it, and nothing downstream consumes it as a number." |
| `SPEC.md` §7b.1 — *Risk comes from the account, not the chart* | `1R = risk_pct × NetLiquidation`. The exposure dial is gone. |

005's scope was "the regime engine: Layer 0, Layer 1, Layer 2, the four hard vetoes, and the
Layer 0 × Layer 1 exposure grid." **Every one of those five is deleted or relocated.** The
vetoes survive, but as a boolean list inside `REGIME-PROMPT.md` PART B, not as a terminal
rule surface.

§5.1 states the causal chain explicitly, and it is worth quoting because it is *why* this is
supersession rather than abandonment:

> the composite's only consumer was the exposure dial, which is also gone (§7b.1) — so the
> score would have been computed for a reader that no longer exists.

**005 was correct and was overtaken.** Its own blocking question — "this is the number that
scales into position size" — stopped being true when the dial was deleted.

---

## Defect 1 — the reduced-denominator arithmetic. **TRANSFERRED.**

005's finding, verbatim in substance: Amendment 1 §A1.5 says rows 10 and 13 are unavailable
so "the pre-open total is out of 9 inputs, not 11." **That is wrong twice.**

1. **Row 13 (TICK / ADD / RSP) is not a pre-open row.** It is an *opening* row, in the 12–14
   card. It cannot be removed from the pre-open denominator because it was never in it.
2. **Removing row 10 from an 11-row card leaves 10, not 9.**
3. And the sharper consequence 005 drew: removing row 13 from the **3-row opening card leaves
   2**, which needs its own rescale. With max +2, "ratifies" requires a *perfect* score and
   "downgrade one step" catches everything else — **the opening card becomes a downgrade
   machine.**
4. `mockup-02` renders `6 / 9` and inherited the error. 005's instruction: **"Do not
   implement 9."**

### What `REGIME-PROMPT.md` PART B does about it — one half fixed, one half absent, one number survived

**Fixed — the row-13 misplacement.** PART B puts row 13 at `09:35–10:00` inside rows 12–14
and states: *"Rows 1–11 are the pre-open bias, scored at 05:00. Max +11"* and *"Rows 12–14
are the ratification, and you cannot know them at 05:00 — leave them `null` with
`pending: true`."* Row 13 is unambiguously an opening row. **005's first point is resolved.**

**Decided, and not the way 005 guessed.** 005's blocking question 3 asked how to rescale, and
proposed proportional bands as "the obvious candidate". PART B decides the opposite:

> state that the GREEN/AMBER/RED bands were set for a denominator of 11 and **do not
> rescale.** Say plainly that the verdict is therefore lower-confidence… **Do not invent a
> rescaled band.**

That answers question 3. Record it as answered *differently from the expectation*, because
anyone reading 005 alone would implement proportional bands.

**Not fixed — the opening-card arithmetic.** PART B gives **no ratification bands at all.**
The source doc's "+2 or +3 ratifies, 0 or +1 downgrades one step, ≤ −1 forces RED" does not
appear. So the downgrade-machine problem is neither solved nor contradicted — the rule it
would apply to is simply absent from the current spec, deferred to whoever eventually
consumes the `pending` rows. **This is the live half of the defect.**

**And the number survived.** PART B's worked example of a reduced denominator reads
**`6 of 9 scored rows`** — the same figure 005 identified as the inherited error and said not
to implement. Stated precisely, because this matters: `6 of 9` is *arithmetically legal* if
**two** of rows 1–11 are unavailable. PART B does not say which rows its example assumes. So
the number that propagated into a `CURRENT` spec is indistinguishable from the error 005
flagged, and a reader has no way to tell them apart. **It should either name the two absent
rows or use a different example.**

**Severity has dropped, and that is the reason to write it down rather than rely on
remembering.** With the exposure dial gone (§7b.1), this arithmetic no longer scales position
size — 005's stated reason for blocking. But the read still renders GREEN / AMBER / RED in
prose that a person acts on, and PART B still prints a denominator. **A defect that stops
being urgent is exactly the kind that gets closed by accident.**

---

## Defect 2 — the row-14 contradiction. **TRANSFERRED, and resolved in the spec.**

005's finding: `mockup-05` puts rows 1–9, 11, **14** in the frozen 08:00 composite. Row 14 is
the first pullback, **10:00–10:30 ET**. It cannot be frozen at 08:00. The source doc has it in
the opening card. 005 said: *"Report which the user wants; do not pick."*

**`REGIME-PROMPT.md` PART B picks, and picks the source doc.** Row 14 is listed at
`10:00–10:30 | First pullback`, inside rows 12–14, and rows 12–14 "cannot be known at 05:00 —
leave them `null` with `pending: true`." A row that must be `null` at 05:00 cannot be in an
08:00 frozen composite. **The contradiction is resolved against `mockup-05`.**

**Transferred rather than closed because the losing document is still on disk.** `mockup-05`
still renders row 14 in the frozen composite. Under H9 v3 §3d it now carries an on-screen
banner naming `SPEC.md` §3.1 and stating that its Layer 0 row set is not in the design — so a
reader is warned, but **the wrong arrangement is still rendered**, and the banner says
"historical mockup", not "row 14 is in the wrong card". Whoever redraws these sheets owns the
repair.

---

## Design note 2 shipped, as `REGIME-PROMPT.md` §2

005's design note 2 — *"Archive the regime read the way 004 archives watchlists"* — argued
that Amendment 1 §A1.6 wants ~1,250 session observations to validate Layer 0, and a dated
immutable record of every read is that sample **accumulating for free from day one**, where
otherwise "the validation starts from zero on the day someone decides to run it."

`REGIME-PROMPT.md` **§2, "What consumes this, and when"** ships exactly that argument:

> **None of these can be run retroactively over prose**, which is why the YAML ships from day
> one even though nothing reads it yet. **This is the cheapest thing in the whole project to
> get right early and among the most expensive to fix late.**

The mechanism differs — a locked YAML snapshot joined to the trade log on `session_date`,
rather than 004's two-folder archive — but the reasoning is identical, and §2 adds the guard
005 did not: *"Querying this store against outcomes requires a pre-registration with a
predicted direction, declared before the query runs (`SPEC.md` §12.7). Capture is
unconditional; mining is not."*

**Design note 2 is the one part of 005 that shipped.** It shipped somewhere else, under a
different mechanism, which is why it would have been invisible if this note only recorded
what was built.

---

## What is left open, and who owns it

| # | item | owner |
|---|---|---|
| 1 | **The ratification bands are absent from `REGIME-PROMPT.md` PART B.** Rows 12–14 are captured as `pending` with no rule for scoring them, and the 2-row downgrade-machine case is unaddressed. | whoever specifies the `pending`-row consumer |
| 2 | **PART B's `6 of 9` example** should name which two rows it assumes absent, or use a different figure. As written it is indistinguishable from the error 005 flagged. | `REGIME-PROMPT.md` v1.2 |
| 3 | **`mockup-05` still renders row 14 in the frozen composite.** Bannered as historical, but the specific error is not named. | mockup redraw |

## Not done

No code, no tests, no config. `SPEC.md` and `REGIME-PROMPT.md` were **not edited by this
closure** beyond H9 v3's §13 heading change, which is a separate task. The three items above
are recorded, not repaired — repairing a `CURRENT` spec inside a task-closure note is how a
document acquires changes nobody reviewed.
