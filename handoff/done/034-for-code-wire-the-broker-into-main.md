---
id: 034
title: Wire IBKRMarketData into main() so attaching QQQ reaches a real feed
type: product
owner: claude-code
depends: 032
---

**Status** REVIEWED

# 034 — done. Attaching QQQ reaches a real broker, and the numbers render

**`live/attach/ibkr.py` is no longer imported by nothing.** `main()` builds an
`IBKRMarketData` from `config/ibkr.yaml`, hands it to the app, and a key press now
reaches TWS. **`christoph/open/013` is performable** — what to compare is at the bottom
of this note.

**Three defects were found by RUNNING it, not by testing it**, and two of them were
rendering wrong numbers with no error and no flag. They are the most important part of
this note and they are in §3.

**This note needs pasting to chat.** It lands in a repo the design session cannot see.

---

## 1. What was built

| Part | What landed |
|---|---|
| 1 | `config/ibkr.yaml` — five settings, all required, none defaulted |
| 2 | `main()` constructs the connection and passes it in; `HEALTH` renders it |
| 3 | TWS absent is a rendered refusal; the app still launches |
| 4 | The context block renders — **it never did before** |
| 5 | Six tests added to `live/tests/test_attach_is_reachable_by_key.py` |

**The attach binding is unchanged**, as required — `_record_attach` still calls
`attach(symbol, self.md, origin="typed")` and reimplements none of it.

### The one thing 034 asked for that turned out to be two tasks

**`032` made the key press reachable; `034` was scoped to make it *do* something. It also
had to make it *show* something.** `attach()` has computed `context` and `rail` since
S010 and `Attached` carried `symbol` and `since` and nothing else, so **every value the
slice exists to produce was discarded one line after it was measured.** The panel could
say a symbol was attached and nothing about it.

That is the fifth instance of *computed and unreachable* in this tree — after the app
with no entry point (`029`), the palette that lived in a docstring, `attach()` with no key
(`032`), and `IBKRMarketData` imported by nothing (this task). **Rendering it was not
optional**: deliverable 1 asks for the context block quoted, and there was no context
block.

---

## 2. The deliverables

### 2.1 The rendered context block for QQQ at 209 × 54

Live TWS, `client 7`, 2026-08-13 13:24 ET. **This is the tile as a person sees it** —
`ATTACHED` is given 68 × 12 inside a 209 × 54 window:

```
+- ATTACHED ------------------------------------------ since 13:24 +
  QQQ  attached 13:24
    from      IBKR 127.0.0.1:7496 · as of 13:24 · lag 35s
    slot      0/5 slots used
    tape      absent - tape not opened by S010 - no tape componen...
    ADR%      1.63  · 20 sessions, excl. today
    ADR $     11.83  · 20 sessions, excl. today
    ADR used  67.00  · 20 sessions, excl. today
    room up   3.90  · 20 sessions, excl. today
    room down 19.76  · 20 sessions, excl. today
    ATR14     13.14  · Wilder RMA, n=14, 59 true ranges
    ext 10    1.42  · 10-day SMA / ADR $
    ext 20    2.59  · 20-day SMA / ADR $
  12 of 26 · +14 more ↓
```

**The other fourteen rows are measured, carried on the day record, and cannot be seen
from the running program.** There is no scroll key. Rendered here by asking the panel for
a height it will never get:

```
    ext 50    1.68  · 50-day SMA / ADR $
    VWAP      730.68  · bar-derived · 16,425,888 sh · 566 min · 2...
    cum vol   16,425,888.00  · 566 min from 2026-08-13 04:00:00
    RVOL      0.92  · 13:25 · 20d median
    RVOL_rel  — (no sector mapping)
    PDH       727.25  · prior session
    PDL       722.92  · prior session
    PMH       725.46  · 330 pre-market bars
    PML       722.80  · 330 pre-market bars
    ORH       726.02  · 5 opening-range bars
    ORL       724.03  · 5 opening-range bars
    52wH      748.65  · 52 weeks
    52wL      555.60  · 52 weeks
    round     47.00  · ±11.83 of 733.14
  26 of 26 · end
```

**`RVOL_rel` refuses by name rather than rendering `1.0`** — QQQ is an ETF and has no
industry, so `_sector_etf` correctly returns `None`. That refusal is the design working.

**This is OBS-042 and it gates the UAT** — see §4.

### 2.2 The TWS-closed refusal

`config/ibkr.yaml` pointed at port 9, `python -m live.tui` launched, **exit code 0, every
panel rendered**:

```
+- HEALTH ------------------------------------- updates · none yet +
  sources   IBKR 127.0.0.1:9
            — (connection refused - nothing is listening)
  last seen — (nothing seen)
  frames/ticks  — (no ticks received)
  4 of 4 · end
  ----------------------------------------------------------------
  regime    [ NOT BUILT ] (no file for today)
```

Connected, for contrast:

```
  sources   IBKR 127.0.0.1:7496
            connected · client 7 · read-only
```

**The endpoint and the state are on separate rows, and that is measured rather than
stylistic.** On one row the cell is `— (IBKR 127.0.0.1:7496 not connected - connection
refused)`, 58 columns against the ~56 a `HEALTH` tile has at 209 × 54 — so `fit`
truncated **the reason** and kept the endpoint, which is the half a reader can already
guess. The first two attempts at this shipped a refusal that said `... not connected -
[WinError 1225] T...`. Two things changed: the OS message became a short canonical one,
and the row was split.

### 2.3 The two reds

Both against `live/tui/app.py` at `HEAD`, with everything else in place, so each red is
the defect itself rather than an import error.

**Red 1 — the context block:**

```
E  AssertionError: the ATTACHED panel does not render 'ADR%'. attach() computed it
   and the record dropped it, which is 034.
E    ATTACHED renders:
E    +- ATTACHED ------------------------------------------ since 13:11 +
E      QQQ  attached 13:11
E      1 of 1 · end
```

**Red 2 — the connection:**

```
E  AssertionError: HEALTH does not name the connection that failed:
E    +- HEALTH ---------------------------------------- updates · none yet +
E      sources   — (no feed connected)
E      last seen — (nothing seen)
E      frames/ticks  — (no ticks received)
E    assert '127.0.0.1:9' in ...
```

**`— (no feed connected)` is the whole finding in one string**: one message for *nothing
tried*, *connected*, and *attempted and refused*.

### 2.4 What enforces read-only — **code, not convention**

**`readonly=True` is passed to `IB.connectAsync` in `live/attach/ibkr.py::connect`.** The
API session negotiates read-only with TWS, which then refuses order submission on this
connection regardless of what any caller asks. That is enforcement in the tree, and it is
`ib_async`'s own documented parameter — verified present in the installed signature
(`ib_async 2.1.0`) rather than assumed.

**A second, structural one:** `_ThreadedIB` exposes exactly `reqContractDetails` and
`reqHistoricalData`. It is deliberately **not** a `__getattr__` proxy — a forwarding proxy
would silently forward `placeOrder`. What is not written there cannot be reached through
there.

**Neither depends on TWS's global read-only checkbox.** I did not inspect that setting and
make no claim about it.

---

## 3. Three defects found by running it — the important section

### 3.1 The thread bridge raised `TypeError` while 99 tests passed

**`ib_async`'s synchronous API cannot be called from inside Textual's event loop.**
Measured, not assumed:

```
RuntimeError: This event loop is already running
```

`IB.connect()` and every `reqX()` wrap `loop.run_until_complete`, which is illegal
re-entrantly, and the TUI's attach runs inside `on_input_submitted` — a coroutine on
Textual's loop. Making `MarketData` async would change the Protocol, `attach()` and all of
`test_attach.py`; `util.patchAsyncio()` monkeypatches asyncio underneath a framework that
owns the loop. **So the client got its own loop on its own daemon thread.**

**And the bridge was broken, and the suite was green at 99 passed.** The first live attach
rendered:

```
  — (QQQ: contract lookup failed (TypeError))
```

A correctly-rendered refusal naming an exception class that says nothing. Two faults, one
symptom:

1. **`reqXAsync` returns a `Future`, not a coroutine.** `run_coroutine_threadsafe` accepts
   only a coroutine and raises `TypeError` on a Future.
2. **The awaitable must be BUILT on the broker loop.** Calling `reqXAsync()` on the
   caller's thread binds the Future to the caller's loop, which nothing is running.

`call()` now takes a **factory**, not an awaitable. **Why no test caught it:** `FakeIB`
answers synchronously, so every fixture test goes straight into `IBKRMarketData` and
**never touches `_ThreadedIB` at all** — the code actually standing between the TUI and
`ib_async`. `test_the_thread_bridge_carries_a_real_async_client` now drives it against a
fake whose `reqXAsync` returns a `Future`, and asserts every request ran on the
`ibkr-broker` thread.

### 3.2 `formatDate=2` is UTC, and four rail values were plausible and wrong

**This is the one worth reading twice.** `Bar.ts` is a string that two consumers slice by
position:

- `attach.py` builds pre-market with `_clock(b.ts) < "09:30"` and the opening range with
  `"09:30" <= _clock(b.ts) < "09:35"`. **Against UTC stamps that is 04:00–05:30 ET and
  05:30–05:35 ET.**
- `intraday_sessions` splits sessions on `b.ts[:10]`, so any bar after 20:00 ET carries the
  next day in UTC and is filed as its own session — silently shifting the 20-session RVOL
  reference.

Measured, before and after, same symbol, minutes apart:

| row | before (UTC) | after (ET) |
|---|---|---|
| `PMH` | `725.46 · **90** pre-market bars` | `725.46 · **330** pre-market bars` |
| `PML` | `723.11 · 90 pre-market bars` | `722.80 · 330 pre-market bars` |
| `ORH` | **`723.82`** · 5 opening-range bars | **`726.02`** · 5 opening-range bars |
| `ORL` | **`723.37`** · 5 opening-range bars | **`724.03`** · 5 opening-range bars |
| `cum vol` sample | `from 2026-08-13 08:00:00+0...` | `from 2026-08-13 04:00:00` |
| block stamp | `as of **17:18** · lag 55s` | `as of **13:20** · lag 39s` |

**90 pre-market bars is ninety minutes; a 04:00 ET anchor gives 330.** The opening range
was taken four hours before the open. **No error, no flag, four well-formed numbers.**

**Fixed at the seam** — `_eastern()` in `IBKRMarketData._bars`. That is the only place it
can go: `core` is timeframe-agnostic and a fix there would be `core` learning a broker's
wire format. **This is beyond 034's literal scope and I did it anyway** — the task's whole
deliverable is a context block for Christoph to compare against his charts, and shipping
values known to be wrong is the defect this project is named for. Two tests pin it, both
seen red against the unfixed `_bars`.

**A fixture could not have caught this.** `FakeIB` emits naive strings that already look
Eastern — exactly how anyone writes a fixture. `UtcFakeIB` now stamps them the way IBKR
does.

### 3.3 `request_timeout_s: 30` refused RVOL on a live attach

```
    RVOL      — (no answer in 30s (request_timeout_s))
```

The 20-day 1-minute request — the RVOL reference, much the largest of the four — exceeded
30 s at 13:24 ET **while `021` held five `keepUpToDate` streams on the same account**. An
earlier attach in the same session answered inside 30 s, so this is at the edge rather
than past it, and **pacing is per account and shared**. Raised to 60; RVOL then rendered
`0.92`. The value is in config with that measurement in its `note`.

**Raising it lengthens the worst-case UI freeze by the same amount** — see OBS-041.

---

## 4. Findings that are not defects

**All four are rows in `docs/observations/OBSERVATIONS.md`**, `OBS-040`–`OBS-043`,
review-by 2026-11-13.

- **OBS-040 — a `socket.socket.connect` guard does not stop an asyncio client, and this
  repo has one that is trusted to.** My first launch guard patched exactly that, copying
  `tests/test_keepuptodate_scale.py`, and **the launched app still connected to live TWS**
  — the screen came back reading `connected · client 7 · read-only`. On Windows
  `asyncio` uses a `ProactorEventLoop` and `create_connection` reaches the socket through
  `ConnectEx`. `034`'s guard now patches both. **`021`'s does not, and I did not change
  it** — it still catches the synchronous-import incident it was written for.
- **OBS-041 — the attach blocks the UI thread**, measured at **13.7 s** for a live QQQ
  attach. Unfreezing it means moving the attach to a Textual worker, which changes the
  binding 034 required unchanged and breaks how the pilot tests synchronise.
- **OBS-042 — the context block is 26 rows, the tile gets 10–12, and nothing can scroll.**
  §4e says `+14 more ↓` honestly, but the rows are unreachable rather than off-screen.
  **This gates `013`** — see §6.
- **OBS-043 — `Measured` has no as-of or lag field**, so §3's *source, as-of, lag on every
  value* is rendered **block-level**. Each row still carries its own `sample`. Deliberately
  not stamped at render time: that would say when the screen was painted.

### What the context block needed that is not built

**Nothing was missing to compute it** — `attach()` and `_context_block()` produce all 26
rows and the scope held; no indicator was added. What is missing is **somewhere to put
it** (OBS-042) and **a per-value time to stamp it with** (OBS-043).

---

## 5. Tests, and the numbers

**Six added**, all in `live/tests/test_attach_is_reachable_by_key.py`. **No third
reachability suite** and **`test_attach.py` untouched**, as required.

| Test | What it pins |
|---|---|
| `..._renders_the_context_block_not_only_the_symbol` | values, samples and the stamp render. **Seen red** |
| `..._refused_connection_renders_its_host_and_port_and_the_app_lives` | `connect()` returns rather than raises; HEALTH names host and port; the app still attaches afterwards. **Seen red** |
| `..._thread_bridge_carries_a_real_async_client` | §3.1 — a `Future`-returning client, on the broker thread |
| `..._as_of_renders_in_eastern_not_in_the_wire_format` | §3.2, block stamp |
| `..._opening_range_is_eastern_and_not_the_wire_format` | §3.2, the rail. Seen red against unfixed `_bars` |
| `..._nothing_in_this_suite_opens_a_broker_socket` | the guard, **with a positive control asserted first** |

**No network in the suite**, at two levels: the in-process test patches
`socket.socket.connect` for the four broker ports and proves the guard fires before
trusting it; the subprocess launches get a `sitecustomize` patching **both**
`socket.socket.connect` and `asyncio.base_events.BaseEventLoop.create_connection`. That
also makes the TWS-closed demonstration deterministic — without it the same command
renders a connection on Christoph's desk and a refusal in a clean checkout.

### The suite, verbatim

```
8 failed, 335 passed, 1 warning in 28.49s
```

**The baseline before this task was `8 failed, 329 passed`** — the **same eight**, plus my
six. **Nothing regressed.** The eight are pre-existing and none is mine:

```
FAILED tests/test_handoff_state_declared.py::test_every_task_file_declares_a_state
FAILED tests/test_observations_ledger.py::test_every_retired_uat_has_a_register_row
FAILED tests/test_observations_ledger.py::test_refusal_b_a_retired_uat_with_no_destination_is_red
FAILED tests/test_pytest_collection.py::test_every_directory_holding_tests_is_declared
FAILED tests/test_regime_prompt_invariants.py::test_no_bare_six_of_nine
FAILED tests/test_regime_prompt_invariants.py::test_no_bare_six_of_nine_anywhere_in_specs
FAILED tests/test_regime_snapshot_could_not_do.py::test_the_format_still_lacks_a_key
FAILED tests/test_uat_has_a_file.py::test_every_declared_uat_exists_as_a_file
```

They name tasks `021`–`027` and UATs `013`/`014`/`017`/`020`, and I checked they predate
the `033`/`034` inbox arrivals. **`test_pytest_collection` fails because of leftover
worktrees from `024` and `029` under `.claude/worktrees/`, which contain test directories.
Mine is removed; those two are not mine to delete.** `033` appears to be the task that
owns this set.

### `021` was not disturbed

**`client_id: 7`. Never 121.** No process belonging to `021` was stopped, restarted or
reconnected. Request cost: **four live attaches** during development, four historical
requests each (60 D daily, 20 D 1-min, 1 D 1-min, 1 Y daily), plus five short connects
that made no request. Attaching one symbol, as the task permits — no polling loop.

---

## 6. `013` is now performable — what to compare

**Launch:**

```powershell
cd D:\Dev\momentum
C:\venvs\trading\Scripts\python.exe -m live.tui
```

Press `a`, type `QQQ`, press enter. **TWS must be running on 7496** — if it is not, the
app still launches and `HEALTH` says so.

**Compare against your charts**, in the order they render:

- **`ADR%` and `ADR $`** — Kullamägi's TC2000 convention, 20 sessions, **excluding today**.
  Not ATR; the two must never agree by construction.
- **`ATR14`** — **Wilder's RMA**, not a simple 14-day mean. The most common way this is
  implemented wrong, and it agrees with the right answer often enough to survive a spot
  check.
- **`ext 10/20/50`** — distance from each SMA **in ADR-dollars**, not percent.
- **`VWAP`** — session VWAP **including pre-market**, anchored 04:00 ET. On a gapper this
  is deliberately not your RTH-anchored VWAP and they will differ early.
- **`RVOL`** — today against a 20-session median at the same minute, both pre-market
  inclusive.

**Two caveats you need before you look:**

1. **`PDH/PDL`, `PMH/PML`, `ORH/ORL`, `52wH/52wL` and `round` are below the fold and you
   cannot scroll to them** (OBS-042). If those are what you wanted to check, say so — it
   changes what gets built next.
2. **These four rail values changed today** (§3.2). If you compared an earlier build
   against your charts and they disagreed, **that was this bug**, not your charts.

**A ~13 s freeze on attach is expected** (OBS-041). The terminal is not hung.

---

## 7. What I could not do

- **Move the attach off the UI thread.** 034 requires the binding unchanged and the
  existing pilot tests synchronise on `pilot.pause()`, which does not wait for a worker.
  OBS-041.
- **Make the whole context block visible.** The tiling is fixed by S009 and 034 does not
  scope changing it. OBS-042.
- **Stamp each value with its own as-of and lag.** `Measured` has no field for it.
  OBS-043.
- **Fix `021`'s socket guard.** OBS-040. Changing another task's test from inside this one
  is how a task acquires work nobody scoped.
- **Confirm TWS's global read-only setting.** I did not inspect it and make no claim; the
  read-only enforcement I *do* claim is `readonly=True` in this tree's code.
- **Clear the eight pre-existing failures.** Not this task, and `033` looks like the one
  that owns them.
- **Verify against a second broker or the paper account.** Only `7496` was exercised.

---

## 8. Housekeeping

- Worked in a git worktree, `.claude/worktrees/034-broker-into-main`, merged no-fast-forward
  and **removed on completion.**
- `config/ibkr.yaml` added to `BOOTSTRAP_ALLOWLIST` — **one entry**, and OBS-008 still
  stands.
- `033` and `034` arrived through `tools/sync_from_drive.py`, not by hand:
  `2 new · 033, 034 · 0 differing`, source folder byte-for-byte unchanged.
- **`verify.ps1` run at 2026-08-13 19:28:17 +02:00** (13:28 ET), HEAD
  `2070193`, tree clean, 179 evidence rows re-hashed with 0 mismatches.
- `export-handoff.ps1` run after the commit; the HEAD it recorded is in §9.

## 9. Export

Run after the final commit. **Syncing this note does not close it** — `REVIEWED` needs
your reading, and `DONE` needs both parties.

**Paste this note to chat.** On 2026-08-11 four correct done-notes were written and none
reached the design session, and nothing in the repo can detect that.
