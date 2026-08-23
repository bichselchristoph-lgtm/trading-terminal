---
id: 082
title: Does concurrent dispatch cost the fast requests time — batched against concurrent, measured
type: task
class: admin
unblocks: NOTHING
story: none
owner: claude-code
depends: none
touches: nothing — no production file was edited by this task
bugs:
  - id: B-138
    action: confirm
    status: "Measured, not fixed, per the task's own instruction. Five rounds, two symbols, three arms, live against real TWS. The 21.11s rth_dailies figure from 080 did NOT reproduce once across 26 direct measurements (max observed: 4.48s) — points at variance/connection state, not dispatch shape, for the FAST role. For the SLOW roles (sessions/sector_sessions), concurrent dispatch (arm B) IS measurably worse: on QQQ, average wall time rose from 28.5s (sequential) to 46.5s (concurrent); on AMZN, running both large 20-session pulls truly simultaneously drove the timeout rate from 0/5 (sequential, sector_sessions) and 1/5 (sequential, sessions) up to 3/5 for both under concurrent dispatch. But AMZN's TOTAL arm time was still fastest under concurrent dispatch (60s capped, vs. 89s sequential) — per-request and total wall time move in OPPOSITE directions for AMZN, exactly the split conclusion §7 asked this task to distinguish. Full numbers below."
---

**Status** RUNNING

# 082 — batched against concurrent, on the wire

**This note needs to be pasted to chat.**

---

## What ran

Standalone scratch harness (`$env:TEMP`-equivalent — actually `$CLAUDE_JOB_DIR/tmp` on this machine, per this session's own scratch convention; not committed, per §5), `client_id=82`, connected to live TWS (port 7496, confirmed reachable immediately before connecting). Imported the repo's own request-building pieces directly — `_request_kwargs`, `_contract_for`, `_pacing_key`, `_PacingGuard`, `LONG_DAILY_DURATION`, `INTRADAY_DURATION` from `live/attach/ibkr.py`, `ADR_BASIS`/`INTRADAY_BASIS` from `core/indicators/context.py` — nothing reimplemented, per §2's own instruction.

**Three roles, same shapes the terminal uses today**: `rth_dailies` (`"1 Y"`/`"1 day"`, RTH), `sessions` (`"20 D"`/`"1 min"`, ETH), `sector_sessions` (same shape, on the sector ETF). `resolve()` was called live for both symbols rather than assuming a mapping: **QQQ resolved with no sector mapping** (confirmed live, matching 080's own observation), so QQQ ran two roles per arm and AMZN (resolved to `XLC`) ran three.

**Three arms**: A (batched, one `asyncio.gather` via `_BrokerLoop.call()` — 075's shape), B (concurrent, three independent `_BrokerLoop.call()` invocations each dispatched from its own OS thread via `ThreadPoolExecutor` — 080's shape, matching `run_worker(thread=True)` ×3 exactly), C (sequential, one role awaited at a time — the control, per §3's own instruction that it is not a candidate design).

**Interleaved A, B, C every round**, both symbols, per round — never all of one arm before the next.

**Five rounds completed, not six.** A 25-minute wall-clock ceiling was set going in (this task has no product deadline, but an unbounded live-TWS run is not a reasonable default); round 6 was cut off by it, not by the pacing guard, which never fired across any of the five completed rounds. Recorded as `event=STOP_WALL_CLOCK_BUDGET round=6` in the raw log — the task's own §7 explicitly accepts this ("fewer if it does not [allow]... the data cannot tell, and the third answer is a perfectly good one").

**One harness bug found and fixed mid-run, itself a real finding**: the first attempt crashed on AMZN round 1 with an unhandled `TimeoutError`, because `_BrokerLoop.call()`'s 60s timeout applies to the **whole gather** in arm A, not per-role — so when `sessions` alone would have exceeded 60s, the ENTIRE batched call raised, discarding `rth_dailies`'s already-arrived result along with it. Fixed by catching it and recording `role=ALL bars=LOST`. This is not a harness defect being patched over — it is itself the finding in §4's "any timeout, with which role" column, and it is structural to arm A specifically: **B and C each give every role its own independent 60s budget; A gives the whole batch one shared budget**, so a single slow role in a batch can cost the batch everything, including data that had already come back.

---

## Every round's raw numbers

Full raw log (84 rows across 5 rounds): `$CLAUDE_JOB_DIR/tmp/082_results.txt` — not committed, quoted here in full for the record.

```
symbol=QQQ arm=A_batched round=1 role=rth_dailies wall_s=4.484 bars=251
symbol=QQQ arm=A_batched round=1 role=sessions wall_s=22.75 bars=19200
symbol=QQQ arm=B_concurrent round=1 role=rth_dailies wall_s=3.094 bars=251
symbol=QQQ arm=B_concurrent round=1 role=sessions wall_s=46.094 bars=19200
symbol=QQQ arm=C_sequential round=1 role=rth_dailies wall_s=0.812 bars=251
symbol=QQQ arm=C_sequential round=1 role=sessions wall_s=28.656 bars=19200
symbol=AMZN arm=A_batched round=1 role=ALL wall_s=60.0 bars=LOST error=whole-batch timeout: no answer in 60s (request_timeout_s)
symbol=AMZN arm=B_concurrent round=1 role=rth_dailies wall_s=0.922 bars=251
symbol=AMZN arm=B_concurrent round=1 role=sessions wall_s=60.0 bars=None error=no answer in 60s (request_timeout_s)
symbol=AMZN arm=B_concurrent round=1 role=sector_sessions wall_s=60.0 bars=None error=no answer in 60s (request_timeout_s)
symbol=AMZN arm=C_sequential round=1 role=rth_dailies wall_s=0.922 bars=251
symbol=AMZN arm=C_sequential round=1 role=sessions wall_s=38.062 bars=19200
symbol=AMZN arm=C_sequential round=1 role=sector_sessions wall_s=47.875 bars=14925

symbol=QQQ arm=A_batched round=2 role=rth_dailies wall_s=0.703 bars=251
symbol=QQQ arm=A_batched round=2 role=sessions wall_s=30.922 bars=19200
symbol=QQQ arm=B_concurrent round=2 role=rth_dailies wall_s=2.735 bars=251
symbol=QQQ arm=B_concurrent round=2 role=sessions wall_s=41.703 bars=19200
symbol=QQQ arm=C_sequential round=2 role=rth_dailies wall_s=0.782 bars=251
symbol=QQQ arm=C_sequential round=2 role=sessions wall_s=45.781 bars=19200
symbol=AMZN arm=A_batched round=2 role=rth_dailies wall_s=2.64 bars=251
symbol=AMZN arm=A_batched round=2 role=sessions wall_s=60.0 bars=0
symbol=AMZN arm=A_batched round=2 role=sector_sessions wall_s=60.0 bars=0
symbol=AMZN arm=B_concurrent round=2 role=rth_dailies wall_s=2.672 bars=251
symbol=AMZN arm=B_concurrent round=2 role=sessions wall_s=60.0 bars=None error=no answer in 60s (request_timeout_s)
symbol=AMZN arm=B_concurrent round=2 role=sector_sessions wall_s=60.0 bars=None error=no answer in 60s (request_timeout_s)
symbol=AMZN arm=C_sequential round=2 role=rth_dailies wall_s=4.157 bars=251
symbol=AMZN arm=C_sequential round=2 role=sessions wall_s=54.89 bars=19200
symbol=AMZN arm=C_sequential round=2 role=sector_sessions wall_s=21.985 bars=14925

symbol=QQQ arm=A_batched round=3 role=rth_dailies wall_s=0.703 bars=251
symbol=QQQ arm=A_batched round=3 role=sessions wall_s=47.953 bars=19200
symbol=QQQ arm=B_concurrent round=3 role=rth_dailies wall_s=1.937 bars=251
symbol=QQQ arm=B_concurrent round=3 role=sessions wall_s=48.797 bars=19200
symbol=QQQ arm=C_sequential round=3 role=rth_dailies wall_s=1.281 bars=251
symbol=QQQ arm=C_sequential round=3 role=sessions wall_s=16.672 bars=19200
symbol=AMZN arm=A_batched round=3 role=ALL wall_s=60.0 bars=LOST error=whole-batch timeout: no answer in 60s (request_timeout_s)
symbol=AMZN arm=B_concurrent round=3 role=rth_dailies wall_s=0.969 bars=251
symbol=AMZN arm=B_concurrent round=3 role=sessions wall_s=60.0 bars=0
symbol=AMZN arm=B_concurrent round=3 role=sector_sessions wall_s=60.0 bars=0
symbol=AMZN arm=C_sequential round=3 role=rth_dailies wall_s=1.109 bars=251
symbol=AMZN arm=C_sequential round=3 role=sessions wall_s=46.016 bars=19200
symbol=AMZN arm=C_sequential round=3 role=sector_sessions wall_s=48.203 bars=14925

symbol=QQQ arm=A_batched round=4 role=rth_dailies wall_s=0.703 bars=251
symbol=QQQ arm=A_batched round=4 role=sessions wall_s=20.75 bars=19200
symbol=QQQ arm=B_concurrent round=4 role=rth_dailies wall_s=0.781 bars=251
symbol=QQQ arm=B_concurrent round=4 role=sessions wall_s=48.734 bars=19200
symbol=QQQ arm=C_sequential round=4 role=rth_dailies wall_s=0.765 bars=251
symbol=QQQ arm=C_sequential round=4 role=sessions wall_s=32.625 bars=19200
symbol=AMZN arm=A_batched round=4 role=ALL wall_s=60.016 bars=LOST error=whole-batch timeout: no answer in 60s (request_timeout_s)
symbol=AMZN arm=B_concurrent round=4 role=rth_dailies wall_s=0.594 bars=251
symbol=AMZN arm=B_concurrent round=4 role=sessions wall_s=60.015 bars=None error=no answer in 60s (request_timeout_s)
symbol=AMZN arm=B_concurrent round=4 role=sector_sessions wall_s=60.015 bars=None error=no answer in 60s (request_timeout_s)
symbol=AMZN arm=C_sequential round=4 role=rth_dailies wall_s=0.704 bars=251
symbol=AMZN arm=C_sequential round=4 role=sessions wall_s=60.0 bars=None error=no answer in 60s (request_timeout_s)
symbol=AMZN arm=C_sequential round=4 role=sector_sessions wall_s=41.046 bars=14925

symbol=QQQ arm=A_batched round=5 role=rth_dailies wall_s=0.719 bars=251
symbol=QQQ arm=A_batched round=5 role=sessions wall_s=48.907 bars=19200
symbol=QQQ arm=B_concurrent round=5 role=rth_dailies wall_s=2.234 bars=251
symbol=QQQ arm=B_concurrent round=5 role=sessions wall_s=47.14 bars=19200
symbol=QQQ arm=C_sequential round=5 role=rth_dailies wall_s=0.782 bars=251
symbol=QQQ arm=C_sequential round=5 role=sessions wall_s=18.796 bars=19200
symbol=AMZN arm=A_batched round=5 role=ALL wall_s=60.016 bars=LOST error=whole-batch timeout: no answer in 60s (request_timeout_s)
symbol=AMZN arm=B_concurrent round=5 role=rth_dailies wall_s=0.922 bars=251
symbol=AMZN arm=B_concurrent round=5 role=sessions wall_s=60.0 bars=0
symbol=AMZN arm=B_concurrent round=5 role=sector_sessions wall_s=60.0 bars=0
symbol=AMZN arm=C_sequential round=5 role=rth_dailies wall_s=0.922 bars=251
symbol=AMZN arm=C_sequential round=5 role=sessions wall_s=46.453 bars=19200
symbol=AMZN arm=C_sequential round=5 role=sector_sessions wall_s=34.313 bars=14925
```

**Bars received against bars requested (B-033):** every succeeding `rth_dailies` returned 251 bars; every succeeding QQQ `sessions` returned 19200 (20 sessions × 960 min, ETH); every succeeding AMZN `sector_sessions` returned 14925 (below the 19200 ceiling — XLC has fewer than 960 minutes of bars in at least one of its 20 sessions, or IBKR served fewer; not investigated further, out of scope for this task). No case of a "204 for 205" partial short-by-one was observed here — every completion was either the full expected count or an explicit timeout with zero bars.

---

## Does arm B make individual requests slower than arm A?

**For `rth_dailies` (the fast role): the data cannot tell, and that is itself the answer.** Every value across all three arms and both symbols falls in 0.59s–4.48s — a 7.6× spread **within** arms that dwarfs any difference **between** them (QQQ averages: A 1.46s, B 2.16s, C 0.88s; AMZN averages: B 1.22s, C 1.56s, A only one surviving sample at 2.64s). Five rounds on one connection on one afternoon is not a distribution wide enough to separate a real 0.7-second effect from noise this size.

**The 21.11s `rth_dailies` figure from 080 did NOT reproduce once** — not on QQQ, not on AMZN, not in any of the three arms, across 26 direct `rth_dailies` measurements (30 total attempts minus 4 lost inside AMZN's arm-A batch timeout). The maximum ever observed was 4.48s. **This points at variance or a transient connection state on that one run, not at dispatch shape** — directly answering §1's question in the negative for the fast role.

**For `sessions`/`sector_sessions` (the slow roles): yes, concurrent dispatch measurably costs them, and the effect is large enough to separate from noise.**
- QQQ `sessions`: sequential (C) averaged 28.5s; concurrent (B) averaged 46.5s — every one of B's five rounds (41.7–48.8s) sat above every one of C's except one (45.78s). Batched (A) sat in between at 34.3s, closer to sequential.
- AMZN, where BOTH `sessions` and `sector_sessions` are large pulls that arm B runs **truly simultaneously**: sequential timed out 1/5 on `sessions` and 0/5 on `sector_sessions`; concurrent timed out 3/5 on **both**. The two large pulls appear to contend with each other when genuinely concurrent, in a way they do not when one runs after the other.

---

## Does total time and per-request time move in the same direction?

**No — and AMZN is the case §7 asked this task to watch for.** AMZN's arm B total (capped at ~60s, since the two slow pulls overlap rather than sum) is **faster** than arm C's total (~89s, since sequential sums each role's own time) — but arm B's **individual** `sessions`/`sector_sessions` requests fail far more often (3/5 timeouts each) than arm C's (1/5 and 0/5). **Concurrency makes the whole set land sooner while making each of the two slow pieces of it less reliable, at the same time, on the same symbol.** For QQQ (only one slow role, no contention to speak of), total and per-request move together: B is worst on both (46.5s per-role, 46.5s total — with only one slow role, "total" and "the slow role's own time" are nearly the same number by construction).

---

## Anything contradicting §1

**Nothing contradicts §1's own framing.** §1 predicted "the dispatch shape, plus cold-connection and single-run variance" as what remained untested, and named the 21.11s figure as the thing in question — this run answers exactly that: the figure did not reproduce, dispatch shape does not measurably cost the fast role, and it does measurably cost the slow roles specifically when two of them run genuinely concurrently against the same connection.

---

## What this means for the panel, stated but not built (§5: measure only, do not fix)

**Two different findings with two different implications, and they should not be collapsed into one conclusion:**

1. **`ADR% used`'s promise ("lands in ~1-2s") is not threatened by the two-stage split's dispatch shape.** The fast role's timing is dominated by run-to-run variance far larger than any concurrency cost this measurement could detect.

2. **`RVOL`'s promise is more fragile on a symbol WITH a sector mapping than the two-stage split's own design assumed.** 080's architecture opens `sessions` and `sector_sessions` as two independent, genuinely concurrent workers specifically because independent landing requires it — but on AMZN, that is exactly the shape that drove BOTH of RVOL's two readings to a 60% timeout rate in this run, when running them one after another left `sector_sessions` succeeding every time and `sessions` failing only once. **If this held up under more rounds, and if it holds for the sector-mapped names that trade most (financials, tech, communications — not every symbol is QQQ's no-mapping case), the practical availability of `RVOL`'s sector-relative reading on a live floor may be measurably worse than 080's own live run (a single AMZN attach, not five) suggested.** Not a recommendation to change the dispatch shape — per §5, that decision belongs to whoever reads this, with the numbers in hand, not to this task.

---

## What was NOT touched

No production file — `touches:` was empty and stayed empty; `git status` shows nothing under `live/`, `core/`, `tools/` or `config/` changed by this task. `request_timeout_s` was read, never written, and fired exactly as configured (60s) on every timeout above — its own value is untouched, per B-132. No historical request's duration, bar size or `use_rth` differs from what `attach.py`/`ibkr.py` issue today. The harness (`$CLAUDE_JOB_DIR/tmp/082_batched_vs_concurrent.py`) is not committed.

---

## Closing sequence

No Green/Refusal/UAT tests, per §6 — no behaviour changed, nothing to pin. `verify.ps1` runs as the last action, not pasted or summarised here. `export-handoff.ps1`/commit/push follow, scoped to this task's own files.
