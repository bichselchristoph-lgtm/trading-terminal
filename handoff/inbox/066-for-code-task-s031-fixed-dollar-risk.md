---
task: 066
class: product
story: S031
epic: 7
repo: D:\Dev\tws_order
depends: none
touches: tws_order sizing module, tws_order CLI, tws_order tests
---

# 066 — S031: size from a fixed dollar risk

**If `handoff/inbox/066-for-code-task-s031-fixed-dollar-risk.md` exists in your tree and `handoff/done/066-*.md` does not, this task is for you. Otherwise stop reading and ignore this message.**

---

## 0. This one is in the other repo

**All work is in `D:\Dev\tws_order`. Nothing in `D:\Dev\momentum` changes.**

**That makes it disjoint from `065` by construction — different repo, different index, different suite.** If a session is running both, they can proceed in parallel as separate subagents. **They must still commit separately, to their own repos.**

**`062` Part 1 read that repo: clean, 37 tests green, and no secrets test.** That last fact is Part B below.

---

## 1. The story

**S031 · Epic 7 · Trader.** *As a trader, I want to size from a fixed dollar risk figure, so that every position risks the 1R amount I actually trade rather than a percentage of an account balance that moves.*

**Closes B-041**, and unblocks S026 — which is the whole reason this is first.

---

## 2. The partition

| Part | Owns | Work |
|---|---|---|
| **A** | The sizing module and the CLI | `--risk-usd`, its five refusals |
| **B** | A new test file | The secrets test this repo does not have |

**A and B are disjoint and run as two subagents.** **B does not depend on A and must not wait for it.**

**Do not split A further.** The arithmetic and its refusals are one file and one decision; two agents in it would be a queue wearing a partition's clothes.

**Neither subagent commits. The parent commits once.** Convention, not a control — stated so it is treated as weaker.

---

## 3. Part A — `--risk-usd`

**Acceptance criteria, from S031. These are the exit tests; they are not restated in different words:**

1. **Given `--risk-usd` with a dollar value, When it sizes, Then the share count is that dollar amount divided by the per-share risk.**
2. **Given both `--risk-usd` and `--risk-pct`, Then it refuses and names both flags as mutually exclusive.**
3. **Given neither flag, Then it refuses and names the missing choice — nothing defaults.**
4. **Given `--risk-usd` non-positive or unparseable, Then it refuses and names the value it received.**
5. **Given per-share risk of zero because the stop equals the entry, Then it refuses rather than dividing.**

### **The arithmetic is Decimal, not float**

**`(9.95 − 10.0) ÷ 1.0 = −0.050000000000000710` classified a scratch as a loss.** That is B-031, and it passed thirty-five tests because they were built from literal R values rather than from prices.

**So: Decimal inputs, and the tests are built from prices.** A test written from a share count you already computed can only ever agree with the code — B-029.

### **Share counts round down, never up**

**Rounding up risks more than 1R.** A sizer that quietly exceeds the risk figure is worse than one that refuses, because the excess is invisible at exactly the moment it matters.

### **1R is received, never read**

**RISK owns the 1R figure. `tws_order` takes it as an argument and never reads it from config.** A sizer that can find its own risk number is a second authority on how much you risk.

### **Criterion 3 is the one that will feel wrong to implement**

**A default is the natural thing to write and it is exactly what this refuses.** A silent percentage default sizes a position nobody chose. **The refusal is the feature.**

---

## 4. Part B — the secrets test this repo does not have

**Definition of Done condition 1 reads: tests green, each seen red first, including the secrets test.** **`tws_order` has no secrets test**, so no story in this repo can currently meet condition 1 — including this one.

**Why it is not a formality.** `momentum`'s `test_no_secrets.py` **went green on both occasions a live API key sat in a committed file.** A test never seen failing is a test whose green means nothing.

**Required:** a secrets test in `tws_order`, **demonstrated red against a scratch file containing a realistic fake credential under `$env:TEMP`, then green against the real tree.** **Do not create a file containing a credential-shaped string inside the repo, even temporarily** — that is the thing being prevented.

**Match `momentum`'s test in intent, not by copying it blindly.** Read that one first; if its patterns are what let two real keys through, say so rather than reproducing the hole.

---

## 5. A stale constraint on the story, now cleared

**S031's edge cases say `verify.ps1` describes `D:\Dev\momentum` and says nothing about `tws_order`'s suite, so DoD condition 1 has no instrument there.**

**That was true when the story was written and `062` closed it.** `verify.ps1` §10 now reports `tws_order`'s path, HEAD and raw pytest output. **The instrument exists; use it.**

---

## 6. Not in this task

- **S026 and S028.** Blocked on a TRADE mockup that does not exist — the old size-stage mockup is dead by decision, MOCKUP-INDEX §3.
- **B-032**, `winner_min_r`'s identical float boundary. Same class, other repo, `momentum`'s RISK.
- **B-076**, the ATR floor refit. A threshold, so Christoph's.
- **Order placement, transmit, staging.** Read-Only API is on. **Nothing this sizes can transmit, and no refusal is designed for a path that cannot be reached** — B-022.
- **Anything in `D:\Dev\momentum`.**

---

## 7. Exit tests

**Green.**
- The five acceptance criteria above, each seen red first.
- **Tests built from prices, not from literal R values or from a share count the code produced.**
- The secrets test exists and **was seen red against a scratch fixture outside the repo.**
- `tws_order`'s existing 37 tests still pass.

**Refusal — criteria 2 through 5 are the refusal tests.** They are the majority of this story and none is optional.
- **A refusal names what it received**, never a bare failure.
- **No refusal path returns a reduced share count.** It does not resize.

**UAT (Christoph).**
- Size one real setup from a dollar figure and check the share count by hand.
- **Confirm that giving neither flag refuses rather than picking one.**

---

## 8. The closing sequence, and it is not the usual one

**`tws_order` is not in any Drive sync pair and has no export.** So:

1. **Commit and push in `D:\Dev\tws_order`.**
2. **Then, from the `momentum` main checkout, run `verify.ps1`** — §10 captures `tws_order`'s HEAD and raw suite output, which is how this work becomes visible to the design session at all.
3. **Write the done-note in `momentum`'s `handoff/done/`**, naming the `tws_order` commit hash.
4. **`export-handoff.ps1`, then push `momentum`.**

**Step 2 is the whole reason `062` existed.** Without it a green suite in the other repo is a claim with nothing behind it.

---

**This note needs to be pasted to chat.**
