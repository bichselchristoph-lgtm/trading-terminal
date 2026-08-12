---
id: S010
title: Attach a symbol, and the context block
status: RUNNING — stays RUNNING until this note reaches the design session
owner: claude-code
ran: 2026-08-12, 12:30 → 16:20 ET
tree: D:\Dev\momentum
---

# S010 — attach a symbol, and the context block

**Status** RUNNING

**`S010` was free.** No done-note, no collision with the bare-numbered tasks.

**All seven parts done.** Parts 0–5 built against fixtures while the `019` capture held the only
client; **part 6 ran after 16:00 ET**, once the capture had closed and released `clientId 11`.

**Suite: 154 → 182 passed, 0 failed.** +28 tests.

> **This note has to be pasted into chat.** Writing it is not reporting it.

---

## Part 0 — the `BUILD-PLAN.md` contradiction, confirmed and built as ruled

**Confirmed, and it is worse than the task describes.**

`2c-bis` says VWAP is bar-derived, one basis, and *"the tick-derived variant is retired."*
The contradicting text is in item **`2b`**, not item 2 — and `2b` does not merely disagree about
the default, it **specifies the label format for the retired basis**:
*`VWAP 47.31 (tick-derived · pre-market incl. · from 04:00 · 18.4M sh)`*, plus a fallback string
*`VWAP 47.28 (bar-derived — tick budget exhausted)`*.

**So a reader following `2b` gets three wrong things: the basis, a label implying a choice
exists, and a substitution state that `2c-bis` deletes.**

**`2c-bis` was built.** Not built, deliberately: the `tick budget exhausted` state, the
1,000-tick pagination, the boundary-second dedup. `test_vwap_is_bar_derived_and_says_so`
asserts none of the strings `tick-derived`, `tick budget` or `fallback` can appear in a rendered
VWAP label.

**`BUILD-PLAN.md` was not edited.** Reported here as a spec defect. **A spec that says two
things is worse than one that says the wrong thing**, because a reader cannot tell which is
current — and §010 is long enough that most readers will hit `2b` after `2c-bis` and take the
later text as the amendment.

---

## Parts 1–3 — what was built

### `core/` is born

The tree had **no `core/` at all**. `core/indicators/context.py` is pure — stdlib only, no
first-party imports — which is what let the entire slice be built and tested while TWS was
unavailable.

**Three fixtures exist specifically because the wrong implementation passes a spot check:**

- **ADR% excludes today.** The test replaces today's bar with a 200/50 monster and asserts the
  answer does not move. A 20-day window that quietly includes today is off by one *every day*,
  and on a normal day the error is invisible.
- **ATR is Wilder's RMA, not a mean of the last 14 true ranges.** The fixture plants one spiked
  bar so the two diverge by more than 0.1; on a flat series they agree, which is precisely how
  the wrong version survives review.
- **RVOL's denominator is a median curve.** One 1000× session dropped into twenty. With a mean,
  today's reading is silently deflated at **every minute of the session**, not at one point.

**`Measured` cannot hold a half-populated state** — a value *or* a reason, never both, never
neither. Constructing one raises. `warming` is not reachable from here, because there is no
cache that could produce it.

### The attach sequence

`MarketData` is a **Protocol**, so all four refusals run with no broker. **That constraint
produced a better design than convenience would have** — the whole surface is exercisable on a
machine with no TWS at all.

Step 2 precedes step 3; step 4 does not gate step 3.
`test_the_slot_is_checked_before_any_historical_request_is_spent` asserts the call order
directly, and then asserts the context block is **fully populated anyway** — which is the point
of the ordering rather than a side effect of it.

---

## Part 6 — the three live attaches, in full

**After 16:00 ET.** `readonly=True`, **`clientId 22`** — 11 belongs to the capture and was
released cleanly. Server time `2026-08-12 20:06:41+00:00`.

### 1 · AAPL — liquid large-cap

```
attached      : True          qualified     : True
contract      : conId=265598 SMART primary=NASDAQ sector_etf=XLK
slot state    : 0/5 slots used
tape          : absent - tape not opened by S010 - no tape components in core
playbook      : no trigger level declared
  ADR%               2.3226   (20 sessions, excl. today)
  ADR $              7.0887   (20 sessions, excl. today)
  ADR used          41.6157   (20 sessions, excl. today)
  room up           10.0387   (20 sessions, excl. today)
  room down          4.1387   (20 sessions, excl. today)
  ATR14              8.5365   (Wilder RMA, n=14, 59 true ranges)
  ext 10            -1.1963   (10-day SMA / ADR $)
  ext 20            -2.6760   (20-day SMA / ADR $)
  ext 50            -1.0194   (50-day SMA / ADR $)
  VWAP             302.1160   (bar-derived · 31,807,279 sh · 727 min · 08:00:00 to 20:06:00 UTC)
  cum vol       31,807,279    (727 min from 2026-08-12 08:00:00+00:00)
  RVOL               0.8771   (20:06 · 20d median)
  RVOL_rel           1.1478   (vs sector · 20:06 · 20d median)
-- level rail
  PDH 309.9700 · PDL 302.7900   (prior session)
  PMH 305.2000 · PML 304.2700   (90 pre-market bars)
  ORH 304.8500 · ORL 304.6800   (5 opening-range bars)
  VWAP 302.1160 · 52wH 344.5700 · 52wL 223.7800
  round 28 levels               (±7.09 of 302.25)
```

**ADR% 2.32 and ATR₁₄ 8.54 are visibly different quantities** on the same name — 7.09 dollars
against 8.54. That is the gap-inclusion difference doing exactly what §010 2f says it does, and
it is why they may never share a label.

### 2 · CULP — thin small-cap

```
attached      : True          qualified     : True
contract      : conId=2586004 SMART primary=NASDAQ sector_etf=XLY
slot state    : 0/5 slots used
  ADR%               4.3958   (20 sessions, excl. today)
  ADR $              0.1517   (20 sessions, excl. today)
  ADR used           6.5939   (20 sessions, excl. today)
  room up            0.1417   ·  room down  0.1617
  ATR14              0.1565   (Wilder RMA, n=14, 59 true ranges)
  ext 10            -0.1055  ·  ext 20  -0.6495  ·  ext 50   0.7491
  VWAP               3.4720   (bar-derived · 7,932 sh · 722 min · 08:10 to 20:11 UTC)
  cum vol            7,932    (722 min from 2026-08-12 08:10:00+00:00)
  RVOL           see note     ·  RVOL_rel  see note
-- level rail
  PDH 3.4900 · PDL 3.3500 · PMH 3.5000 · PML 3.5000
  ORH 3.5000 · ORL 3.5000 · 52wH 4.8000 · 52wL 2.7000
  round 1 level                (±0.15 of 3.46)
```

**7,932 shares in a whole session, against AAPL's 31.8 million — a factor of 4,000.** The thin
name behaves as intended: **ADR% is nearly double AAPL's (4.40 % vs 2.32 %) while ADR $ is
1.5 cents**, which is the percentage-versus-dollars distinction the sizing slice will depend on.
Its pre-market high and low are identical at 3.5000, as are ORH and ORL — a name that printed
one price for the whole opening range. **Nothing refused; it is simply a very quiet stock.**

### 3 · QQQ — an ETF, expected to have no sector mapping

```
attached      : True          qualified     : True
contract      : conId=320227571 SMART primary=NASDAQ sector_etf=None
  ADR%               1.7016   ·  ADR $  12.3720  ·  ADR used  27.3198
  ATR14             13.3737   (Wilder RMA, n=14, 59 true ranges)
  ext 10             0.9985  ·  ext 20   1.8322  ·  ext 50   0.8249
  VWAP             724.5270   (bar-derived · 19,489,956 sh · 734 min · 08:00 to 20:13 UTC)
  RVOL               0.6814   (20:13 · 20d median)
  RVOL_rel      unavailable   (no sector mapping)          <-- REFUSAL C, LIVE
  PDH 723.3800 · PDL 715.5000 · 52wH 748.6500 · 52wL 555.6000
```

**`RVOL_rel unavailable (no sector mapping)` — verbatim.** Not `1.0`, not blank. An ETF has no
industry of its own, so the mapping correctly returns `None` rather than guessing, and the
refusal names itself.

**Every field on all three either shows a number that can be checked by hand or names why it
cannot.**

---

## The defect the live run found in my own code

**The first live run rendered `RVOL unavailable (no 20-session reference for 20:03)` on all
three symbols.**

**Cause: the two sides of the ratio were on different bases.** `today_minutes` fetched with
`useRTH=False` — correct, because session VWAP includes pre-market — while `intraday_sessions`
fetched the 20-session curve with `useRTH=True`. An RTH-only curve has **no key past the
close**, so at 16:03 ET there was nothing to divide by.

**`SPEC.md` §010 2f states the rule I broke, in one sentence:** *"RVOL must simply match itself
— today and the 20-session reference on the same basis."*

**What makes this worth reporting rather than just fixing: the symptom was a refusal, and that
was luck.** Running one minute earlier, inside RTH, the same mismatch would have divided a
**pre-market-inclusive numerator** by an **RTH-only denominator** and rendered a plausible
number — a stock at RVOL 1.4 reading as 1.9, with nothing to indicate anything was wrong. **The
version that refuses is the fortunate version of this bug.** Fixed, with that reasoning in the
comment at the call site rather than only here.

**Second, smaller defect from the same run:** the tape refusal rendered `absent - RuntimeError`,
the exception *class* rather than its message. Now `absent - tape not opened by S010 - no tape
components in core`, which a reader can act on.

---

## Refusals

| | Result |
|---|---|
| **A** — kill a request mid-fetch | **PASS.** Fail the daily request: ADR%, ADR $, ADR used, room up/down and ATR₁₄ all carry `pacing limit, retry in 42s`, while **VWAP and RVOL still render** — they came from other requests. `test_a_partial_adr_is_impossible_by_construction` proves there is no state where ADR $ exists and ADR% does not |
| **B** — same symbol inside 15 s | **PASS in fixtures**, rendering `queued - 11s`. **NOT exercised live** — see below |
| **C** — no sector mapping | **PASS in fixtures AND live.** QQQ rendered `unavailable (no sector mapping)`; asserted not `1.0` and not blank |
| **D** — ambiguous ticker | **PASS.** Candidates render, `r.contract is None`, `r.qualified is False`. Asserts **no contract was qualified** — not that the best one was |

**Refusal B was not exercised live, and I am not reporting it as though it were.** The live
re-attach of AAPL came **roughly seven minutes** after its first fetch, because the three
symbols in between made ~16 historical requests. The 15-second cooldown had legitimately
expired, so `slot state: 0/5 slots used` is the **correct** answer to what was actually asked.
It is covered by `test_refusal_b_the_same_symbol_twice_inside_the_cooldown` against a fixture.

---

## Part 4 — the seam

`test_the_seam_two_attach_times_agree_to_the_cent` reconstructs the same window at two attach
times and asserts **VWAP to the cent and cumulative volume exactly.**

**It asserts both, and the reason is `008b`'s measured asymmetry.** VWAP survives a uniform
double-count because both terms of `Σ(WAP × volume)` scale together; **cumulative volume does
not.** A seam test on VWAP alone would pass while volume was 2× wrong — and volume is RVOL's
numerator, so the failure would put names in front of you that nothing was happening in. A
second test pins the asymmetry directly: 30,000 shares against 60,000.

---

## Part 5 — recorded as owed, not written

**`SPEC.md` §6b.1c** requires that a symbol process cannot size, stage or evaluate a limit,
**enforced structurally.** The sizing and staging modules do not exist, so the real test — no
edge in the module graph, `size_for()`'s parameter list containing no rule type — **would pass
because its subject is absent.**

**Owed by `S011`**, and stated in the test's own docstring so a future reader cannot mistake the
weak version for the rule. What *is* checked today is the source text, which at least fails if
someone adds the import before `S011` lands.

**A second thing is owed and was not in the task.** The predecessor's
`tests/test_import_boundaries.py` — forbidding any edge between `harness` and `live` — **has
never been carried into this tree.** `core/` arrived under this slice with the rule stated in
two documents and nothing checking it. I wrote the narrow half
(`core/tests/test_core_imports_nothing_first_party.py`, **AST-based, because an import-time
check passes on a lazy in-function import**) plus a guard that goes red the day `harness/`
appears.

---

## Which `SPEC.md` §4 refusal terms this slice made reachable

| term | reachable? | producer |
|---|---|---|
| `unavailable (<reason>)` | **YES** | every `Measured.absent` path — failed request, short history, no sector, no WAP |
| `absent, not zero` | **YES**, in substance | `Measured` refuses to be constructed with neither a value nor a reason |
| `NOT BUILT` | yes, but **not from here** — `S009a`'s pipeline panel |
| `no-source` | yes, **not from here** |
| `warming` | **NO, and structurally so.** It survives on tape baselines alone and there are no tape components in core |
| `partial` · `reduced denominator` | **NO** | no producer in this slice |
| `unfitted` · `untested` | **NO** | nothing here is fitted |
| `STALE` · `FROZEN` | **NO** | no freshness tracking in this slice |
| `superseded` · `flagged, not an error` | **NO** | no producer anywhere in the tree yet |

**Seven of the fourteen remain constants with no producer.** That is not a gap to fill — they
belong to slices that have not run — but it is worth knowing that `grammar.py`'s vocabulary is
half-unused, because a constant nobody produces is a constant nobody has tested.

---

## Exit tests

| Test | Who | Result |
|---|---|---|
| **Green** | Claude Code | **154 → 182 passed, 0 failed.** Includes the no-disk-write assertion and the two-attach-times seam test |
| **Refusal A** | Claude Code | **PASS** |
| **Refusal B** | Claude Code | **PASS in fixtures; not exercised live** — stated above |
| **Refusal C** | Claude Code | **PASS in fixtures and live** |
| **Refusal D** | Claude Code | **PASS** |
| **UAT** | Christoph | Attach a name you know well and check ADR%, ATR and RVOL against your own charts **before looking at anything else.** Then attach it twice — once pre-open, once mid-session — and confirm every value agrees. **Check the VWAP label carries its basis and its sample in both.** Write the record to `christoph/open/` |

**`test_no_disk_write_on_the_attach_path`** compares `git status --porcelain` across two full
attaches. **BUILD-PLAN says that if this slice needs a cache the decision was wrong**, so it is
a test rather than a sentence.

---

## The commit split

| commit | subject |
|---|---|
| `0cc4fc7` | Eight more allowlist entries, and core/ is born |
| `5037bea` | S010: core/indicators/context.py — the context block's arithmetic |
| `e9650cc` | S010: the attach sequence — five steps, three failing independently |
| *(this batch)* | S010 part 6: the live IBKR adapter, and the RVOL basis fix |
| *(this batch)* | 019's done-note, 018 part 1's note, OBS-017 and the UAT register |

---

## Anything that was wrong on contact

**1 · The `BUILD-PLAN.md` contradiction is in `2b`, not item 2, and it is three-fold.** Part 0.

**2 · My own RVOL basis mismatch, found only by running it live.** The fixtures could not catch
it: they are internally consistent by construction, and the bug lives in *which real request
each side makes*. **A slice that had shipped on fixtures alone would have shipped this.**

**3 · Refusal B could not be exercised live in the same run as three attaches**, because the
cooldown is 15 s and the run takes minutes. Reported rather than claimed.

**4 · The task's `MarketData` had no live implementation and the task did not ask for one.**
Parts 1–5 describe the sequence; part 6 says *attach three symbols*. Nothing connects them, so
`live/attach/ibkr.py` was written to make part 6 possible. **It is new surface that was not
specified**, and it is where the RVOL defect lived — worth reviewing on its own terms rather
than as an assumed detail.

**5 · `handoff/inbox/S010-*.md` did not exist when the task was first given.** I stopped and
reported rather than reconstructing it from `BUILD-PLAN.md` §010; Christoph placed the file
afterwards. **Recorded because the alternative — building from the plan entry — would have
produced something nobody specified, and the contradiction in part 0 is exactly what that
would have got wrong.**

---

**Paste this into chat. `S010` stays `RUNNING` until it lands there.**
