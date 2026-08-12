# 012 · UAT — the first five minutes of tape

**Slice** 012
**Status** DONE · **Owner** Christoph only
**Path** `christoph/done/012-uat-first-five-minutes.md`
**Signed** Christoph, 2026-08-12 · **Answered** by `handoff/done/012-live-qqq-tape-capture.md`

> **Replacement file, 2026-08-12. Header only.** The original declared `**State** OPEN` — a key
> name outside the convention and a value outside the five states — and a `**Path**` pointing at
> `christoph/open/`, which it had already been retired from. **`HANDOFF-PROTOCOL.md` v1.1 rules
> the key is `**Status**` and the five states are the whole vocabulary.**
>
> **§2's answers are carried across exactly as signed, including their typing.** Nothing was
> corrected, tidied or re-worded. The design session may not edit a pre-registration; it may
> only fix a header it wrote wrong in the first place.
>
> **The value `DONE` is Christoph's, given 2026-08-12.** The other four `christoph/done/` UATs
> use `REVIEWED — <qualifier>`; this one is `DONE` because `012`'s done-note answered it and
> both parties closed `012`.

---

## 1. Why the question changed

**Observation.** Claude Code asked for a pre-registered estimate of the *number of prints* in
09:30:00–09:35:00 ET. Christoph's answer: no basis for a point estimate in prints; he can read
share volume for the first candle in TradingView, not print count.

**Observation.** The session total — **565,957 trades** — was already reported in chat before the
estimate was requested.

**Inference (design session's, not established fact).** Two separate things went wrong with the
original construction, and they pull in opposite directions:

1. **A point estimate in prints was unanswerable.** Print count is a quantity nobody has ever
   been shown a value for. Asking for one invites a fabricated number, and a fabricated
   pre-registration does not test intuition — it destroys the test while appearing to pass it.
   *"I cannot estimate this"* is a valid, recorded outcome, not a failure to complete UAT.
2. **The anchor is already set.** Because 565,957 is known, any magnitude estimate for five
   minutes is now contaminated. That door is closed and cannot be reopened.

**Recommendation, adopted below.** Re-ask the question as a **share of the session** rather than
a count. That quantity is un-poisoned by the anchor, it is answerable from ordinary trading
intuition, and the gap it measures — *how front-loaded is the tape?* — is the finding 012's UAT
was actually after.

---

## 2. Pre-registration — filled in before reading anything computed

**A · What share of the session's 565,957 trades landed in 09:30:00–09:35:00 ET?**
Pick exactly one bracket:

- [x] under 1 %
- [ ] 1 – 3 %
- [ ] 3 – 6 %
- [ ] 6 – 12 %
- [] over 12 %

**B · Typical (median) print size in QQQ at the open, in shares.** One number:

`__Can't give a meaningul estimate other than looking it up which you can do better._____ shares`

**C · Optional, and read *before* filling A and B, or not at all.** TradingView consolidated
volume of the 09:30 five-minute candle:

`__164.28k_____ shares`

**D · If any of the above cannot be answered, write "cannot estimate" and why.** That is a
result, not a blank.

---

Signed `___Chirstoh_________________` Date/time `___Aug 12, 2026 10:25 UTC+2_________________`

*Signed and closed. Corrections go in the next document, not here.*

---

## 3. The basis trap in this UAT — **and §3 was wrong, both times**

> **Corrected 2026-08-12, after the measurement.** This section originally asserted that
> TradingView was consolidated and the capture single-venue, and predicted the capture would be
> the *smaller* number. `012b` then argued the reverse labelling. **Both were wrong**, and the
> record is kept rather than rewritten because the error is the lesson.

**What is actually true**, from `handoff/done/012-live-qqq-tape-capture.md`:

| | basis |
|---|---|
| The capture's **trades** stream | `reqTickByTickData("AllLast")` — **consolidated across 18 venues**, including FINRA |
| The capture's **depth** stream | **single venue, ARCA**, by configuration |
| TradingView's 5-min volume | labelled `NASDAQ`; its default US feed is Cboe One — four lit exchanges, odd-lot filtered |

**So both quantities in §2C are consolidated-ish and the gap runs the other way.** Measured:
TradingView 164,280 shares against the capture's **873,482** in the same window — **the capture
is 5.32× LARGER.**

**The cause is not established.** Cboe One's four venues plus odd-lot filtering, against
eighteen venues unfiltered with **88.9 % of prints being odd lots**, accounts for the direction
and roughly for the size. **Confirming it would need TradingView's venue list for that session.**
Recorded as the most probable explanation, not as fact.

**Why this section is preserved rather than fixed.** Two parties reasoned carefully about which
quantity was which and both got it backwards. **The failure was not the labelling — it was
comparing two numbers whose bases nobody had actually read off the code.** That is the recurring
pattern, caught here in the act.

---

## 4. The result

| | |
|---|---|
| **pre-registered** | **under 1 %** |
| **measured** | **2.909 %** — 16,461 of 565,957 trades |

**One bracket high.** The tape is roughly **3.5× more front-loaded** than the intuition allowed:
five minutes is 1.2 % of a 414-minute session and carried 2.9 % of its prints.

**B was recorded as "cannot estimate", which the pre-registration correctly treats as a result.**
Measured: mean 47.5 shares per print across the session, 53.1 in the opening five minutes.

**The UAT worked exactly as designed.** The number was committed before it could be contaminated,
and the gap is the finding.
