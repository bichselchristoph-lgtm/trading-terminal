---
task: 071
class: product
story: S034 S035 S037
epic: 4
supersedes: 070
depends: none
touches: the ADR statistic, the ATTACHED renderer, the panel snapshot fixtures
---

# 071 — the ATTACHED context block, reduced to four rows

**If `handoff/inbox/071-for-code-task-attached-context-block.md` exists in your tree and `handoff/done/071-*.md` does not, this task is for you. Otherwise stop reading and ignore this message.**

---

## 0. Supersedes 070. This is the only ATTACHED task running until it lands

**070 is retired.** It targeted mockup v1.0, drawn against a stale screenshot with the full 21-row panel still showing. **The mockup has moved twice since — v1.1 cut fifteen rows, v1.2 removed the header's `since HH:MM`.** 071 targets **v1.2**, the current one, and is the only correct target.

**Christoph's direction, 2026-08-23: focus only on the ATTACHED panel until it is done.** Nothing else in this task list competes with it. **Do not pick up other inbox items ahead of this one.**

**`ATTACHED mockup — the context block and its states`, v1.2, in the Drive `Mockups/` folder, is the specification for layout.** ATTACHED-SPEC v1.5 carries the reasoning. **Where a word differs, the mockup wins on layout and the spec wins on meaning.**

---

## 1. What the panel is today, read from a live screenshot, not assumed

**A screenshot taken 2026-08-23 09:19 shows the panel currently renders thirteen lines beyond the header:** `from`, `slot`, `tape`, a row-count line, `ADR% used`, `RVOL rel`, `VWAP`, a VWAP continuation line, and eight level rows — `PDH PDL PMH PML ORH5 ORL5 ORH15 ORL15`.

**Two things that screenshot already answers, so do not re-derive them:**

- **`ADR% used` and the no-ATR ruling are already correct on screen.** `16.7%` rendered with its bar; no ATR row was present anywhere. **Part 2 of the old 070 (`ADR% used`) may already be done — verify, do not rebuild blind.**
- **Eight level rows currently render inside ATTACHED, and the panel reports `21` rows total.** This contradicts the design session's earlier assumption that most levels were unbuilt. **They are built. They are simply in the wrong panel.**

---

## 2. Part 0 — inventory against the mockup, before any edit

**Confirm against the current render, item by item:**

1. **Does `ADR% used` still render correctly**, with its bar and `ADR20 RTH` basis? (Likely yes — confirm, do not assume.)
2. **Is any ATR row present anywhere in this panel?** (The screenshot shows none. Confirm on a second symbol.)
3. **List every row beyond the four the mockup keeps** — `from`, `slot`, `tape`, the row-count line, the VWAP continuation, and each of the eight level rows, by name.
4. **The file set this task must write**, and whether it is disjoint from anything task `067` (the LEVELS rail) might also touch.

**Report the inventory even where it confirms the mockup exactly.** It is the record that the panel matches the drawing, not an assumption of it.

---

## 3. The target — four rows, nothing else

```
+- ATTACHED -------------------------------------------+
  QQQ         attached 09:19:07

  ADR% used   16.7% ▓▓▓░░░░░░░░░░ of $10.66 ADR20 RTH
  RVOL rel    1.4x · avg 0.86x · cum 22.1M sh
  VWAP        $712.97 · +$1.28

  4 of 4 · end
```

**Row 1 — the symbol row.** Symbol, then `attached HH:MM:SS`. **Seconds, not minutes** — `09:19` and `09:19:59` are a minute apart on a panel whose job is what happened when.

**Row 2 — `ADR% used`.** Percentage, bar, then `of $ADR20 · ADR20 RTH` inline. **No continuation line below it.**

**Row 3 — `RVOL rel`**, with `avg` and `cum` on the same line.

**Row 4 — `VWAP`**, price then signed distance. **No continuation line below it.** Nothing renders below a value — the row is the row.

**`4 of 4 · end`.**

**The header carries no `since HH:MM`.** When a symbol is attached there is nothing for the header to declare, so it is bare. **The header is not always bare** — §5 and §6 below still use it, for `ATTACHING QQQ` and `queued · 11s`. **An empty header on a landed panel is itself the correct signal: attached, nothing to report.**

---

## 4. Remove six things, and removal is two operations each

**Remove:** `from` · `slot` · `tape` · the row-count line · the VWAP continuation line · **all eight level rows** — `PDH PDL PMH PML ORH5 ORL5 ORH15 ORL15`.

**Removing the row is half of it.** `B-028` already records the ADR dollar value continuing to reach the renderer after its row was deleted from an earlier cut. **A field that does not exist cannot leak; a field that still arrives in the record can.** So: remove each row, and remove the corresponding field from the record the renderer reads. **A test asserts each field's absence from that structure**, not merely its absence on screen.

**Where each removed value now lives — do not delete the underlying computation, only this panel's rendering of it:**

| Removed here | Lives in |
|---|---|
| `from` (broker address, as-of stamp) | SOURCES, HEALTH. **B-006: the broker address renders in one place** — the same screenshot showed it in both ATTACHED and HEALTH, which is the defect this removal fixes |
| `slot` | Wherever slot management renders — not this panel |
| `tape` | The TAPE pane, which already states absence and why |
| the row-count line | Nowhere, when landed. **It returns only in the partial state — §6 below** |
| the VWAP continuation | Nowhere. Deleted, not moved |
| the eight level rows | **The LEVELS rail, task `067`.** It does not exist on screen yet |

**The eight-level removal creates a real gap and the task should say so in its done-note, not paper over it.** Between this task landing and `067` landing, `PDH`, `PDL`, `PMH`, `PML`, `ORH5`, `ORL5`, `ORH15` and `ORL15` are on no screen at all. **That is a known, accepted, temporary state — not a defect to silently work around by leaving the rows in.**

---

## 5. The other three states, verified against the mockup

**058 built the worker, the atomic swap and the badge. This task verifies them against v1.2, it does not rebuild them.**

**Attaching** — mockup §3:
```
+- ATTACHED · QQQ -------------------- ATTACHING QQQ +
  (values land in one paint)
  1 of 1 · end
```
Old values drop at once. No row fills independently.

**Nothing attached** — mockup §4:
```
+- ATTACHED ----------------------------- not attached +
  – (nothing attached)
  1 of 1 · end
```

**Cooldown** — mockup §6:
```
+- ATTACHED ------------------------------- queued · 11s +
  QQQ         queued · 11s   (15s same-contract cooldown)
  1 of 1 · end
```
**Never a silent drop.**

**Where the built behaviour and the mockup differ, the mockup is the specification and the code changes.** Report every difference found, including ones fixed silently before this task — that list is what tells the design session whether 058's original drawing was ever right.

---

## 6. Partial gather — mockup §5

```
+- ATTACHED -------------------------------------------+
  QQQ         attached 09:19:07

  ADR% used   unavailable — pacing limit, retry in 42s
  RVOL rel    unavailable (no sector mapping) · avg 0.86x
  VWAP        unavailable (splice unverified)

  2 of 4 rows unavailable
  4 of 4 · end
```

**The row-count line returns here, exact, no tilde.** The live screenshot showed `~2 of 21 rows unavailable` — **the tilde reads as approximately, which is the same objection that retired `~level` from the LEVELS rail.** A count of unavailable rows is exact or it is not a count.

**`RVOL_rel` reads `unavailable (no sector mapping)`, never `1.0`, and `avg` still renders beside it** — one field's refusal does not blank the row.

---

## 7. Parallelism

**Removal, `ADR% used` verification, and the three non-landed states are disjoint if Part 0's file map says so.** They plausibly share one renderer file, in which case: **remove first, then verify `ADR% used` against a clean set, then the three states.** Do not force parallelism onto a shared file — Part 0 decides, not this ordering by default.

**No subagent commits. The parent commits once.**

---

## 8. Not in this task

- **`B-076`, the ATR multiplier.** Christoph's.
- **The LEVELS rail itself.** `067`. This task only removes the eight rows from ATTACHED; it does not build where they go.
- **`B-005` / `B-011`**, the basis-tail truncation guard. If a tail is cut at 62 columns here, report it — the mockup was drawn wide enough that it should not be, and a cut tail here is a live instance worth a row, not a rebuild of the guard.
- **`UI mockup — core surface panels`**, which still draws the old five-plus-level layout. Design session's to retire.
- **The TRADE stop table.** Separate mockup, separate task.

---

## 9. Exit tests

**Green.**
- **The landed panel renders exactly four rows** plus `4 of 4 · end`, matching §3 above.
- **The header carries no `since HH:MM`.** The symbol row carries `attached HH:MM:SS` with seconds.
- **All six removed items are gone from the panel and from the record the renderer reads**, each confirmed by a test asserting field absence.
- **`ADR% used` still correct** — percentage, bar, `ADR20 RTH` basis inline, no continuation line.
- **The three non-landed states match mockup §3, §4, §6.**
- **The partial state matches §5, with an exact unavailable count and no tilde.**

**Refusal.**
- **`ADR20` unavailable** ⇒ the row reads `unavailable` with its reason.
- **Splice unverified** ⇒ `VWAP unavailable (splice unverified)`.
- **No sector mapping** ⇒ `RVOL_rel unavailable (no sector mapping)`, never `1.0`.

**UAT (Christoph).** `christoph/open/038-*`. **Note: 038 was written against the five-row v1.0 layout and needs a quick re-read against v1.2 before use — flag this to the design session in the done-note rather than editing 038 directly.**

---

## 10. The closing sequence

Per `CLAUDE.md`, from the main checkout. One commit.

**The done-note must state, plainly:** the Part 0 inventory, every difference found against the mockup, and the accepted gap where the eight level rows have no screen until `067` lands.

---

**This note needs to be pasted to chat.**
