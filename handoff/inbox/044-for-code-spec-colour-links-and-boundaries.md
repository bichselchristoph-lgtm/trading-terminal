---
id: 044
title: Colour links, a boundary is not a float, and five duplicate ledger ids
type: spec
class: admin
answers: OBS-059, OBS-054, OBS-062
unblocks: S012 — the level rail cannot be built while a level state has no way to render, and the risk limits cannot be trusted while a scratch can classify as a loss
owner: claude-code
tree: D:\Dev\momentum
---

**Status** WRITTEN

# 044 — a link is not a verdict, a boundary is not a float, and an id is not a suggestion

**Type: spec. Class: admin.** Three rulings, all answering questions Claude Code raised.

**v1.1 rewrites Part 3.** v1.0 described one duplicate ledger id. **There are five**, and the fix is
different because three exported done-notes cite them.

> **Read this cold. The session that wrote it cannot answer questions.**

---

## Addressing

**If `handoff/inbox/044-for-code-spec-colour-links-and-boundaries.md` exists in your tree and
`handoff/done/044-*.md` does not, this task is for you. Otherwise stop reading and ignore this
message.**

**Work in a worktree.** Remove it when the task completes.

---

## Part 1 — colour marks relation. It never marks judgment.

**`042` Part 4 was stopped correctly.** `SPEC.md` §4.1 binds each colour to a kind — blue a
parameter, amber a failed rule or a refusal, green and red fitted signals, white a measurement, grey
a label. **A level state and a distance are none of those. The rule offered them zero colours, not
one, and Claude Code did not take one.**

### The ruling

**§4.1 is unchanged. Nothing is bound to `gapped over`, to `clear for`, or to any other state.**

**§4.1a is added, as a separate and orthogonal channel:**

> **A link colour ties a value to the line that explains it. It says these two are the same thing.
> It says nothing about whether either is good.**

**Why this survives the no-verdict conviction.** A verdict is a claim about one thing. **A link is a
claim about two**, and it cannot be read as a judgment because it never appears alone.

### Three constraints, and they are the rule

1. **The link colour carries no meaning on its own.** Seeing it tells you only that there is more
   below.
2. **It is always used in pairs or groups. A linked token with no partner on screen is a defect** —
   see the test.
3. **It never replaces a kind colour.** A refusing row stays amber. The link colours only the token
   that names *which* row the explanation belongs to.

### What it replaces

**Footnote marks, everywhere.** No `*`, no `†`, no `‡`, no numbered footnotes, in any panel. **The
shared token is the legend.**

```
▲ above  PMH [PML] · ORL5 · LOD · [PDL] PDO [PDC] [PDH] · PWL PWO
         ▸ clear for 1.4ADR
         [PML] $722.80 gapped over
         [PDL] $722.92 reclaimed 11:04:12h ET
         [PDC] $726.80 gapped over
         [PDH] $727.25 lost 13:38:40h ET
```

*(square brackets stand for the link colour; they are not rendered)*

**Notes appear in the same order as the entries they belong to.** Nothing depends on it — the
repeated token already pairs them — but it removes a scan.

### It applies to every panel, not only the rail

Any value with an explanation line: a basis note, a caveat, a refusal reason, a window definition.

```
TRADE      [LCC5] the current candle is still forming — this stop
                  can only widen, and the share count only fall
ATTACHED   [VWAP] bar-derived, anchored 04:00h ET — tick-derived is
                  unavailable (splice unverified)
TAPE   [at level] anchored when price first entered ±0.02ADR of
                  $733.39; resets if it leaves by more than that
```

**`unavailable (splice unverified)` stays amber.** Only `[VWAP]` is linked.

### The hue

**Violet. Christoph's ruling, 2026-08-15.** It is unused by §4.1.

**One hue for all pairs on a panel** — four linked pairs share it. If that proves too many to read,
**the fix is fewer notes, not more colours.**

**`c024` confirms it is legible at 209×54 in his palette.** If violet is not legible, that is a
finding and a question — **not a licence to reuse green.**

### The test

**Every linked token has a partner on screen.**

Positional, scoped to the render layer. **Seen red by emitting a linked token with no matching
note.** This is the test that stops the link colour drifting into meaning *important*, which is a
verdict wearing a hat.

---

## Part 2 — a classification boundary is not evaluated in floating point

**`OBS-054`. This is the design session's defect.** `039` specified inclusive boundaries at `±0.05R`
and `+1.0R` and never said what arithmetic they are evaluated in.

**The measured consequence:**

```
(9.95 − 10.0) ÷ 1.0  =  −0.050000000000000710
```

**A trade that made nothing and lost nothing classified as `L`** — the only class feeding
`losses_max_day` and both R-lost caps. **A limit firing on a rounding error, indistinguishable on
screen from a bad day.**

### The ruling

**`R_closed` is computed from `Decimal` inputs and rounded before it is compared.**

- `avg_fill`, `avg_exit` and `stop_at_entry` are exact cent quantities. **Read them as `Decimal`,
  not as `float`.** The float is removed at the source rather than tolerated at each comparison.
- **The quotient is rounded to 4 decimal places** — `ROUND_HALF_EVEN` — and the rounded value is
  what classifies, what is stored, and what is rendered.
- **The stored `R_closed` and the classified `R_closed` are the same number.** A record that says
  `−0.0500` and a class of `L` must never coexist.

### Sweep the class, do not patch the instance

**`OBS-054` records the fix as unswept. `winner_min_r: 1.00` has the identical defect at the other
end** — a genuine `+1.0R` can land as `P`.

**Find every comparison against a configured threshold in the risk and classification path and
report each one**, with whether it is now exact.

### The tests

| Case | Must classify as |
|---|---|
| `R_closed` exactly `−0.0500` | `BE` |
| `R_closed` exactly `+0.0500` | `BE` |
| `R_closed` exactly `+1.0000` | `W` |
| `R_closed` exactly `+0.9999` | `P` |
| `R_closed` exactly `−0.0501` | `L` |

**Constructed from prices, not from a literal `R_closed`.** A test that hands the classifier a
Decimal it already rounded tests nothing — **it must go through the same arithmetic the real path
does**, which is how the original defect got past a suite of 35 tests.

**Seen red against the pre-fix code.**

---

## Part 3 — five duplicate ledger ids, and three exported files cite them

**`OBS-062`.** `OBS-044`, `OBS-045`, `OBS-046`, `OBS-047` and `OBS-053` **each name two different
findings.** Two sessions allocated the same numbers on the same day and nothing checked.

**This is already causing harm, not just confusion.** Claude Code declined to mark `OBS-044`
resolved after `043`, because *"OBS-044 PROMOTED"* would equally have read as closing **"a
`keepUpToDate` subscription dies silently and every health signal stays green"** — a live finding
about a stop-level feed. **A correct refusal, and the reason it was needed is the defect.**

### The ruling

**The earlier allocation keeps the number. The later one is reallocated forward.**

**Why that way round.** `037` allocated `044`–`047` first, and `041` and `043` cite them in
done-notes **already exported to Drive**. `handoff/` is copy-and-keep — those files cannot be edited
without putting the tree and Drive out of sync on bytes. **Moving the earlier findings would break
three documents; moving the later ones breaks none.**

**For each of the five:**

1. **Determine which finding was written first.** Use the ledger's own ordering, or the commit that
   introduced each row. **If the order cannot be established for a pair, stop and report that pair**
   — do not guess, and do not use "which one seems more important".
2. **The later finding takes the next free `OBS-NNN`.**
3. **A row is added to the ledger recording the move**, in the form:
   `OBS-063 — was briefly OBS-044. Reallocated 2026-08-15 (OBS-062).`
   **So a reader chasing a citation lands somewhere that explains itself.**
4. **Nothing in `handoff/` is edited.** Not done-notes, not task files, not accepted copies.

**Report both findings for each of the five pairs**, so Christoph can confirm the ordering was read
correctly. **If any reallocation would change what an exported done-note appears to have said, stop
and report instead.**

### The test

**Every `OBS-NNN` in `docs/observations/OBSERVATIONS.md` is unique.** Positional, scoped to that
file. **Seen red by duplicating one.**

**This is the cheap half and it should have existed before any of this.** Same shape as the `035`
collision one folder over, and the same fix: **a number is read, never inferred as free.**

---

## Part 4 — one smaller thing from the same report

**`038`'s units test encoded the spacing it was not testing** — `" ADR"` with the space baked into
`UNIT_MARKS`, so closing the space made three rows read as unitless. **The test asserted the bug.**

**Confirm it now asserts the rule rather than the current output, and say how you know the
difference.** *A test written from what the code does can only ever agree with it.*

---

## Not in scope

No panel layout work — that is `S012`. **No edits to anything under `handoff/`.** No changes to any
basis or limit value. No `tws_order` changes.

---

## Last action

**Run `verify.ps1`.** Do not paste or summarise. Do not quote a test count.
**Then run the export**, from the main checkout — not from a worktree (`OBS-045`, the `037` one).

---

## Exit tests

| test | who | what |
|---|---|---|
| **Green** | Claude Code | `verify.ps1` ran. The orphan-link test, the five boundary tests and the id-uniqueness test all seen red first |
| **Refusal** | Claude Code | A linked token emitted with no matching note ⇒ the render fails loudly rather than shipping a colour that means nothing |
| **UAT** | Christoph | `c024` — confirm violet is legible at 209×54 in his palette, and that a level state and its note read as one thing |

---

## Report

1. Whether violet was legible, or what stopped it.
2. **Every comparison against a configured threshold in the risk path**, and whether each is now exact.
3. The five boundary tests, and the red they were seen against.
4. **Both findings for each of the five duplicated ids**, and which was written first, and how you established it.
5. Which ids were reallocated, and to what.
6. Whether `038`'s units test now asserts the rule or the output, and how you can tell.
7. **What you could not do**, and why. Empty is suspicious.
