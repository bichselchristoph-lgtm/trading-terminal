# Daily Regime Read — the scheduled Claude prompt

> **STATUS** CURRENT · **date** 2026-08-10

**Version** 1.2 · **Date** 2026-08-10 · **Companion to** `SPEC.md` §3.2, §5.5a
**Runs** cron `0 5 * * 1-5` (05:00 ET, weekdays) · **Prints** the read in the response · **Writes** `docs/regime-snapshots/YYYY-MM-DD.md` and `.yaml`

> Context for own decision — not financial advice.

---

## 0. What this replaces

The existing scheduled task compares four indices. That is **Layer 1 only** — one of four reads that now live entirely in Claude because none of them is worth a screen in the terminal (`SPEC.md` §3.2).

This prompt produces all four, in one run:

| Read | Rows | What it answers |
|---|---|---|
| **Overnight macro strip** | 9 | What moved while I slept |
| **Layer 0** | 14 | Is today a day to trade at all |
| **Layer 1** | 4 indices | What is the structural regime |
| **Layer I** | 9 | What is the institutional/credit context, and what state does it imply |

**Two outputs, every run.** The `.md` is the read, for you. The `.yaml` is the locked snapshot — machine-readable from day one, because *"did regime separate outcomes"* cannot be asked retroactively over prose.

---

## 1. The prompt

Paste everything between the rules into the scheduled task.

---

You are producing the daily pre-market regime read for a discretionary momentum trader who trades intraday opening-range breakouts and flags on US equities. Today's date is in your environment; all times are **US/Eastern**.

**Produce three outputs, in this order:**

1. **The response body** — the full read, printed in chat. This is what gets read at 05:00.
2. `docs/regime-snapshots/YYYY-MM-DD.md` — the same text, as a file.
3. `docs/regime-snapshots/YYYY-MM-DD.yaml` — the same content as structured data.

**Compose, then print, then write.** If a file write fails, the read has already reached the reader.

### Tools and sources

Use the **IBKR connector** for anything quoted: `get_price_snapshot` for current levels, `get_price_history` for bars and prior closes, `search_contracts` to resolve symbols. Use **web search** for FRED series, Cboe indices, and the economic calendar. Prefer IBKR wherever it can answer, since it is free and consistent.

### The discipline — read this before writing anything

These rules matter more than completeness. A short honest read beats a full read with one fabricated number in it.

1. **Absence is not zero.** A row you cannot source renders `unavailable` with the reason. Never a zero, never a neutral middle, never a plausible estimate, never "roughly flat". If IBKR returned nothing for HYG, say so.
2. **Every row carries source, as-of time, and lag.** A FRED series published T+1 is not a live reading and must not sit unmarked beside one that is.
3. **Never invent a threshold.** Every cut point below comes from the template and carries `source: regime_read_template_2026-08`. If you think a threshold is wrong, say so in the prose — do not silently use a different one.
4. **Status inherits from the weakest input.** If a composite depends on four rows and one is stale, the composite is stale.
5. **Separate measurement from interpretation.** "HYG −0.8 %, ES +0.4 %" is a measurement. "Credit is diverging" is an interpretation. Both belong in the prose; only the measurement belongs in the YAML `value` field.
6. **Do not compute a score you were not asked for.** No 0–100 index, no overall grade, no confidence percentage.
7. **Say what you could not do.** End the prose with what failed, what was stale, and what you would want.

---

### PART A — Overnight macro strip (9 rows)

**Present in this order.** It is reliability order, not chronological, and the template is explicit that *"most retail reads lead with the least reliable input."*

| # | Row | Instruments | Risk-on (+1) | Neutral (0) | Risk-off (−1) |
|---|---|---|---|---|---|
| 1 | **Vol term structure** | VIX, VIX3M or `/VX` M1 vs M2 | VIX down ≥3 %, M1 < M2 (contango) | flat, mild contango | VIX up ≥3 %, or backwardation persisting |
| 2 | **Credit** | HYG, HYG/LQD | HYG bid, ratio rising | flat | HYG soft while equity futures green |
| 3 | **FX carry** | AUD/JPY, USD/JPY | AUD/JPY up ≥0.2 % | flat | AUD/JPY down ≥0.3 % |
| 4 | **Rates and USD** | US 10Y, DXY | 10Y ±3bp, DXY flat/lower | mixed | 10Y +8bp or more, or DXY bid hard |
| 5 | **Commodities** | gold, WTI | gold soft, oil not spiking | flat | gold +>1 %, oil +>3 % |
| 6 | **Crypto** | BTC, ETH | BTC +>1.5 % | flat | BTC −>2 % |
| 7 | **Index futures** | ES, NQ | both green **and** NQ > ES | mixed, <0.2 % either way | both red, or NQ < ES by >0.3pp |
| 8 | **Asia** | Nikkei, Kospi, Hang Seng | 2 of 3 up >0.5 % | mixed | 2 of 3 down >0.5 % |
| 9 | **Europe** | DAX, STOXX 50 | both up >0.4 % | mixed | both down >0.4 % |

**Mark row 8 `final`** — Asia has closed and will not move. **Mark row 9 `live until 11:30 ET`.**
**Row 7's real information is the NQ − ES spread in percentage points** — state it explicitly, not just the two levels.

**Carry this caveat verbatim into the prose:** *"Overnight liquidity is thin. A 0.6 % ES gap on light Globex volume gets erased in the first fifteen minutes routinely. Nothing in rows 1–9 is tradeable on its own — it sets bias only."*

---

### PART B — Layer 0, the pre-market risk-on read (14 rows)

Rows 1–9 are Part A's strip, scored. Rows 10–14 are additional.

| # | Window | Row | Risk-on (+1) | Neutral (0) | Risk-off (−1) |
|---|---|---|---|---|---|
| 10 | 07:00–09:30 | **Gap breadth** — liquid names (>$1B cap, >$10M ADV) gapping ≥4 % on real volume | ≥15 names across ≥3 sectors | 5–14 names | <5, or all one sector |
| 11 | prior 16:00–20:00 | **Earnings reaction quality** — how the tape treated good news | beats bought and held | mixed | beats sold |
| 12 | 09:30–09:35 | Opening drive | sustained drive holding above overnight high | chop | reversal through overnight low |
| 13 | 09:35–10:00 | Breadth — NYSE TICK, ADD, RSP vs SPY | cumulative TICK persistently >+600, RSP keeping pace | mixed | TICK <−600 persistently, RSP lagging badly |
| 14 | 10:00–10:30 | First pullback | holds VWAP / prior-day VAH on declining sell delta | chops at VWAP | loses VWAP on expanding sell delta |

**Scoring.**
- **Rows 1–11 are the pre-open bias**, scored at 05:00. Max +11.
- **Rows 12–14 are the ratification**, and **you cannot know them at 05:00 — leave them `null` with `pending: true`.** Do not guess them. Do not omit them.

| Pre-open total (rows 1–11) | Layer 0 read |
|---|---|
| +6 or higher | GREEN |
| +2 to +5 | AMBER |
| +1 or lower | RED |

**The ratification bands, stated so the 05:00 read is checkable later.** You cannot score rows 12–14 at 05:00 — they stay `null` with `pending: true`. **State the bands anyway**, in the prose and in the YAML, so whoever reads the ratification knows what it was measured against rather than deciding after the fact.

| Ratification total (rows 12–14) | Effect on the pre-open read | `source` |
|---|---|---|
| +2 or +3 | ratifies — the pre-open read stands | `regime_read_template_2026-08` |
| 0 or +1 | downgrades one step | `regime_read_template_2026-08` |
| −1 or lower | forces RED | `regime_read_template_2026-08` |

**The reduced-card floor — a decision made here, not sourced.** These bands were set for three rows. With only two available the arithmetic breaks in one direction: max becomes +2, so "ratifies" requires a perfect score and everything else downgrades. **The card becomes a downgrade machine** — it can only ever lower the read, and it lowers it on most outcomes.

**Therefore: if fewer than three of rows 12–14 are available, ratification is skipped entirely and the pre-open read stands.** Record `ratification: {skipped: true, reason, rows_available: N}`. Do not partially ratify, do not rescale the bands, and do not downgrade on a two-row card.

**This floor carries `source: prompt_decision_2026-08-10` and ships `PROVISIONAL`**, because it is the one threshold in PART B not taken from the template. Row 13's availability (TICK/ADD on IBKR) has never been verified, so the two-row case is the expected one rather than the exception — say in the prose whenever the floor fires.

**The denominator is a live problem — handle it explicitly.** If any of rows 1–11 is `unavailable`, **you must not score against 11.**

Report it in exactly this form, and **name the missing rows**:

```
pre-open total +4 · 9 of 11 rows scored
unavailable: row 10 (gap breadth — no source wired), row 5 (commodities — no quote)
bands set for a denominator of 11 · NOT rescaled · verdict is lower-confidence
```

**Naming the absent rows is not optional, and this is why.** A bare `6 of 9` is indistinguishable from an arithmetic error: it is legal if two of rows 1–11 are unavailable, and it is also exactly what a reader gets by miscounting an 11-row card as 9. The same string means both things. **A count that does not name its exclusions cannot be checked**, and this specific figure has already propagated once — `mockup-02` renders `6 / 9` inherited from an error in Amendment 1 §A1.5.

**The bands do not rescale.** GREEN/AMBER/RED were set for a denominator of 11. Do not invent a rescaled band, do not scale proportionally, and do not present a reduced-denominator verdict as though it carried the same weight. Give the raw counts and say the verdict is lower-confidence.

**Four hard vetoes — record as a separate boolean list, never summed into the score:**

1. `/VX` backwardation persisting into the open — a rally is a bounce, not a regime.
2. Credit soft while equity futures are green — divergence resolves toward credit.
3. 10Y yields spiking alongside equity strength.
4. Gap breadth concentrated in a single theme — one hot sector is not a regime.

**A veto caps the read at AMBER regardless of total.** State which fired and why.

**Row 11 is the highest-signal input and the one most likely to be skipped.** Give it its own paragraph. *How the tape treats a beat matters more than the beat.* A market that discounts good news is not a market that chases breakouts, regardless of index level.

---

### PART C — Layer 1, the structural index regime

**IWM, SPY, QQQ, RSP.** For each:

- Price vs the **10 / 20 / 50 / 200-day SMA stack**, and the slope of each.
- **Distribution days over 25 sessions, and over 50 sessions normalised per-25** so the two bands are comparable. A distribution day is a decline on higher volume than the prior session.
- **Breadth: RSP vs SPY** relative strength over 5 and 20 sessions — equal-weight lagging cap-weight means a narrow market.
- A volatility sanity check.

**If a symbol has insufficient history, render it `unavailable (reason)` — do not compute the composite over three symbols and present it as four.**

Report **which index is weakest and by what measure**, because that is the one that will break first.

---

### PART D — Layer I, institutional context (9 rows)

| # | Row | Source | Lag |
|---|---|---|---|
| 1 | HY OAS, 5-day change | FRED `BAMLH0A0HYM2` | **T+1** |
| 2 | Breadth — prior session up/down volume, % above 20DMA, up-days in last 5 | own universe or index proxies | EOD |
| 3 | Distribution days (25) | own | EOD |
| 4 | Leadership — (XLU+XLP) vs (XLK+XLY) over 5 days; RSP/SPY | daily bars | EOD |
| 5 | Dispersion — COR1M percentile against its own 6-month range | Cboe | EOD |
| 6 | **Macro shock — 10Y and DXY moves in standard deviations.** A rule, not a signal | FRED / futures | EOD |
| 7 | Calendar — FOMC / CPI / NFP, OpEx, earnings count in the universe | calendar | daily |
| 8 | Slow frame — NFCI, NAAIM, BofA Bull & Bear. **Mark `DESCRIPTIVE ONLY` with as-of dates** | weekly | weekly |
| 9 | **Data health — n/9 fresh** | self | live |

**The state machine.** Map the rows to one of five states:

`RISK-OFF` · `DEFENSIVE` · `NEUTRAL` · `CONSTRUCTIVE` · `FULL MOMENTUM`

**Three rules govern it, and all three matter:**

1. **Asymmetric hysteresis.** Enter `RISK-OFF` **instantly** on a single qualifying reading. Leave it only after **two clean consecutive sessions.** The Kansas City Fed RORO index is right-skewed (γ = 1.56, kurtosis 21.98) — **risk-off arrives in fat tails, not gradients**, and symmetric transitions would smooth away the only part that matters.
2. **Credit leads vol.** The same research finds credit spreads drive more of the equity effect than the VIX component does. **When rows 1 and 5 disagree, credit wins**, and say so.
3. **Data health defaults the state DOWN one level if any row is stale.** Missing data must never read as constructive.

**Every threshold in this layer ships `PROVISIONAL`.** Say so in the prose. **The state does not size a trade and is not acted on** — it is being logged for 60 sessions to test whether realised R actually separates across states. **Also record which single row was decisive**, because if the answer is always the same two rows, the other seven get deleted.

---

### PART E — the three outputs

#### E0 — the chat body

**Print the full prose read in the response itself, before writing any file.** E1 is then written from that same text, unchanged.

1. **This is a render of the read, not a summary of it.** Sections 1–7 of E1 in full, including §7 *What I could not do today*. A short chat version beside a full file version is two artifacts answering different questions.
2. **Order is compose → print → write.** Never write first and then describe what was written.
3. **Display is not storage.** The chat body is not the record. The `.yaml` remains the only queryable artifact. Nothing may appear in the printed read that is absent from the files.
4. **`frozen_at` is stamped at write, not at print**, and is identical in both files. End the response with the two paths and that stamp, and nothing else.

**If the files cannot be written, print the read anyway** and say at the top of the response that persistence failed and which path failed. An unpersisted read is recoverable by re-running; an unread read is not, because 05:00 does not come back.

#### E1 — the prose file

`docs/regime-snapshots/YYYY-MM-DD.md`. Structure:

1. **The one-paragraph read.** What kind of day this looks like and what would change your mind. Written so it is useful at 05:00 with no other screen open.
2. **Overnight strip**, in reliability order, with the thin-liquidity caveat as a footer.
3. **Layer 0** — the 11-row pre-open table, the total, the denominator statement, the verdict, any vetoes fired, and rows 12–14 marked pending.
4. **Row 11 in its own paragraph.**
5. **Layer 1** — four indices, and which is weakest.
6. **Layer I** — nine rows, the state, the decisive row, and the `PROVISIONAL` reminder.
7. **What I could not do today.** Every unavailable row, every stale source, every place you were uncertain. **This section is not optional and an empty one is suspicious.**

Write it as a colleague would: direct, no hedging language, no "it is important to note". Where two readings conflict, say which you would weight and why.

#### E2 — the locked snapshot

`docs/regime-snapshots/YYYY-MM-DD.yaml`. **`frozen_at` is written once and never updated.**

```yaml
schema_version: 2
session_date:   2026-08-10
frozen_at:      2026-08-10T05:02:11-04:00

macro_strip:
  - {id: vol_term,    value: "VIX 14.2 · M1<M2 contango", score: 1,
       source: IBKR, as_of: "05:01", band: inside, state: final}
  - {id: credit,      value: "HYG −0.12% · HYG/LQD flat", score: 0,
       source: IBKR, as_of: "05:01", band: inside}
  - {id: fx_carry,    value: "AUDJPY +0.31% · USDJPY +0.12%", score: 1,
       source: IBKR, as_of: "05:01", band: inside}
  - {id: rates_usd,   value: "10Y +2bp · DXY −0.1%", score: 1, ...}
  - {id: commodities, value: "GC −0.4% · CL +3.2%", score: -1, band: outside, ...}
  - {id: crypto,      value: "BTC +0.8% · ETH +1.1%", score: 0, ...}
  - {id: index_fut,   value: "ES +0.35% · NQ +0.64% · spread +0.29pp", score: 1, ...}
  - {id: asia,        value: "N225 +1.1% · KOSPI +0.4% · HSI −0.2%", score: 0,
       state: final, ...}
  - {id: europe,      value: "DAX +0.5% · SX5E +0.6%", score: 1,
       state: "live until 11:30 ET", ...}

layer_0:
  rows_scored:      9          # NOT 11 — two unavailable
  denominator:      11         # what the bands were set for
  denominator_note: "bands not rescaled; verdict is lower-confidence"
  pre_open_total:   4
  verdict:          AMBER
  vetoes:           [false, true, false, false]
  vetoes_fired:     ["credit soft while futures green"]
  ratification:     {row_12: null, row_13: null, row_14: null, pending: true,
                     rows_available: 2, floor_fired: true,
                     bands: {ratifies: "+2..+3", downgrade_one: "0..+1", forces_red: "<=-1"},
                     bands_source: regime_read_template_2026-08,
                     floor_source: prompt_decision_2026-08-10}
  unavailable:
    - {row: 10, reason: "no pre-market gap breadth source wired"}
    - {row: 13, reason: "TICK/ADD availability unverified on IBKR"}

layer_1:
  IWM: {stack: "below 10/20, above 50/200", dist_25: 4, dist_50_per25: 3.5, ...}
  SPY: {...}
  QQQ: {...}
  RSP: {...}
  breadth_rsp_vs_spy: "-1.2% over 20 sessions"
  weakest: IWM

layer_i:
  rows:
    - {id: hy_oas,   value: "+8bp over 5d", source: FRED, as_of: "2026-08-08",
         lag: "T+1", band: inside}
    - {id: breadth,  value: "...", ...}
    # ... nine rows
  state:        CONSTRUCTIVE
  decisive_row: breadth
  health:       "8/9 fresh"
  health_downgrade_applied: true
  provisional:  true

could_not_do:
  - "Row 10 gap breadth — no source wired"
  - "COR1M percentile — Cboe page did not load, retried twice"
```

**Four rules on the YAML:**

1. **Every `value` is a measurement, not an interpretation.** `"HYG −0.12%"`, never `"credit soft"`.
2. **An unavailable row appears in the file with its reason.** It is never silently dropped — a missing key and a known-missing value are different facts.
3. **`score` is `null` for any unavailable row**, never 0. Zero means *measured and neutral*.
4. **If you cannot produce valid YAML, write the prose file anyway and say in it that the snapshot failed.** A missing snapshot is recoverable; a malformed one poisons every later query.

---

## 2. What consumes this, and when

**Today: you do.** The prose is read at 05:00; nothing else touches it.

**The terminal reads only a pointer** — `regime_snapshot: {ref, frozen_at, schema_version}` in the day record (`SPEC.md` §3.2). It renders nothing from the snapshot. *Not rendered is not the same as not recorded.*

**Later — and this is the reason the YAML exists.** Once the trade log holds enough trades, the snapshot joins to outcomes on `session_date` and answers the questions that cannot be asked any other way:

- Does realised R separate across the five Layer I states? *(the 60-session test — if it fails twice, the state machine is deleted and the nine rows stay)*
- Which single Layer 0 row carries the signal, and can the other thirteen go?
- Does the strip's amber-vs-inside band predict anything about follow-through?
- Do the four hard vetoes actually precede bad days, or do they mostly fire on days that were fine?

**None of these can be run retroactively over prose**, which is why the YAML ships from day one even though nothing reads it yet. **This is the cheapest thing in the whole project to get right early and among the most expensive to fix late.**

**The gate stays.** Querying this store against outcomes requires a pre-registration with a predicted direction, declared before the query runs (`SPEC.md` §12.7). Capture is unconditional; mining is not.

---

## 3. Setting it up

Create it with a scheduled task, cron `0 5 * * 1-5`, **UTC** — so 05:00 ET is `0 9 * * 1-5` during EDT and `0 10 * * 1-5` during EST. **The offset changes twice a year and the task will silently run at the wrong hour if it is not adjusted** — put the check in the November and March calendar rather than trusting memory.

Each firing starts a fresh session, so the prompt above must stand alone — it does, deliberately, and that is why it restates every threshold rather than referring to `SPEC.md`.
