---
task: 072
class: product
story: S037
epic: 4
depends: none
touches: the attach path, the ATTACHED renderer, the attach tests
---

# 072 — attaching a second symbol does not change the panel

**If `handoff/inbox/072-for-code-task-attach-does-not-switch-symbol.md` exists in your tree and `handoff/done/072-*.md` does not, this task is for you. Otherwise stop reading and ignore this message.**

---

## 0. What was observed, and only what was observed

**Christoph, 2026-08-23, on the running terminal:**

- **QQQ was attached.** An earlier screenshot recorded it as `attached 09:19`.
- **He then attached AMZN.**
- **The panel still shows QQQ.**
- **The attach time now reads `09:38`.**

**That is the whole observation. No cause is named here and none should be inferred before the state is read.**

**But one thing in it is worth carrying into Part 0:** the timestamp moved and the symbol did not. **Something in the attach path ran to completion while the symbol it was supposed to change stayed put.** That narrows where to look without asserting what is wrong.

---

## 1. Why this is the highest-priority defect on the panel

**The screen shows QQQ's real numbers under a fresh timestamp, to a trader who believes he is looking at AMZN.**

**Every value on it is well-formed and correct — for the wrong symbol.** That is the archetype this project keeps cataloguing, in the one place where the cost is a position rather than a misread.

**And it is worse than a frozen panel.** A frozen panel looks frozen. **Here the clock is moving, and a moving number vouches for the stale ones beside it.** The same shape as the accumulate-path defect, where a nearly-right VWAP made a six-times-wrong volume look trustworthy.

**It also means S037 is not met.** Criterion 2 reads: *when the old values are dropped, one screen-level ATTACHING badge renders and no stale value remains on screen.* **A stale symbol is the largest possible stale value.**

---

## 2. Part 0 — reproduce and read the state

**Do not start from a theory. Reproduce first, then read.**

1. **Attach QQQ. Attach AMZN. Record what renders after each**, including the header, the symbol row and the attach time.
2. **Does the attach coroutine run for the second symbol at all?** Report what you observed, not what the code appears to do.
3. **Does contract resolution succeed for AMZN?** If it fails or returns candidates, that is a finding.
4. **Does anything write a new attach timestamp on a path that does not also set the symbol?** The observation says one moved and the other did not.
5. **Try a third symbol, and try attaching QQQ again after AMZN.** *Does any second attach work, or is it specific to AMZN?*

**Report the state you read, and where you could not read it, say so and stop rather than naming a cause.** *"Likely transient"* was written into a failure note four times about a file that had been deleted.

---

## 3. There are two defects here and the second one stands regardless

**Defect A — the attach did not switch symbols.**

**Defect B — nothing said so.**

**B is a defect even if A turns out to have a legitimate cause.** Suppose AMZN genuinely cannot be attached — no market data subscription, a replay fixture holding only QQQ, an unresolvable contract. **The panel must say that. It must never continue to render the previous symbol with a new timestamp.**

**Fix both. If the cause of A is outside this task's reach, fix B and say so plainly in the done-note** — a refusal that renders is worth more than a cause that is guessed at.

---

## 4. What correct looks like

**On a successful switch:**

```
+- ATTACHED · AMZN -------------------- ATTACHING AMZN +
  (values land in one paint)
  1 of 1 · end
```

then

```
+- ATTACHED -------------------------------------------+
  AMZN        attached 09:38:41

  ADR% used   22.4% ▓▓▓▓░░░░░░░░ of $4.18 ADR20 RTH
  RVOL rel    0.9x · avg 1.12x · cum 8.4M sh
  VWAP        $231.07 · −$0.42

  4 of 4 · end
```

**The symbol, the values and the timestamp change together or none of them change.**

**On a failed switch:**

```
+- ATTACHED --------------------------- attach refused +
  AMZN  could not attach — <the reason, named>
  QQQ remains attached — attached 09:19:07
  2 of 2 · end
```

**The previously attached symbol is named as such, with its original timestamp.** **It is never presented as the thing you just attached.**

---

## 5. The tests

**Each must be seen red before it is accepted green.**

1. **Attach A, then attach B ⇒ the panel renders B.** Symbol, values and timestamp all B's.
2. **Attach A, then attach an unresolvable symbol ⇒ a named refusal.** The panel does not render A with a new timestamp. **This is the test that would have caught the reported behaviour.**
3. **Attach A, then B, then A again ⇒ the panel renders A**, with a new timestamp, and none of B's values remain.
4. **No path writes an attach timestamp without also writing the symbol.** Assert it at the record, not at the screen.

**Test 4 is the structural one.** The others check behaviour; this one removes the shape the behaviour came from. **If the timestamp and the symbol can be set independently, they will drift again.**

---

## 6. Not in this task

- **The four-row reduction, the removals, the header.** That is `071`, and it is the panel's layout. **If `071` has not landed, do not do its work here** — and say in the done-note which of the two ran first, because the second one inherits the first's tree.
- **The LEVELS rail.** `067`.
- **The tape, the slot ledger, the watchlist.** Only the attach path and what the panel renders.
- **`B-114`**, the attach wall-clock measurement. Related, separate, needs TWS up.

---

## 7. Exit tests

**Green.**
- **All four tests in §5, each seen red first.**
- **The reproduction in Part 0 is recorded in the done-note**, including whether any second attach works or only AMZN fails.

**Refusal.**
- **A symbol that cannot be attached produces a named refusal**, and the previously attached symbol is either absent or shown as previously attached with its own timestamp.
- **Never the previous symbol under a new attach time.**

**UAT (Christoph).**
- Attach QQQ, then AMZN, then QQQ again.
- Attach something that does not exist.
- **Confirm the panel never shows a symbol you did not just ask for.**

---

## 8. The closing sequence

Per `CLAUDE.md`, from the main checkout. One commit.

**The done-note states what Part 0 observed, which of the two defects were fixed, and — if A's cause was not established — that it was not.** **A record that asserts an unchecked cause is worse than no record, because it stops the reader looking.**

---

**This note needs to be pasted to chat.**
