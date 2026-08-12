---
id: 012a
title: Pre-open correction to 012 — depth venue and quote basis
status: DONE — both phases resolved before 09:00 ET
owner: claude-code
ran: 2026-08-11, 05:07–05:12 ET
tree: D:\Dev\momentum
---

# 012a — pre-open correction

**Status** DONE

**Nothing was left unresolved at the deadline.** Both phases completed by **05:12 ET**, with
3 h 48 m of margin. The capture starts at 09:00 ET on the 012 configuration as amended here.

**Headline: 012a's hypothesis about `ISLAND` is not borne out.** Depth stays on **ARCA**.

---

## Phase A — all three venues probed

Probed in the specified order at **05:07 ET**, `numRows=10`, each cancelled before the next.

| # | venue | dims | observation, on its face |
|---|---|---|---|
| 1 | `ISLAND` | **0×0** | **code 10089** — *"Requested market data requires additional subscription **for API**. See link in 'Market Data Connections' dialog for more details.**QQQ NASDAQ.NMS/DEEP**"* |
| 2 | `NASDAQ` | **0×0** | **code 10089** — byte-identical message, same feed identifier |
| 3 | `ARCA` | **9×9** | **served**, top 721.15 / 721.34 |

**Used: `ARCA`.** `ISLAND` refused, so per 012a I report the code and stay put. I did not
iterate further venues, signed up for nothing, changed no subscription.

### Reported without inference, which is the refusal exit test

Three things are observations, and I am not extending them into a claim about the account:

1. Both `ISLAND` and `NASDAQ` return **the same code, 10089**.
2. Both name **the same feed identifier: `NASDAQ.NMS/DEEP`** — so on this account, for this
   contract, the two exchange strings resolve to one feed. **The premise that `ISLAND` is a
   different route to TotalView does not hold here.**
3. The message's own wording contains **"for API"**. That is in the string IBKR returned; it
   is not my gloss.

**What I am not saying:** that the account lacks TotalView. Christoph has confirmed he holds
it, and nothing above contradicts that. The refusal names a feed and a subscription
requirement *for API access*; why an entitlement Christoph holds produces that string is a
question this probe cannot answer, and answering it from the code alone is precisely the
error 012a exists to correct.

### A correction to 012a's own figure

012a says to record the new dimensions *"against ARCA's `240×240`"*. **ARCA was never 240×240.**
My phase-0 report gave two adjacent lines:

```
ARCA top bid: DOMLevel(price=720.38, size=240.0, marketMaker='')
ARCA top ask: DOMLevel(price=720.46, size=240.0, marketMaker='')
...
ARCA  *** DEPTH AVAILABLE — 4 bids / 3 asks
```

**240 was the share size at the top level; the dimensions were 4×3.** The comparison is
therefore **4×3 at 04:38 ET → 9×9 at 05:07 ET** — the book deepening as pre-market fills, on
a request for 10 rows rather than 5. Not a venue difference at all.

This is my reporting defect, not the design session's reading: I printed a size and a
dimension in adjacent lines without labelling either.

---

## Phase B — quote basis stamped, and it is better than `unverified`

### The value written

```
quote_basis: "ibkr_l1_multivenue_aggregate_not_verified_nbbo"
```

**On every trade line and every quote line.** Verified live in a 45-second smoke test:
10 of 10 trades carried the field and a quote.

### How it was verified — partially, from the API

012a allows `"unverified"` if the API cannot confirm the basis. It partly can, so I measured
rather than defaulted:

| what the API reported | value | what it establishes |
|---|---|---|
| `Ticker.marketDataType` | **1** | live, not delayed or frozen |
| `Ticker.bidExchange` | **`'KQZ'`** | **three venues** quoting the bid at one instant |
| `Ticker.askExchange` | **`'PZ'`** | two quoting the ask |

A multi-character attribution means the inside is an **aggregate across venues**, not one
book. That is measured fact.

**What the API does not report, and the label therefore does not claim:** whether that
aggregate equals the consolidated SIP/NBBO. IBKR's product name says "Non Consolidated", but
that is Christoph's statement of what he pays for, not something the API confirms — so the
label ends `not_verified_nbbo` rather than asserting either way.

### Per-line attribution, which is stronger than the label

Each line also carries **`bid_exchange`** and **`ask_exchange`** as reported at that instant.
This matters because the attribution **varies tick to tick** — the smoke test caught `'Q'`/`'P'`
(one venue each side) minutes after `'KQZ'`/`'PZ'` (three and two). A single static label
would have averaged that away; per-line, a later reader can see exactly which venues were at
the inside when any given print happened.

**Nothing was reclassified and no delta computed.** The capture stays raw; this adds fields.

### The subscription set, labelled by source

Written once into every stream's `START` record and to
`records/tape/QQQ-2026-08-11-provenance.json`:

- **Stated by Christoph** (via 012a): NASDAQ TotalView-OpenView; the full North America
  subscription set including NYSE ArcaBook and Cboe BZX Depth; US Real-Time Non Consolidated
  Streaming Quotes (L1).
- **Reported by the API**: `marketDataType=1`; the bid/ask exchange sample above; the
  three-venue depth probe with codes.

**The API exposes no market-data-subscription tag at all** — I checked `accountValues()`,
which returns monetary tags only (`StockMarketValue`, `MoneyMarketFundValue`, …). So the
subscription list is *entirely* Christoph's statement, and the sidecar says so in the field
name: `subscriptions_source: "Christoph, via task 012a — NOT reported by the API"`.

---

## The pattern, stated plainly

**Three mis-transcriptions in one session, all the same shape: a specific observation read as
a general fact.**

| # | who | the reading | what it actually said |
|---|---|---|---|
| 1 | me, phase 0 | "depth is NOT available; skip L2" | SMART returned 10092 and NASDAQ returned 10089. Two specific refusals on two venues out of seven. **ARCA and BATS served it.** |
| 2 | me, phase 0 | "the account does not hold TotalView" | 10089 says a subscription is required *for API* for the feed `NASDAQ.NMS/DEEP`. It says nothing about what the account holds. Christoph holds it. |
| 3 | design session, 012a | "ARCA's 240×240" | 240 was the top-of-book **size**; the dimensions were 4×3. |

**All three are the same failure and it is the one this project names most often**: the
distance between *what was observed* and *what it means* was crossed silently, and the
conclusion then travelled into the next document as a premise. #1 and #2 became the reason
ARCA was chosen over a book that was never actually ruled out. #3 became a comparison target
that never existed.

**What it implies for how phase-0 reads are written.** The defect is not carelessness — each
reading was plausible. It is that observation and diagnosis were written in the same
sentence, so the diagnosis inherited the observation's authority. Two changes would have
caught all three:

1. **Report the code and the literal string first, in their own line, and the reading second,
   marked as a reading.** 012a's refusal exit test is exactly this rule, and applying it to
   Phase A is what made the `NASDAQ.NMS/DEEP` collision visible.
2. **Never report a refusal on a subset as a property of the whole.** "SMART and NASDAQ
   refused" is a fact; "depth is unavailable" required five more venues I had not tried.

**And a smaller one for me:** label units at the point of printing. `240` next to `4 bids /
3 asks` invited exactly the misread it got.

---

## Exit tests

| test | result |
|---|---|
| **Green** | All three venues probed and reported with codes or dimensions. Every trade and quote line carries `quote_basis`, verified live: **10/10** in a 45 s smoke test. Capture starts on time at 09:00 ET. |
| **Refusal** | The `ISLAND` and `NASDAQ` refusals are recorded as **code 10089 plus the literal message**, with the "for API" wording and the `NASDAQ.NMS/DEEP` feed name quoted. **No inference about the account is attached** — the section above says explicitly what is not being claimed. |
| **UAT** | Depth did **not** move to `ISLAND`, so there are no two books to compare. The comparison that does exist is ARCA **4×3 at 04:38 → 9×9 at 05:07**, which is the book filling out pre-market, not a venue difference. |

## Unresolved at 09:00 ET

**Nothing.** Both phases closed at 05:12 ET.

One thing is *open but not blocking*, and it is not mine to close: **why an account holding
TotalView gets 10089 on `NASDAQ.NMS/DEEP` for API access.** The probe can only report the
code. If it matters for tomorrow's multi-ticker run, the place to look is the API-vs-TWS
entitlement distinction the message's "for API" wording points at — but that is a reading, and
it belongs to Christoph and IBKR, not to a probe.

## Incidental finding, for 008a's open question

The smoke test's trade venues included **`FINRA`** alongside `NASDAQ`, `DRCTEDGE` and others.
008a Test 5 left open what `whatToShow="TRADES"` volume includes, and could not obtain a
consolidated figure. **`FINRA` prints are off-exchange/TRF**, so the tick-by-tick stream does
carry them. Today's capture will settle that question with a per-venue count as a free
by-product — no extra work, and it closes a gap 008a recorded as unrun.

## Configuration unchanged

`clientId 11`, three streams, raw-only, append-only with 100-record flush, gap records into
every stream, 60 s heartbeat, and the four live-verification assertions — all stand. No
subscription changed, nothing adopted, `live/` untouched, no delta computed.

**Not committed.** `momentum-harness` untouched at `1afcecf`.
