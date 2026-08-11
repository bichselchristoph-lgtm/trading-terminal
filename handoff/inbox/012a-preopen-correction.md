# 012a — Pre-open correction to 012: depth venue and quote basis

**Status** DONE · **Date** 2026-08-11 · **Type** correction · **Deadline** must complete before 09:00 ET
**Runs in** `D:\Dev\momentum`. Amends task `012`, which is RUNNING. **Does not replace it** — `012` stands except where this file says otherwise.

> Read this cold. The session that wrote it cannot answer questions.
> **This has a hard deadline.** If any item cannot be settled before 09:00 ET, **start the capture anyway on the 012 configuration and report what was unresolved.** A capture that runs on a thinner book beats a session lost to a probe.

---

## Why

Two findings in the phase-0 report rest on wrong premises. Christoph has confirmed from account management that he **holds NASDAQ TotalView-OpenView and pays for the full North America subscription set**, including NYSE ArcaBook and Cboe BZX Depth.

**Finding 1 — the 10089 was misdiagnosed.** It was read as the account lacking TotalView. The account has TotalView. The refusal therefore came from something else, and the most likely cause is the exchange string: **IBKR serves NASDAQ TotalView depth under `ISLAND`, not `NASDAQ`.** This matters because **QQQ is NASDAQ-listed** — TotalView is its deepest book, and ARCA was selected over it on the strength of a wrong reading.

This is the same shape as the 10092/10089 error already corrected once today: *a specific refusal read as a general absence.* It is now the second instance in one session, which makes it a pattern worth naming in the done-note rather than a one-off.

**Finding 2 — the budget claim inverts again.** Depth costs nothing at the margin. The monthly fee is already paid and does not scale with ticker count. **The constraint on tomorrow's multi-ticker run is line count, not money.** Task `013`'s framing of depth as "the expensive line" is wrong and will be corrected there; do not act on it.

---

## Phase A — re-probe depth, before 09:00 ET

Probe `reqMktDepth` on QQQ against, in order:

1. `ISLAND`
2. `NASDAQ`
3. `ARCA` (the current 012 configuration — the known-working control)

**Report per venue: error code if refused, and book dimensions if served.** Capture the same snapshot shape already used — bid levels × ask levels — so the venues are comparable on one basis.

**If `ISLAND` serves the book, switch the depth stream to it** and record the pre-open dimensions against ARCA's `240×240`. If it refuses, **report the exact error code and stay on ARCA.** Do not iterate through further venues; do not sign up for anything; do not change any subscription.

**Do not treat a refusal as evidence about the account.** Report the code and what it says on its face. The diagnosis is a separate act from the observation, and conflating them is what produced this task.

---

## Phase B — stamp the quote basis on every line

This is the item that matters most, and it is small.

The account's L1 line is **US Real-Time Non Consolidated Streaming Quotes**. If that is what stamps bid/ask onto each trade, **the quote in force is not the NBBO.** At-bid/at-ask classification run against a non-consolidated quote answers a different question than the same rule run against a consolidated one — and nothing in the stored file currently says which was used.

**Every trade line gains a field naming the quote basis**, e.g. `quote_basis: "nonconsolidated_ibkr_l1"`. Name what is actually in force, verified from the API's own reporting where possible; **if it cannot be verified before the open, record `quote_basis: "unverified"` and say so in the done-note.** Do not guess a label that reads as authoritative.

**Do not reclassify. Do not compute delta.** The capture stays raw. This adds one field so a later reader knows which question the stored quote answers.

**Also record once, in a header record or sidecar, the market data subscriptions active during the run** — as reported by the API or as stated by Christoph, whichever is available, labelled as to which. This is the provenance of every classification anyone derives later.

---

## Do not

- Do not delay the 09:00 ET start for any item here.
- Do not change, add, or cancel any market data subscription.
- Do not adopt anything, or touch `live/`.
- Do not compute delta or score row 14.
- Do not modify `012`'s other configuration — clientId 11, three streams, raw-only, append-only, gap records, 60s heartbeat, and the four live-verification assertions all stand.

---

## Exit tests

| Test | Who | What |
|---|---|---|
| **Green** | Claude Code | All three venues probed and reported with codes or dimensions. Every trade line carries `quote_basis`. Capture starts on time. |
| **Refusal** | Claude Code | Confirm that a venue refusal is reported as a code plus its face meaning, **with no inference about the account attached.** The second misdiagnosis in one session is what this test exists to prevent. |
| **UAT** | Christoph | If depth moved to `ISLAND`, compare the two book dimensions. A materially deeper book means today's data is better than yesterday's plan assumed. |

## Done-note must state

- All three venue probes: exchange, code or dimensions, which was used.
- The `quote_basis` value written, and how it was verified — or that it was not.
- The subscription set recorded, and whether it came from the API or from Christoph.
- Whether anything here was left unresolved at 09:00 ET, and what.
- **The two-misdiagnoses-in-one-session pattern, stated plainly**, since it bears on how phase-0 reads are written in future tasks.
