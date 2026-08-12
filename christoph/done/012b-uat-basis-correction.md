# 012b · Correction — the two bases in the 012 UAT are the wrong way round

**Status** RUNNING · **Owner** Christoph only · **Blocks** reading 012's 09:30–09:35 count
**Corrects** `christoph/open/012-uat-first-five-minutes.md` §3
**Does not touch** §2. The pre-registration is signed and closed.
**Written** 2026-08-12 by the design session

> **Read this before the 09:30–09:35 number is looked at.** After is too late — §3's whole
> function is to set the reader's expectation, and it currently sets it backwards.

---

## 1. Why this is a separate file

The signed file says *"Once signed, this file is closed to edits."* **That rule is correct and
is being kept.** §3 is analysis rather than a signed answer, but the design session is not the
party that signed the document and must not re-issue it — a pre-registration re-emitted by the
other party is no longer evidence of what was committed, however faithfully the answers are
carried across.

**It is also not folded into the next task file**, which is the standing convention for
corrections. That convention assumes the correction can wait for the next task. This one
cannot: 012's done-note is being written now, and the number it contains is the number §3
governs.

---

## 2. What §3 says, and why it is wrong

**§3 as written:**

| | basis it asserts |
|---|---|
| TradingView 5-min volume | **consolidated tape** — every venue plus off-exchange prints |
| The capture | **single venue** |

and therefore: *"The capture's count is expected to be the smaller number, for structural
reasons. If it comes out smaller, that is not evidence of loss."*

**Both halves are contradicted by evidence that arrived after it was written.**

**Observation, from the TradingView screenshot.** The chart header reads `QQQ · Invesco QQQ
Trust, Series 1 · 5 · NASDAQ`. The 09:30 bar is `Vol 164.28 K`, and the session's Volume MA
sits at `38.08 K` per five-minute bar.

**Observation, from `012a`'s done-note.** The trade stream's venue attribution in a 45-second
smoke test included `FINRA`, `NASDAQ` and `DRCTEDGE`. `FINRA` prints are off-exchange/TRF.
Separately, the L1 quote attribution was `'KQZ'` on the bid and `'PZ'` on the ask — three
venues and two venues at one instant.

**Inference — the design session's, and it is a reading, not a fact.** These point the
opposite way from §3. The capture's trade stream is **multi-venue and carries off-exchange
prints**, which is the property §3 assigns to TradingView. The TradingView bar is labelled
`NASDAQ` and its magnitude — roughly 38 K on an average five-minute bar, implying order-of-3 M
shares for the session against QQQ's consolidated daily volume — is what a **single venue**
looks like, which is the property §3 assigns to the capture.

**So the expectation inverts. The capture is likely the larger number.**

---

## 3. What this changes about how the number is read

**§3's warning is not withdrawn — it is the thing that fired.** Two quantities sharing a name
and answering different questions is exactly what §3 was written to catch. It caught it, and
then assigned the labels the wrong way round.

The operative consequence:

- **A capture count materially larger than TradingView's implied count is expected, not a
  defect.** Under §3 as written it would have read as anomalous.
- **A capture count materially *smaller* than TradingView's is the finding.** Under §3 as
  written it would have read as structurally normal and been dismissed. **That is the failure
  this file exists to prevent.**
- **Neither number may be printed beside the other without its basis attached.** Not
  `volume` — `volume@arca_depth`, `volume@ibkr_multivenue_prints`, `volume@tradingview_nasdaq`.

**What is still not established.** I cannot confirm from here what TradingView's `NASDAQ`
label denotes — venue prints only, or a consolidated series shown under its primary listing
exchange. **That is one lookup and it should be done before the comparison is made**, because
the whole correction above rests on it. If it turns out to be consolidated after all, §3 was
right and this file is wrong.

---

## 4. Two further corrections to the same file, neither urgent

**§4.5 calls the Row 14 task `013`. That number is taken** — `013` is *adopt
HANDOFF-PROTOCOL*. **The Row 14 task is `014`.** Second collision on this sequence; the first
was `012`/`013` and produced the `SNNN` build-slice split.

**The header key is `**State**`; the vocabulary says `**Status**`, and `OPEN` is not one of
the five states.** `HANDOFF-PROTOCOL` v1.1 rules both: one key name, five values. **The fix is
a header cleanup across `christoph/`, not a regex that tolerates variants** — a pattern that
permits drift is not a guard. That work belongs in `014` and is not done here.

---

## 5. What is deliberately not in this file

**No instruction to Claude Code**, and no inbox task. If Claude Code needs this, it is given
the path and reads it.

**Nothing in §2 of the signed file is touched, restated, or interpreted.** The bracket that was
ticked and the TradingView figure that was recorded stand exactly as signed. This document
changes only what the *comparison* means — never what was predicted.
