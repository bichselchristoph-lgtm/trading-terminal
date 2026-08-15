# Trading Terminal — Consolidated Spec

> **STATUS** CURRENT · **date** 2026-08-10

**Version** 1.1 · **Date** 2026-08-09 · **Status** DRAFT FOR APPROVAL
**v1.1 change:** Layer 0 leaves the terminal (it is produced by the scheduled cloud task); **no verdict colour renders anywhere** until there is data behind it. §4.1, §12.
**Supersedes** nothing. Sits *above* the Drive corpus as the single entry point; the Drive specs remain the detailed record.

> Context for own decision — not financial advice.

---

## 0. What this document is

A consolidation of ~123 Google Drive specs, the `D:\Dev` codebase, five HTML mockups, `D:\chbichOneDrive\...\_Trading` (425 files), and fresh external research, into one buildable specification.

**Three things changed as a result of the research.** They are the reason this is a new document rather than an index.

1. **A fourth layer is added — Layer I, institutional context.** Twelve rows, mostly free data, replacing narrative with observables. §5.4.
2. **The stock grader becomes a first-class component with its own registry.** It was scattered across six incompatible A+/A/B/C ladders in six files. §6.
3. **Databento per-byte, traded tickers only** — the replay harness pulls the symbol-days you actually traded, after the close. §7.2 *(revised from v1.0's $199/mo Standard subscription)*.

**One thing did not change and must not:** the two human gates, and the rule that a panel rendering a value with nothing behind it is worse than a panel rendering nothing.

**A fourth change, made after the first review pass, applies that rule harder than v1.0 did (§4.1, §12):**

4. **Layer 0 is out of the terminal, and no verdict colour renders anywhere.** Layer 0 already exists as a scheduled cloud task producing prose; duplicating it in the terminal builds a fourteen-row scoring machine to answer a question that is already answered. And every remaining green/amber/red — the Layer I five-state dial, the exposure grid, the `HALF SIZE` badge, the grader's letter, the detector polarity colouring — is a **judgement** whose cuts were never fitted on this trader's data. v1.0 kept them because they were in the mockups. They come out. The terminal renders **measurements, rules, and data states**; the trader supplies the verdict until a fitted one can be earned. Everything removed is preserved in §12, not deleted.

---

## 1. Product definition

**What it is.** A running operational surface for one trader making manual decisions on a trading morning. A Python TUI redrawing in place in Windows Terminal.

**What it does.** Twelve stages between two human gates: ingest → regime → indicators → rank → **[HUMAN: what to trade]** → size → stage → **[HUMAN: whether to send]** → manage → reconcile → journal → archive.

**What it does not do.** It does not decide, it does not scan the market, it does not transmit an order, and it does not gatekeep the watchlist — it scores and sorts; nothing is removed.

**The eleven tenets** (project instructions) are the constitution. Two are load-bearing enough to restate as build rules:

- **Tenet 2 — absence is not zero.** Confirmed experimentally: Song & Szafir (IEEE VIS 2018) found zero-filling produced *worse* analyst calibration than interpolation, and silent removal degraded confidence even when analysts did not consciously notice it. Explicit missing-data marking scored highest. ([paper](https://cmci.colorado.edu/visualab/papers/song_VIS_2018.pdf))
- **Tenet 3 — status inherits from the weakest.** Enforced in the render layer, not by discipline.

---

## 2. Architecture

### 2.1 Repositories — unchanged, two

| Repo | Role |
|---|---|
| `momentum-harness/` (GitHub: `momentum`) | Umbrella. `core/` (shared, imports nothing first-party) · `harness/` (research) · `live/` (operational) · **new: `live/tui/`** |
| `tws_order/` | The only code that can place an order. Stays separate. Gated by `tws_order_separation` in `preregistration.yaml`. |

`tests/test_import_boundaries.py` already forbids edges between `harness` and `live`. The TUI lives under `live/` and inherits that boundary.

### 2.2 The central simplification — one day record

Everything the terminal shows is a field in one append-only record per session. Producers write it; the renderer reads it and computes nothing.

```
records/day/YYYY-MM-DD.json
{
  schema_version, session_date, generated_at,
  regime_snapshot: {ref, frozen_at, schema_version},     # a POINTER to the Claude
                                                         #   task's YAML. No rows.
  fills:       [{exec_id, perm_id, order_ref, symbol, side, qty, price, commission_state, on_watchlist, watchlist_content_key}],
  layer_2:     {playbook, n, follow_through_rate, status},
  watchlist:   {provenance: {...}, rows: [{symbol, metrics, dimensions, rank, absent: [...]}]},
  tickets:     [{..., risk_pct_used, risk_pct_default, rules_failed: [...], acknowledged: [...]}],
  book:        {findings: [...]},
  health:      {sources: [{name, last_seen, state}], gaps: [{interval, cause}]}
}
```

**Four fields are deliberately absent.** There is no `layer_0`, no `layer_i` and no `layer_1` — **every regime layer is produced by the Claude task, and the record carries only `regime_snapshot.ref`** (§3.2). And there is no `exposure` — the dial is deleted, and 1R comes from the account alone (§7b.1). **A field that does not exist cannot be rendered by accident**, which is the §4.1 rule enforced one layer below the screen.

**Why this is the whole architecture.** Every panel is a projection of one field. Every refusal is a value in that field, not an exception. Backtesting is replaying the record. Counterfactual re-scoring is recomputing producers over stored inputs. The TUI becomes a pure function `record → screen`, which makes it snapshot-testable.

**Rule:** `renderer(record)` must be a pure function. If the record has no `scored_value`, the screen has no score.

### 2.3 Render layer — Textual

**Decision: Textual** (8.2.x, MIT, Python 3.9–3.14), run from PowerShell in Windows Terminal.

Rationale, in order of weight:

1. **`pytest-textual-snapshot` turns "refusal is a designed display state" into a test that fails.** This is the single most important property available. A test that boots the app with an empty Layer 0 and snapshots the screen will go red the moment someone makes a missing row render `0.00`. The project's recurring failure — "a correct warning sat in a file nobody was instructed to open" — is exactly what a snapshot test fixes. ([testing guide](https://textual.textualize.io/guide/testing/))
2. Native Windows Terminal support with no WSL requirement.
3. Compositor does genuine partial updates (segment cuts, occlusion discard), so a 3-cell change in a 40-row grid does not repaint the terminal.
4. Async-native: shares one asyncio loop with `ib_async`.

Accepted risks: single-maintainer project (Textualize wound down May 2025; McGugan maintains it personally) — **pin the exact version**. `DataTable` is O(m²) in *columns* — keep the watchlist grid under ~18 columns or swap in `textual-fastdatatable`.

Rejected: **urwid** (weak Windows, no snapshot testing), **prompt_toolkit** (no grid layout, no snapshot testing — reconsider only if order entry becomes a command line), **Rich alone** (no focus model or key dispatch), **blessed/py-cui** (you write the compositor, which puts the render stack back in the failure surface), **PowerShell-native** (adds an IPC seam and a serialization surface between the Python that computes and the shell that draws — the opposite of removing failure surface). **Sixel/kitty graphics are unavailable in Windows Terminal**; all charts are block/braille.

**"PowerShell terminal" in the project instructions is read as *where it runs*, not *what it is written in*.** That reading is confirmed and the decision is closed (§11) — Python/Textual, run from PowerShell in Windows Terminal. It is recorded here as an assumption, not as a question.

### 2.4 Feed and render — three layers, no layer skips the middle

```
ib_async (async worker, Textual's loop)  →  state store  →  set_interval(0.1) repaint
```

- **Feed handlers only write.** Never touch a widget.
- **State store:** last-writer-wins per symbol; each record carries `value, ts_exchange, ts_received, seq, presence, confidence`. Conflating a quote is a feature; **conflating a fill is a bug** — fills, order state changes, rejections and limit breaches travel on a separate bounded `asyncio.Queue` drained fully every frame.
- **Repaint at 10 Hz**, diffing `seq` and updating only dirty cells. The published reference point for trading GUIs is a 50 ms conflated flush at 3,000–4,000 updates/sec; 100 ms is comfortably inside that.
- **CPU-bound indicator work** goes to `@work(thread=True)` and returns via `post_message()`.
- **Instrument ticks-received vs frames-painted and render the ratio.** A render loop falling behind is itself a trust state.
- Never `ib.run()`, never `util.startLoop()`, never a second loop.

This satisfies "render never blocks on write" structurally: the render reads the store, persistence drains a separate queue, and only under genuine backpressure does *saving* shed load — recorded as `backpressure_shed`, never silently.

---

## 3. The surfaces

Six, not five. The mockups describe 1–5; the project description names "monitor results" and Tenet 5 requires it, so **06 Review** exists.

**The table below is retained as the panel inventory; the numbers are historical, not navigation targets** (§3.0a).

| # | Panel group | Role | Mockup |
|---|---|---|---|
| 01 | **Ingest** | Watchlist drop → verify → commit | `mockup-01-ingest.html` |
| ~~02~~ | ~~**Regime**~~ | **Deleted — §3.2.** Every regime layer is produced by the Claude task | ~~`mockup-02-regime.html`~~ retired |
| 03 | **Desk** | Ranked watchlist + live session context + **attached symbol (§6b)** | `mockup-03` + `mockup-05` |
| 04 | **Size & stage** | Two inputs → size → staged order → reconcile | `mockup-04-size-stage.html` |
| 05 | *(not a screen)* | Live session context is a **band inside 03** | `mockup-05-live-context.html` |
| 06 | **Review** | Outcome vs result, adherence, Layer 2 feed | *new* |

### 3.0a Panels, not screens — the surface model dissolves

**On a wide monitor, nothing should need switching.** A keystroke to reach a panel is a keystroke spent, and worse, it means the thing you are not looking at is invisible rather than merely peripheral. **The unit is the panel; a "surface" is only a saved arrangement of panels.**

This is already the mechanism — §4.3's `config/layout.yaml` declares per component whether it renders and where. Extending `slot` from an ordinal to a **region on a grid** makes screens unnecessary rather than merely optional, and the layout file stays the single place layout is decided.

**But the four are not the same kind of thing, and tiling all of them equally would be wrong.**

| Panel group | Kind | Earns permanent space? |
|---|---|---|
| **Ranked watchlist · attached symbol · tape** | **Persistent** — you watch them | Yes |
| **Sizing · risk rows · health bar** | **Persistent** — a limit first seen at breach has already failed (§7b.1) | Yes |
| **Ingest** | **Episodic** — used once, pre-market, for about thirty seconds | No. Opens over |
| **Review** | **Episodic** — post-close | No. Opens over |

**Ingest and Review are tasks, not instruments.** Giving them permanent real estate spends the best part of a large screen on panels that are dead for 99 % of the session. They open over the layout and close again.

**So the default wide arrangement is: watchlist, attached symbol and tape across the top; sizing, risk and health along the bottom; nothing hidden, nothing switched.** `Ctrl+P` still reaches everything for the long tail.

#### The terminal does not build window management

**Decided: no screen-management keys, no drag-and-drop, no custom layout mode.** `Ctrl+Tab` rotates focus between panels and that is the entire navigation surface. **Everything else is the operating system's job**, and building a second window manager inside a console application would be the worst kind of scope: expensive, permanently half as good as the real one, and unnecessary.

**But there is a real constraint behind this, and it is worth being precise about.** A Textual application is **one process painting one console window.** Windows can move and size that window; it cannot drag a panel out of it, because from the OS's point of view there is nothing there to drag — just characters. **OS-level window arrangement needs more than one window, and more than one window needs more than one process.**

That collides with §6b.1c: **one process, because the market-data slot model is a ledger and a ledger with two writers is not a ledger.**

**The collision is resolvable, and the architecture already resolves it — just not yet.** §2.2 makes `renderer(record)` a pure function of the day record. So the split is not one process into two peers, but **one owner and N read-only viewers**:

| | Holds the IBKR connection | Writes the day record | Renders |
|---|---|---|---|
| **The terminal** (one, always) | yes | yes | yes |
| **A viewer** (zero or more, later) | **no** | **no** | yes |

A viewer subscribes to the day record and paints panels from it. **It cannot consume a slot, cannot place an order, and cannot disagree about state, because it computes nothing.** One ledger, one writer, as many windows as Windows can arrange — and each viewer is its own console window, so **Windows Terminal's own pane splitting and your window manager do exactly what you want with no terminal-side code at all.**

**Not built now, and deliberately not.** In core there is one process, so there is one window, so `Ctrl+Tab` and the tiled layout are the whole story. **What matters today is only that nothing forecloses the viewer** — and nothing does, provided the renderer stays a pure function of the record and no panel reaches around it to compute something itself. **That property is already tested** (§2.2's rule, enforced by the snapshot suite), so the cost of keeping this door open is zero.

**If a viewer is ever wanted, it is a small slice, not a redesign.** That is the return on `renderer(record)` being pure, and it is worth stating plainly so the constraint is not quietly traded away for a convenient shortcut in some panel.

**Three snapshot widths, not two** — 80×24, 120×40 and **240×70** — because a layout that is correct at 120 columns and broken at 240 fails silently on the machine you actually use.

#### Panels scroll, and scrolling is a new way to hide a warning

**Every panel scrolls independently when its content exceeds its region.** A thirty-name watchlist in a twelve-row box scrolls; it does not truncate and it does not shrink the font of a console that has no fonts.

**But scrolling is the sixth version of this project's recurring failure.** The pattern is already named — *five times a correct warning sat in a file nobody was instructed to open* — and a row scrolled below the fold is exactly that, one layer closer. **Content out of view is content nobody read**, and a limit breach at row 19 of a 12-row viewport is indistinguishable from no limit breach at all. Three rules follow, and none is optional:

1. **Never-scroll rows are pinned to their panel.** The risk and limit rows (*a limit first seen at breach has already failed*, §7b.1), the health bar, any failed rule, and any active refusal are **sticky** — they hold position while the rest of the panel moves under them. A panel's scrollable region is what is left after its pinned rows.
2. **A panel with content below the fold says so.** `3–14 of 31` in the border caption, and `+7 more ↓` at the edge. **"Nothing more here" and "more below" must not render identically** — that is *absence is not zero*, applied to a viewport instead of a value.
3. **`window too small` narrows to mean one thing**: even the pinned rows do not fit. That is a genuinely different state from *scrollable*, and conflating them would let a usable screen refuse and an unusable one scroll.

**Tested, not intended.** Scroll position is part of the snapshot, so a layout change that pushes something below the fold shows up as a diff. And one test asserts the property directly: **drive a failed rule into a panel scrolled to the bottom and confirm it is still visible** — because the pinned band caught it. Without that test the pinning rule is prose, and prose is what this project has repeatedly learned does not hold.

**One caution, and §4.3 is the instrument for it.** A large screen makes it *easy* to show everything, which makes it easy to show things that never change a decision — the constraint stops being pixels and becomes attention, which was always the scarcer input. **`config/layout.yaml`'s history is what catches this**: a panel you never demote and never look at is indistinguishable from a useful one until the log says otherwise. Tiling raises the value of that log rather than removing the need for it.

**Mockup mapping** (files keep their historical numbers):

| Panel group | Mockups |
|---|---|
| Ingest | `mockup-01` |
| Watchlist · attached symbol · tape | `mockup-03`, `mockup-05`, `mockup-06` |
| Size · stage · risk | `mockup-04`, `mockup-07` |
| Review | `mockup-08` | Hotkeys for the ten things done hourly, palette for the hundred done weekly.

### 3.2 The regime surface is deleted

**Decided: no regime surface in the terminal.** Not a thin one, not a band. The whole read — Layer 0, the overnight macro strip, Layer I, **and the Layer 1 index read** — is produced by the Claude scheduled task and consumed there, as prose plus a locked snapshot (§5.5a). **It is not worth a screen.**

Layer 1 was the last holdout, and its case was the cross-check in §5.2 — *two computations of the same quantity from different code paths, compared, is a free correctness test.* **With only one computation there is nothing to cross-check**, so that argument retires with the surface rather than surviving it. Recorded here so it is not re-adopted later as though it still applied.

**Layer 2 survives, on Review.** It is your own follow-through rate, computed from the trade log, and it belongs beside the outcomes it is derived from rather than on a regime screen it never needed.

**Not rendered is not the same as not recorded**, and that distinction is why this stays cheap. The day record keeps a pointer:

```
regime_snapshot: {ref, frozen_at, schema_version}   # a reference, not the rows
```

That one line is what makes *"did regime separate outcomes"* answerable later. **The rows live in the snapshot, the session links to them, nothing renders.** Deleting the surface costs a screen and loses no evidence — which is only true because the snapshot is YAML rather than prose (§5.5a).

**What it buys:** core drops from eight slices to seven, one navigation target disappears, and the terminal stops carrying any panel whose content is produced elsewhere and better.

### 3.1 Mockup defects to fix, not inherit

The mockup audit found nine. Six matter. **The first three are resolved by deletion rather than repair** (§4.1) — the disputed thing is no longer rendered:

1. ~~Sheet 02 renders Layer 0 as a live AMBER composite with `vetoes 0/4`; sheet 05 declares `NOT BUILT — 0 of 14 rows`.~~ **Resolved by removal.** The composite, the exposure grid and the `HALF SIZE` badge on sheet 04 all go. This was the defect that motivated §4.1: three separate panels were rendering a value with nothing behind it, and each repair attempt produced a more carefully-qualified version of the same unfounded number.
2. ~~Layer 0 counts disagree: 02 scores `6/9` out of 11; 05 says 14 rows.~~ **Moot in the terminal.** The denominator is the cloud task's problem now (§12.1), and it does not scale position size any more because the dial is gone.
3. ~~Gap breadth is simultaneously "unavailable" (02) and `18 names / 4 sectors` (05).~~ **Moot** — neither renders.
4. **Sheets 01–04 use the path `tradesignals\`, which is an archived read-only repo.** Sheet 01's subtitle names `D:\tradesignals\watchlists` as the ingest drop folder. Update to `momentum\`.
5. **Box widths are 69–71 chars against a 71-char bottom border.** Invisible in HTML, visibly broken in a fixed-width console. Normalise, and account for ambiguous-width `·` and `—`.
6. **States specified in prose with no rendered form:** slot exhaustion, the 15-second attach cooldown, same-name-different-content and schema-drift ingest refusals, the never-naked stop-cancel breach. **Design each or the sheet is incomplete against its own spec.**

Also: sheet 01's refusal list shows two hard errors; the spec names four. Note that `MissingProvenanceCompanion` is **decided obsolete** (open question `scanner-provenance-requirement-dropped.md`) but still fires in `core/watchlist.py` — land inbox task 007 first.

---

## 4. Refusal grammar

Three orthogonal axes, each with its own channel, **never collapsed into one grey**:

| Axis | States | Channel |
|---|---|---|
| **Freshness** | live · aged · stale · frozen-at-HH:MM | age suffix + dim ramp |
| **Presence** | present · absent · not-yet-computed | value vs `—`, never `0.00` |
| **Confidence** | full · degraded · refused · unfitted | glyph prefix + border style |

A cell that is fresh, present and full-confidence renders as a plain number. **Any deviation renders differently *and* renders the reason.**

**Vocabulary** (from the mockups, now canonical): `unfitted` · `n/a — <reason>` · `untested` · `partial` · `unavailable (<reason>)` · `absent, not zero` · `superseded` · `flagged, not an error` · `reduced denominator` · `NOT BUILT` · `STALE` · `FROZEN` · `warming` · `no-source`.

**Badges:** amber-inverse = read this and decide (`[ AGE ]`, `[ PRESS SUBMIT IN TWS ]`). Dim-inverse = the system is refusing, not failing (`[ STALE ]`, `[ FROZEN ]`, `[ NOT BUILT ]`, `[ NO SOURCE ]`) — moved off red per §4.1, because a value that never arrived cannot have failed. **Red-inverse is reserved for one badge**: `[ STOPPED — DAILY LIMIT ]`. `[ HALF SIZE ]` is **removed** — it was a verdict, not a state.

**Panel captions are provenance.** The right-hand end of every panel border carries source, as-of time, sample window, or safety state: `computed 08:00 ET` · `IBKR · 07 Aug` · `intraday_orb · last 20` · `not transmitted` · `updates · last 09:47:12`. A live panel without an update stamp is the `[ STALE ]` anti-state.

**Status encoding is by position and typography, never colour alone** (also survives 16- and 256-colour degradation over SSH). The four-colour grammar in §4.1 reduces the load on this rule but does not remove it — the everyday pair is blue/amber, which deuteranopes read without difficulty, and green/red is reserved for the fitted case:

| Kind | Weight |
|---|---|
| Book findings | Highest — own zone, screen edge |
| Rules | Strong — plain text, pass/fail glyph, reason inline |
| Indicators | Normal |
| Context | Dimmed |
| **Predictions** | **Dimmed + shaded + "unfitted" in the zone header** |

*A prediction must not be able to render at the same visual weight as a rule. Enforced by layout, tested by snapshot.*

### 4.0a Number formatting is one function, in config

**The same quantity renders identically on every panel, because there is one formatter and its precision comes from config** (§4.4). Two panels printing `1.4 ADR` and `1.44 ADR` for one number is a small thing that reads as two numbers.

| Kind | Precision | Example |
|---|---|---|
| **Ratios and multiples** — ADR distance, ATR distance, RVOL, extension | **1 decimal** | `1.4 ADR` · `3.1×` · `+2.6 ATR` |
| **Percentages** | **1 decimal** | `ADR 2.8 %` · `risk 0.40 %` |
| **Prices** | **2 decimals** (4 below $1.00) | `48.07` · `0.9412` |
| **Money** | **whole dollars, thousands-separated**; cents only where cents are the point | `−$1,254` · `1R $497` · `offset 5c` |
| **Share counts** | **whole, thousands-separated**; abbreviated above 1M | `265 sh` · `18.4M sh` |
| **Times** | **seconds where seconds matter, otherwise minutes** | `09:36:00` · `42 min` · `retry in 42s` |

**Rounding is display-only and never re-enters a calculation.** A stop priced at `48.0713` renders `48.07` and **stages at `48.0713`** — the rendered value is a projection, exactly as §2.2 requires of everything else on screen.

**One exception, and it is the one that matters: a threshold and the value compared against it render at the same precision.** `stop 1.4 ADR · ceiling 1.0` is readable; `stop 1.44 · ceiling 1.0` invites the question of whether the comparison used the rounded number. **It did not — but the panel should not raise the question.**

**Every rule renders its reason and its measured value.** `✗ extended vs 10-EMA (2.6 ATR)`, never a bare `✗`.

### 4.1 No verdict colour — the standing rule

**Colour carries data state only. It never carries a judgement about the market, a stock, or a trade.**

| Colour may say | Colour may not say |
|---|---|
| this value is stale / frozen at 08:00 | this setup is good |
| this value is absent, and here is why | the market is risk-on |
| this rule failed, and here is the measurement that failed it | this regime deserves half size |
| the system has refused, and cannot proceed | this detector is bullish |

The distinction is **falsifiable now vs. fitted later**. `stop 1.4 ADR · ceiling 1.0` is a rule against a declared threshold with the measurement shown — checkable today. `RISK-OFF`, `A+`, `HALF SIZE`, a `TRUE` on `PullbackDefending` — each is a claim that a cut point predicts something, and **no cut point in this system has been fitted on this trader's data**. Three of the six grader ladders were fitted on synthetic tape; the rest are practitioner lore (§6.5).

#### The four-colour grammar

An earlier draft used green for *inside a declared threshold* and red for both *rule failed* and *system refusing*. **That merged two different questions under one colour and overloaded a third.** Compliance with a preference you invented is not the same event as a claim about the market coming true, and neither is the same as a value being missing. The grammar separates them, and it maps onto the component kinds (§4.2) rather than onto how alarming something feels:

| Colour | Kind it belongs to | Means | Example |
|---|---|---|---|
| **blue** | **Rule / parameter** | A declared parameter, and a value sitting **inside** its declared band. *This is a fact about your own config, not about the market* | `risk 0.50 % · cap 2.00` · `stop 0.7 ADR · ceiling 1.0` · `PROVISIONAL` threshold markers |
| **amber** | **Rule** | **Outside** a declared band — a rule failed, `enforcement: warn` | `stop 1.4 ADR · ceiling 1.0 (orb_v3, unfitted, intraday_orh)` |
| **green** | **Signal / prediction** | A **fitted** signal measured against its pre-registered expected outcome, **and the measurement held** | *(nothing today)* |
| **red** | **Signal / prediction** | The same measurement, **and it failed** | *(nothing today)* |
| **dim + inverse badge** | any | The system refusing: absent, not built, warming, stale, frozen, no-source | `[ NOT BUILT ]` · `[ STALE ]` · `absent, not zero` |
| **red-inverse badge** | the one blocking rule | `[ STOPPED — DAILY LIMIT ]`. The single case where the terminal stops (§4.2) | `daily loss −2.1R · limit −2.0R` |

**Green and red render nowhere today, and that is the point.** Nothing in this system is fitted. If the palette is bound to the taxonomy rather than to mood, then the *absence* of green on the screen is an honest report of the project's state, and the first green ever displayed will mean something specific: a claim was pre-registered, measured against outcome, and held. **A snapshot test asserts that no green and no red appear while the pre-registration file holds zero fitted entries** — which makes §4.1 enforceable by palette, not by discipline.

**Three consequences worth stating plainly.**

1. **Refusal moves off red entirely.** Absence is not failure — a value that never arrived has not been measured, so it cannot have failed. It renders dim with its inverse badge, which is what §4 already specified before colour was layered on top. This also frees red to mean one thing.
2. **Blue and amber carry the everyday load, and that pair is colourblind-safe.** §4 already required that status never depend on colour alone, because ~1 in 12 men cannot reliably separate red from green. Under this grammar the red/green pair is *reserved for the rare validated case* and the daily path is blue/amber — which deuteranopes read without difficulty. The accessibility requirement stays, but the common case stops relying on the hard discrimination.
3. **Blue must not collide with `--dim`.** The existing `--dim:#6E8CA5` is already a desaturated blue and means *context, lower weight*. The parameter blue needs to be clearly brighter and more saturated — and both must survive 16-colour degradation over SSH, where blue is in the base palette and the distinction has to fall back to typography.

**What this does not change.** Colour is still never the only channel. The weight hierarchy below still governs, `enforcement` is still a required field, and no colour anywhere attaches to a **verdict with no visible comparison** — a green `A+` remains impossible, now for two reasons: the letter is not rendered at all (§6.3), and green is not available to anything unfitted.

**What replaces a verdict is the measurement plus the word for "not established".** Not a neutral middle, not a dimmed verdict — those still put a judgement on screen and merely apologise for it. Layer I logs `RISK-OFF` to the record without rendering it (§5.4); the grader emits its dimension vector without a letter (§6.3); detectors render `M3 signed vol −412k (band ±180k)` without a polarity colour (§6b.2).

**Why the rule and not case-by-case discipline.** Every one of these was defended individually when it was written, and collectively they filled the screen with unfounded colour. The rule is enforceable by test — `_state_cell` and its polarity argument are deleted rather than conditioned — and case-by-case discipline is not.

**The path back.** Each removed verdict has a named readmission criterion in §12. None returns because it feels right; each returns when the trade log supports fitting its cuts and the fit survives a holdout.

### 4.2 Surfaced, not refused — the second standing rule

**The terminal shows. It does not block a trade and it does not change a size.** Every threshold in this document — stop width, range budget, open risk, concentration, PDT count, SSR, borrow, squeeze fuel, micro-range, the do-not-trade list — is **a rule that renders as a warning, never a block.**

#### The vocabulary is the project's own, and an earlier draft invented a synonym for it

A previous version of this section called these things *advisories*. **The word appears nowhere in the codebase, nowhere in the Drive corpus, and nowhere in the tenets.** It was a new noun for a kind that the taxonomy already defines, which is precisely the failure mode Amendment 7 was written to stop: *"'Signal' is now reserved SOLELY for the composition kind. One word, one meaning, everywhere."* The term is withdrawn.

The seven component kinds (*Trading Context Dashboard — Component Spec* §1) are unchanged and binding:

| Kind | Contract | Carries |
|---|---|---|
| **Indicator** | stream → series. Deterministic measurement | source, method, warm-up state, causality at *t* |
| **Rule** | **state → bool + reason. An imposed constraint** | **nothing to fit — it is a preference** |
| **Prediction** | state → score. A claim about the world | fitted/unfitted, threshold_version, fit sample |
| **Signal** | composition → categorical + reasons | inherits the weakest input's status |
| **Context** | external fact, unvalidatable | source, timestamp, never scored |
| **Trade management** | side effects — orders | separate process |
| **Book validator** | book state → findings + severity | read-only, never acts |

**Every threshold in §7b is a `Rule`.** *"state → bool + reason"*, *"an imposed constraint"*, *"nothing to fit — it is a preference"* — that is an exact description of `stop ≤ 1.0 ADR`. The pre-registration file already classifies the nearest neighbours this way: *"the four vetoes and the exposure grid are RULES — imposed constraints that need no validation because they are preferences about sizing, not claims about the world."*

**What was actually missing is not a noun but a field.** The taxonomy has no way to say whether a rule blocks. That distinction lived only in prose — *"Extension is a warning, never a block"*, *"Warning only, never a block"* — and prose is what this project has repeatedly learned does not hold. So, following Amendment 9's precedent exactly (*"Output form is a declared field on the signal, NOT a new component kind"*):

```yaml
rule:
  id:          stop_width_ceiling
  measures:    abs(entry - stop) / ADR
  threshold:   1.0                      # EP: 1.5
  enforcement: warn                     # warn | block  — REQUIRED, no default
  source:      orb_v3_tradebook          # never a bare number
  timeframe:   intraday_orh              # which entry timeframe it was validated on
```

`enforcement` is **required with no default**, for the same reason `lookback` is required with no default in `SignalSpec`: a default of `warn` would let a rule that should block register as a warning by omission, and a default of `block` would silently recreate the thing this section removes. **The kind count stays at seven.**

#### The verbs, corrected

The earlier draft said these *fire*. In this project's own usage they do not:

| Thing | Verb | Quoted from the corpus |
|---|---|---|
| **Trigger** | **fires** | *"Setup confirmed \| trigger fires (e.g. flag break)"* · *"break fires > ~30–45 min after the open"* |
| **Rule** | **fails** — and its two failure causes must be distinguishable | *"A rule failing because its input has not loaded is indistinguishable from a rule failing on the merits, and that is the worst available error."* A rule whose input has not arrived renders **not-ready, never false** |
| **Signal** | composes · inherits · renders · separates or is dropped | *"Signals that fail to separate get dropped from the score, not carried at low weight"* |
| **Indicator** | measures · returns a raw value | *"returns a raw value — never a score, never a threshold comparison"* |
| **Detector** | **evaluates**, returning a `Result` | `def evaluate(self, st: MarketState) -> Result` |
| **Sizing** | **refuses** | `SizingError("… refusing to size a zero-risk order.")` |

So: **a rule fails, renders its measurement and its reason, and the trade proceeds.** Nothing fires.

#### Why warn rather than block

§4.1 removed verdicts because their cut points were never fitted. **A blocking rule is a verdict with the trader's hands tied behind it** — the identical unfounded number, now with authority. The ≤1×ADR ceiling is practitioner lore validated on someone else's entry timeframe (§6.4); enforcing it converts lore into policy. And the CPOE evidence in §7b.4 is unambiguous: override rates of 46–96% are what happens when everything is a hard stop, and the cost is that the warnings which *should* be read stop being read.

**This is also not a new convention — it is an existing one, generalised.** `core/watchlist.py` already says it twice, in code: *"Surfaced, not refused. A repeated symbol is information the user judges."* and *"NEVER RAISES and never blocks. Staleness is shown, not enforced … Callers display this; nothing gates on it."* §4.2 applies the watchlist's own rule to the ticket.

#### One rule carries `enforcement: block`, and only one

**The daily loss limit.** Breached ⇒ the terminal will not stage another order this session, and says so in red.

The evidence beats the principle in exactly this one place. Coval & Shumway: morning losers take above-average afternoon risk (31.2% vs 27.0%) and the prices they set revert 27% faster — the moment this rule fails is the moment your judgement is measurably at its worst, which is when a warning you can wave through is worth least. Every other rule here assumes a trader reading it in a normal state. This one exists for the state where that assumption fails, and a pre-commitment device that can be overridden in that state is not a device.

**It is enumerated**: `HARD_BLOCKS = frozenset({"daily_loss_breached"})`, one call site in `stage()`, contents asserted by test. A second member is then a visible one-line diff in a named constant. **Reconciliation-unknown and pre-registration-incomplete are not in it** — they were blocks in v1.0 and are now `enforcement: warn` at the highest severity.

**Scope, confirmed:** it blocks **`BUY` and `SHORT` only. `SELL` and `CLOSE` are always available** — a limit that traps you in a position is not a risk control, it is the opposite of one.

**Reset, confirmed: automatic at the session boundary.** A bad Tuesday costs you Tuesday and nothing more. No morning re-arm ceremony — the limit's job is to stop the spiral inside a session, and asking you to re-authorise each morning would add friction on 249 good days to buy nothing on the one bad one. The rolling-month limit is what carries the longer horizon, and it does not reset daily.

Note the limit of what `block` can mean: the terminal has no path to send an order, so it blocks its *own* staging, not your trading. You can always place a trade in TWS by hand; the friction is real and the last resort is yours.

#### The line this does not cross

Beyond that one rule, these refusals stand, because none of them is about trade permission:

| Remains a refusal | Because |
|---|---|
| Refusing to **render** a number it does not have (`ABSENT`, `NOT BUILT`, `warming`, `unavailable`, `not-ready`) | This is §4.1. Refusing to fabricate is not refusing you |
| The **ingest refusals** — `MalformedFilename`, `ArchiveCollision`, `WatchlistSchemaError`, `WatchlistDataError` | Integrity of the record. Trade any symbol you like; git history stays honest |
| The **two human gates** — what to trade, and pressing submit in TWS | Not the terminal blocking you. It has no path to send an order, by construction |
| `SizingError`, `StopResolutionError`, `AmbiguousContractError` | Not judgements — the arithmetic has no answer, or the symbol is ambiguous and guessing is worse |

### 4.2a What "structural" means here

This cannot depend on nobody later adding an `if rule.blocks:`. Four constructions, each with a test:

1. **`enforcement` is a required field with no default**, and `block` is legal in exactly one place — a test asserts that the set of rules with `enforcement: block` equals `HARD_BLOCKS`. The defect is made *representable but immediately visible*, rather than forbidden in prose.
2. **Sizing cannot see rules.** `size_for(nlv, risk_pct, entry, stop) -> Size` — the signature does not accept them and cannot be given them; a test asserts the parameter list, and a second asserts the sizing module does not import the rules module at all.
3. **Staging refuses only on the enumerated set.** `stage(ticket, acknowledgements) -> StagedOrder` raises only on the refusals above plus `HARD_BLOCKS`. A test enumerates every raise site in the staging path and fails if a new one appears. Failed rules travel **on** the staged order as a recorded field, never as a precondition of producing it.
4. **The trade record carries what was shown and what was chosen.** Every rule that failed, its measurement, and whether it was overridden — so §8 can measure the override rate per rule. **This is how a rule earns `enforcement: block` or earns deletion, and the only way it can.**

**The acknowledgement keystroke.** The two former blocks — reconciliation unknown, pre-registration incomplete — render at the highest warn severity: the ticket stages, but you press a key to proceed, and **that keypress is written to the trade record.**

Its purpose is measurement, not friction. §7b.4 deletes any rule overridden more than 80% of the time — but that number exists only if the record can tell *shown* from *seen and proceeded anyway*. Without the keystroke every rule looks 100% overridden, the 80% test has no input, and nothing on the ticket can ever be pruned. **The keystroke is how a rule earns its place or loses it.** Ordinary rules need no keypress; they are pruned by whether they ever coincide with a trade you regret, which the log answers on its own.

**Wording follows.** Outside the one blocking rule, no panel says `BLOCKED`, `REFUSED` or `NOT ALLOWED` about a trade. The vocabulary is `warn · acknowledged · overridden`, and the sentence form is *"stop 1.4 ADR · ceiling 1.0 (orb_v3_tradebook, unfitted, intraday_orh)"* — measurement, threshold, provenance, timeframe, no imperative.

---

### 4.3 Layout is declared, and the declaration is data

**Not every indicator, signal or component appears on screen.** A config file declares, per component, whether it renders and *where*:

```yaml
# config/layout.yaml — committed, one component per line
surface_03:
  - {id: rvol_or,        slot: 1,  visible: true}
  - {id: adr_used,       slot: 2,  visible: true}
  - {id: extension_ema20,slot: 3,  visible: true}
  - {id: m4_tape_speed,  slot: 11, visible: true}
  - {id: m6_print_size,  slot: null, visible: false, reason: "never changed a decision, 2026-09"}
```

**The screen is finite and your attention is the scarcest input in the system.** Position is therefore a choice you are already making, every day, whether or not anyone records it. This records it.

#### Position is an ordinal, and its history is the measurement

Slot 1 is not the same statement as slot 14, and `visible: false` is a third statement again. So the datum is the **ordinal**, not a boolean — and the useful object is not today's layout but **the layout's history**: a component demoted twice and re-promoted once tells you far more than where it currently sits.

**This is free, because the file is committed.** `git log config/layout.yaml` is a time series of your own revealed judgement about every component in the system, with dates and — because the `reason` field is required on any change — with the argument you made at the time. It is the same trick as the watchlist archive being a sampling frame: an artifact that had one purpose turns out to carry a second, better one, provided it is versioned and nothing rewrites it.

#### Tenet 7 is what makes this non-circular

**A hidden component still computes and still writes to the day record.** *Display is not storage.* If hiding an indicator also stopped recording it, only visible components would ever accumulate evidence, the inference would be circular by construction, and nothing off-screen could ever earn its way back on. **`visible: false` is a rendering instruction and nothing else** — enforced by a test asserting the producer set is independent of the layout file.

That also means demotion is cheap and reversible, which is the property that makes you willing to do it honestly.

#### What this measures, and what it does not

**It measures what you use. It does not measure what works** — and the gap between those is the interesting part.

A component can hold slot 1 for a year because it is genuinely decisive, or because it has been there since the first build and nobody questioned it, or because it is *reassuring* rather than informative. Real-estate incumbency is a strong bias and this method cannot see it. Equally, a component may sit at `visible: false` and be valuable — you never gave it a fair trial.

So the layout history is **one of two independent rankings, and they get compared**:

| Ranking | Source | Answers |
|---|---|---|
| **Revealed preference** | `config/layout.yaml` history | What do I actually look at |
| **Measured contribution** | Override rates (§7b.4), detector hit rates (§12.5), grader dimension separation | What actually separates outcomes |

**Where the two disagree is the finding**, and it is the most valuable output of this mechanism. A component you keep at slot 2 that never separates anything is a comfort object. A component you hid that does separate is a real miss. Neither is visible from either ranking alone.

#### The terminal must never reorder itself

**Layout changes are manual edits by you, with a reason.** No auto-promotion, no usage-driven reordering, no "we noticed you look at this a lot."

The reason is structural and it is the same one behind removing the exposure dial: **a system that both measures your preference and shapes it destroys the measurement.** If the terminal reorders based on what you attend to, position stops being your revealed judgement and becomes the terminal's, fed back to you. The record would then say you valued something you were merely shown more prominently.

This also keeps the mechanism honest as an input to **§12.7's prioritisation pass** — which ranks candidates by argument. Layout history ranks them by months of behaviour. Two independent methods, run against each other, is worth considerably more than either.

### 4.4 Every setting is declared, in config, exactly once

**No setting lives in code. Not a threshold, not a window, not `useRTH`, not a default in a function signature.** This is the third standing rule and it is enforceable the same way as the first two.

**The failure this prevents is not "a number in code" — it is a number in *two* places.** A config key plus a default in the signature is two sources of truth, and the default wins silently on the day the key is missing or misspelled. **That is how a value nobody chose ends up sizing a position.**

#### The mechanism, and it is one already used three times

**Required, with no default.** `lookback` in `SignalSpec`, `enforcement` on a rule (§4.2), `mode` on the stop offset (§7b.2) — each is required precisely so that omission is an error rather than an inherited value. **Extend it to everything.** A missing key raises `ConfigError` naming the file and the key; it never falls back.

```
config/
  risk.yaml         risk_pct_default · risk_pct_cap · daily_loss_usd · monthly_loss_usd
                    open_risk_cap_R · concentration_cap
  data.yaml         use_rth per indicator · bar sizes · durations · vwap_anchor
                    vwap_basis · pacing budgets · cooldowns
  indicators.yaml   adr_days · atr_days · atr_smoothing · rvol_days · rvol_reference
                    sma_lengths · extension_bands
  rules.yaml        every rule: id · measures · threshold · enforcement · source · timeframe
  layout.yaml       per component: slot · visible · reason        (§4.3)
  data_budget.yaml  per_run_usd · rolling_30d_usd · overrun_alert_pct  (§7.2)
  playbooks/*.yaml  entry_construction · window_scale · baseline_policy  (§5b)
```

**One directory, one file per domain, one loader.** The loader is the only code that reads them, which makes "required, no default" enforceable in a single place rather than at every call site.

#### Every value carries its source, and the source vocabulary matters

`source` is a required field, not documentation, and it is drawn from a closed list:

| `source` | Means | May it be tuned? |
|---|---|---|
| `christoph_preference` | You chose it | **Yes** — it is yours |
| `tradingview_convention` · `qullamaggie_faq_2021` · `orb_v3_tradebook` | Adopted from a named external convention | Yes, but you are then off-convention and the cross-reference breaks |
| `lore_uncredited` | Practitioner folklore with no published test | Yes, and **it should render `unfitted` wherever it appears** |
| `fitted@<version>` | Estimated from your own data, with a holdout | **Only by refitting** |
| **`constraint:<source>`** | **Not a choice at all** | **No.** Changing the number does not change the world it describes |

#### Constraints are prefixed by source, and every one carries a note

**Any value that is imposed rather than chosen is marked `constraint:` with the authority that imposes it**, and **`note` is required** — not documentation, a field, empty-or-missing is a test failure.

```yaml
tick_cooldown_s:
  value:  15
  source: constraint:ibkr
  note:   "Same-symbol tick-by-tick re-subscribe cooldown. Not a choice.
           Under another broker this may be absent, longer, or replaced by a
           limit on a different axis entirely — re-derive it, do not port it."
```

**The reason for the prefix rather than one flat marker is portability, and it is the whole point.** Different authorities have completely different half-lives:

| Prefix | Imposed by | Survives a broker switch? |
|---|---|---|
| `constraint:ibkr` | The broker's API | **No — every one must be re-derived** |
| `constraint:tws` | The Trader Workstation client specifically | **No**, and some cease to exist rather than changing value |
| `constraint:sec` | Regulation | **Yes** — SSR, PDT, settlement follow the market, not the broker |
| `constraint:exchange` | Venue mechanics | **Yes** — tick size, session hours, half-day closes |
| `constraint:databento` | The data vendor | **No**, but independently of the broker |

**`grep 'constraint:ibkr' config/` is the port checklist**, generated for free and always current. That is the artifact this rule exists to produce: **the set of assumptions baked into the design because of one vendor, enumerated, each with a note saying what it would become elsewhere.** Without it, a broker migration means re-discovering every one of them by hitting it in production.

**The known inventory today**, so it is not rediscovered later:

| Value | Prefix | Why it is not a choice |
|---|---|---|
| 15 s same-symbol tick cooldown · 5 tick-by-tick slots · **3 concurrent `reqMktDepth`** · ~100 market-data lines | `constraint:ibkr` | Subscription limits at base entitlement. **Depth at 3 is what caps simultaneous attaches** (§6b.1c) |
| ~60 historical requests / 10 min · 1,000 ticks per request · 50-simultaneous historical cap | `constraint:ibkr` | Pacing. Shapes the three-request attach (§6b.1b) |
| `useRTH` defaults to `True` and fails silently | `constraint:ibkr` | An API default, not a preference — and the reason every call site must declare it |
| `reqExecutions` is client-scoped | `constraint:ibkr` | Why manual TWS fills can return zero rows (§8.2a) |
| `transmit=False` orders cleared on restart · `permId` the only stable order identity | `constraint:tws` | Why the staging store is ours and not TWS's (§7b.3) |
| SSR triggers at −10 % vs prior close · PDT 4 day-trades in 5 sessions | `constraint:sec` | **Survives any broker change.** Enforced by the market, stated by the terminal (§7b.1a) |
| RTH 09:30–16:00 ET · half-day closes · tick size | `constraint:exchange` | Session facts. Also why `core/session.py` must be the single source (§008) |
| 1,000-record pages · schema availability per dataset | `constraint:databento` | Vendor, not broker — moves independently |

**Two tests.** Every `constraint:*` value has a non-empty `note`. And **`--dump-config --constraints` prints them grouped by prefix** — which is the migration document, written by the system rather than by someone's memory.

#### Two tests, because prose does not hold

1. **No literals at the call sites.** A test scans the indicator and fetch layers for numeric and boolean literals passed as arguments. The specific instance already spec'd — *every `reqHistoricalData` / `reqHistoricalTicks` call site declares `useRTH` explicitly* — is the general rule applied to the parameter most likely to be silently wrong, because **its API default is `True` and getting it wrong returns RTH-only data with no error.**
2. **`--dump-config` prints every effective value with its file, key and source.** The real question at 09:31 is *"what is this actually using right now"*, and it must be answerable in one command rather than by reading five files and a signature. **A setting that cannot be printed is a setting that is not in config.**

---

## 5. The layer model

**Three layers in the terminal.** Order of authority: **Layer 2 overrides everything. Layers only downgrade.**

### 5.1 Layer 0 — deliberately not in the terminal

**Layer 0 is produced outside the terminal by the scheduled cloud task and consumed as prose.** The task runs pre-market, writes `docs/regime-snapshots/YYYY-MM-DD.md`, and that document *is* the pre-market risk-on read. The terminal links to the morning's file and shows its as-of time. It does not parse it into rows, does not score it, and nothing downstream consumes it as a number.

#### 5.1a Absence has two states, not one

**`[ NOT BUILT ]` on its own is ambiguous, and the ambiguity is dangerous.** Before the market opens, no file is the expected state. After the task was scheduled to have run, no file means **the pipeline failed** — and the two must not render identically, because the one that needs action looks exactly like the one that does not.

This is not hypothetical. The scheduled task is a **cloud** task (§A1, resolved 2026-08-10: a local Desktop task is not being used), so it writes to the cloud session's own filesystem and its output does not reach this disk on its own. Every day currently renders the absent state. On top of that, the task reaches IBKR through a claude.ai connector whose availability depends on the claude.ai login staying valid; when that login expires the task keeps running and produces nothing. **An expired login and a normal pre-open morning would otherwise look the same on screen.**

| State | When | Renders |
|---|---|---|
| **`[ NOT BUILT ]`** | No file for today, and the task's scheduled time has **not** passed. | Dim-inverse, per §4's refusal grammar. The system is refusing, not failing. |
| **`[ NOT BUILT — OVERDUE Nh ]`** | No file for today, and the scheduled time passed **N hours ago**. | Amber-inverse: read this and decide. Carries the hours since the run was due and the expected path. |

The second is an **amber** badge, not dim, because §4 reserves dim-inverse for "the system is refusing, not failing" — and an overdue snapshot is a failure, not a refusal. It is not red: red-inverse is reserved for `[ STOPPED — DAILY LIMIT ]`.

**The overdue threshold comes from config, not a literal** (§4.4), keyed to the task's cron. **Never infer that the task ran from the presence of a file** — a file written yesterday and not overwritten is a third failure that reads as success, so the check is on today's date, not on any file existing.

**Why this is the right shape and not a retreat.** The fourteen-row card was going to be built to answer a question a person already answers each morning by reading five paragraphs. The rows that would have cost the most to wire (gap breadth needs an export; TICK/ADD/RSP availability was never verified) are exactly the ones the prose handles for free. And the composite's only consumer was the exposure dial, which is also gone (§7b.1) — so the score would have been computed for a reader that no longer exists.

**What does not leave with it: the overnight macro rows.** Layer 0's rows 1–9 are not a scoring apparatus, they are nine cheap measurements of what happened while you slept — FX carry, rates and the dollar, commodities, Asia and Europe, crypto. When Layer 0 left the terminal they left with it, which was wrong: the scoring was the unfounded part, not the observations. They return as **§5.5**, split between the cloud task and the terminal.

The full 14-row model, the denominator arithmetic, and the mid-session-veto question are preserved verbatim in **§12.1**. Nothing about it is decided against; it is deferred, and it comes back only if the prose read proves insufficient in a specific, stated way.

### 5.2 Layer 1 — daily index regime

IWM / SPY / QQQ / RSP. MA stack 10/20/50/200 + slopes, distribution days (25 and 50 sessions, **normalised per-25** so bands compare), breadth via RSP vs SPY, volatility sanity check.

**`live/regime/regime_pull.py` is currently not runnable.** The consolidation moved the script body into `main()` but left `pull()` referencing a module-global `ib` and `row()` referencing `results`/`order`, which are now locals. It raises `NameError` on the first call. Import coverage cannot see this. **This is the single clearest demonstration that `live/` needs behavioural tests, and it is the first thing to fix.**

The scheduled task "Daily market regime read (Layer 1)" (cron `0 5 * * 1-5`, writing to `docs/regime-snapshots/YYYY-MM-DD.md`) already produces this read via IBKR and Claude. **Keep it running as the independent check.** Two computations of the same quantity from different code paths, compared, is a free correctness test — and per §2.2 the terminal's version writes into the day record while the scheduled task writes prose. Diverging numbers are a finding.

### 5.3 Layer 2 — own follow-through

The only playbook-dependent layer, and it overrides the others. Measured per playbook — pooling timeframes is meaningless.

**There is no trade log in the tree.** Layer 2 has nothing to compute from and renders `unfitted — n below calibration floor`. **This is the highest-leverage missing artifact in the entire system**: it blocks Layer 2, the grader's calibration, the similarity prior, the scoring loop, and every claim in §8.

### 5.4 Layer I — institutional context *(new)*

**The ask:** distil corporate, banking, prop-desk and market-data insight into consumable pre-market context.

**The research finding that shapes it:** "risk-on/risk-off" is four different questions and only two are yours.

- Market makers (Jane Street, SIG, Optiver) classify *realized-vs-implied vol and inventory*, not direction. Borrowing their vocabulary would be a well-formed value answering a different question.
- Bank morning calls produce a **narrative written after the overnight session**, not a pre-registered classification. Useful as colour, useless as signal. **There is no free daily US-equity desk note.**
- Multi-manager pods (Millennium, Balyasny) *do* run a hard discrete state machine — but it is **P&L-driven, not market-driven**. A PM who hits a stop gets capital cut regardless of the tape.
- **Therefore: the binding daily state variable at a real shop is your own risk budget, not the market's mood.** That is the most transferable finding in the whole research pass, and it is why the card's last rows are personal.

**The strongest single empirical result:** the Kansas City Fed RORO index (first PC of daily changes across credit, equity/vol, funding, FX/gold) finds **credit spreads drive more of the equity effect than the VIX component does**, and the index is right-skewed (γ=1.56, kurtosis 21.98) — **risk-off arrives in fat tails, not gradients.** ([KC Fed](https://www.kansascityfed.org/data-and-trends/risk-on-risk-off-index/), [wp 24-12](https://www.kansascityfed.org/documents/10594/rwp24-12charistedmanlundblad.pdf)). Two consequences, both encoded: build **credit** before VIX; and make the state machine **asymmetric** — instant into RISK-OFF, two clean sessions to leave.

**The strongest result about *momentum specifically*:** Daniel & Moskowitz, *Momentum Crashes* — the dangerous state is not "risk-off", it is **high variance plus a market that has already fallen and is trying to bounce**, where momentum's beta goes to roughly −1.80 in up markets. A gap-down-then-reclaim in a downtrend is the intraday shadow of that. A steady grind lower in low vol is not. ([paper](https://www.kentdaniel.net/papers/published/mom12.pdf))

**The card — 9 rows, 30-second read.** Rows 1–6 freeze at 08:00; 7–9 are context and health. **It was twelve.** The three live overnight rows moved to the strip (§5.5), which measures the same instruments with longer provenance and no state machine attached — *the same quantity in two places is the failure this project keeps having, so one of them had to go.*

| # | Row | Source | Lag |
|---|---|---|---|
| 1 | HY OAS 5-day change | [FRED](https://fred.stlouisfed.org/series/BAMLH0A0HYM2) | **T+1** |
| 2 | Breadth: prior up/down volume, % >20DMA, up-days in 5 | own universe | EOD |
| 3 | Distribution days (25) | own | EOD |
| 4 | Leadership: (XLU+XLP) vs (XLK+XLY) 5d; RSP/SPY | daily bars | EOD |
| 5 | Dispersion: COR1M percentile / 6mo | [Cboe](https://www.cboe.com/us/indices/implied/) | EOD |
| 6 | Macro shock: 10Y and DXY in σ — **a rule, not a signal — `enforcement: warn`, top severity** | FRED/futures | EOD |
| 7 | Calendar: FOMC/CPI/NFP, OpEx, universe earnings count | calendar feed | daily |
| 8 | Slow frame: NFCI, NAAIM, BofA B&B — **`DESCRIPTIVE ONLY`, with as-of dates** | weekly | weekly |
| 9 | **Data health: n/9 fresh; state defaults DOWN one level if any row is stale** | self | live |

*Moved to §5.5, not deleted:* overnight ES/NQ · VIX level and term structure · live credit divergence.

**State vocabulary — computed and logged, not rendered (§4.1).** `RISK-OFF` · `DEFENSIVE` · `NEUTRAL` · `CONSTRUCTIVE` · `FULL MOMENTUM`, each with a desk action (flat / half-size + A+ only / normal + confirmation / full size / press and allow adds). The state machine is **built in slice 013 and writes into the day record from day one** — that is what makes the 60-session separation test possible. **The screen shows the nine rows and their measurements; it does not show the state name, and there is no desk action on screen.**

This is a smaller change than it looks. v1.0 already said the layer does not size a trade for 60 sessions; §4.1 only closes the gap between *not sizing* and *not being read as if it did*. A `FULL MOMENTUM` banner that officially changes nothing still changes what a person does at 09:31.

**Every threshold in this layer ships as `PROVISIONAL`.** Log the state daily *without* letting it change behaviour, then check whether realized R actually separates across states, and log which row was decisive. If the state is driven by rows 1 and 5 alone, delete 7 and 8. **Nine honest rows beat twelve.**

**Readmission (§12.3):** the state name renders when 60 sessions are logged **and** median R separates across states by more than the within-state spread on a holdout. Failing that test twice deletes the state machine and keeps the rows.

**Rows deliberately NOT built** — each would look authoritative and is not:

| Rejected | Why |
|---|---|
| Dealer gamma / GEX / flip level | Dealer *sign* is inferred, not observed. Every retail GEX product hides that. Maximum authority-per-unit-evidence on the whole screen. |
| FINRA short volume % | FINRA's own [Information Notice 05/10/19](https://www.finra.org/rules-guidance/notices/information-notice-051019) disqualifies it: unconsolidated (their worked example: 20% vs 10.7% same day), MM-inflated, not short interest. |
| Buyback blackout | State Street, 1994–2018, 136 months: all regression p-values > 0.05 in every window. |
| McClellan / Zweig breadth thrust | ~12 lifetime observations of a signal selected *for* its perfect record. |
| "VIX contango = risk-on" | Base state ~80% of days. ≈0 bits. |
| CFTC COT | Three business days stale before publication. |
| ICI/EPFR/Lipper flows | Weekly, revised, about an allocation horizon you don't trade. |
| GS RAI / Citi Macro Risk Index | Methodology not public. Unverifiable. |
| Put/call as a state input | 0DTE broke comparability with its own history at the 2023 structural break. |
| **A continuous 0–100 risk score** | **Hides that four inputs are stale, and invites trading a 62 differently from a 58 on no evidence.** |

### 5.5 The overnight macro strip — in the Claude task, not in the terminal

**Decided: the strip does not render in the terminal.** It is produced by the scheduled Claude task alongside the rest of the pre-market read, and **frozen as a snapshot**. The terminal reads that snapshot; it never re-quotes, never recomputes, and never shows a live version beside it.

**Source: `Regime Read Template — Layer 0`, rows 1–9**, stripped of scoring — vol term structure · credit · **FX carry AUD/JPY + USD/JPY** · rates and the dollar · **gold and WTI** · crypto · index futures with the NQ−ES spread · Asia · Europe. Presented in the template's own **reliability order** — *credit and vol term structure > FX carry > overnight index futures > gap breadth > single-stock movers* — because *"most retail reads lead with the least reliable input."*

**Why this is the right place for it.** The strip is a *read*, and reading nine macro instruments and saying what they mean together is what the Claude task is good at. The terminal's only possible addition was a Δ-since-snapshot column — which buys one thing (drift) at the cost of nine live quotes, a refresh affordance, a staleness state, and a second place where the same nine numbers exist. **Two computations of the same nine instruments in two processes is how two series with one name end up disagreeing**, and the drift it was buying is the least reliable part of the least reliable panel.

### 5.5a The locked snapshot — the interface between Claude and the terminal

**The task emits YAML, not only prose.** Prose is for you; the snapshot is for every consumer that comes later.

```
docs/regime-snapshots/YYYY-MM-DD.md     ← the read, for a human
docs/regime-snapshots/YYYY-MM-DD.yaml   ← the same content, locked
```

```yaml
schema_version: 2
session_date:   2026-08-10
frozen_at:      2026-08-10T05:02:11-04:00   # written once; never updated
macro_strip:
  - {id: vol_term,  value: "VIX 14.2 · M1<M2 contango", as_of: "05:01", band: inside}
  - {id: fx_carry,  value: "AUDJPY +0.31% · USDJPY +0.12%", as_of: "05:01", band: inside}
  - {id: commodities, value: "GC −0.4% · CL +3.2%", as_of: "05:01", band: outside}
  # ... nine rows
layer_0:
  ratification:   {row_12: null, row_13: null, row_14: null, pending: true,
                   rows_available: 2, floor_fired: true,
                   bands: {ratifies: "+2..+3", downgrade_one: "0..+1", forces_red: "<=-1"},
                   bands_source: regime_read_template_2026-08,
                   floor_source: prompt_decision_2026-08-10}
layer_i:
  rows:      [...]            # nine rows, each with value, source, as_of, band
  state:     CONSTRUCTIVE     # computed here, on trial, NOT rendered by the terminal
  decisive_row: breadth
  health:    "8/9 fresh"
```

**`schema_version` moved 1 → 2 on 2026-08-10**, when `REGIME-PROMPT.md` v1.2 added the
**reduced-card floor**: if fewer than three of rows 12–14 are available, ratification is
skipped entirely and the pre-open read stands. The `ratification` block above is what v1.2
emits to record that. A v1 snapshot has none of those keys, so **without the bump a reader
cannot tell a v1 snapshot from a v2 one where the floor did not fire** — the two are
indistinguishable, and property 4 below is what makes the difference actionable. A bump with
no recorded cause is one nobody can evaluate later, which is why this paragraph exists.

**This example is not the full v2 shape.** It shows the keys named above and omits others v1.2
emits — `layer_0`'s scoring fields, the whole `layer_1` block, `could_not_do`, and the
per-row `score` / `source` / `state` fields on `macro_strip`. **Read `REGIME-PROMPT.md` PART
E2 for the emitted shape**; a consumer written against this block alone would be written
against a shape that was never produced.

**Four properties, and each is load-bearing:**

1. **Frozen. `frozen_at` is written once and never updated.** A snapshot that quietly refreshes is not the thing you read at 05:00, and the whole point of a snapshot is that it is the thing you read at 05:00.
2. **The terminal reads it and does not recompute it.** It renders the values with the frozen stamp and the age. `renderer(record)` stays a pure function; the snapshot enters the day record as `regime_snapshot: {ref, frozen_at, schema_version}` and its rows travel as data.
3. **Machine-readable from day one, even though nothing consumes it yet.** Prose cannot be joined to a trade log. **Every session logged from now on becomes a row in the eventual "did regime separate outcomes" test** — and that test is impossible to run retroactively over prose. This is the cheapest possible thing to get right early and the most expensive to fix late.
4. **A missing file is a state, not an error.** No snapshot for today ⇒ `[ NOT BUILT ]` with the date, never a blank panel and never yesterday's file silently reused. `schema_version` mismatch ⇒ refuse to parse and say so.

**Cost:** extend the existing task's prompt to emit the YAML alongside the prose. No new infrastructure, no market-data lines, no refresh affordance, no staleness machinery in the terminal.

## 5b. The playbook config — the single standardized input

The playbook is what makes every other component specific. Five things already key off it in the Drive spec: Layer 2 measurement scope, signal lookback, outcome definition, signal availability, universe filter. **Two more must, and currently do not.**

```yaml
playbook:
  id: intraday_orb_1m
  timeframe: 1m
  universe_filter: <selection criteria>
  indicators: [...]          # SELECTS from the registry; never redefines
  rules: [...]
  predictions: [...]
  outcome: <forward excursion horizon>
  holdout: <declared per playbook>
  status: unfitted | fitted@<version>

  # ── 6th binding: which level is THE level, and which side ──
  entry_construction:
    trigger_level:   or_high        # resolver NAME, not a price
    trigger_side:    above          # above | below — inverts the whole cluster
    or_window_min:   1              # 1 | 5 | 60
    buffer:          {mode: atr_frac, value: 0.05}
    arm_after:       "09:30"        # failed-bounce short arms 09:45
    min_range:       {mode: spread_mult, value: 3}   # micro-range DNT
  invalidation_default: or_low

  # ── 7th binding: windows scale with the range, they are not constants ──
  window_scale:      range_fraction
  detector_window:   0.33           # 20s on a 1-min OR, 100s on a 5-min
  reclaim:           0.42
  baseline_policy:   warm_or_refuse
```

### 5b.1 Why the sixth binding exists

`detectors.py:501` reads `level = st.break_level4 if st.break_level4 is not None else st.or_high4`, with `config.yaml` setting `breakout_minutes: 1`. **The entire absorption/defence cluster is hardcoded to one playbook's level, long-only.** On a flag breakout at 11:20, `PullbackDefending` renders a confident verdict about a price from 09:31 — computed correctly, and about a different question.

`entry_construction` already exists as a field in the Drive schema. **Nothing subscribes to it.** It is declared and unread.

`trigger_level` and `trigger_side` become **required parameters with no default**, for the same reason `lookback` is required with no default in `SignalSpec`: a default of "OR high" is precisely what let a flag detector answer about the open. With no playbook attached, the pane renders `no trigger level declared` rather than silently watching 09:31.

`trigger_side: below` inverts the polarity of the whole cluster in one flag rather than needing a mirrored detector set. **The machinery already exists and nothing drives it** — `_state_cell` colours TRUE/FALSE by polarity with `BEAR` inverting, and `GroupScore` takes polarity as a constructor argument.

### 5b.1a Two modes of use, and the playbook question resolved

**The correction that forced this section.** The terminal is not the only screen. You watch the market in TradingView, in IBKR, and elsewhere, and you may come to this terminal **only to size and issue an order** — with no attach, no tape pane, and no playbook selected. **At submit time there is no spare second: a keystroke that makes you choose a playbook makes your entry late, and a late entry costs more than any statistic is worth.**

Earlier drafts of this document assumed every trade passes through the analytical path. That assumption is wrong and everything built on it needed revising.

**Two first-class modes. The second is not a degraded version of the first.**

| | **Analytical path** | **Fast path** |
|---|---|---|
| You | attach a ticker, read the tape, decide here | decided elsewhere; here only to size and stage |
| Playbook | `playbook_attached` **required, no default** | **none, and none is asked for** |
| Tape pane | running | never opened |
| Keystrokes on the send | as many as you like | **the minimum, and no field may be added to it** |

**Standing rule: nothing may be made mandatory on the fast path.** Not the playbook, not a thesis, not an acknowledgement that is not already there. Any field the system wants is collected *after* the send or not at all. This is §4.2 applied to journaling — **the cost of not filling something in is lost measurement, never a refused or delayed trade.**

#### So: when is the playbook required?

| Field | When | Required? |
|---|---|---|
| **`playbook_attached`** | at attach | **Required, no default — but only because the tape pane cannot compute without it.** If you never attach, no computation runs, so there is nothing to parametrise and nothing is asked |
| **`playbook_traded`** | **after the close, at review** | **Required before the trade is *analysable*, never before it is *sent*.** Defaults to `unassigned` |

The earlier draft made `playbook_traded` required to stage. **That was wrong** — it put a decision on the critical path to buy a field that is just as accurate collected three hours later, and considerably more accurate, since by then you know what the trade actually was.

**`unassigned` is a real, rendered state.** The review surface shows `14 of 61 trades unassigned` and **excludes them from every per-playbook statistic, saying so.** The pressure to tag comes from watching your own sample shrink, not from a modal.

**Tagging is a post-close pass and must be nearly free** — the day's fills in a list, one keystroke each, with a **suggested** playbook derived from what is already known: whether it was on the watchlist, the fill time relative to the open, whether a playbook happened to be attached at that moment, and the price structure around entry. **Suggested, never auto-applied.** Auto-assignment would fabricate the exact field every downstream analysis depends on, and it would do it invisibly.

#### Attached and traded may disagree, and that is data

`attached: intraday_orb_1m · traded: intraday_flag` is a countable event. If rare, the attach step is working; if common, either the pane needs re-binding more often than it gets it, or your morning list is showing you a different setup than you think. **Neither is visible if one field overwrites the other, and neither exists at all if the field is only collected at send.**

**Re-binding the pane is one keystroke and does not detach** — the subscription does not change, only the computation over it, so it costs no slot and incurs no 15-second cooldown, recomputing from the backfill buffer already in memory. The pane **marks the re-bind point** rather than presenting one series computed two ways.

**Consequence for the grader.** A ticker already carries up to six grades, one per playbook (§6.2), so the ranked list can show *"A on flag, ungradeable on ORB"* before you attach — which is what makes an attach-time choice informed rather than a guess.


### 5b.2 Why the seventh binding exists

The detector constants are absolute where they should be relative to the range. Since `breakout_minutes: 1` is the config default, these were plausibly tuned **for** the 1-minute case — which means it is the 5-minute playbook they fail to transfer to.

| Constant | On a 1-min OR (60s) | On a 5-min OR (300s) |
|---|---|---|
| `size_absorption.window_s: 20` | **33% of the range** | 6.7% |
| `pullback_defending.reclaim_s: 25` | **42%** | 8.3% |
| `size_reloading.window_s: 20` | 33% | 6.7% |
| `tape_reader.hold_max_secs: 30` — "upper end of normal hold" | **half the range** | 10% |
| `level_claim.recent_s: 60` | **the entire range** | 20% |

One set of tuned numbers transfers across all three OR windows if it is expressed as a fraction of the playbook's own range. Tenet 6, applied inside a single config file.

**`baseline_policy: warm_or_refuse` is the 1-minute-specific consequence.** `tape_reader` needs `hold_baseline_min: 12` completed holds before C1–C4 fire, against a rolling `hold_baseline_n: 60`. On a 1-min ORB the trigger is at 09:31:00 and twelve completed holds almost certainly have not occurred. `rolling_flow.py` has the same shape and is honest about it — z-scores suppressed *and withheld from the baseline* until saturation. **A detector with a cold baseline renders `warming`, never FALSE.** A FALSE at 09:31 meaning "no baseline yet" is indistinguishable from "no absorption," and that is the worst available error.

The **micro-range refusal** is the other 1-minute gate, and it is currently prose only: ORB v3's do-not-trade list has *"micro range — opening range < ~2–3× the spread."* On a $14 name with a 3-cent spread a 1-minute range can sit under 9 cents. It belongs on the ticket as a rule with `enforcement: warn` (§4.2), with the range and the spread both shown.

**Standing hypothesis to log against, not assume:** ORB v3 already pre-registers *"1-min refinement shows nothing outside the bloated-range case."* Kullamägi's published position points the same way — the 1-min ORH has a materially higher failure rate than the 5- or 60-min, and for EPs he buys the 1-min then *adds on the 5-min for confirmation*.

---

## 6. The stock grader

### 6.1 The problem it solves

Six different A+/A/B/C ladders currently share the same letters and mean different things: the 15-min-ORB 8-point rubric (A+ = 7–8), `Stock Grading.xlsx` implementing it, `setup_grader.py`'s volume-ratio A–F table, `orb_validator/reference.py`'s weighted six-component 85/72/58/42 bands, `flag_monitor.py`'s "A+/A/B/C per the playbook rubric", and `tape_reader.py`'s four-component 5-minute grader.

**A terminal rendering "Grade: B" must carry which ladder produced it.** This is the canonical pattern — a well-formed value answering a different question — in its purest form.

### 6.2 The design: one dimension library, N playbook rubrics

A single composite would have to answer "is this a good stock?", and the setups **disagree definitionally**. Extension above the 20-EMA is a *disqualifier* for a pullback, a *prerequisite* for a parabolic short, and *irrelevant* to an ORB. Six-month dormancy is a *positive* for an EP and a *negative* for a breakout. Rolling these into one number produces a different wrong answer for every consumer.

So: **13 dimensions in one library; each playbook selects a subset, weights them, and declares some as gates.** A ticker gets up to six grades and may be A for one and ungradeable for the rest.

| # | Dimension | Measurable | Computable today? |
|---|---|---|---|
| D1 | Liquidity | 20d median $ volume; share volume; spread bps | ✅ (spread ❌) |
| D2 | Range budget | ADR% (Kullamägi 20-session H/L), ATR₁₄; **risk feasibility = stop ÷ ADR** | ✅ |
| D3 | Relative strength | recency-weighted percentile of 1M/3M/6M return | ✅ |
| D4 | Trend / stage | 8 trend-template booleans; Kell cycle state from 10/20 EMA + 50/200 SMA | ✅ |
| D5 | Base quality | RMV-style tightness; contraction sequence; base duration | ✅ |
| D6 | Extension | (close−EMA20)/ATR; (low−EMA10)/ATR | ✅ |
| D7 | Relative volume | **RVOL_daily** (time-of-day cumulative) and **RVOL_OR** (first-5-min vs 14d) | ✅ |
| D8 | Catalyst quality | present, type, freshness, SUE/surprise | ❌ news + estimates |
| D9 | Location vs levels | ATR distance to PDH/PDL, PMH/PML, 52wk, VWAP, swing | ✅ |
| D10 | Regime fit | **context rows, not a multiplier** (§4.1) — reads Layers 1/2 and the Layer I rows, never recomputes them | ✅ |
| D11 | Prior move / dormancy | max % over 1–3M; days since >1 ADR move | ✅ |
| D12 | Float / supply | free float, turnover, days-to-cover | ❌ fundamentals |
| D13 | Independent movement | return minus β×index; rank within sector | ⚠️ needs sector map |

**Ten of thirteen are computable from OHLCV today.**

### 6.3 The mechanism

1. **Gates first.** Any gate at F ⇒ **`UNGRADEABLE`, naming the failing gate and its measurement.** Not "grade C", not a low number. *A setup missing its defining feature is not a bad instance of the setup; it is not the setup.* **Gates render** — they are declared rules with the measurement shown, which is what §4.1 permits. `UNGRADEABLE` is a statement about the grader, **not a refusal to let you trade it** (§4.2): the ticker stays selectable, stays attachable, and can be staged.
2. Score weighted dimensions, normalise 0–1. **Computed and stored; not rendered as a letter.**
3. ~~Band: A+ ≥ 0.90, A ≥ 0.80, B ≥ 0.65, C ≥ 0.50.~~ **Suspended (§4.1).** Those four cuts are the sharpest unfounded numbers in the document: six ladders in six files disagree about what the same letters mean, and `tape_reader`'s were set on three synthetic tapes. A letter is a prediction wearing a measurement's clothes.
4. ~~Apply the D10 regime cap.~~ **Suspended** — there is no composite to cap and no dial to feed it (§7b.1). D10 renders as context rows.
5. **Emit the vector. There is nothing else to emit.** Per-dimension values, their gate results, and the normalised composite as a **rank position within today's watchlist** — "3rd of 14 on this playbook's weighting" is a statement about today's list, not a claim that a 0.83 is tradeable.
6. **Any dimension whose data was missing renders `ABSENT`, never a neutral middle**, and the rank inherits it: a ticker missing a weighted dimension is ranked in a separate `partial` block below the fully-measured ones, never interleaved.

**Why ranking survives and banding does not.** Ranking needs only that the weighting is *ordinally* sensible — and per Dawes (§8), equal weights on correctly-signed dimensions are hard to beat out of sample. Banding needs the cut points to be *calibrated*, which requires the trade log that does not exist. **Readmission (§12.4):** letters return when ≥150 logged trades let each playbook's cuts be fitted and the fit holds on its declared holdout.

### 6.4 The one rule that must not be ported carelessly

Kullamägi's **stop-width veto — reject any setup whose low-of-day stop is more than 1× ADR (EP: 1.5×) from entry** — is the most mechanical and least-copied rule in his method, and it is a *tradeability filter*, not a risk rule: it rejects setups whose R:R geometry is broken before entry.

**But** the most rigorous public replication ([VladPetrariu](https://github.com/VladPetrariu/Qullamaggie-breakout-scanner), 13,500 picks, 12 exit variants) found: *"every variant tighter than 3×ATR flipped the median return negative — they get whipsawed by normal pullbacks. Trailing stops are net-harmful even at 3×ATR."*

These do not actually contradict — the backtest tests a **daily-close** screen, where a tight stop sits an arbitrary distance below yesterday's close; Kullamägi's stop sits below a **same-day structural low** reached via an intraday ORH entry. **Both rules ship, each bound to its own entry timeframe: ≤1×ADR for intraday-ORH entries (EP 1.5×), a 3×ATR floor for daily-close entries.** The terminal records which timeframe a stop rule was validated against and **hard-refuses to apply either across timeframes** — a ≤1×ADR stop on a daily-close entry destroys the edge, and a 3×ATR floor on an ORH entry rejects the geometry the setup depends on. Neither refuses a trade (§4.2); the refusal is against *mislabelling a rule*, which is a different thing.

### 6.5 What is validated and what is lore

**Published research behind it:** the 5-min ORB on top-20 relative-volume "stocks in play" (Zarattini/Barbon/Aziz, [SSRN 4729284](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4729284) — 7,000 stocks 2016–2023, Sharpe 2.81, 36% alpha; independently replicated on QuantConnect at Sharpe 2.396 with a ~17% win rate); post-earnings drift as the mechanism behind episodic pivots (~12–15%/yr, 60-day drift); cross-sectional momentum. **Caveat on the ORB paper: the companion QQQ study assumed no spread and no slippage, on exactly the names with the widest spreads at 09:35.** Re-run with your broker's actual historical half-spread before believing the magnitude.

**Practitioner lore with no published out-of-sample test** — every one of these must be a named, versioned parameter carrying its source string, never a magic number: ADR% thresholds of any value · the eight trend-template numbers as specific numbers · VCP contraction counts and depths · the 30–40% breakout volume spike · pivot width · "surfing the 10/20 MA" · the entire Cycle of Price Action as a predictive classifier · SMB Radar 6+ · the 9-million-share EP · the 3–5 day / 8–20% momentum-burst budget · "top 1–2% of gainers" · the 30% overnight cap.

**One specific warning.** The **"10-EMA above 20-EMA on QQQ" market filter** appears in nearly every secondary write-up of Kullamägi's method and **is not in any of his own published writing.** The closest primary support is second-hand from the Market Wizards chapter and refers to the **S&P**, not QQQ. *A tradable filter whose index and MA type disagree between sources must not silently drive sizing.*

**On his record:** verified independently for the first time in *Market Wizards: The Next Generation* (Schwager & Coyle, Harriman House, 9 June 2026) — statements, tax documents, brokers contacted with permission, and an auditor, under a stated ~20-factor model. His own last published figure is **$82M (1 Mar 2021)**; the book supports "over $100 million"; everything above that is unsourced. He is **Stockholm-resident, not Estonian tax-resident** — there is no public tax filing. He also lost tens of millions in 2022 by staying long against his own filter, and states plainly that *"most of my money comes from a few big winners — maybe 10–20% of my trades."* **Sample size of one; no amount of statement verification converts a single path into an expectancy estimate.**

---

## 6b. The attached symbol — live tape, book and inference

**This is the surface you open the terminal for.** Select a ticker from the ranked watchlist, attach it, and the terminal hooks L1, L2 and time & sales, backfills the last *n* minutes per the playbook, then reads the live stream.

It is also **the most-built part of the system and the least-tested.** ~22 detectors exist and run; zero have behavioural coverage. Both facts matter to the plan.

### 6b.1 The attach model

| Property | Value | Why |
|---|---|---|
| Process | **Persistent**, with switchable slots. **Exactly one process, ever** — see §6b.1c | Never relaunch per symbol — that discards the warm nightly cache and forces a cold start on every switch |
| Slots | **5** tick-by-tick, config-overridable, +5 per booster pack | 5% of 100 market-data lines |
| **True slot count** | nominal minus active price alarms | Each alarm consumes a line. **Surface the true count, not the nominal 5** |
| L2 slots | **3** concurrent `reqMktDepth` below 400 lines | A watchlist-wide depth view is not purchasable at retail scale |
| Cooldown | **15 s** same-symbol tick-by-tick | Re-attach inside the window renders **queued with a reason**, never a silent drop |
| Exhaustion | A **visible state** requiring explicit detach | Must not silently fail on the 6th attach |
| Tape type | `AllLast` (includes combos/derivatives/avg-price) vs `Last` (clean regular trades) | A declared choice, not a default |

#### VWAP anchors at the pre-market open, and the anchor is a declared parameter

**Decided: session VWAP includes pre-market.** It anchors at **04:00 ET or the first print, whichever is later**, not at 09:30.

**On the names you trade this is not a detail, it is most of the number.** A gapper that has already done two million shares between 04:00 and 09:30 has a pre-market VWAP that is *where the level actually is* at 09:31 — the participants who set it are the ones in the stock. An RTH-anchored VWAP on that name starts from nothing at the open and spends the first twenty minutes converging toward a level the pre-market already established, which is precisely the window the 1- and 5-minute playbooks trade.

```yaml
vwap_anchor:  premarket_open        # premarket_open | rth_open | first_print
use_rth:      false                 # per indicator, never global
```

**The anchor is declared and rendered, because "VWAP" is now two different numbers wearing one name** — the defect this document exists to catch, and this instance is worse than most because **most charting platforms default to RTH-only.** If you read a VWAP off TradingView and the terminal computes a pre-market-inclusive one, **the two disagree, the disagreement is invisible, and it lands in `|entry − stop|`** (§7b.2). So the panel says it every time:

```
VWAP 47.31  (1-min bars · pre-market incl. · from 04:00 · 18.4M sh)
```

#### One data source, and it is IBKR

**Decided: IBKR is the only input. TradingView is not a data source, not a cross-check, and not an authority on any number this terminal renders.** It contributes **definitions only** — the formula conventions, with Kullamägi's parameters — and nothing else.

##### Two IBKR access paths, and they are not interchangeable

**"IBKR" names two entirely different mechanisms in this spec, and until now they shared one word.** They have different authentication, different failure modes, different data, and different consumers. Naming them apart is not pedantry: a plan that says "get it from IBKR" is ambiguous about which one, and the two fail in opposite ways.

| | **IBKR cloud connector** | **Local TWS via `ib_async`** |
|---|---|---|
| What it is | A claude.ai MCP connector, reached from Anthropic's cloud | A socket to TWS/IB Gateway on this machine, port `7496`/`7497`/`4001`/`4002` |
| Auth | Its own, tied to the **claude.ai login**. Cannot be renewed unattended — a non-interactive run has no `/mcp` panel to run the OAuth flow. | None beyond TWS being logged in. No cloud dependency. |
| Needs TWS running? | **No.** | **Yes.** |
| Used by | The **scheduled pre-market read** (§5.1, `REGIME-PROMPT.md` PART A–D) | The **terminal, during a live session** |
| Fails by | **Going quiet.** An expired claude.ai login makes the tools unavailable; the task still runs and writes nothing. Renders as absence, which is why §5.1a exists. | **Failing loudly.** A refused socket is immediate and unambiguous. |
| Data | What the connector exposes | Richer: full `reqHistoricalData`, `keepUpToDate` streaming, contract details |

**The asymmetry is the point.** The connector's failure is silent and needs a display state to surface it (§5.1a). TWS's failure is loud and needs no such treatment — **when TWS is down the terminal must say so and refuse, never substitute.**

**Measured, not assumed** (tasks 008a/008b, 2026-08-10, AMZN): the local path returned 7,800 one-minute bars in one request in 2.4 s and streamed a forming bar at a ~5 s cadence for 32 minutes with zero errors. It also surfaced a defect the connector's shape would not have exposed — `useRTH=0` inflates ADR% by **+1.1662 points, +44.6 %** — which is why the local path is the terminal's and not merely a fallback. See §4.4 for the `use_rth` constraint that finding produced.

**Do not collapse these into one config key or one client.** They are two sources with two reliability profiles, and a single `ibkr:` block would let a change intended for one silently alter the other.

**This resolves the venue problem by dissolving it.** TradingView's default US equity feed is Cboe One, four lit exchanges, about 25 % of the tape, with odd-lot filtering on all intraday North American bars ([TradingView](https://www.tradingview.com/support/solutions/43000473924-is-us-stock-market-data-free-by-default/) · [Cboe](https://www.cboe.com/market_data_services/us/equities/cboe_one/)). IBKR is consolidated and it is where the order goes. **So when the chart and the terminal disagree, the terminal is right and the chart is the approximation** — and the earlier instruction to "set the platform to match" is withdrawn. **Expect a difference, know its cause, do not chase it.**

**What TradingView still supplies, and it is worth being exact about, because the settings are where these go wrong:**

| Quantity | Convention adopted | The detail that is usually got wrong |
|---|---|---|
| **`ADR%`** | `mean over 20 days of (high/low − 1) × 100`, **excluding today**, from **daily RTH** bars | Kullamägi's own TC2000 formula, from his FAQ. **Not** TradingView's built-in ADR or screener ADR%, which compute `(mean(H) − mean(L)) / close` over **14** — a different estimator that normalises once by today's close instead of each day by its own low |
| **`atr_d14`** | 14-period ATR on **daily RTH** bars, **RMA-smoothed** | **RMA, not SMA.** TradingView's ATR is *"a Relative Moving Average (RMA) of the True Range"* — Wilder's smoothing, α = 1/14 ([ATR](https://www.tradingview.com/support/solutions/43000501823-average-true-range-atr/)). A simple mean of the last 14 true ranges is a **different number**, and it is the most common way this is implemented wrong |
| **True Range** | `max[(H−L), \|H−C₋₁\|, \|L−C₋₁\|]` | The prior *close* — including the gap. This is what makes ATR different from ADR, which ignores gaps entirely |

**Both are computed from IBKR daily bars with `useRTH=True`.** The convention is TradingView's; the data is not.

**VWAP is computed from one-minute bars, one basis, no alternative** (§6b.1b):

```
VWAP  =  Σ(Bar.WAP × volume) ÷ Σ(volume)     1-minute bars, from the declared anchor
```

**`reqHistoricalTicks` is not used for VWAP, and the tick-derived variant is retired.** One basis means there is nothing to declare per row, nothing to substitute, and nothing to disagree — **strictly better than two correct options with a label distinguishing them.** The approximation is small because `Bar.WAP` is the bar's *own* weighted average rather than a typical price; the only error is weighting each minute by its total volume at that minute's WAP, which diverges inside minutes where price moved sharply. **That error is now the number, not a deviation from one.**

Note this is still **not** TradingView's convention, which accumulates `hlc3` per bar — `Bar.WAP` is materially closer to tick-weighted at no extra cost.

**What it deletes:** 1,000-tick pagination, boundary-second de-duplication, the separate tick pacing question, the `tick budget exhausted` substitution state, and the two-basis label on every VWAP row.

**On TradingView the anchor does follow the extended-hours setting** — this is documented at the Pine level. `session.isfirstbar` *"if extended session information is used, only returns true on the first bar of the pre-market bars"*, while `session.isfirstbar_regular` *"is the same whether extended session information is used or not"* ([Pine sessions](https://www.tradingview.com/pine-script-docs/concepts/sessions/)). **So ETH must be ON, or the 04:00–09:30 bars do not exist on the chart and can never enter the calculation.**

**But the built-in VWAP's behaviour under ETH is not documented anywhere**, and it is the crux. **Do not rely on it — plot the anchor explicitly** with a one-line study, so the behaviour is declared rather than inherited:

```pine
plot(ta.vwap(hlc3, session.isfirstbar))          // 04:00 anchor when ETH is on
plot(ta.vwap(hlc3, session.isfirstbar_regular))  // 09:30 anchor, ETH-invariant
```

**Why your chart will still read differently, so the difference is expected rather than investigated.** Three causes, all structural, none a defect:

1. **Venue.** Cboe One is ~25 % of the tape; IBKR is consolidated. **Absolute share counts will never reconcile**, and VWAP differs because the venue mix is itself price-relevant.
2. **Source basis.** TradingView accumulates `hlc3` per bar; this terminal accumulates `price × size` per print. Identical anchors and identical data still diverge by cents on wide-ranging bars.
3. **Odd-lot filtering**, applied to every intraday North American bar on TradingView and not by IBKR.

**None of these is worth chasing.** Use the chart to see; use the terminal to size.

#### `use_rth` is a per-indicator declaration, never a global switch

Making it uniform would be wrong in both directions, and the fetch code must not have a single setting:

| Indicator | Extended hours? | Why |
|---|---|---|
| **Session VWAP, cumulative volume, volume profile, cumulative delta** | **included** | The pre-market participants set the level |
| **ADR%, ADR $** | **excluded — 09:30–16:00 ET, and DEFINITIONALLY so** (`038`) | These come off **daily** bars, and on TradingView the extended-hours toggle is labelled *"Extended Hours (Intraday only)"* — it provably cannot affect a daily bar. TC2000, Kullamägi's own platform, is the same: *"extended hours data only appears on intraday charts."* **The convention is RTH-only because both platforms make anything else impossible**, **`038` supersedes the reasoning while keeping the conclusion.** The platform argument above is wrong on its facts — a daily bar *is* altered by the flag — but ADR is RTH for a better reason: **Average *Day* Range is the mean of each session's own `High − Low` and has NO gap term**, which is precisely what distinguishes it from ATR. So it measures the session actually traded. It will **not** match a TWS figure computed over 04:00–20:00 bars, and that is correct rather than a defect ([TradingView](https://www.tradingview.com/pine-script-docs/v4/essential/extended-and-regular-sessions/) · [TC2000](https://help.tc2000.com/m/69401/l/861229-how-to-shade-pre-post-market-session-on-charts)) |
| **The 10/20/50 SMA stack** | **UNRULED by `038`; currently excluded** | `038` Part 1 rules on levels, on ADR and on ATR. **The SMA stack is none of those and nothing in `038` decides it**, so it keeps the RTH basis it already had. `036` proposed ETH and was superseded before that row was adopted — **changing it on the strength of a superseded document is the failure this project keeps having.** Declared as `SMA_BASIS` so a future ruling has one place to land |
| **ATR — see §6b.1b-ATR below** | **depends on the timeframe it is computed on, and must be named** | ATR has *no session logic of its own.* It consumes the high/low/close of whatever bars it is given |
| **Opening range (ORH/ORL)** | **excluded by definition** | The opening range is a regular-session object |
| **RVOL(t) and its 20-session median curve** | **must match itself** | Whichever is chosen, today and the 20-session reference must use the same basis, or the ratio compares two different quantities |
| **PMH / PML** | **pre-market only** | That is what they are |

### 4.4a Sessions, levels, units and windows — the `038` rulings

**Added 2026-08-14 under `038`, which supersedes `035`, `035a` and `036`.** Christoph's rulings, and they follow from what each object *is* rather than from preference. `036` reached the right answer for ADR and ATR and **the wrong one for `PDH`/`PDL`**; the reasoning below is the durable part.

#### 4.4a.1 Six windows, and a level carries its window

| Level | Window (ET) | |
|---|---|---|
| **PDC** | 16:00 closing auction | prior day close |
| **PDO** | 09:30 opening auction | prior day open |
| **PDH / PDL** | **09:30–16:00, prior day** | prior **regular** session extremes |
| **PMH / PML** | 04:00–09:30, today | pre-market extremes |
| **AMH / AML** | 16:00–20:00, prior day | post-market extremes |
| **ORH / ORL** | 09:30–09:35, today | opening range |

**Why `PDH`/`PDL` are RTH, and this is the part to record.** If they were ETH, then on any day the extreme occurred after 16:00, **`PDL` *is* `AML`** — one number, two names, and no way to tell which you are looking at. **A level that silently changes identity depending on when the extreme occurred is the canonical defect of this project.** Confirmed on Christoph's own QQQ chart for 2026-08-13: the session low of `722.34` sits in the early pre-market, so an ETH `PDL` would have been `PML` that day.

**The distinction that makes the table consistent:**

- **ADR is a statistic** — mean of session ranges, no gap term. **RTH, definitionally.**
- **ATR is a statistic** — its true range spans the prior close, so the gap is the measurement. **ETH 04:00–20:00.**
- **PDH/PDL/PMH/PML/AMH/AML are not statistics. They are levels.** They exist because price traded there, in a named window, **and the window is part of the name.**

**ADR being RTH does not propagate to `PDL`; ATR being ETH does not either.** Different kinds of object.

##### The remaining thirteen — RTH, ruled 2026-08-15 under `041`

**`038` ruled six windows and left thirteen levels undeclared.** They kept whatever basis they happened to have, **which is not a decision.** Christoph's ruling closes it:

| Group | Levels | Window (ET) |
|---|---|---|
| **Today** | `HOD` `LOD` | **09:30–16:00** |
| **Prior week** | `PWH` `PWL` `PWO` `PWC` | **09:30–16:00** |
| **Prior month** | `MoMH` `MoML` `MoMO` `MoMC` | **09:30–16:00** |
| **Long** | `52wH` `52wL` `ATH` | **09:30–16:00** |

**The argument is COMPOSITION, and it is stronger than the thin-print one.** `PWH` is the highest price of the prior week, so **it must be the maximum of that week's `PDH`s**. `MoMH` must be the maximum of the weeks; `52wH` the maximum of the months. **`038` made `PDH` RTH — so if `PWH` were ETH the chain stops composing**, and you get a week whose high is above every day inside it with no row on the panel able to explain why. **Break the chain anywhere and the level rail stops being one structure.**

**`PWO` and `MoMC` follow automatically.** A week's open is its first day's open; a month's close is its last day's close. Both are already RTH auction prints under `038`.

**`HOD`/`LOD` are the `PDL` argument exactly.** An ETH `HOD` on a gap-down morning **is** `PMH` — one price, two names, no way to tell which you are looking at.

**The thin-print argument reaches the same conclusion and is weaker, so it is recorded second:** a handful of odd lots at 03:00 should not set a price a position is sized against.

**Nothing `038` ruled changes and no statistic moves.** `PDH`/`PDL`/`PDO`/`PDC` RTH · `PMH`/`PML` 04:00–09:30 · `AMH`/`AML` 16:00–20:00 · `ORH`/`ORL` RTH by definition · `ADR` RTH · `ATR14` ETH · `VWAP`, `RVOL`, cumulative volume ETH anchored 04:00 — **all unchanged.**

**The cost, recorded so it is not discovered later.** `52wH`, `52wL` and `ATH` **will not match a TradingView chart with extended hours enabled**, on any name whose extreme printed outside regular hours — and Christoph trades with ETH charts on. On QQQ they agree today; on a gap-and-fade small cap they will not. **This is a known and accepted divergence, not a defect. Do not "fix" it later** (`OBS-053`).

**The SMA stack — 10/20/50/200 — remains deliberately unruled.** Ruling a value nothing consumes is admin. **It must be ruled before anything consumes it** (`OBS-051`).

**A seventh window is coming.** The SEC approved Nasdaq's 23/5 proposal on 2026-04-10 targeting December 2026, and NSCC plans 24×5 clearing from 2026-06-28. **Structure the taxonomy so a seventh window can be added; build nothing for it** (`OBS-049`).

#### 4.4a.2 A basis is declared in code, beside the definition — never in `config/`

**This is the correction that supersedes `036`**, which put `use_rth` into a config file. **Do not.**

**A setting is a choice. A basis is a fact about what the indicator is.** ADR is RTH by definition; a config key implies it could sensibly be otherwise and invites someone to flip it in a hurry. **Christoph's ruling: this is not a user setting in the terminal, now or in this slice.**

Each indicator carries its basis as a **constant declared beside its own definition** — `core/indicators/context.py`, the `SessionBasis` type — and the value that reaches the request comes from that constant: **never from a literal at the call site, never from config.**

**§4.4 says every setting lives in `config/`, once. A session basis is EXEMPT because it is not a setting**, and that exemption is stated here and in the code so that the next person does not move it into config for consistency and quietly turn a definition back into a preference. **An exemption that is not written down is an exemption that gets undone.**

**Number PRECISION is a genuine setting and stays in config** — `config/formatting.yaml`, per §4.0a. The two halves of the distinction are deliberately visible from both sides.

#### 4.4a.3 Every rendered value prints its basis or its anchor

```
    ADR%      1.6%  · 20 sessions, excl. today · 09:30-16:00 ET
    ADR $     $11.83  · 20 sessions, excl. today · 09:30-16:00 ET
    ATR14     $15.61  · Wilder RMA, n=14 · 04:00-20:00 ET
    PDH       $727.25  · prior session · 09:30-16:00 ET
    PDL       $723.55  · prior session · 09:30-16:00 ET
    VWAP      $730.68  · bar-derived · 566 min · 04:00 anchor · 04:00-20:00 ET
```

**Without this the panel shows two volatility numbers four rows apart, on different sessions, and a reader compares them.** It took a UAT and four chart screenshots to settle what one field in the detail column answers permanently.

**A value that carries its basis can be compared with something. A value that does not can only be argued about.**

**A row whose basis is missing renders `— (no basis declared)`, never an unlabelled number.**

#### 4.4a.4 Every value renders its unit

**Christoph's ruling: all numbers need units. Always.**

| Kind | Rule |
|---|---|
| Prices, distances, dollar ranges | **`$` prefix** |
| Share counts | **`sh` suffix** |
| Ratios / multiples | **`×` suffix, and the baseline named** — `6.1×` alone is the `12.4M` complaint again |
| ADR distances | **both** — `+$0.25 · 0.19 ADR`. ADR is a dollar quantity used as a ratio |
| Percentages | **name the referent** — `78% of $1.29`, not bare `78%` |
| Times | **`HH:MMh` 24-hour, and `ET`** |

**`ET` is not optional.** Christoph is in Cape Town, the levels mean nothing except in exchange time, and `034` lost four values to a UTC/ET slicing defect. **A bare clock time on this panel is the same defect wearing a different hat.**

Precisions come from `config/formatting.yaml` (§4.0a). **One wording difference, recorded rather than silently resolved:** §4.0a's example renders a percentage as `2.8 %` with a space and `038` renders `78%` without. The implementation follows `038`.

#### 4.4a.5 A level has a state, not only a distance

**Distance says where it is. State says what happened to it.**

| State | Meaning |
|---|---|
| `untested` | Price has not reached it today |
| `gapped over` | **Price crossed it without trading through it** |
| `traded through` | Price crossed it with trades at the level |
| `reclaimed` | Crossed back from below to above |
| `lost` | Crossed back from above to below |

**`gapped over` is the strongest of these and the reason the row exists.** Nobody got the chance to exit there, so positions taken before the gap are still held. **A level traded through on volume is spent; a level jumped over is loaded.** `PDC` most of all — being above or below the institutional print is a different day.

##### `clear for` — distance to the next claimed level

```
BREAKING  $48.55  flag high · yours 10:11h ET
  overhead   $48.80  ORH     +$0.25   0.19 ADR
             $49.60  PDH     +$1.05   0.81 ADR
  underfoot  $48.20  PML     −$0.35   0.27 ADR
  ▸ clear for 0.19 ADR
```

**One number: how far the move runs before it meets something.** 0.19 ADR clear is a muted breakout; 1.2 ADR clear is a different trade at the same entry price. **Symmetric, because a level just under a stop is a stop that gets run and then reverses.**

**This REPLACES `room up` / `room down` rather than joining them.** Those measure room in the ADR *budget*; `clear for` measures room to the next obstacle. **Having both invites reading one as the other**, which is the defect this section is mostly about.

**The lookahead cap is a threshold and renders `unfitted`** — suggested first three levels or 1.5 ADR, whichever comes first, but nothing is fitted until Christoph has watched it.

**Specified, not built.** `038` changes no panel layout, so `room up` / `room down` are still rendered today.

#### 4.4a.6 A window is a definition, and there are two of them

**Specification only — tape components are not in core and `038` builds none of this.**

**A tape reading states its window, its step, and its band, or it has no defined meaning.**

**The rolling window — what is happening now.** At each step, every trade whose **exchange timestamp** falls in the interval from `now − W` to `now`, classified buyer- or seller-aggressive, summed per side. **Default `W = 60s`, stepped `5s`.**

**Why stepped.** A 10 Hz repaint cap solves CPU and not readability. **A number changing ten times a second is unreadable even when it is cheap to draw** — that is Time and Sales in a smaller box. A 60s window stepped at 5s is twelve stable readings of the same measurement.

- **The row states the step** — `60s window · stepped 5s`. It is up to 5s stale by construction and that must not be silent.
- **Counts step; events do not.** A sweep is discrete and its *arrival* is the thing you want immediately. Sweep arrivals are exempt from the step.
- **The step size is empirical and unfitted.** Answer it by replaying a captured session at 1s, 5s and 10s. **Research, not a slice.**

**The anchored window — who has been winning, and for how long.** Anchored at the moment price **first entered the band around a level**, and running until it leaves.

```
at level since 09:52h ET · 19min · buyers 4.2M sh · sellers 4.1M sh · price +$0.02 · within ±0.02 ADR
```

**This is what absorption actually is.** Real absorption runs for many minutes; a 60s window is exactly the wrong length to see it. **The rolling window says the level is under pressure now; the anchored one says who has been winning.**

- **The band is stated and is ADR-based**, not cents — `±0.02 ADR` transfers between a $4 name and a $700 one; `±$0.03` does not.
- **Resets when price leaves the band beyond a threshold; re-anchors on return.** The reset threshold is unfitted.

**What neither window can see, and the panel must not imply otherwise:** anything before the window opened; order *within* the window (340k buy then 95k sell renders identically to the reverse); and, for the rolling window, whether the volume was at the level at all — **which is precisely why the anchored window states its band.**

**Bars are not units of time.** A window expressed in bars declares its bar size **and** its session, or it has no defined length — a 20-period MA spans three sessions on RTH bars and 1.25 on ETH. **Prefer the clock form wherever the quantity is really about time.** Nothing currently rendered is exposed to this (`OBS-050`).

#### ATR is two different numbers, and the spec must name which

**ATR is not a session-aware indicator.** TradingView's own documentation gives only `TR = max[(H−L), |H−C₋₁|, |L−C₋₁|]` smoothed by an RMA, with one input — `Length`. **No session rule at all** ([ATR](https://www.tradingview.com/support/solutions/43000501823-average-true-range-atr/)). It therefore inherits the basis of the bars it is handed, which makes "ATR₁₄" ambiguous on its own:

| Name | Bars | Extended hours | Where it is used here |
|---|---|---|---|
| **`atr_d14`** | daily | **INCLUDED — 04:00–20:00 ET.** ~~excluded, unchangeably — ETH cannot alter a daily bar~~ **Corrected 2026-08-14 under `038`, and the struck text was factually wrong**: IBKR returns different daily highs, lows and volumes for `useRTH=True` and `False`. Measured, not argued — Christoph's `013` UAT read `ATR14 13.14` against TWS's own daily ATR(14) of ≈`15.6`, **−16 %**. The true range spans the prior close, so **the gap IS the measurement** and it must come off the series whose close-to-close relationship is the real one | The **3×ATR stop floor** for daily-close entries (§7b.2) · the tight-stop rule (0.25 ATR) |
| **`atr_i14`** | intraday, playbook timeframe | **included when extended hours is on** | Not currently consumed by any rule. Available, and must be requested with `useRTH=False` if it is wanted |

**Both are legitimate; they are simply not interchangeable, and neither may be called "ATR" unqualified.** Pre-market bars have small individual ranges and large gaps *between* them, so an intraday ATR with ETH on moves in both directions relative to the RTH-only version depending on which effect dominates — **which is exactly why it cannot be substituted silently.**

**Everything currently spec'd as "ATR₁₄" means `atr_d14`.** That is deliberate: it is the basis TradingView's daily chart uses by default, so the cross-check works without configuring anything.

**`reqHistoricalData` and `reqHistoricalTicks` both default to `useRTH=True`, and getting it wrong returns RTH-only data silently** — no error, no warning, just a different number. **Every fetch site declares it explicitly**, and a test asserts that no call site omits the parameter.

**One honest caveat on pre-market prints.** They are thin and wide-spread, and a handful of odd lots at poor prices can pull a pre-market-inclusive VWAP more than their size deserves. **That is a property of the level, not an error in it** — it is where trades actually happened — but it argues for rendering the pre-market share of volume alongside, so an anchor built on 40k shares is distinguishable from one built on 2M: `pre-mkt 2.1M of 18.4M sh`.

#### What IBKR actually does — verified, and it changes two things

Researched against IBKR's own documentation. **Two findings overturn earlier claims here; both are recorded rather than quietly corrected.**

**1. IBKR historical data is filtered, and IBKR says its VWAP differs from the live feed.** Verbatim: *"Historical data at IB is filtered for trade types which occur away from the NBBO such as combo legs, block trades, and derivative trades"* and — decisively — ***"Differences are expected in other fields such as the VWAP between the real time and historical data feeds"*** ([Historical Data Filtering](https://www.interactivebrokers.com/docs/tws-api/doc/market-data-historical/historical-data-limitations/historical-data-filtering)).

**So the earlier claim that "attaching at 10:12 gives the same numbers as attaching at 09:29" was false.** If one path accumulates the live stream and the other reconstructs from history, the two VWAPs disagree by construction, on IBKR's own statement.

**The fix keeps the property and drops the mechanism: cumulative values are *always* reconstructed from history, never accumulated live — even when attached since the open.** One basis, one source, always. VWAP, cumulative volume, the profile and cumulative delta refresh on a cadence, one request per symbol per interval, rendering their as-of. **The live stream drives the tape components; it never drives a stop level.** Correctness beats freshness on a number that sizes a position — and this **dissolves the splice problem entirely**, because there is no join left to deduplicate.

**2. IBKR now runs an overnight US equity session, 20:00–03:50 ET**, Sunday through Friday ([US Overnight Trading](https://www.interactivebrokers.com/en/trading/us-overnight-trading.php)). **Whether those prints fall inside `useRTH=0` is undocumented** — and if they do, a `useRTH=0` "today from the open" request anchors VWAP at **20:00 the previous evening**, not 04:00.

**Therefore `useRTH` must not be used to define the VWAP session.** Request `useRTH=0` and **filter the returned bars by timestamp to the declared anchor.** The anchor is ours, in config, never inherited from a broker flag whose window we cannot inspect.

**Three further verified facts worth acting on:**

- **`useRTH` has no default in `ib_async`** — a required positional, `useRTH: bool`. The "silent default" risk described earlier **does not exist for this parameter**; a wrong value must be typed deliberately. The per-call-site declaration rule stands regardless, because the value differs per indicator.
- **`useRTH` on *daily* bars is undocumented.** No IBKR page states whether it changes a daily bar's high/low/volume, and the parameter text carries no bar-size carve-out — so a plain reading says it applies, which would mean `useRTH=0` yields extended-hours dailies and **a different ADR.** Use `useRTH=1`, and **test it**: pull the same daily series both ways on a symbol with a large pre-market gap and diff high/low/volume. Cheap, and it settles the question permanently.
- **`Bar.WAP`** is *"the bar's Weighted Average Price (only available for TRADES)"* ([Bar](https://interactivebrokers.github.io/tws-api/classIBApi_1_1Bar.html)). **Reconstruct session VWAP as `Σ(WAP × volume) / Σ(volume)`, not from `hlc3`** — materially closer to tick-weighted at no extra cost. Its own formula is unpublished, which is worth noting and does not change the choice.

#### Pacing is a design constraint, not a tuning detail

Quoted precisely, because several circulate in wrong forms ([Historical Data Limitations](https://interactivebrokers.github.io/tws-api/historical_limitations.html)):

- *"Making identical historical data requests within 15 seconds."*
- *"Making **six or more** historical data requests for the same Contract, Exchange and Tick Type within two seconds."* — **not** "one per two seconds", the common misquote.
- *"Making more than 60 requests within any ten minute period."*
- *"When BID_ASK historical data is requested, each request is counted twice."*
- *"The maximum number of simultaneous open historical data requests from the API is 50."*

**Three requests per attach against 60 per ten minutes is comfortable while symbols are attached one at a time by typing — exactly what core does.** It stops being comfortable at scale: **30 symbols × 3 requests = 90 requests, 50 % over the ten-minute budget, ~15 minutes to complete.** That is a hard constraint on the ranked-watchlist slice, and the strongest argument yet for it sitting outside core.

#### Databento is the default for replay. IBKR is the default for live. They are different jobs

**Decided: the shadow evaluation and every replay pull come from Databento, not IBKR.** This is not a reversal of *"IBKR is the only input"* (§6b.1b) — that rule governs the **live terminal**, where the broker's own view is the correct one because it is the venue you trade against. **Replay is a different job with different requirements**, and the two now have one source each:

| | Source | Why |
|---|---|---|
| **Live terminal — every indicator, every stop level** | **IBKR only** | It is your broker. Its view is the one your order meets |
| **Replay, shadow evaluation, calibration** | **Databento only** | Batch delivery, no pacing, no session window, no restart to survive |

**What this deletes is worth listing, because it was all accidental complexity:** the ≈9-hour overnight job · resumability across the daily IB Gateway restart · pacing contention with the live attach path · the undocumented question of whether tick requests share the historical budget · the 3-year tick history limit. **None of it was buying anything except a saved subscription fee that no longer applies**, since the pull is per-byte on ~8 symbol-days a session and sits well inside the existing cost gate (§7.2).

**The `reqHistoricalTicks` capability question is therefore closed as an open item** and moves to §12.9, the source-decision layer, where it belongs — a later optimisation, not a prerequisite.

#### The consequence that must not be lost: validation and live run on different tape

**A detector validated on Databento replay runs live on IBKR.** These are not the same tape, and IBKR says so itself: historical data is *"filtered for trade types which occur away from the NBBO such as combo legs, block trades, and derivative trades"*, while Databento delivers full MBO per venue with no such filtering.

**So the replay answers "what would this have done on Databento's view", and the terminal answers "what does this do on IBKR's view."** That is the canonical defect of this document — a well-formed value answering a different question — arriving through the back door of a sensible cost decision.

**It cannot be eliminated, so it is measured.** The parity test in slice 017 changes purpose: **it was written to assert equality between live-captured and historical streams, and equality is now not expected.** It becomes a **measurement of divergence** — run the same component over the same session from both sources and record the difference, per component. Then:

- A component whose Databento-vs-IBKR divergence is **small relative to its effect size** validates honestly on replay.
- A component whose divergence is **the same order as its effect** cannot be validated this way at all, and must render `unvalidatable — source divergence exceeds effect` rather than borrowing confidence from a test that did not apply to it.

**Recording the divergence per component is the deliverable**, not a pass/fail. Without it, every replay-derived hit rate silently inherits an unmeasured error.

Limits: **1,000 ticks per request**, `TRADES`/`BID_ASK`/`MIDPOINT` only, *"data will not be returned from multiple trading sessions in a single request"*, and *"to complete a full second, more ticks may be returned than requested"* — so pages are not exactly 1,000 and the boundary second must be de-duplicated. **Last 3 years only**, L1 subscription required.

**The arithmetic.** A liquid US large cap prints on the order of 400,000 trades a session *(an estimate, not an IBKR figure)*. That is 400 requests per symbol, **12,000 for thirty symbols** — at 6 requests a minute, **≈33 hours.** Not an overnight job.

**The answer hinges on one undocumented point**: whether tick requests share the 60-per-10-minutes budget at all. If bounded only by the general ceiling, the same 12,000 requests take **≈3.3 hours**. **Test it directly — fire 70 tick requests in ten minutes on one symbol and watch for pacing error 420.**

#### It runs after hours, and that changes the verdict

**The job runs after the close, and with the eight-symbol cap (§8.2b) it fits.** The window from 16:00 ET to 04:00 is **twelve clean hours**; eight symbols is **≈8.9 hours** in the pessimistic case where tick requests share the historical budget, and **≈2.4 hours** if they do not. **Feasible either way, with margin in the worse case.**

**Pacing does not relax after hours — the limit is the API's, not the market's.** What after-hours actually buys is different and more important:

- **No contention with the live terminal.** Both share one pacing budget. A shadow pull running during the session would starve the attach path — or be starved by it — and neither would report why, because a pacing rejection looks like a slow request. **They must never overlap, and this is the reason.** *(Whether a separate client ID gets its own budget is **undocumented** — do not design around it; assume one shared budget until tested.)*
- **The session is closed, so the endpoint is fixed.** A full-session pull completes in one pass rather than chasing a moving end time, and the result is final rather than provisional.

**One operational constraint that will bite a nine-hour job: IB Gateway restarts daily.** An unattended pull spanning midnight ET **will be interrupted**. So the job must be **resumable**, checkpointing per symbol-day and per tick-page, and it must **treat a disconnection as expected rather than as a failure** — resuming from the last committed page instead of restarting the symbol. **A nine-hour job that cannot survive one restart is a job that never completes**, and it would fail quietly overnight where nobody is watching.

Until the pacing question is settled, keep **Databento on demand as the fallback** for the pass pile (§7.2) — it costs little at eight names a day and does not care about restarts.

#### Settle time — considered and rejected as the wrong unit

**The question:** should VWAP and the tape be required to run for *n* seconds before they display or compute? **Recommendation: no**, and the reason is that time is a proxy for the thing actually being asked about.

**Time and data diverge wildly.** Thirty seconds on NVDA is several thousand prints; thirty seconds on a $9 name at 11:40 may be four. **A fixed *n* is simultaneously far too long for one and far too short for the other**, which is exactly the defect §5b.2 catches in the detector windows — absolute constants that were tuned on one case and silently mean something different on the next. **Do not reintroduce it one layer up.**

Taking the three candidates in turn:

| | Does it need a settle? | Why |
|---|---|---|
| **VWAP and session-cumulatives** | **No — nothing to wait for.** They are reconstructed complete from the open at the instant of attach. A delay would withhold a finished value for no reason | above |
| **Tape components** | **Already handled, and by the right unit.** `tape_reader` requires `hold_baseline_min: 12` completed holds against a rolling `hold_baseline_n: 60`. **That is a count, and a count is correct** — 12 holds arrive in 30 seconds on a fast tape and ten minutes on a slow one, and the baseline is ready when it is ready | §5b.2 |
| **The subscription itself** | **Yes, and it is small and unrelated to the market.** `ibkr.py` already does `self.ib.sleep(1.0)` after account requests so the callback can populate. Same trap for market data: **~2 s, and it is about not reading an empty snapshot, not about the calculation being trustworthy** | — |

#### What to build instead: render the sample, not a timer

**The real question is never "has enough time passed", it is "is there enough behind this number" — so show that.**

```
VWAP 47.31  (1-min bars · pre-market incl. · from 04:00 · 18.4M sh)
```

That single line answers the trust question better than any delay could, and it answers it *differently for each symbol*, which a fixed *n* cannot. **A thin name showing `0.3M sh · 42 min` is telling you something a timer would have concealed by simply letting the value through.** Same lesson as a per-symbol median curve over a fitted one, and as range-relative detector windows over absolute ones: **measure the data, do not proxy it with the clock.**

#### The real risk on attach is the splice, and a delay does not fix it

Reconstructing from history and then continuing live creates a **seam** at the handover, and it fails in both directions:

- **Overlap** — prints present in both the historical pull and the live stream are **counted twice**, inflating cumulative volume and dragging VWAP toward whatever traded around the join.
- **Gap** — prints between the historical cutoff and the live subscription becoming active are **lost entirely**, and lost silently.

**Waiting *n* seconds makes the gap larger, not smaller.** The fix is ordering and identity:

1. **Subscribe live first and buffer**, then fetch history — never the reverse.
2. **Fetch history with an explicit end timestamp**, and discard buffered live ticks at or before it.
3. **Deduplicate the join on exchange timestamp plus sequence**, not on arrival order.
4. **Assert the seam in a test**: reconstruct a session at two different attach times and require identical cumulative volume and VWAP to the cent. A double-count or a gap shows up immediately, and nothing else will surface it.

**If the seam cannot be closed for a given symbol, the value renders `unavailable (splice unverified)` rather than a number that is quietly a little wrong.** A VWAP off by three cents does not look broken — it looks like a VWAP — and it is a stop level (§7b.2), so it becomes position size.

**Backfill on attach.** Window is **playbook-driven, default 3 minutes, anchored to confirmation (moment 2)** — not to the fill, and not to the session open. This is what lets confirmation-cutoff indicators (delta, speed, block activity, pre-trigger pullback shape) compute correctly on a mid-session attach.

Never backfill the whole session; tape older than the window is discarded, not reconstructed. Historical tick requests have **their own pacing budget and a 50-simultaneous cap — separate from the live 15-second cooldown, do not conflate.** Backfill failure degrades gracefully: the slot still attaches live, and the missing pre-attach window reads `unavailable`, never zero. Where an indicator needs the open (minute-one RVOL, `first_bar_strength`) and attach is later than open + window, serve from the nightly baseline or read `N/A` — **never silently zero.**

### 6b.1a-seq The attach sequence — what happens, in what order, and what renders when

**Attach does five things, and they are not one operation.** Writing the order down matters because three of them can fail independently, and each failure must leave the others working.

| # | Step | Blocking? | If it fails |
|---|---|---|---|
| 1 | **Resolve the contract** | **Yes** — nothing proceeds | Ambiguous ⇒ render the candidates and ask. **Never pick the most liquid** |
| 2 | **Check the tick slot** | No | Exhausted ⇒ render it **now**, before the fetches, naming what to detach. Cooldown ⇒ `queued · 11s` |
| 3 | **Dispatch three historical requests** | No | Per-row `unavailable (reason)`. Others still render |
| 4 | **Open the tick-by-tick subscription** | No | The context block is useful without a tape. **Attach succeeds; the pane says the tape is absent and why** |
| 5 | **Bind the playbook** | No | `no trigger level declared` — the pane knows nothing to watch |

**Step 2 comes before step 3 deliberately.** If there is no slot, you should learn that in the first frame — not after three historical requests have been spent against a 60-per-10-minutes budget on a symbol you are about to detach.

**Step 4 does not gate step 3, and this is the point of the whole ordering.** A symbol with no free tick slot still gives you ADR, ATR, extension, the level rail, both RVOLs and session VWAP — **everything the sizing panel needs.** The tape is an enrichment, not a precondition, and an attach that refuses wholesale because one of five slots was busy would be a worse terminal than one that says so and carries on.

#### What renders when

- **Immediately** — contract, slot state, and the tape's *raw prints* as they arrive. **The tape itself needs no baseline**: price, size, aggressor side and the timestamp are observations, and they render from the first print.
- **Within seconds** — the context block, each row independently as its request returns. No row waits for another.
- **After saturation** — components with a baseline. `tape_reader` needs `hold_baseline_min: 12` completed holds against a rolling 60. **Never FALSE**: a FALSE meaning "no baseline yet" is indistinguishable from "no absorption," and that is the worst available error.

#### Warming starts at 09:25, because the 1-minute ORB fires at 09:31:00

**A baseline that begins accumulating at the open cannot be ready for a trigger one minute later.** The 1-minute playbook arms at 09:30 and the break comes at 09:31:00; twelve completed holds will not have occurred. **So the subscription opens at 09:25 and the baseline warms through the pre-open**, and `attach_warm_at` is a declared config value, not an assumption in code.

**Render the projection, not just the count.** `warming 7/12 · ready ~09:29 at current rate` — because at 09:27 the question is not *"how far along is it"* but ***"will it be ready in time"***, and only the projection answers that. On a thin name the honest answer is sometimes no, and knowing that at 09:27 is worth considerably more than discovering it at 09:31.

**The baseline is pre-open-derived, and that is a different population — so it is labelled.** Prints between 09:25 and 09:30 are thinner and wider-spread than RTH prints, so a baseline saturated there describes pre-open behaviour and is then applied to the open. **It renders `baseline: pre-open 09:25–09:30`**, and a component whose baseline never re-saturated on RTH prints says so.

**It cannot be seeded from history instead, and the reason matters.** Everything else in this document is reconstructed from IBKR historical data — but the tape baseline is **compared against live prints**, and IBKR historical is filtered where the live stream is not (§6b.1b). **A baseline built from filtered history and measured against unfiltered live prints compares two bases**, which is the defect this document exists to catch. The baseline must accumulate from the same stream it will be judged against. **That is precisely why it needs the five minutes.**

#### Pre-warming under one-symbol-per-process

**Launch a symbol process per name you intend to trade, at 09:25.** Five tick slots is five processes — and the true count is nominal minus active price alarms, so it may be four.

**The allocation screen disappears** (§6b.1c): there is no *"which five of eight"* to render, because launching a process *is* the allocation and not launching one *is* the decision not to. **What survives is the consequence, and it is unchanged**: a name attached cold at 09:31 renders `warming 0/12` exactly when the trigger fires, plus the 15-second cooldown if it was previously attached. **In practice a name that was not pre-warmed cannot be traded on a 1-minute ORB** — a real limit on how many setups one morning can hold, not a UI detail.

**The risk process renders the count**, because it is the one that sees all of them: `4 of 5 tick slots held · CRDO NVDA AMD SMCI`. A symbol process cannot know this and should not guess.

#### The level state machine has two bases, and must say which

The claim states — `untested · claimed · lost · reclaimed` — start at attach for tick data. **But price crossed those levels before you attached, and pretending otherwise would be a lie of omission.**

So the machine is **reconstructed from historical bars back to the anchor, then runs tick-granular from attach**, and each state carries which basis produced it:

| Basis | What it can establish | What it cannot |
|---|---|---|
| **bar-reconstructed** (before attach) | That price traded through a level, and when | **Whether it was defended.** Defence is a prints-and-replenishment observation and bars do not carry it |
| **tick-live** (from attach) | Both | — |

**A level shows `claimed 09:41 (bar)` or `claimed 09:41 (tick)`, and they are not the same claim.** The first says price held above; the second says it held above *and* the tape showed it being held. **Absent that distinction the pane would present a weaker observation in a stronger one's clothes** — the defect this document exists to catch, arriving through a convenience.

**A level never reads `untested` when the truth is that nothing was watching.** Before the reconstruction window it renders `unknown before 04:00`.

#### Tape events append to a log. They do not alert

**Decided: a state transition writes a timestamped line into an in-pane event log, and nothing else happens.** No pop, no sound, no colour change, no push.

**An alert is a claim that this transition matters, and nothing has established that.** §4.1 removed verdicts because their cut points were never fitted; an alert is a verdict with a noise attached, and it would be the loudest unfounded thing on the screen. The pinned-row rule (§3.0a) already keeps the most recent transition visible without interrupting anything.

**And the log is the raw material for the only test that could ever justify an alert.** Every transition, timestamped, with its basis and the level, joined later against outcomes: *do level reclaims precede follow-through, or do they mostly precede nothing?* **Until that has an answer, a transition is something that happened, not something you should act on** — and the interface should say exactly that much and no more.

Format: `10:14:32  47.30  reclaimed (tick) · 3rd test · held 41s`. Appended, scrollable, **pinned to its last three lines** so the pane can scroll without hiding what just happened.

### 6b.1b Attaching a symbol that is not on the list

**Three ways a symbol reaches the pane, and only one was specified:**

| Source | Status |
|---|---|
| Selected from the ranked watchlist | Specified |
| **Typed in directly** — you saw it elsewhere and want a close look | **New. Nothing defined this** |
| **Pushed by another scanner or alert** — something popped and you want to inspect it | **New** |

The second and third are the same path with a different origin, and they matter because **they are how the fast path becomes the analytical path**: you spotted it in TradingView, you want the tape before you commit, and the terminal has no row for it.

**`/` opens a symbol field. Type, enter, attached.** No dialog, no confirmation, no requirement that it exist anywhere else in the system.

#### Every indicator comes from IBKR on demand — there is no local database

**Decided: the context block depends on no persisted local store.** ADR, ATR₁₄, extension from the 10/20/50 SMA, the level rail, RVOL and its sector comparison are all computed from `reqHistoricalData` at attach time, or requested directly. **Nothing is served from a nightly cache, because there is no nightly cache.**

**This is a simplification, not a cost.** The earlier design had a warm cache for watchlist names and a cold path for everything else — which meant two code paths, two failure modes, a nightly job to maintain, and a symbol that behaved differently depending on whether you had prepared for it. **With everything on demand, an ad-hoc symbol and a watchlist symbol are the same symbol**, and the `warming` state disappears for everything daily-derived. The only thing that genuinely still warms is the **tape baseline** (`hold_baseline_min: 12` completed holds), because that is about the live session and cannot be fetched.

**It also removes the worst failure this path had.** An ADR computed from whatever partial history happened to be in memory feeds the stop-width rule and therefore the size — the single most likely place for a fabricated number to reach a position. If the historical request fails, **the indicator renders `unavailable (reason)` and sizing refuses on that mode**. There is no half-populated cache to fall back on because there is no cache.

**What it costs, stated honestly.** IBKR paces historical requests at roughly 60 per 10 minutes, with a 15-second same-contract cooldown. Per attach: **one daily-bar request** (20–60 sessions — ADR, ATR, extension, the level rail) · **one intraday request** for the 20-session RVOL series · **one today-from-the-open request** for every session-cumulative value (session VWAP, cumulative volume, the volume profile, cumulative delta). **Three requests per symbol** — comfortable at the rate you attach, and each must render its own state: `fetching dailies…`, then the values, or `unavailable — pacing limit, retry in 42s`.

**One in-session memo is permitted and is not a database.** The sector ETF's 20-session series is identical for every name in that sector, so it is held in memory for the session rather than re-requested per symbol. **Nothing is written to disk, nothing survives a restart**, and that is the line: memoising within a run is not a local store, and if the process dies the next one fetches again.

#### What is honestly absent, and must render that way

An ad-hoc symbol still arrives with **no watchlist row, no grader vector and no pre-market context**. Each renders **`ABSENT` with its reason**, never a zero and never a neutral middle:

- **Grader:** `not graded — not on today's watchlist`. Not `UNGRADEABLE` — that word means a gate failed, and no gate was evaluated.
- **Sector:** if `contractDetails` resolves no sector, `RVOL_rel` renders `unavailable (no sector mapping)` — **never 1.0**, which would read as *"in line with its sector"* when the truth is that no sector was found.
- **Tape baselines:** `warming`, never `FALSE` — the existing rule, and it bites hardest here.

#### Two things that must not happen

**1. The contract must never be guessed.** `tws_order` already refuses this: *"Symbol resolved to 2 contracts — ambiguous, refusing to guess."* A typed symbol goes through the same qualification, and an ambiguous one **renders the candidates and asks**, rather than picking the most liquid and being right most of the time.

**2. An ad-hoc symbol is never written into the watchlist archive.** The archive is the sampling frame — *the population you selected from, frozen before you chose* (§8.2a). Injecting symbols you found mid-session would silently convert it into "everything I looked at", which is a different denominator, retroactively, for every statistic already computed against it. **This is precisely the defect that retired `watchlist_builder`.** Ad-hoc attaches are recorded in the **day record**, with their origin (`typed` · `scanner` · `alert`), and nowhere else.

#### It gives you the off-list flag for free

An ad-hoc attach is the moment the system learns a symbol is off-list — which is exactly the classification population ③ needs (§8.2a), captured at the time rather than reconstructed afterwards. It also creates a small fifth group worth keeping: **considered ad hoc, not taken.** Cheap to record, and the only evidence that will ever show whether your mid-session improvisations are worth the attention they cost.

**Replay consequence.** The post-close pull's symbol list becomes `watchlist ∪ traded ∪ ad_hoc_attached`, with ad-hoc-but-not-traded rows taking **bars, not tick** — the cheap tier, since the question about them is only *"what did it do after I passed"*.

### 6b.1c One symbol per process — the model, revised

**Revised decision: run one terminal process per attached symbol, each attached to exactly one ticker, and keep risk in exactly one place.** An earlier version of this section said *"one process, never several"* on the grounds that the market-data slot model is a ledger and a ledger with two writers is not a ledger. **That objection was correct about a variable allocation and does not survive a fixed one.**

#### Why the objection dissolves

The problem was never plurality. It was that **two processes could each believe they had three depth slots, and between them have three.** Constrain each process to **exactly one tick subscription, never more**, and the arithmetic becomes trivial rather than contended: *N* processes consume *N* slots, and the invariant holds by construction rather than by coordination. **The thing that made a ledger necessary was the variability, and one-per-process removes it.**

Three further costs also shrink to nothing:

- **Depth (3 concurrent) does not bite in core**, because the depth-dependent component — displayed-depth reliability — waits for slice 016.
- **Pre-warming stops being an allocation problem.** Launch five processes at 09:25. There is no *"which five of eight"* screen to design, no allocation state to render, and no decision that is implicit at 09:31 because it was never made at 09:25. **A whole subsystem disappears.**
- **Crash isolation arrives free.** One symbol's process dying takes one symbol with it.

And it is what you wanted from the layout anyway (§3.0a): **each process is its own console window, so Windows arranges them.** No window manager to build.

#### The one constraint that must come with it

**Risk, sizing and staging live in exactly one process, and symbol processes cannot perform them.**

This is not a preference. The daily and monthly loss limits are the only hard blocks in the system (§4.2), and they are **session-wide quantities**. **Five processes each independently evaluating "am I within the daily limit" could each answer yes and collectively breach it** — five times over, with every one of them correct in isolation. **The single guarantee this terminal makes about stopping you would be void.**

So:

| | Owns | May do | May not do |
|---|---|---|---|
| **Risk process** (exactly one, always) | account state, P&L, both limits, the ticket, staging | size, stage, enforce | attach a symbol |
| **Symbol process** (zero or more, one ticker each) | one tick subscription, its own historical fetches, its tape and context panes | render, observe | **size, stage, or evaluate a limit** |

**Enforced structurally, not by discipline** (§4.2a): the symbol process **does not import the sizing or staging modules at all**, and a test asserts it. `HARD_BLOCKS` is evaluated in one place because there is only one place that can evaluate it.

**A symbol may be attached in at most one process** — the 15-second same-symbol cooldown is a broker-side fact, and two processes racing on one ticker would produce a queue neither could explain. A lockfile keyed on symbol is enough.

#### What it costs, honestly

**More window-switching.** Read the tape in one window, size in another. On a large screen with Windows arranging them this is cheap; on a laptop it would not be.

**The day record fragments.** §2.2 assumes one record per session and `renderer(record)` pure. Now each symbol process writes `records/day/YYYY-MM-DD/<symbol>.json` and the risk process writes the session-level file. **The purity property survives per process**, which is what the snapshot tests actually need — but any analysis joining them must do so explicitly, and a session with a missing symbol file must read as *missing*, never as a session where that symbol was not attached.

#### The five-slot limit governs T&S only

**`reqTickByTickData` is what the five concurrent slots limit.** Historical bar requests do not consume one, and a `reqMktData` quote line is a third budget again (~100 lines).

**So a symbol process rendering context, VWAP and the stop table needs no tick slot at all.** The slot is required only by the **tape components**, which arrive in slice 012. **Before then — and for any symbol you are watching rather than reading the tape on — the five-process ceiling does not apply.** The binding constraint there is the historical pacing budget, which is a different number and a different failure.

**Stated plainly, because it changes what "five" means:** five is the limit on *how many symbols you can read the tape on simultaneously*, not on how many terminal windows you can have open.

#### The pacing budget is per account, and it breaks the refresh cadence as specified

**Confirmed: 60 requests per 10 minutes is per account, not per client ID.** Processes do not multiply the budget — **they divide it.** That is fine for attaches and fatal for the cumulative refresh as it was written.

**The arithmetic, and it does not work.** §6b.1b re-requests session VWAP, cumulative volume, the profile and delta **every 30 seconds per symbol** — 2 requests/minute each. Five symbol processes is **10 per minute, 100 per ten minutes.** The budget is 60. **That is 67 % over, and it would fail as pacing rejections that look like slow requests rather than as an error.**

**The fix is arithmetic, not coordination.** Choose a cadence that is safe **at the maximum process count**, so the budget is spent by construction and nothing has to be negotiated at runtime:

```
requests_per_10min  =  processes × (600 / cum_refresh_s)
```

| `cum_refresh_s` | 5 processes | Headroom against 60 |
|---|---|---|
| 30 | 100 | **−40, breaks** |
| 60 | 50 | 10 — everything else starves |
| **120** | **25** | **35 for attaches and ad-hoc** |

**Default `cum_refresh_s: 120`.** Three requests per attach means 35 spare covers eleven attaches in ten minutes, which is far more than a morning needs.

**Enforced at launch, once, by the one process that can count.** The risk process **refuses to start the Nth symbol process** when `N × (600 / cum_refresh_s)` would exceed the budget, and says so with the arithmetic. One check at launch beats permits handed out at runtime — and it is the *only* coordination the multi-process model needs.

#### Measured: `keepUpToDate=True` replaces the cadence — and the update semantics are the finding

**Verified 2026-08-10 (task 008b, AMZN, TWS 178, 12:34→13:06 ET, 32.03 min).** `reqHistoricalData(keepUpToDate=True)` **accepts `useRTH=False`, returns a 515-bar payload anchored at exactly 04:00, keeps that anchor as it grows, and ran 32 minutes with 376 updates, zero API errors and no dropped connection.**

**So `session_vwap_refresh_mode: keep_up_to_date` is the default and `cum_refresh_s: 120` becomes a documented fallback.** Two consequences:

- **The pacing arithmetic stops binding for session VWAP.** One open request per symbol against the 50-simultaneous cap, rather than a repeating request against 60-per-10-minutes.
- **Staleness drops from 120 s to ~5 s** — measured median 5.002 s, mean 5.106, min 4.196, max 14.477, about 11.4 updates a minute. **A 24× improvement on a value used as a stop level**, and it lands exactly where §6b.1b said it mattered: the first thirty minutes, where session VWAP moves fastest.
- **There is no seam.** The initial payload already reaches 04:00 and extends forward without sliding, so the anticipated "one historical request then `keepUpToDate` from there" join **does not exist and cannot be got wrong.**

#### The forming bar is revised in place, and getting this wrong has the worst possible failure signature

**344 of 376 updates restated the forming minute; 32 appended a new one. Zero were unclassifiable.** Mutated fields: `average` (which is `Bar.WAP`, the VWAP price source), `barCount`, `close`, `high`, `low`, `volume`. **`open` is not mutated**, correctly — a forming bar's open is fixed at its first print.

**So both terms of `Σ(WAP × volume)` change on every update. Any accumulator must replace the forming minute's contribution wholesale, never add to it.**

**The measured cost of adding instead, over 33 bars:**

| | correct (replace) | naive (add) | error |
|---|---:|---:|---:|
| VWAP | 277.451666 | 277.453806 | **+0.214 ¢** |
| volume | 796,911 | 4,730,374 | **5.94× — 3,933,463 phantom shares** |

**The asymmetry is the finding, and it inverts where the risk was assumed to be.** The repeated counts land at nearly the same price and very largely cancel, so **VWAP survives the bug at two tenths of a cent.** Volume does not cancel at all — it multiplies by roughly the update rate.

**This is the worst failure signature available: the number you would sanity-check stays plausible while the number you would not is six times wrong.** A VWAP that looks right is exactly what stops anyone examining the volume beside it.

**And the exposure is RVOL, which is worse than a denominator problem.** `RVOL(t)` divides *today's cumulative volume* by a 20-session median curve — **the inflated figure is the numerator**. A 5.94× overstatement does not render as an absurd number that invites suspicion; **it renders a quiet name at RVOL 0.8 as RVOL 4.8, which reads as a stock in play.** RVOL is a selection criterion, so the defect would not merely mislead a panel — **it would put names in front of you that nothing was happening in.**

**Retained as a `constraint:ibkr` with its note**, because it is broker semantics rather than a choice: *"under another broker, re-measure — append-only streaming would invert this rule entirely."*

#### The one claim still resting on an untested limit

**Five concurrent `keepUpToDate` streams on one account have not been tested.** IBKR limits *simultaneous open historical requests* (documented at 50) **separately from the request-rate budget**, and 008b probed one stream in one process. **The pacing conclusion holds for one symbol and is an inference for five.**

**Test it before the cadence is removed from a five-symbol console** — otherwise the failure arrives on a morning with five names attached, which is the morning it matters. Until then, **`cum_refresh_s` stays in config as a working fallback rather than as a comment.**

**The honest cost: VWAP is up to two minutes old, and that matters most exactly when it matters.** A session VWAP moves slowly by construction — by 10:00 it carries hours of volume and two minutes of prints barely shift it. **But its rate of change is highest in the first thirty minutes**, which is when the ORB playbooks trade. **So the as-of stamp is not decoration on this row**, and a VWAP-based stop staged at 09:34 against a value computed at 09:32 should show both times. Adaptive cadence — fast near the open, slow later — is the obvious refinement and is **deliberately not built yet**: it trades a fixed, checkable budget for a variable one, and the fixed version should be lived with first.

### 6b.1a The context block — what renders the moment a ticker is attached

Every field below already exists in code or in a Drive spec. Nothing here is invented. Rendered as **mockup-06**.

**Range budget** — `core/indicators/adr_move.py`, `adr_used.py`

| Field | Definition (verbatim from the module) | Note |
|---|---|---|
| `ADR%` | mean over N days of `(high/low − 1) × 100`, **excluding today** | Kullamägi convention, from his FAQ verbatim as a TC2000 formula. **NOT ATR — ignores gaps.** Default N=20. **RTH-only, because daily bars cannot be anything else** |
| ⚠ | **Do not cross-check against TradingView's built-in ADR or screener ADR%** | Those compute `(mean(H) − mean(L)) / close` over **14** days — a different estimator normalised once by today's close, where this one normalises each day by its own low. **The two disagree before session definitions are even in play.** Use a community script implementing `mean(H/L − 1)` over 20 ([example](https://www.tradingview.com/script/EfuMxaXm-ADR-20-Qullamagi-corner-value-v6/)) |
| `ADR $` | `ADR% × today's open / 100` | |
| `ADR used` | `(current − open) / ADR`, as a % with a 20-cell bar | `>100%` prints `OVER` |
| `room left` | distance to a full ADR, both directions | |
| Verdicts | `2x+ ADR from the open — abnormal (EP/catalyst territory)` · `full ADR consumed — chasing here buys range that's gone` · `quiet — under a quarter of the budget` | Ships in the module already |

**Extension** — `adr_move.py`, described in its own docstring as *"the extension read"*

Distance from the **10 / 20 / 50-day SMA in ADR units**, plus move from an anchor (`--from PRICE` / `--from-low N`). Rule of thumb carried in the module: *">3–4 ADR above the 10-day = extended; >10 ADR off a base low with no consolidation = the move already happened."* **These are preferences, labelled as such in config so nobody later reads them as fitted.**

**Gap and pre-market** — `live/ep_premarket.py`

`prior RTH close` · `20d ADR%` and its dollar equivalent · `50d avg volume` · `PM last` · `PM high / low` · **`gap` in % *and* in ADR units** (`2+ ADR gap → catalyst territory`) · **`PM range vs daily ADR budget`** as a % of ADR with a bar.

**Volume, three ways, never one** — same module:

- `[raw]` — pre-market volume as % of a normal full day. Assumption-free.
- `[naive]` — projected full day using a fixed multiplier. The module's own words: **`k=8, made-up constant`.**
- `[curve]` — projected using *this name's own* median pre-market/full-day ratio.

Plus the RVOL family of §8.4 with its basis in the displayed value: cumulative-to-now, at-time-of-day, opening-range 5-minute, and peer-normalised.

**Levels and claims** — `live/levels.py` (`ReferenceLevels`, `VolumeProfile`) + `live/marketstate.py`

Prior day H/L/C · pre-market H/L · overnight H/L · opening range H/L · session VWAP · anchored VWAP · swing highs/lows · 52-week H/L · gap edges · round numbers · 5-day volume profile.

**Moving averages carry a claim state, not just a price.** 9/20 EMA (5-min), 10/20/50 SMA (daily), each in one of four states — **`untested · claimed · lost · reclaimed`**, with the crossing timestamp and, where claimed, the defended-strength (a *prediction*, rendered `unfitted`). **The side toggle inverts which claims matter — a short wants the MA rejected from below, not claimed from above — but the rail itself does not flip.** Price structure is direction-agnostic; the interpretation is not.

All distances render in **ATR/ADR units, dollars secondary** — so a $4 biotech and a $300 mega-cap read identically.

### 6b.1b The session before the session — per ticker

Nightly / session-cached tier, **not live-on-attach**. `core/session.py` already models every phase correctly — `premarket_open=04:00`, `rth_close=16:00`, `postmarket_close=20:00`, half-day variants at 13:00/17:00, and a `Phase` enum. **Nothing consumes those phases for a ticker-level extended-hours read.**

| Window | Fields | Status |
|---|---|---|
| **Prior after-hours 16:00–20:00** | volume vs 50d · close-location in the AH range · **reaction verdict: bought · mixed · sold** · gap between AH close and today's PM open | **Not built.** Only two `LevelClaim` resolvers exist — `> Post market high/low` — which are prices, not a read |
| **Pre-market 04:00–09:30** | PM last · high/low · gap in % and ADR units · PM range as % of ADR budget · the three labelled volume projections | Built in `ep_premarket.py` |
| **Pre-market structure** | HH/HL sequence · candle quality · position in the PM range · volume by hour | **Not built.** Lives in the 15-min ORB tradebook as an 8-criteria rubric |
| **Overnight 20:00–04:00** | render only if the name traded | ~1,400 symbols, ~0.1% of volume. Usually **ABSENT** |

**Why the after-hours read matters most of the four.** Layer 0 row 11 asks the market-wide version — *"beats bought and held, mixed, or beats sold"* — and the spec calls it **"the highest-signal input and the one most likely to be skipped."** The per-ticker version is arguably more useful and does not exist. Your EP playbook depends on it directly (*"an EP without a known catalyst is not an EP"*), and your disqualifier list already contains *"prior after-hours sold beats"* as a score override. **The rule exists; nothing computes it.**

**The caveat that changes how a gap reads.** Pre-market is now **5.91% of total consolidated volume, up 111% year on year**, with over 30% of it trading before 07:00. On NYSE Arca, roughly **8 of 10 non-S&P-500 pre-market shares are retail-driven**, against 4 of 10 for S&P 500 names. **An 8% pre-market gap in a small or mid-cap is substantially a retail print.** That argues for weighting the `[curve]` volume projection above the gap percentage, and for a displayed caveat on non-S&P names.

### 6b.2 Detector inventory, mapped to the question being asked

Source: `live/detectors.py`. Rendered in `GROUP_ORDER`: `OPENING_RANGE · BREAKOUT · FAKEOUT · ALGO_TRAP · LEVEL_CLAIM · VOLUME`, each with a group score computed over **evaluable** members only, with exclusions counted so a score is never silently inflated.

**Reduced from 22 to 11 per `ORDER-FLOW-EVIDENCE.md` §4.5.** Twenty-two named detectors were measuring roughly nine quantities; rendering them as separate rows manufactured the appearance of independent confirmation from one input counted many times.

| # | Component | Kind | Absorbs | Grade |
|---|---|---|---|---|
| M1 | **prints-at-price + replenishment** | measurement | `PullbackDefending` `SizeReloading` `SizeAbsorption` | CONFIRMED (order-splitting long memory) |
| M2 | **displayed depth reliability** | measurement | `Spoofing` `NoLiquidityReloading` `PassiveIceberg` | measurable, validatable against own fills |
| M3 | **signed aggressive volume + error band** | measurement | `AggressiveLifting` `RedPrints` | CONFIRMED contemporaneous |
| M4 | **tape speed vs own baseline** | measurement | `SpeedAcceleration` `DeceleratingPace` | sound for regime, untested for direction |
| M5 | **touch imbalance — large-tick gated** | measurement | `BidStacking` `AsymmetricalBidStack` | CONFIRMED, tick-size conditional |
| M6 | **print-size distribution** | measurement | the salvaged part of `BlockOrders` | distribution only, never individual prints |
| E1 | **sweep / ISO proxy** | event | `CleanSweeps` `SweepInterception` | CONFIRMED phenomenon; validate first |
| E2 | **level claim state machine** | event | `LevelClaim` `FreshHighClaim` + MA claims | modest independent evidence |
| G1 | **relative volume family** | gate | `PhaseVolumeRatio` | CONFIRMED (−0.02R vs +0.08R) |
| G2 | **opening-range structure** | gate | `OpeningRangeRung` `AboveDayLowClaim` | CONTESTED — tested both ways |
| R1 | **spread state** | **relocated to regime** | `WideningSpread` | CONFIRMED (Glosten-Milgrom/Kyle) |

**Deleted:** `BlockOrders` (contradicted — medium trades carry the impact, and 64% of prints are odd lots) · `PassiveIceberg` (needs order IDs; hidden orders measured *less* informative than displayed) · `ImmediateContinuation` (same fact as M1 over a shorter window — double-counting).

**None of the eleven carries a directional score.** E2 is the state machine of §6b.1c.

### 6b.2a The level state machine

The thing the detectors currently fire about independently, made one object: *tested, held, tested, held, then broke or failed.* One record per level per session — playbook-scoped via `entry_construction.trigger_level`.

```
level_id · resolver · price · side · armed_at
  tests: [{t, prints_at_price, size_consumed, replenished, outcome}]
  state: untested | claimed | lost | reclaimed     (+ crossing timestamp)
  test_count · holds · broke_at · held_after_break
```

**The discriminant is prints, not size.** Size vanishing without prints at that price is a market maker repricing — the most common thing on screen and directionally meaningless. Size **repeatedly consumed and reappearing** is a participant working a parent order. M1 keys on the tape, which is consolidated and near-complete; the old `SizeReloading` keyed on the book, which is a minority sample.

Naming, so the log is unambiguous: `C1` hold on the bid (bullish) · `C2` hold on the offer (**bearish** — prints at the offer with the offer holding means sellers are absorbing buyers) · `C3/C4` hefty hold at ≥5× volume **and** ≥5× duration vs rolling median, `+` at ≥10× · `absorbed THROUGH` / `BOUGHT THROUGH` on the break.

Plus `live/tape/tape_reader.py` (C1–C11, 5-minute setup grader) and `rolling_flow.py` (Lee-Ready classified flow at 30 s / 60 s / 5 m / 15 m, with **z-scores suppressed *and withheld from the baseline* until the window saturates** — a 15-minute z sat at +1.7 for the first 15 minutes on a stationary synthetic tape, so warm-up is not cosmetic).

### 6b.3 Capability matrix — check this before wondering why a panel is blank

Feeds declare what they can measure; detectors declare what they need. A detector whose capability is absent renders **N/A with the reason**, never a false negative. `BOOK_FLOW` and `ORDER_ID` are deliberately separate — most "order flow" questions are *size at a price* questions that a level-depth delta answers directly, and collapsing the two would make IBKR report N/A for measurements it makes perfectly well.

| Capability | Databento MBO replay | IBKR live |
|---|---|---|
| `L1` best bid/offer | ✅ | ✅ |
| `L2` aggregated depth | ✅ | ✅ |
| `BOOK_FLOW` size change at a level | ✅ | ✅ |
| `ORDER_ID` per-order identity and lifetime | ✅ | ❌ |
| `TAS` time & sales | ✅ | ✅ |
| `AGGRESSOR` venue-supplied trade side | ✅ | ✅ |
| `MULTI_VENUE` consolidated tape | **per-slice** — see below | ✅ |

| Detector | Requires | Databento replay | IBKR live |
|---|---|---|---|
| `LevelClaim` · `FreshHighClaim` · `AboveDayLowClaim` · `PhaseVolumeRatio` · `OpeningRangeRung` | — | ✅ | ✅ |
| `AggressiveLifting` · `SizeAbsorption` · `SpeedAcceleration` · `ImmediateContinuation` · `BlockOrders` · `RedPrints` · `DeceleratingPace` | `TAS` | ✅ | ✅ |
| `NoLiquidityReloading` · `PullbackDefending` · `BidStacking` · `SizeReloading` | `BOOK_FLOW` | ✅ | ✅ |
| `WideningSpread` | `L1` | ✅ | ✅ |
| `PassiveIceberg` | `L1` + `TAS` | ✅ | ✅ |
| `CleanSweeps` | `L2` + `TAS` | ✅ | ✅ |
| `AsymmetricalBidStack` | `L2` | ✅ | ✅ |
| **`Spoofing`** | `BOOK_FLOW` | ✅ full | **⚠ degraded** |
| **`SweepInterception`** | `TAS` + `MULTI_VENUE` | **❌ N/A** | ✅ |

**`MULTI_VENUE` on Databento is a property of the slice, not of the vendor.** `feeds.py` declares `DatabentoReplayFeed.capabilities` as a **class attribute** while `IBKRFeed` sets `self.capabilities` per instance — so the replay adapter can never report multi-venue even when replaying a merged slice. **That is a defect, not a fact.** `selection/phase3/ticks/` already holds `trades_{XNAS,XNYS,ARCX,BATS,XASE}` across 245 dates. **Fix: derive capability from the data** (count distinct `publisher_id`), and merge venue streams on **`ts_recv`, never `ts_event`** — venue matching-engine clocks differ, `ts_recv` is NY4 capture time and monotonic per symbol, and Databento's own consolidated-BBO example merges on exactly that key.

**Two asymmetries worth internalising.**

`Spoofing` runs on IBKR but marks itself **degraded**, because without per-order identity it infers the shape from size leaving a level with no prints at that price. That is a real observation, but it cannot separate one large order from several small ones, cannot see a pull-and-repost that nets out inside one coalesced update, and **will read a repricing market maker as a pull.** Rendered `TRUE~` in yellow with the reason on its own line.

`SweepInterception` is the mirror: it needs the consolidated tape, so it works live on IBKR and is **unavailable in Databento single-venue replay**. Consequence for slice 018 — *that detector cannot be validated by replay*, and any backtest claiming to have exercised it is claiming something false.

### 6b.4 Measurement versus inference — the boundary that must render differently

The detectors measure. Several of the readings you want are **claims**, and per Tenet 3 they carry a fit status and must not render at the same visual weight as a rule.

| Reading | Kind | Status |
|---|---|---|
| Cumulative delta, tape speed, print-size distribution, book depth at level | **Indicator** — a measurement | Needs no validation. Carries its basis. |
| Aggressor side | **Indicator, but the gate for everything else** | `lee_ready` where quotes exist, `tick_rule` fallback otherwise — **the method is declared.** The fallback misclassifies precisely on fast one-sided tape, i.e. the moments that matter. |
| **Absorption** | **Prediction** | The measurement is signed volume against price response over a window. *"Absorption"* is the interpretation. |
| **Defended level strength** | **Prediction — a structured signal** | A list of price zones, each with a strength and which side defended it. Each zone's strength is a claim that can be wrong. **An inferred defended level must not masquerade as a raw fact.** |
| Setup grade A+/A/B/C from `tape_reader.py` | **Prediction, uncalibrated** | Cuts were set on **three synthetic tapes only**. An A+ currently means the components agree, not that it works. |

Recalibration procedure for the grader, when there is finally an outcome log: log with `--grade-log`, compute forward MFE/MAE at 15 and 30 minutes, bucket by grade, and **test the ordering first**. If the ordering is flat the *weights* are wrong, not the thresholds. **Never change weights and thresholds in the same pass** — you learn nothing from a move you cannot attribute.

### 6b.5 Refusal states specific to this surface

Beyond the general grammar in §4:

- **Detached symbol renders `STALE`**, not frozen-looking-live. The old symbol's last values are still true; they are just no longer now.
- **Slot exhaustion** is a named state with the current count and what to detach.
- **Re-attach inside 15 s** is queued and says so.
- **Backfill gap** reads `unavailable` for the pre-attach window, and the indicators depending on it read `N/A`, not zero.
- **Every panel carries its age**; past its budget it degrades to not-ready rather than showing a stale number that looks live.
- **Throttle frames, never events.** Every print enters delta, RVOL and print distribution losslessly. Display coalesces at ~250 ms (price/levels), ~500 ms (tape metrics), 1 s (RVOL/velocity); the record does not. *Dropping trades corrupts asymmetrically — the fastest tape drops most, exactly when the number matters.*
- **Hysteresis at display only.** A rule oscillating at 1.99 / 2.01 ATR makes the panel unreadable, so apply a dwell — but the evaluation and the record stay unthrottled, or a display convenience silently changes a rule's semantics.

---

## 7. Data and vendors

### 7.1 What exists at zero marginal cost

| Store | Size | Coverage |
|---|---|---|
| `cache/1min/` | 57 MB | **SPY/QQQ/IWM 1-minute, 2021-08 → 2026-08**, 1,254 sessions each |
| `selection/phase3/ticks/` | 956 MB | trades + imbalance, 5 venues, **245 dates 2024-08 → 2025-07** |
| `selection/phase3/statistics/` | 146 MB | same window |
| `replay/AMZN-2026-08-03-open.json` | 316 MB | 1.07M MBO records, **one name, one venue, 23 minutes** |

Five years of index minute bars support **all Layer 0/1 validation at zero cost** — ~1,250 observations, one per session, with no selection effect. That is the cheapest honest validation available anywhere in this project.

### 7.2 Databento — traded tickers only, per-byte

**Decision: no subscription. Pull the symbol-days you actually traded, after the fact.** This was v1.0's open decision 3 and it is closed — Standard at $199/mo bought a universe-wide corpus to support research that is not what this system does first.

**Why the cheap version is also the better one.** The replay harness exists to answer *"what did the tape look like on the trades I took?"* — which needs one symbol × one session per trade, not 24,000 symbols × 8 years. At ~20 trades a month that is a few dozen symbol-days: a fraction of the subscription, and it lands you in **exactly the sample that matters**, because a detector's hit rate against forward excursion (§12.5) is only measurable where you have both the tape and the outcome.

It also removes the selection problem the subscription would have created. A universe-wide corpus invites searching it for setups, which is Phase 3, which is halted. A traded-tickers-only pull **cannot be searched for an edge** — it contains only trades that already happened. The constraint is a feature.

**What it costs.** `tbbo` for one liquid symbol-day is small; MBO for one symbol-day is the expensive schema and is only needed where a playbook hinges on book reconstruction. `harness/spend.py`'s reserve-then-close ledger already maps: `get_cost` is the reserve, delivered bytes are the close. **Call `get_cost` before every pull and log the delta** — a persistent gap means the query shape is not what you think it is.

#### The post-close pull is cost-gated and unattended

**Not a prompt on exit.** Exiting is the worst available moment to ask — you are leaving, the day is over, and a dialog on quit gets dismissed reflexively. **It is a scheduled job after the close**, in the same shape as the pre-market regime read: the session ends, the day record is complete, the job runs, and whatever it decides is waiting on the terminal next morning when you can read it with a clear head.

**Step 1 — build the symbol-day list. It is not just the watchlist.**

```
symbol_days = watchlist(today) ∪ traded(today) ∪ ad_hoc_attached(today)
```

The union matters. Off-watchlist trades (population ③, §8.2a) are by definition absent from the list, and they are **precisely the ones you cannot reconstruct later** — an improvised trade with no tape pulled is unmeasurable forever. The watchlist half serves population ② (the pass pile); the traded half serves ① and ③.

**Step 1a — resolve the schema per symbol, and do not pull tick data for anything that does not need it.**

**Granularity follows the playbook, and the playbook already declares it.** A flag breakout on the daily chart is answered by daily bars. A 5-minute ORB is answered by minute bars. Only the components that read the tape need the tape. Pulling `tbbo` uniformly across the list buys tick data to answer questions that bars already answer, at a large multiple of the price.

**The default is a flat two-tier rule, and it is deliberately simple:**

```
traded today      →  tick data   (tbbo; mbo only where a book component is on trial)
watchlist only    →  OHLC bars   at the playbook's timeframe
```

**Predictable beats optimal here.** You can state this rule from memory, which means you can predict the bill before the job runs — and a cost gate you cannot predict gets ignored.

**The capability-derived schema below is an optimisation on top, and it may only make a pull cheaper, never more expensive.** If a traded symbol's playbook selected no tape components at all, its tick pull downgrades to bars. Nothing in the derivation can upgrade a watchlist row to tick.

**The derivation uses two fields that already exist:**

```
schema(symbol_day) = coarsest schema that satisfies
                     ∪ requires  over the playbook's selected components
```

Every detector already carries `requires: Set[Capability]` (§6b.3). If no selected component requires `TAS`, there is no reason to buy trades. If none requires `BOOK_FLOW`, there is no reason to buy MBO. **A new config knob here would be a second source of truth for something the capability declarations already answer** — and the two would drift.

| What the playbook's components need | Schema | Relative cost |
|---|---|---|
| Daily structure only — flag / base / trend template on the daily | `ohlcv-1d` | negligible |
| 5-min ORB, no tape components | `ohlcv-1m` | very low |
| 1-min ORB, level and volume gates | `ohlcv-1s` or `tbbo` | low |
| Tape components — M1, M3, M4, M5, M6, E1 | `tbbo` | moderate |
| Book components — M2 displayed-depth reliability, replenishment | `mbo` / `mbp-10` | **high, and the only expensive case** |

**Pull the finest granularity actually required, once, and aggregate upward.** Never pull 1-minute and 5-minute separately — 5-minute bars are a `resample` away and buying both is paying twice for the same information in two shapes, which is also how two series with one name end up disagreeing.

**Two consequences that change the economics.**

1. **The pass pile is nearly free.** Population ② asks *"did it trigger and follow through"* — bars answer that for most playbooks. So the expensive tape schema collapses onto the traded symbols whose playbooks actually used tape components, which is a small number per day rather than the whole watchlist.
2. **Where bars suffice, IBKR may cover it at zero cost** and Databento is not needed for that symbol at all. This is the same question as open decision 6 (§11), one granularity coarser and therefore much easier to satisfy.

**Coarser data is honest degradation, not a silent downgrade.** If a symbol-day was pulled as bars and a component requiring `TAS` is later run against it, that component renders **N/A with its reason** and the verdict **inherits the weakest input's status** (Tenet 3) — exactly as a live feed lacking a capability does today. **The stored symbol-day carries the schema it was pulled at**, so a later reader cannot mistake a bar-derived verdict for a tape-derived one. Re-pulling finer later is always possible; discovering afterwards that you compared two different bases is not recoverable.

**Step 2 — price it before pulling.** `metadata.get_cost` returns an estimate for the exact query. This is already the reserve half of `harness/spend.py`'s reserve-then-close ledger; here the reserve becomes **the gate**, not just a log line.

**Step 3 — two thresholds, both declared, and the rolling one is the real protection.**

```yaml
# config/data_budget.yaml
per_run_usd:        5.00     # under this, pull without asking
rolling_30d_usd:   50.00     # hard ceiling on the month — never auto-exceeded
overrun_alert_pct: 20        # estimate vs delivered, beyond which it is a finding
```

**A per-run threshold alone is not a budget.** `$5.00` silently spends `$100` a month at 20 sessions. The rolling cap is what actually bounds the spend, and **a run is auto-approved only if it passes both** — under the per-run threshold *and* leaving the 30-day cap intact.

**Step 4 — under both thresholds, it pulls. But silent means unattended, not invisible.**

The next morning the terminal renders one line: `replay data · 31 symbol-days · $2.14 · month-to-date $18.60 of $50.00`. An unattended process that spends money with no surface is the "correct warning sitting in a file nobody opens" failure with a credit card attached. **It runs without asking; it never runs without telling.**

**Step 5 — over either threshold, it stages a decision and pulls nothing.**

Consistent with §4.2 — surfaced, not refused. The morning panel shows the estimate, **the five most expensive symbols by cost** (a spike is almost always one illiquid name with an enormous MBO day, or an unusually long watchlist, and naming them makes the call a one-glance decision), and three options: pull everything · **pull traded symbol-days only** — the cheap subset that keeps ① and ③ measurable and sacrifices only the pass pile — · skip today. **Whichever you choose is recorded**, so the log eventually shows what a skipped day cost you in measurability.

**Step 6 — reconcile the estimate against delivered bytes.** `get_cost` is the reserve; delivered bytes are the close. **An overrun beyond `overrun_alert_pct` is a finding, not a rounding error** — it means the query shape is not what you think it is, and that same misunderstanding is in every pull you have already made.

#### Source: Databento now, an IBKR decision layer later

**Where IBKR provides the data free, it is always preferable** — a bar is a bar, and paying for one you already have access to is pure waste. But **source selection is not in core.** Core pulls from Databento, one source, one code path.

The reason is that a decision layer is where the subtle defects live: two sources define a session differently, timestamp differently, adjust for splits differently, and a series stitched from both without declaring which segment came from where is *the* canonical defect in this document. **One source, then a layer that can be tested against it** is the safe order — with Databento as the reference precisely because it is the one that costs money and therefore gets checked.

**The later layer** routes per (symbol-day, schema): IBKR where it is free and sufficient, Databento otherwise. **Its acceptance test is parity** — pull the same symbol-day from both, compare bar-for-bar, and require agreement or an explained difference. **Every stored symbol-day carries its source**, so a mixed series can always be decomposed. §12.9.

**Purchase order:**
1. **$0** — spend the free credits on `metadata.list_unit_prices` for every equity dataset and **cache the rate table in the repo**. Then one week of `XNAS.ITCH` mbo for a single name to validate the replay engine end to end.
2. **Per session, ongoing** — the post-close job, at the schema each symbol-day's playbook actually requires. Most rows are bars; `tbbo` only where tape components were selected. Cheap enough to be automatic under the thresholds above.
3. **On demand** — MBO only for the specific symbol-days where a book-dependent component is on trial. This is the one expensive schema and it should never be the default for anything.
4. **Only for a validated edge, $1,500/mo Plus** — this is what buys live Nasdaq TotalView MBO and live NYSE/Arca/American imbalance. Live NOII is the best predictor of the Nasdaq open and there is no cheaper source. **Buy it to execute an edge, never to find one.**
5. **Defer indefinitely — Adjustment Factors ($225/mo).** Intraday momentum on unadjusted same-day prices doesn't need it; flag split-affected symbol-days from a free source and refuse them rather than paying to patch them.

~~**Verify before subscribing:** whether `imbalance` is bundled under L0 or L3.~~ **Moot** — no subscription, and Layer 0 is no longer in the terminal (§5.1).

#### The base rate is not lost — it just does not come from Databento

An earlier draft of this section said traded-tickers-only forfeits the base rate. **That is wrong, and the reason is that the ORB is mechanically defined.** An opening range has a high and a low; price either takes it or does not; the forward excursion from that level is arithmetic. **None of that needs tape.** It needs minute bars, over the names that were candidates — and the archived watchlist says exactly which names those were, every session, in git.

So the sampling frame already exists and the data is free:

| Question | Sample | Source | Cost |
|---|---|---|---|
| **Did it trigger? Did it follow through? What was the excursion?** | **Every name on the archived watchlist**, taken or not | IBKR historical minute bars, pulled overnight | **$0** |
| Did the book replenish, was volume signed against you, was it a sweep (M1–M6, E1–E2) | Traded symbol-days only | Databento `tbbo` / `mbo` | per-byte |

**The split is: bars answer "what happened", tape answers "why".** The first is where the base rate lives and it is free. The second is only interpretable where you also have the outcome — which is the trades you took.

**This makes the watchlist archive load-bearing in a way slice 009 did not anticipate.** It stops being a provenance record and becomes **a sampling frame**: the population you selected from, frozen before you chose, in commit order. It is *one* of four populations, never the only one — §8.2a defines all four and forbids pooling them. That is a genuinely rare thing to have — most retail post-hoc analysis reconstructs the candidate set after the fact and inherits every hindsight bias in the reconstruction. **Because the drop folder is unversioned and only clean drops are committed, git history records universes actually traded rather than everything ever dropped** — which is precisely what a base rate requires.

**State the conditioning honestly, because it is still there.** The base rate is *conditional on your watchlist*, not on all US equities — it answers "of the names I put in front of myself, how do ORBs behave", which is the question that matters and is not the same as the universal one. Tape statistics carry the tighter condition: `on trades taken, n=43`. **Two different denominators, and they must never be printed in the same table without their labels.**

**Four Databento facts that change the code:**

- **`tbbo` is the correct backtest primitive** — every trade with the pre-trade BBO already joined, removing the trade-classification inference step entirely.
- **Order and gate on `ts_recv`, not `ts_event`.** `ts_event` is when the venue's engine acted; you could not have known then. `ts_recv` is monotonic per symbol and is the earliest instant the information physically existed at NY4. Merging venues on `ts_event` is a subtle lookahead. Databento's own consolidated-BBO example merges on `ts_recv`.
- **Evaluate indicators on `F_LAST`**, not per record, or you compute on torn intermediate book states. Refuse the session on `F_MAYBE_BAD_BOOK`; refuse the row on `F_BAD_TS_RECV`. Treat `F_SNAPSHOT` as state init, never as a market event.
- **`trades` on a direct venue feed carries no condition column, and that is correct rather than missing.** ITCH separates message *types* — `P` non-cross, `Q` cross (carrying the cross-type), `B` broken — so a record reaching Databento's `trades` schema from a single-venue delivery is a **regular on-book trade by construction**. Absence is a positive statement here, not a gap. Auction identification never depended on a code: `auction_anchoring.verification` was **DISCHARGED 2026-08-08 at 133/133** via price/size matching against the imbalance stream.
  **The narrow caveat that does survive:** *consolidated*-volume eligibility (CTS/UTP sale conditions for late, out-of-sequence, derivatively-priced and odd-lot-ineligible prints) is a property of consolidated products, not of your single-venue slices. If you ever compare a summed `trades` figure against a consolidated one, make it carry its basis — `volume@xnas_prints`, never `volume` — or use `EQUS.SUMMARY` `statistics`.
  ⚠️ **`core/config/condition_codes.yaml` still carries a banner asserting the opposite** and `handoff/inbox/condition-codes-config-is-unverified.md` is still `PARTIALLY_CONSUMED` with the rewrite owed. Fix in slice 008 — a config file that misleads the next reader is the failure mode the handoff convention exists to prevent.

**Also:** raw symbol conventions differ per dataset (`BRK.B` on Nasdaq vs `BRK B` CMS elsewhere) — a mismatched request silently resolves to nothing. `instrument_id` is **remapped daily**; never key a cross-day store on it. Use **batch, not streaming**, for anything that becomes a repo artifact (streaming re-bills every run; batch bills once and re-downloads free for 30 days).

`harness/spend.py`'s reserve-then-close ledger maps exactly: **`get_cost` is the reserve, delivered bytes are the close.** Log the delta — a persistent gap means your query shape isn't what you think it is.

### 7.3 IBKR — the constraints that shape the screen

- **Market data lines: 100 default.** Tick-by-tick capped at **5% of lines → 5 concurrent tape slots** base, +5 per booster pack. **Each price alarm consumes a line** — surface the *true* available slot count, not the nominal 5.
- **`reqMktDepth` capped at 3 concurrent below 400 lines.** A watchlist-wide L2 view is not purchasable at retail scale. Design around three depth slots.
- **15-second same-symbol tick-by-tick cooldown.** Historical tick requests have a separate budget and a 50-simultaneous cap — do not conflate.
- **`reqMktData` is 250 ms aggregated snapshots, not ticks.** Any indicator whose semantics depend on tick sequence (tape speed, print-size distribution) computes a *different quantity* from `reqMktData` than from `reqTickByTickData`. The basis must travel with the value.
- **`permId` is the only stable order identity** across sessions and clients; `orderId` is client-scoped and may not be unique to an account. **Key order records on `permId`.**
- **Corrections arrive as an extra `execDetails` with an identical `execId` except the digits after the final period.** Dedupe on the prefix, keep the highest suffix, or you double-count corrected fills.
- **`commissionReport` arrives separately.** Commission-pending is a distinct state, not zero commission.
- **`reqGlobalCancel` cancels everything including protective children you did not place.** The kill switch cancels *entries*; "flatten everything" is a separate, differently-shaped action with its own confirmation. Connect as clientId 0 with `reqAutoOpenOrders(True)` so manual TWS orders are visible.
- **`transmit=False` orders live only in that TWS session and are cleared on restart.** So the staged order is a record in *your* store with its own identity and hash; the `transmit=False` submission is an optional pre-flight proving TWS accepted the parameters. **Reconcile the TWS untransmitted set against your store on every reconnect and display the delta.**
- **Order presets are hidden global state** — a preset with an attached stop turns your single order into a bracket you never wrote. Send every order fully specified and compare the `openOrder` echo field-by-field. Never tick "Bypass Order Precautions for API Orders".

Cost: US Securities Snapshot bundle $10 (waived at $30 commissions) + three network L1 feeds at $1.50 ≈ **$14.50/mo**, largely waivable. Nasdaq TotalView L2 +$16.50.

---

## 7b. Order and risk management — the layer where risk is actually managed

Rendered as **mockup-07**. This is not the sizing calculator of the original §12; it is the surface where the account, the invalidation, the regime and the plan meet before anything is staged.

### 7b.1 ~~Risk comes from the account, not the chart~~ Risk comes from config, not from the account

> **REVERSED 2026-08-14 under `039`, by Christoph's ruling, stated twice.** Everything from *"Where `risk_pct` lives"* down to the end of this subsection is the **superseded** argument for percentage-of-NLV sizing. It is kept rather than deleted for the reason this document keeps giving: a reader who remembers the old rule must be able to see that it *changed*, not wonder which of two statements is current. **Where the struck text and the text below disagree, the text below is current.**

```
1R  = risk_usd_per_trade                 declared in config/risk.yaml. Does not move with NLV.
```

~~`1R = risk_pct × NetLiquidation`, risk_pct default 0.50%, cap 2.00%~~

**The ruling.** *"`1R` is a fixed dollar amount declared in config. It does not move with NLV."*

**The rationale, recorded because it is not obvious and because §7b.1 below argues the opposite well.** A risk figure that tracks the account grows position size on a good run and shrinks it on a bad one, **automatically and invisibly**. Christoph wants that behaviour to come later from an explicit rules engine keyed to *sequences of days won and lost* — not from a number that drifts every time the account marks to market. `c015` §Risk 3: *"Risk should not change daily. It should change after N days won, and get reduced when Y days lost in sequence."* **That engine is a requirement for a later version, not core.**

**So the disagreement is not about whether drift happens — the struck text is right that it does, and right that it compounds. It is about whether drift should be a side effect of marking to market or an explicit decision.** `039` makes it explicit and defers the decision.

`risk_pct_default` and `risk_pct_cap` are **removed from the sizing path** and are absent from `config/risk.yaml` rather than present and ignored. If a percentage-of-NLV sanity check is ever retained anywhere, **it warns and never sizes.**

**`tws_order/sizing.py` is NOT changed by this and must not be.** It enforces NLV-based sizing today — `risk_pct ≤ 0` is a hard `ConfigError`, the cap warns rather than silently clamping, the account is never guessed — and that behaviour is correct and tested. It is a separate repository by standing decision. **The terminal must not compute share counts independently: two sizing implementations that disagree is worse than either being wrong.** What an absolute-risk mode there requires is reported in `handoff/done/039-risk-and-trade-classification.md` and is not built here.

**NLV, never buying power** — this is already enforced in `tws_order/sizing.py`. `risk_pct ≤ 0` is a hard `ConfigError`; the cap warns rather than silently clamping; the account is never guessed.

#### Where `risk_pct` lives, and where you see it

**Config is the default; the ticket is the decision; the record is the truth.** One file, one panel line, one recorded field:

```yaml
# config/risk.yaml — the only place these numbers are declared
risk_pct_default:   0.40     # % of NLV risked per trade — THE declaration
risk_pct_cap:       2.00     # % of NLV — hard ceiling on any single trade
risk_pct_cap:       2.00     # ticket refuses to accept a larger value
daily_loss_usd:     2000     # US dollars — HARD BLOCK (§4.2)
monthly_loss_usd:   5000     # US dollars — HARD BLOCK, rolling calendar month
open_risk_cap_R:    3.0      # rule, enforcement: warn
concentration_cap:  2        # rule, enforcement: warn — same sector/theme, same direction
```

Everything here is a **named parameter carrying its source string**, like every other threshold in the system. `risk_pct_default` is your preference and is labelled `source: christoph_preference`, not `fitted`.

**Every value in that file renders blue on screen** (§4.1) — it is a declared parameter, a fact about your own config, and blue says exactly that and nothing about the market.

**Risk is declared as a percentage of NLV, and NLV is read live from IBKR — never configured.**

```
1R  =  risk_pct_default × NetLiquidation      NLV from reqAccountSummary
```

**The percentage is the declaration precisely because it must move with the account.** Position size compounds as the account grows and contracts as it shrinks, automatically, with nothing to re-tune. **A fixed dollar risk would be the defect** — the same $500 on a doubled account is a steadily smaller position in real terms, and on a halved one it is twice the exposure. **Drift here is not a problem to warn about; drift is the entire function.**

**Set the initial value so 1R lands near $500** — a starting size, not a primitive:

| NLV | `risk_pct_default` for ≈ $500 |
|---|---|
| $100,000 | 0.50 % |
| $125,000 | **0.40 %** |
| $150,000 | 0.33 % |
| $200,000 | 0.25 % |

*Pick from your actual NLV; the $124,300 in the examples is illustrative. Once set it does not need revisiting as the account moves — that is the point.*

**The dollar figure is the readout**: `0.40 % × NLV 124,300 = 1R $497`. The percentage is what you declared; the dollars are what it means today.

**`risk_pct_cap: 2.00` is the hard ceiling on any single trade**, applied to the per-ticket override. `tws_order/config.py` already implements `clamp_risk_pct` and already warns rather than clamping silently.

**One inconsistency to be aware of, because it will bite quietly.** Risk is a percentage and the loss limits are dollars, so **they scale differently.** At $497 per trade the $2,000 daily limit is four losses; if the account doubles, 1R becomes ~$1,000 and the same $2,000 is **two**. The limits tighten in trade-count terms without anyone changing them. That may be exactly right — a fixed tolerance for real money lost, regardless of account size — or exactly wrong, and it is not obvious which. **It is why both limit rows render headroom in losses rather than only dollars**, so the tightening is visible as it happens rather than discovered on a bad day. Revisit when the account has moved materially.

**NLV is read once at session start and frozen, with the live value shown beside it.** Same pattern as the 05:00 snapshot, for the same reason: **if NLV re-read continuously, position size would shrink as the day's losses accumulated** — defensible as anti-martingale, but the number would move under you mid-session and two trades an hour apart would be sized against different accounts with no record of why. Frozen at start, stamped, with `live −$1,240` beside it. **If IBKR is unreachable, sizing refuses rather than falling back to a remembered value** — `tws_order/config.py` already raises `ConfigError` with *"No account resolved. Refusing to guess."*

**It renders as a full line on the sizing panel (mockup-07), always, never collapsed into the size:**

```
RISK   0.40 % × NLV 124,300 (IBKR · frozen 08:12 · live −$1,240) = 1R $497   [edit] cap 2.00 %
DAY    used  −$746   limit  −$2,000    headroom −$1,254   (2.5 of 4 losses left)
MONTH  used −$2,310  limit  −$5,000    headroom −$2,690   (5.4 of 10 losses left)
```

**Both limit rows render headroom in *losing trades*, not only dollars.** `−$2,690` reads as a lot of room; `5.4 losses left` reads as what it is. The count is the quantity you actually reason with when deciding whether to take the next one, and it is the one the dollars hide.

**The limits are declared in US dollars.** Both of them. Dollars are unambiguous at the moment the limit bites, they do not drift when `risk_pct` or the account changes, and they are the unit you actually think in when you are down. **R is shown alongside, computed from dollars — never the other way round**, and it is parenthesised to make clear which is the declaration and which is the derivation. Deriving the limits *from* R is a possible later refinement, not a starting point.

*(An earlier draft declared these in R and rendered `limit −2.0R −$2,486` from a 2%-of-NLV figure — which was wrong by a factor of two, since $2,486 is 4.0R at 0.50% risk. The two units were displayed side by side as though they agreed. Declaring one unit and computing the other removes the class of error, whichever unit is chosen.)*

**A rolling-month limit is new, and it is a second blocking rule.** `HARD_BLOCKS` was built with exactly one member so that a second would be a visible one-line diff in a named constant (§4.2) — this is that diff, made deliberately rather than arriving quietly:

```python
HARD_BLOCKS = frozenset({"daily_loss_breached", "monthly_loss_breached"})
```

The monthly limit is the one that matters more and fires far less often. A daily limit stops a bad morning; **a monthly limit stops a bad month, which is the failure mode that actually ends accounts** — six ordinary red days in a row never trip a daily limit once.

The `[edit]` is the per-trade override. It is bounded by `risk_pct_cap`, it takes a keystroke, and **the value actually used is written into the pre-registration record** (§7b.3) alongside the default it deviated from. That last part is what makes it worth having: sizing down on a day that feels wrong is a decision the log can eventually evaluate, whereas a dial that sizes for you leaves no record of what you would have chosen (§12.2).

**The day row is red at breach and it is the one row that stops something** (§4.2). It renders from the first trade of the session, not from the moment it matters.

**The regime dial is removed (§4.1).** v1.0 had `L0 × L1 → cell → fraction of 1R`, defaulting down with Layer 0 `NOT BUILT`. With Layer 0 out of the terminal the grid has one axis, and that axis's cut points were never fitted — the dial would be a nine-cell table producing a multiplier from an unvalidated classification of an unvalidated input. **1R is `risk_pct × NetLiquidation`, full stop.** Nothing between the account and the size.

**Where the discretion goes instead:** `risk_pct` is a field on the ticket, defaulted from config, editable per trade, and **the value used is recorded in the pre-registration** (§7b.3). Sizing down on a day that feels wrong is a decision you make and the log captures — which is also the only way the question ever becomes answerable, since a dial that sizes for you leaves no record of what you would have chosen. **Readmission (§12.2):** the multiplier returns when the log shows realized R separating across regime cells.

Permanently displayed alongside, because a limit first seen at breach has already failed:

| Row | Why |
|---|---|
| Daily loss limit, used, **headroom** — **the one hard block** (§4.2) | Coval & Shumway: morning losers take above-average afternoon risk 31.2% vs 27.0%, and the prices they set revert 27% faster. The moment it fires is the moment judgement is measurably worst, which is why this is the one rule carrying `enforcement: block` |
| Open risk in R, against an aggregate cap | Correlation cap: max 2–3 simultaneous same-direction ORB entries — index correlation peaks in the first 30 minutes |
| Sector / theme concentration | A tag cap, deliberately cruder and more robust than a computed correlation matrix |
| Day-trade count in 5 sessions | PDT |

### 7b.1a Four declared sides — never three, never inferred

The Drive spec says **"four declared sides (side never inferred)."** They are four different operations, not sign flips.

| Side | What it does | Gates that must fire |
|---|---|---|
| **BUY** | opens or increases long exposure | buying power · concentration cap |
| **SHORT** | opens **negative** exposure | borrow/locate · HTB fee · SSR state · squeeze fuel |
| **SELL** | **reduces a long only** — capped at held qty, must never open a short | held qty > 0 |
| **CLOSE** | flattens whatever exists | position exists; **direction derived from the broker** |

**CLOSE is the one place inference is correct**, and the spec should say so explicitly — the direction comes from the broker's reported position, not from a guess. Every other side is declared by you.

**`tws_order` implements three of four.** `--side {buy,sell,short}`. It already gets the hard part right: `--side sell` with `held_qty <= 0` rejects rather than opening an accidental short, and sell quantity is capped at held. **There is no `close`.** `--cancel` cancels *orders*, which is a different operation from flattening a *position*. The `[ FROZEN ]` breach state deliberately refuses to flatten — *"this system cannot place that order for you"* — which is correct for a breach and leaves the normal case unbuilt. **Slice 020.**

**Five of the nineteen do-not-trade items are short-only and none are in code.** They belong on the ticket the moment SHORT is declared:

1. **SSR active** (triggered at −10% vs prior close) — uptick-only makes a breakdown-momentum entry **mechanically unfillable**. **Rule, `enforcement: warn`, top severity.** *The SEC rule and the broker enforce this; the terminal states it.*
2. **No borrow / HTB fee / no locate** — *"a short you cannot borrow is not a trade."* **Rule, `enforcement: warn`, top severity**, with the fee shown. *Enforced by the borrow desk at submit, not here.*
3. **Squeeze fuel** — low float + high short interest + deal rumour. Rule, `enforcement: warn`.
4. **Shorting a Phase 2 leader** — a red first candle on a strong stock is statistically a dip. Rule, `enforcement: warn`.
5. **Gap-down landing on major support** — that is the mean-reversion book's entry, not this one. Rule, `enforcement: warn`.

Items 1 and 2 are the clearest illustration of §4.2: they are the two most *justified* blocks in the entire document, and they still do not need to be blocks — reality already enforces them. A terminal that blocks them adds nothing except the habit of a terminal that blocks.

**The direction control is a toggle, not a mirror** (Amendment 2 §A2.5). Long and short are separate registrations. The toggle changes which rules apply, which levels matter most, and which prediction variants load — **the rail itself does not flip**, because price structure is direction-agnostic and the interpretation is not. Its stated reason is worth keeping verbatim: *"taking a short while reading a long panel is a plausible and expensive error."*

Downstream, `entry_construction.trigger_side` (§5b) carries the same declaration into the detector cluster, so one flag inverts polarity rather than requiring a mirrored detector set.

### 7b.1b Every closed trade is exactly one of four things

**New under `039` Part 2. Nothing in this document classified a closed trade before.**

```
R_closed = net P&L ÷ risk at entry          net of commissions, in R
```

| Class | Condition | Counts against a limit |
|---|---|---|
| **Winner** `W` | `R_closed ≥ +1.00R` | **no** |
| **Partial** `P` | `+0.05R < R_closed < +1.00R` | **no** |
| **Break even** `BE` | `−0.05R ≤ R_closed ≤ +0.05R` | **no** |
| **Loser** `L` | `R_closed < −0.05R` | `losses` cap |

**All four count toward `trades`. Only `L` counts toward anything else.** `trades = W + P + L + BE` is asserted in code, not assumed — `core/risk/classify.py`.

**THE DENOMINATOR IS `stop_at_entry` AND IT IS FROZEN.** Christoph moves stops up during a trade. Using the *live* stop makes a trailed winner divide by nearly zero, and makes a trailed loser read as a full −1R when a quarter was lost. **`stop_at_entry` is an immutable field on the trade record and is the only denominator.** Every later stop is management, not risk. The record type carries no other stop at all, so the wrong one is unreachable rather than merely discouraged.

**THE BAND IS IN R, NEVER IN PERCENT OF PRICE.** An earlier draft used 1% of entry price. On QQQ at $733 that is $7.33 per share — **on a 480-share position, $3,518, seven times 1R, classified as break even.** `0.05R` bounds it at $25 whatever the instrument costs. Same reasoning as §4.4a's ADR-based band: a threshold in price units does not transfer between a $4 name and a $700 one.

**CLASSIFICATION IS NET OF COMMISSIONS.** A $25 gross scratch that cost $2 to trade is a small loss. Gross-versus-net is an unstated basis, which is this document's most-repeated defect.

> **Note on the formula.** `039` Part 2 states the per-share form `(avg_exit − avg_fill) ÷ (avg_fill − stop_at_entry)` **and** requires classification net of commissions. The per-share form has nowhere to put a commission, so the implementation computes the dollar form, which **reduces to the stated one exactly when commissions are zero** — pinned by a test. Signed quantity carries the direction, so there is no side branch.

**`W`, `P` and `BE` exist as record fields, not as limits.** They are what makes *am I cutting winners short?* answerable later. A month of `P` values clustered near +0.6R says something specific; folded into `W` it would be invisible.

**A trade with no `stop_at_entry` renders `unavailable (no entry stop recorded)` and is never classified.** Never break even — that is the one class counting against nothing, so defaulting to it turns a missing field into a silently free trade. **It also counts toward no limit, which is a gap rather than a decision** — see `OBS-056`.

**`0.05R` and `1.00R` are UNFITTED and render as such.** They gate nothing — no limit depends on either — so they are classification only. Answer them from the record. Tenet 6: thresholds do not transfer.

### 7b.1c Five limits, and every one of them is a loss limit

**New under `039` Part 3.**

| # | Limit | Config key | Window |
|---|---|---|---|
| 1 | Total trades | `trades_max_day` | day |
| 2 | Losing trades | `losses_max_day` · `losses_max_month` | day · month |
| 3 | R lost | `r_max_loss_day` · `r_max_loss_month` | day · month |
| 4 | Dollar safety | `daily_loss_usd` · `monthly_loss_usd` | day · month |

**Reaching any one empties the TRADE panel with the reason and the config key that set it.**

**THERE IS NO CAP ON WINNING TRADES, AND NONE ON GAINS.** An earlier draft carried `winners_max_day: 2`; a later one proposed a gain-based stop, `r_gain_stop_day`. **Both are removed.**

> **Christoph, 2026-08-14:** *"Some trades run 1:15, especially wins, and closing this trade first thing on open might lock me out of a good day."*

**A count cap cannot tell a 15R morning from a lucky scratch** — one 15R winner is `1W`, and a second ordinary trade reaches `2/2`. **A gain cap fails the same way from the other side**: +15R by 09:35 would stop trading for the day. A rule intended to prevent giving back profit would instead fire on the best morning of the quarter. `trades_max_day` still catches overtrading on a good day, so the case is not unprotected — **it is simply not protected by a rule that cannot distinguish a good day from a busy one.**

**Whether Christoph is cutting winners short is a reconciliation question, not a terminal one.** A month of closed trades carrying `R_closed` and `stop_at_entry` answers it directly. The rule cannot be set before the data exists, **and once it exists the answer may be that no rule is wanted.**

**Consequence, stated plainly: every remaining limit stops Christoph when it is going badly and never when it is going well.** That is the whole of the risk model and it fits in one sentence, which is the test for whether it belongs in core.

**THE R LIMITS COUNT LOSSES ONLY, NEVER NET.** A +10R swing closing today must not buy back two losing trades and defer the cap. **Losses accumulate; gains buy no room.** Net R renders alongside as information, with no ceiling:

```
R lost   −1.5R of −2.0R today · −3.5R of −6.0R month
R net    +8.5R today          ← information only, no limit
```

**This also removes any need for the terminal to know whether a trade was intraday or swing.** A swing position may be open for weeks; because its eventual gain masks nothing, the distinction never enters the arithmetic.

**One trade is one round trip.** A trade opens when the position leaves zero and closes when it returns to zero. **Partial exits are position changes that do not reach zero and are therefore not trades.** This requires no side logic and no short-versus-sell classification — the sign of the position carries the direction, and IBKR reports position quantity without the terminal interpreting it. **The terminal does not close positions**; this definition exists so counting is unambiguous, not so the terminal acts.

**Reset is 09:30h ET, not midnight.** A trade at 20:00h belongs to the day that is ending. US/Eastern via `zoneinfo`, never machine locale.

### 7b.1d The lock

**The lock blocks staging and nothing else.** No disconnect. No account change. No interference with an open position. **Every other panel renders normally** — ATTACHED, LEVELS, TAPE, WATCHING, CONNECTION.

`c015` carries two earlier readings — §Risk 3 *"terminal freezes and exits with error"* and §Risk 7 *"other functionality will disconnect"*. **Both are superseded** by Christoph's ruling of 2026-08-14, and this is the record of that.

**The lock outlives the process.** Trades, classification counts, R and dollar totals persist to disk, keyed to the session date — otherwise closing a window clears the limit.

**Open positions are read from the broker, never from disk.** The count is remembered; the position is read. **When the two disagree, the broker wins and the disagreement is surfaced** — Christoph can take a trade directly in TWS and the terminal must not silently under-count.

**Paper is a launch flag.** `--paper` at launch, and **there is no runtime switch, deliberately** — so no order can reach an account other than the one on screen when the terminal started. Relaunching without the flag shows a locked live account and **still renders live data**: open positions, tape, levels, watchlist. **The lock is on staging, not on data.** `PAPER` renders on every panel border and on the submit line — a single corner label is a label that stops being seen. Paper keeps its own counters against the same config limits.

### 7b.1e The dollar safety limit is a bug detector

`daily_loss_usd` and `monthly_loss_usd` already existed above as hard blocks. **Their purpose is now recorded, because it is not what it looks like.**

**It is not a second risk rule.** Limits 1–3 already govern trading. **The dollar limit catches the cases where the R arithmetic above it is no longer true:**

1. **Christoph moves a stop in TWS and the terminal never sees it.** A stop moved 10× wider produces a 10R loss the R counter records as 1R.
2. **A fill lands badly on a volatile name** and 1R is really 1.3R.
3. **A defect** — in the terminal, the OS, the network or the broker. *Something that should not happen, happening anyway.*

**If it fires, the finding is that the R accounting is wrong, not that Christoph traded badly.** **A safety net that only catches anticipated errors is not a net.**

Task `040` establishes whether case 1 is closable. **Neither answer is assumed here.**

### 7b.1f The TRADE panel — content, not layout

```
account  LIVE *1234
open     2R · 384 sh
trades   3/5 today  ·  1W 1P 1L 0BE
losses   1/2 today · 4/12 month
R lost   −1.0R of −2.0R today · −3.5R of −6.0R month
R net    +8.5R today
safety   −$180 of −$2,000 today · −$3,110 of −$5,000 month
risk     $500 per trade (config)
```

**Every limit renders its ceiling.** A number with no ceiling on screen cannot tell you how close you are until it stops you. **`R net` has no ceiling because it has no limit — and that difference must be visible, not inferred.**

**Dollars appear on the `safety` row and the `risk` row only.** `c015` §Risk 2: *"Seeing dollars made and lost encourages overtrading and/or revenge trading."* **Dollar P&L is recorded for data collection and never rendered.**

`open 2R · 384 sh` — two open positions totalling 384 shares.

**The record fields this requires** (`039` Part 6), none of which exist yet:

| Field | Why |
|---|---|
| `stop_at_entry` | **Immutable. The R denominator.** Expensive to add later |
| `avg_fill` · `avg_exit` | Classification inputs |
| `commissions` | Classification is net |
| `class` | `W` · `P` · `L` · `BE`, derived and stored |
| `session_date` | The key the daily counters reset on |
| `ema9` · `ema21` at entry | `c015` §5b, *"new requirement for trade data collection"*. **Never rendered** |

**`ema9` and `ema21` are the one requirement here with no screen presence at all**, which is exactly the kind that gets lost. Held open as `OBS-055`.

### 7b.2 Every stop level priced at once

You pick a **level**, not a number. The table prices every mode simultaneously and sizes each one.

**The five modes, named as you name them:**

| # | Mode | Resolver | Note |
|---|---|---|---|
| 1 | **VWAP** | session VWAP at evaluation time | Moves all session. The row carries its own as-of stamp |
| 2 | **Low of day** | session low so far | `tws_order` `low-of-day`. Also moves — downward only |
| 3 | **Low of last candle** | the last **closed** bar on the playbook's timeframe | Fixed once the bar closes. The safe default |
| 4 | **Low of current candle** | the bar **still forming** | **A moving target by construction** — see below |
| 5 | **Price override** | typed by you | `tws_order` `fixed`. Still takes the offset |

*(ATR-fraction, ADR-fraction and percent stops are computed columns on this table, not separate modes — they are ways of reading a distance, not ways of choosing a level.)*

**Every mode is mirrored for shorts** — high of day, high of last candle, high of current candle — and which side is used follows the **declared** side, never an inference (§7b.1a).

#### The offset applies to all five

```yaml
stop_offset:  {mode: cents, value: 5}         # mode REQUIRED, no default
```

**Every stop sits beyond its level by a declared offset, default 5 cents.** No stop is ever placed exactly at the level — a stop at the low of day is filled by the tick that retests it, and that tick is the most likely single price to trade in the whole session.

**This matches what `tws_order` already does** — its VWAP stop defaults to a 5-cent offset today — so core ships one convention rather than introducing a second.

**`mode` is still required with no default**, because the *unit* is where this goes wrong, not the number. `5` alone is the exact shape of this project's recurring defect — *a well-formed value answering a different question*:

| `mode` | On a $50 stock, ADR 4%, ATR₁₄ $1.80 | |
|---|---|---|
| **`cents: 5`** | **5c** | **The default.** Same convention as `tws_order` |
| `atr_frac: 0.05` | 9c | Scales with recent volatility. Available, not default |
| `adr_frac: 0.05` | 10c | Scales with the day's budget. Available, not default |
| `pct_of_price: 0.05` | **$2.50** | A swing stop on an intraday trade. Legal, but it must be typed deliberately |

`mode` is required with no default for the same reason `lookback` and `enforcement` are: a silent default is how the wrong basis travels. **The offset renders on every row with its basis spelled out** — `LoD 48.12 − 5c = 48.07` — never a bare adjusted price.

**The one thing to watch, and it is a per-trade judgement rather than a rule.** A flat 5c does not scale with price: it is wide on a $9 name and inside the spread on a $400 one. That is fine at the prices you trade and it is why the mode is configurable per playbook — **but the offset is part of `|entry − stop|`, so on a tight micro-range setup it can be the difference that pushes the stop-width rule over its ceiling.** The table shows the offset as its own column precisely so that is visible rather than buried in the stop price.

**Sign follows the declared side.** Long stops sit *below* the level, short stops *above*. A wrong-side result raises `SizingError` and emits no number (§4.2).

#### Mode 4 is a moving target, and the panel must say so

A stop referencing the **current** candle changes every tick until that bar closes. It is a legitimate choice — it is the tightest structural stop available and on a 1-minute ORB it is often the only one inside the ADR ceiling — but it is not the same kind of object as the other four.

It renders `forming — updates until 09:36:00`, with a countdown, and **the size recomputes with it.** At bar close it freezes and the panel says so. **Staging a ticket against an unclosed bar records both the value at stage time and the fact that it was still forming**, because otherwise the pre-registration says a stop was at 48.03 when the trader was looking at a number that had not settled.

Each row shows: **level · offset · stop price · distance $ · distance in ADR · risk/share · resulting size**, and which rules it fails.

**Two rules fire on the table itself:**

- **Rule `stop_width_ceiling` — symmetric, direction-agnostic. ** `|entry − stop| / ADR ≤ 1.0` (EP: 1.5). Renders `1.4 ADR vs 1.0 ceiling — ORB v3, unfitted, validated on intraday-ORH entries only`; **it does not refuse** (§4.2). Absolute distance, so a short's invalidation sitting above entry changes nothing; making it directional would invent an asymmetry that is not there. **The record carries the entry timeframe it was validated against**, because a ≤1×ADR stop is only coherent with an intraday opening-range entry and is actively harmful on a daily-close entry (§6.4) — which is precisely why it warns rather than blocks.

- **Rule `stop_width_floor` — daily-close entries only.** `|entry − stop| ≥ 3 × ATR₁₄`. Renders `stop 2.1 ATR · floor 3.0 (VladPetrariu, 13,500 picks, daily-close screen only)`. Every variant tighter than 3×ATR flipped the median return negative on that screen — they get whipsawed by normal pullbacks. It does not refuse (§4.2).

  **The two stop rules are bound to different entry timeframes, and the terminal hard-refuses to apply either across timeframes.** That refusal is a *labelling* rule, not a trade block: a ≤1×ADR stop on a daily-close entry destroys the edge, and a 3×ATR floor on an opening-range entry rejects the exact geometry the setup depends on. **Both ship; neither travels.** The record carries which timeframe each rule was validated against (§6.4).

- **Rule `range_budget` —  This is where the side genuinely matters.** `adr_used.py` computes `used = (current − open) / ADR`, **signed**, and already prints room in both directions every run — *"room left 0.52 to a full ADR (37.76 up / 35.04 down)"*. Nothing consumes it as a gate. It should:

  ```
  remaining_long  = (open + ADR) − current
  remaining_short = current − (open − ADR)
  budget_ok = remaining_in_declared_direction ≥ |entry − stop|
  ```

  That is R ≥ 1 expressed in ADR units. **A trade can pass gate 1 and fail gate 2**, and on a short into a name already extended down it routinely will: at ADR used −85%, only 15% of the downside budget remains while a stop to the day's high is most of a full ADR away. The long mirror is the case the module already names — *"full ADR consumed. Chasing here buys range that's gone."*

- **Formerly open — now dissolved by §4.2.** "Refuse, or size down?" was open decision 6: the ORB book refuses on a too-wide stop, Failed-Bounce Rollover Short v2 says *"size down rather than widen."* **Neither is now something the terminal does.** The panel shows the ceiling, the measurement, the size at your chosen `risk_pct`, and — because the table prices every stop mode at once — the size that *would* keep you inside the ceiling. You pick. The disagreement between two of your own documents was never going to be settled by a rule; it is settled by 30 logged trades above 1.0 ADR.
- **Rule `stop_inside_noise` — stop inside normal bar noise** (default 0.25 ATR), `enforcement: warn`.

`SizingError` still raises on a zero stop distance, a zero-share result, or a wrong-side stop. That is not a judgement — the arithmetic has no answer (§4.2).

### 7b.3 The management plan is sealed before the send

Pre-registered at stage time, hashed, append-only. Every parameter carries its evidence grade, and the ones without evidence render **unset** rather than a default:

| Field | Default | Grade |
|---|---|---|
| Time stop — no +1R within N | N **unset** until 100 trades | Principle CONFIRMED (Locke & Mann: trading speed predicts survival out of sample); value folklore |
| Trail | structure / VWAP, evaluated **on bar close, not tick** | CONFIRMED intraday (Zarattini) |
| Target | **none** — exit on structure or at 15:55 | CONFIRMED: a 1R–10R target sweep lost to no target at all |
| Breakeven stop | **never** — move to structure instead | CONFIRMED negative: every trigger below 2R reduced returns, worst at exactly 1R |
| Partial | **none** by default | Break-even rule: take *f* at +*k*R only if `q > (W̄−k)·p_win / ((k+1)·p_loss)`, where **q is the share of your losers whose MFE reached +kR** — a number your own log supplies. *f* cancels out |
| Adds | none intraday | No study supports intraday pyramiding |
| Invalidation | phrased as a **cue → response** pair | Gollwitzer/Sheeran, d ≈ 0.65 across 94 studies — the effect depends on specifying the cue |

### 7b.4 The pre-send checklist — formerly "the gate"

**One hard block, down from three (§4.2).** **Daily loss breached** remains a block: staging refuses for the rest of the session and the row renders red. `HARD_BLOCKS = frozenset({"daily_loss_breached"})`, one call site, contents asserted by test. **Reconciliation state unknown** and **pre-registration incomplete** become top-severity warn-rules: full weight, measurement shown, an explicit acknowledgement keystroke that is written to the trade record, refusing nothing.

The **override rate per rule is measured** — any rule overridden more than 80% of the time is mis-calibrated or should be deleted. This mattered when they were warnings competing with blocks; it matters more now that all but one are warnings, because the override rate is the *only* remaining evidence that any of them is worth showing. The CPOE literature is why: override rates of 46–96% are what happens when everything is a hard stop, and the failure mode is not that people override — it is that they stop reading.

Between stage and submit, each check returns pass / **advise** / **stale**, never a silent default: freshness · echo integrity · `whatIf` (empty margin fields = **`unavailable`**, never "no impact") · notional and share caps · price collar · stop sanity with explicit `triggerMethod` · duplicate guard · position and correlation state · daily risk state · reconciliation state · plan completeness. Each renders its measurement; the ticket stages regardless, carrying every failed rule as a recorded field.

**`[ FROZEN ]` survives, narrowed.** It fires only when the system does not know its own state — reconciliation unresolved, echo mismatch, connection lost mid-stage — and it means *this terminal will not show you numbers it cannot stand behind*, which is §4.1, not §4.2. It goes read-only and suggests a manual flatten with symbol, quantity and account. **It has never had the power to stop you trading in TWS and still does not.** Re-arm via config edit plus restart, never a button.

---

## 8. Records, calibration, and the trade log

### 8.1 The three records

**Pre-registration record** — immutable once sealed, hash-stamped at the moment the transmit gate arms:
`plan_id · created_at · symbol · direction · thesis · setup_type · playbook · regime_snapshot{I,0,1,2 with their staleness stamps} · entry_trigger · entry_price_intended · stop_price · stop_basis{structure|atr|hybrid + params + ATR basis} · target(s) · invalidation (as a cue-response pair) · risk_budget · R_per_share · size · time_stop · scaling_convention · whatif_snapshot · plan_hash · sealed_at`

Amendments are **append-only new records referencing the original, never edits.** *An amendment is not a sin; an invisible amendment is.*

**Order record** — keyed on `perm_id`, carrying `order_ref = plan_id` (the cheapest possible link between intent and fill), `submitted_params_json`, `broker_echo_json`, `echo_match`, `transmitted_by`.

**Trade record** — derived and versioned, so re-deriving is safe and a derivation change is visible rather than silently rewriting history. Grouping is **explicit via `plan_id`**, with time/flat heuristics only as a displayed fallback.

### 8.2 Outcome vs result — the distinction that everything depends on

- **OUTCOME** (calibration variable): the clean forward **excursion** from the fill over the playbook's horizon, **independent of how the trade was managed.** Deterministic given the price path; discretion cannot touch it.
- **RESULT** (realized): what the trade netted after management.

If calibration keyed on the result, a good signal managed badly would look like a bad signal. **Both are recorded; only the OUTCOME feeds calibration.**

Third axis: **adherence** — five binaries (entry within tolerance · size within tolerance · stop honoured, not widened · exit reason in a pre-registered category · no unplanned adds) → 0–5. **Never weighted by P&L**, or it reintroduces the outcome bias it exists to remove.

The 2×2 that matters is process × result, and the cell to flag loudest is **bad process / good result** — it is the one that trains you wrong.

**No incumbent journal does this.** Tradervue, Edgewonk and TraderSync all compute from fills; Edgewonk's "planned RRR" and TraderSync's checklists are the closest, but in every case the plan is entered *in the journal, editable, after or alongside the trade.* **None holds a plan committed before entry, timestamped and immutable.** That is the differentiator, and it is cheap because the pre-registration record has to exist anyway to compute R.

**Split confirmed:** Tradervue ← realized results + notes, human review surface. Own DB ← outcomes + signal snapshots, calibration store. Do not let Tradervue's trade model leak back.

### 8.2a The four populations — and why one expectancy number is a lie

Every statistic in this system belongs to exactly one of four populations, and **they are never pooled.** The 2×2 is watchlist membership against whether you took it:

| | **Taken** | **Not taken** |
|---|---|---|
| **On the watchlist** | **① Follow-through.** Did you act on your own preparation, and how did those trades do? | **② The pass pile.** Shadow-evaluated: what would these have done? |
| **Off the watchlist** | **③ Improvisation.** Trades you took that you had not prepared for | ④ The rest of the market. Unobserved, and correctly so |

**Each answers a different question, and the questions are the point:**

- **① alone** is what most journals compute and call "my performance". It is conditional on both your list *and* your selection, so it cannot separate them.
- **① against ②** is **watchlist quality vs selection quality.** If ② outperforms ①, your list is good and you are picking the wrong names off it. If ② is poor across the board, the list is the problem and no amount of better selection fixes it. **These two failures need opposite responses**, and one pooled number cannot tell you which you have.
- **③ against ①** is **does preparation help?** Whether the trades you improvised beat the trades you planned. This is the measurement most likely to be uncomfortable and the one nobody runs.
- **① + ② together** is the honest denominator for any statement about *the watchlist*; **① + ③** is the honest denominator for any statement about *you*. They are different sets and a figure quoting the wrong one is the canonical defect.

**Every statistic renders its population.** `on watchlist, n=612` · `on trades taken from watchlist, n=38` · `off-watchlist trades, n=9` · `watchlist not taken, n=574`. A number without its population does not render.

**Why ③ is trustworthy despite being the least prepared.** Off-watchlist trades are the classic recall-bias trap — you remember the improvised winner and forget the three you gave back. **This log cannot make that error, because the trade record derives from broker fills, not from memory** (§8.1): every off-list trade is captured whether or not you would have mentioned it. That property is what makes ③ worth measuring at all.

**Two honest caveats on ③.** Off-list trades have no pre-market preparation, so much of the grader vector, the context block and the pre-market structure read will render `ABSENT` for them — they are **structurally less measurable**, and a comparison against ① is therefore a comparison of unequal information, not just unequal preparation. Say so on the panel. And ③ is usually small; **it renders `n=9, not established` until it clears the floor** like everything else.

#### Building this is new specification, and four things in the corpus constrain it

A search of the Drive corpus and both repos was run before writing this section. **The traded-vs-watchlist classification is genuinely absent** — no `on_list` field in the pre-registration record, the order record, the derived trade record, the Signal Framework trade-log schema, or the day record. The existing taxonomy is *within-universe* (traded / not-traded among the ~30); this one is *universe-boundary*. So it is new spec, and it must reuse `plan_id` and `watchlist.rows[].symbol` rather than inventing a parallel key.

**Four constraints, each of which would be got wrong by designing fresh:**

1. **No execution-pull code exists. None.** A repo-wide search for `reqExecutions`, `ExecutionFilter`, `execDetails`, `commissionReport`, `orderRef`, `permId`, `Flex` returns **zero hits across both repos.** `tws_order` reads open orders (`get_open_trades` → `reqOpenOrders`), positions and NLV, and nothing else. Nothing is written on fill — the process exits after staging. This is a build item, not a wiring item.
2. **`reqExecutions` is client-scoped, and that is the failure mode most likely to silently return nothing.** `ibkr.py` already documents the same trap for open orders: *"`reqOpenOrders()` is scoped to this API client's session."* **Because transmit is manual — you press submit in TWS — most fills have no `orderId` in the local store at all**, and an execution pull not configured for all-client visibility will return zero rows and look like a quiet day. The broker pull is the source of truth; the local record is a hint. The mockup already says it: *"Believe the broker, not the log."*
3. **The archive has no date lookup.** `core/watchlist.py` gives `archived_names()`, `read_archived()` and `latest_archived()` — but **`latest_archived` takes no date and always returns the newest**. There is no `for_date(d)` and no symbol index. It is a short function built from existing parts, but it does not exist, and **`scanner_watchlists/` does not exist on disk**, so no historical day is answerable. Membership starts producing answers from the first successful ingest forward. *A day with no archived file must render `no watchlist ingested` — distinct from `symbol not on it`.*
4. **Same-day versions are a real ambiguity, not an implementation detail.** Filenames carry `vN`, and if `v1` and `v2` both exist for one date, *"highest version"* answers a different question than *"the universe on screen when the order went in"*. A 09:35 trade scored against a `v2` published at 11:00 is the canonical defect. **Record the ingested snapshot's `content_key` at stage time and reconcile against that exact file** — silently taking `max(version)` is exactly what the tenets forbid.

**One terminology guard.** Layer 2 is *breakout* follow-through per playbook (§5.3). Population ① is *watchlist* follow-through. **Same word, different question** — always qualify which, or this becomes the next well-formed value answering a different question.

**Population ② is what the shadow evaluation produces** (§7.2) — and it is the reason the watchlist archive matters beyond provenance. The archive is the **sampling frame**: the population you selected from, frozen in git before you chose, in commit order. Most retail post-hoc analysis reconstructs the candidate set after the fact and inherits every hindsight bias in the reconstruction. Here the frame is a commit.

### 8.2b Which watchlist was in force at 09:35 — the intra-day problem

**The requirement:** the watchlist is revised during the session. The Drive spec *Watchlist Build — Intraday Scans* defines **post-open refresh scans at 09:35, 09:50 and 10:15 ET**, with additions joining mid-list. So a trade at 09:40 must be attributed to the list that existed at 09:40 — not to a revision dropped at 10:15.

#### The proposed mechanism is refused by the code, and the refusal is right

Ordering does **not** come from the file's created-or-modified date, and this is deliberate. `core/watchlist.py` says so twice, unprompted:

> *"The ordering 'latest file wins' uses the date IN THE VALIDATED NAME, never filesystem mtime. **A copy, a restore or a touch changes mtime without changing which universe the file describes.**"*

There is a test that actively sabotages mtime to prove it — `os.utime(old, (later, later))` and then asserts the *older* file still loses. **The mechanism is a filename token**, `watchlist-YYYY-MM-DD-vN.csv`, and `vN` increments by hand when the list genuinely changes. A second drop with a bumped `vN` is accepted; reusing a name with different content raises `ArchiveCollision` and refuses.

**Keep that.** A filesystem timestamp is metadata about a *file*; the version is a fact about a *universe*. Cloud sync, a restore from backup, or copying the folder would silently reorder history, and it would do it invisibly. This is the same class of error as everything else in this document, applied to ordering.

#### But the requirement is real and is currently unmet

**`vN` gives an order, not a *when*.** Knowing v2 follows v1 does not tell you whether 09:40 was v1 or v2. Three concrete gaps:

1. **Drop time is computed and then thrown away.** `ingest_drop` sets `moment = now or datetime.now(EASTERN)` into `provenance.ingested_at` — and **nothing writes it to disk.** `_copy_into` copies the CSV and its companions, nothing else.
2. **Worse, `read_archived` regenerates `ingested_at` as *now* on every read.** So an archived list reports the time you looked at it, presented as the time it was ingested. **That is well-formed and wrong — strictly worse than absent**, and it is exactly the defect the tenets exist to catch. **Fix it in the same commit as anything that touches this file:** either persist the real value or make the field `None` on read.
3. **The time field was lost as collateral damage, not by decision.** The retired `watchlist_builder` wrote `watchlist_YYYYMMDD_HHMM.csv` — timestamped runs at 09:25 / 09:35 / 09:50 / 10:15. When the scanner was retired on 2026-08-07 the `HHMM` token went with it, and the replacement convention has no clock. **Nobody decided to drop intra-day attribution; it fell out.**

#### The watchlist is capped at eight symbols

```yaml
max_watchlist_symbols: 8      # source: christoph_preference
```

**A drop with more than eight rows is refused at ingestion**, named as such — `WatchlistTooLarge: 12 symbols, cap 8` — and **nothing enters the archive.** It joins the existing refusals as a contract about the file, not a restriction on you: **you can still type `/` and attach any symbol at any time** (§6b.1b). The cap governs what the *prepared list* may contain, not what you may trade.

**This resolves the pacing problem rather than mitigating it.** The arithmetic that was 50 % over budget now has room to spare:

| | Requests | Against 60 / 10 min | Wall clock |
|---|---|---|---|
| 30 symbols × 3 | 90 | **50 % over** | ~15 min |
| **8 symbols × 3** | **24** | **40 % of budget** | **~4 min** |

**And it makes the shadow evaluation plausible again.** §6b.1b put `reqHistoricalTicks` for thirty names at ≈33 hours — not an overnight job. **At eight names it is 3,200 requests, ≈8.9 hours**, which fits an overnight window with margin *if* tick requests share the historical budget, and is trivial if they do not. **The capability question changes from "probably no" to "probably yes"**, and the same test settles it.

**Two more consequences, both good.** Eight rows fit any terminal without scrolling or pagination. And the Databento pass-pile pull drops to roughly 160 symbol-days a month rather than 600 (§7.2), which keeps it comfortably under the cost gate.

**The honest cost, and it is real.** Population ② accumulates more slowly — a base rate over eight names a day takes proportionally longer to reach a usable *n* (§8.2a). **And the selection pressure moves upstream**: with no room for maybes, the scanner has to be right before the terminal ever sees the list. That is probably a discipline worth having rather than a limitation, but it is a shift in where the hard judgement happens, and it should be recognised as one rather than discovered later.

#### The fix: an append-only ingest ledger, committed

Not a new filename convention — the naming rule is sound and re-litigating it would cost the collision refusal. One additional artifact:

```
scanner_watchlists/ingest_ledger.jsonl        # append-only, committed
{"watchlist_date":"2026-08-10","version":2,"content_key":"…",
 "ingested_at":"2026-08-10T09:47:03-04:00","symbols":31}
```

**One row per accepted ingest, keyed on `(watchlist_date, version, content_key)`.** Attribution then becomes a lookup: the list in force at time *T* is the highest version whose `ingested_at ≤ T`. Supersession is derived from the ledger rather than stored — v1 is superseded from the moment v2's row exists — so there is no second source of truth to drift.

**Effectivity is a half-open interval, and it must render as one:** `v1 in force 08:14 → 09:47 · v2 from 09:47`. A trade at 09:40 attributes to v1 and says so on the review row.

**Two hazards, both already known:**

- **`.gitignore` will eat it.** `*.jsonl` matches at any depth, and this exact filename was confirmed ignored before the negation block was added. **A ledger that is silently untracked is worse than no ledger** — it will look present locally and be absent in history. Assert it with `git check-ignore` in a test, the same way the archive directory already is.
- **Backfill is impossible.** `scanner_watchlists/` does not exist on disk — **no watchlist has ever been ingested** — so the ledger answers from its first row forward and nothing earlier. A date with no ledger row renders `ingest time unknown`, distinct from `no watchlist that day`.

#### Consequence for §8.2a

Population ① (on-list, taken) is defined against *"the list in force at fill time"*, not *"any version that day"*. Without the ledger it silently means the latter, and a symbol added at 10:15 would count as prepared-for on a 09:40 trade — **manufacturing follow-through that did not happen.** Until the ledger exists, membership renders `on watchlist (version-ambiguous)` on any date carrying more than one version.

### 8.3 Calibration discipline — the numbers

- **Sample sizes.** To distinguish a 55% win rate from 50% at 95% confidence: **~1,000 trades.** 60% from 50%: **~250.** Any threshold tuned on fewer than ~100 observations renders with an explicit `n = 43, not established`.
- **Multiple testing.** Harvey/Liu/Zhu (*RFS* 2016): a new finding needs **t > 3.0, not 2.0**.
- **Deflated Sharpe.** Store a **trials counter** — every threshold tried, every parameter swept — and render the deflated number, not the raw one. *"A backtest where the researcher has not controlled for the extent of the search involved is worthless, regardless of how excellent the reported performance."* **A panel showing a threshold should show how many thresholds were tried to find it.** Cheapest high-integrity feature in this document.
- **Purged/embargoed CV** (López de Prado). For same-day-exit intraday trades, purging costs one day either side — nearly free.
- **Combination: default to equal weights.** Dawes' *Robust Beauty of Improper Linear Models* — unit weights on standardized, correctly-signed predictors routinely match or beat regression-optimal weights out of sample, because estimated weights carry estimation error large relative to the weight differences. **Moving off equal weights must require passing an explicit test.**
- **Rank vs value.** Composite on cross-sectional ranks (invariant to regime-dependent scale), **but carry a separate absolute gate** — rank compositing manufactures a "best" candidate unconditionally. `rank_score = 0.91` *and* `absolute_gate = FAIL (top RVOL 1.1 < 2.0)` → show the ranking **and refuse the day**.
- **Calibration curve:** Platt (2 params) only. **Isotonic is refused below ~1,000 trades.** Render reliability diagrams **with bin counts printed** — a curve whose bins hold 4 trades each should render the counts, not the curve.
- **Bayesian n-display.** A Beta(α,β) posterior per playbook makes *"not enough evidence yet"* a first-class display state with a visibly narrowing interval, rather than an error. **Highest-value statistical addition available.**
- **Meta-labeling is the right ML shape** and the only one trainable on a few hundred trades: your judgment is the primary model (direction); a small secondary classifier predicts P(this works) and is used for **sizing only, never direction**. It respects both human gates by construction. **Its stated failure condition must be honoured: on a negative-expectancy process it makes things less negative, not positive, and will look like it is working.**
- **Refused:** gradient boosting at this sample size · isotonic below 1,000 · HMM regime labels (~4 transitions/year, identified only up to relabeling) · ADX/Kaufman-ER as an on-off switch (ranked 11th–13th of 13 in a 1,600-backtest median-performance study; the "abstinence trap" costs 4–6pp/yr) · Hurst on intraday windows (three methods, three answers, one name).
- **The sign warning.** Lou/Polk/Skouras (*JFE* 2019): overnight and intraday returns have **persistently opposite** cross-sectional signs for the same characteristics. **Any indicator validated on close-to-close returns may have the wrong sign for open-to-close trading.** Every registry entry must declare which return segment it was fitted on, and the terminal must refuse to compare across segments. Cheapest possible check: recompute any indicator you already trust on open-to-close only.

### 8.4 RVOL — settled: exactly two, and they answer different questions

**This supersedes the earlier five-variant family.** RVOL was a name shared by several quantities, which is why it needed a `basis` field to stop them being compared. **The definition below is decided on its own terms, independent of what was built before**, and it is two things — not five, not one.

#### RVOL-at-time — a continuous function of `t`, not a reading at one moment

```
RVOL(t)  =  cumulative volume from open to t
            ────────────────────────────────────────────
            median cumulative volume from open to t,
            over the last N sessions          (N = 20)
```

**`t` is any minute of the session.** 09:31 and 09:35 are the minutes two playbooks happen to gate on; they are not the definition. **RVOL is evaluable at every minute from the open onward, and it updates live as the session runs.**

**So the denominator is a curve, not a number.** At attach, the 20-session intraday series is reduced to **one median cumulative-volume value per minute of the session** — roughly 390 values for the regular session, plus pre-market if the playbook uses it. `RVOL(t)` is then a lookup and a division on every new bar.

**The comparison is always at the same clock time**, which is the whole point: 400k shares by 09:31 and 400k shares by 11:00 are not the same event, and a full-day ratio cannot tell them apart.

**Median, not mean**, at every minute. One earnings day in a 20-session window inflates a mean reference and silently deflates today's reading — and it would do so across the whole curve, not just at one point.

**Render the shape, not only the number.** A single `RVOL 3.1×` hides whether that came from a violent first two minutes that has since died, or from steady accumulation that is still building. A sparkline of `RVOL(t)` across the session so far costs one row and answers a question the scalar cannot. The current value renders with its time: `RVOL 10:14 = 3.1× (20d median)`.

**Two readings at different `t` do not compare**, and the display makes that unmissable by always carrying the time.

**Reliability improves through the morning, and the panel says so.** At 09:31 the denominator is one minute of volume across 20 sessions — small, noisy, and the ratio built on it is correspondingly unstable. By 09:45 it is far steadier. **This is not a reason to withhold the early reading** — a 1-minute playbook needs exactly that reading — but an early value and a mid-morning value are not equally trustworthy and must not render as though they were.

#### This is a volume curve — and the difference from the retired one is the point

`RVOL(t)` needs a per-minute expectation, which is a volume curve by any other name. **The distinction from `volume_curve.yaml` is not that one is a curve and the other is not.** It is that this one is **empirical, per-symbol, and rebuilt at attach from that symbol's own last 20 sessions** — it is never fitted, never shared between names, and never carried from one period to another. **Tenet 6, applied exactly: thresholds do not transfer, so do not transfer them — re-derive them per symbol, every time, from data you just fetched.**

#### RVOL-vs-sector — is *this name* busy, or is the whole sector busy

```
RVOL_rel  =  RVOL_t (symbol)  /  RVOL_t (sector ETF)
```

**A ratio of ratios, and that is deliberate — it divides out the common factor.** On a morning when the whole of tech gaps, every tech name shows an elevated RVOL and none of it is about the name. This separates them:

| `RVOL_rel` | Reading |
|---|---|
| ≈ 1.0 | The name is doing what its sector is doing. **The absolute RVOL is sector flow, not a stock-specific event** |
| > 1.5 | Genuinely idiosyncratic interest, on top of whatever the sector is doing |
| < 0.8 | **Lagging its own sector** — the sector is being bought and this name is not participating |

**The sector is resolved from IBKR `contractDetails`**, which carries industry and category, and mapped to its sector ETF (XLK, XLF, XLE, XLV, XLI, XLY, XLP, XLU, XLB, XLRE, XLC). **If the symbol resolves to no sector, `RVOL_rel` renders `unavailable (no sector mapping)`** — never 1.0, which would read as "in line with its sector" when the truth is that no sector was found.

#### Both render. Neither replaces the other

They answer different questions and **must never be collapsed into a single number.** `RVOL 09:35 = 3.1× · vs XLK = 1.9×` says *"busy, and busy on its own account."* `RVOL 09:35 = 3.1× · vs XLK = 1.0×` says *"busy, but so is everything it trades with"* — and those are opposite trade decisions from an identical headline figure.

#### What this retires

`rvol_vs_curve` and the `volume_curve.yaml` machinery are **not part of this definition.** That file is `status: UNCALIBRATED_PLACEHOLDER` and documents that two prior curves *cross* — −8.3% at 09:35, +17.6% at 10:00 — so a name reading 5.00 on one curve reads 5.45 on the other. **A per-symbol empirical median curve, rebuilt at attach, removes the calibration question rather than answering it** — there is no fitted parameter left to calibrate, and no curve shared between two names that could disagree about which one they describe. The `hypotheses.volume_curve_transfer: NOT_YET_TESTED` gate stays unreleased and now blocks nothing.

---

## 9. What already exists — the build-on baseline

**Solid, tested, contract-bearing:**

- `core/indicators` + `REGISTRY` — **12 entries, 10 scored** (a test pins the count). Uniform `SignalSpec` contract with `lookback` required and no default. 116 tests.
- `core/watchlist.py` — the whole ingest→archive→snapshot path with provenance, content-hash collision detection, `age_days` that never raises. 45 tests. **But `scanner_watchlists/` does not exist on disk, meaning no watchlist has ever successfully passed through the door.**
- `core/session.py` + `us_equity_calendar.py` — the correct session model, holidays and half-days 2019–2027, `cross_check` → `CalendarDisagreement`.
- `live/marketstate.py` + `detectors.py` + `feeds.py` — a working per-symbol tape engine, ~22 detectors, 6 group scores, capability-driven degradation, replay support.
- **`live/render.py`'s data model is exactly right and re-skinnable.** `Result{state: Optional[bool], quantifier, detail, value, na_reason, degraded, degraded_reason}`; `None → "N/A"` in grey with the reason replacing the detail column; `~` suffix + yellow for degraded; throttle-and-batch so transitions during cool-down are held and emitted as one batch, never lost, never spammed. **Absence already renders with a reason, never a zero.** What must change is the last five lines of `_write` (stdout → frame buffer) and the fixed column constants. **This is a re-skin, not a rewrite — for the per-symbol pane only.**
- The **refusal culture, mechanised**: `test_open_questions.py`, `test_observations.py`, `test_deferred_work.py`, `test_preregistration_gates.py`, `test_import_boundaries.py`, `test_no_secrets.py`. The repo tests its own conventions. This is unusual and valuable.
- `tws_order/` — real prepare-not-transmit: with `auto_transmit=False` **all three legs carry `transmit=False`**, so TWS holds the whole linked group unsent. Refuses to size a zero-risk order, refuses to guess an account, refuses to stack a second bracket, refuses to open an accidental short on `--side sell`, refuses to resolve a stop from all-zero bars, and reconciles every leg's status after a 1.5s settle.

**Missing, in blocking order:**

1. **`core/regime.py` does not exist.** No Layer 1 module, no Layer I, no Layer 2, no macro strip. (Layer 0, the exposure grid and the vetoes are deliberately not built — §5.1, §7b.1, §12.)
2. **No trade log** → Layer 2, grader calibration, similarity prior and scoring loop are all blocked on one artifact.
3. **No ranked watchlist panel.** Nothing consumes `WatchlistSnapshot` for display.
4. **No playbook config.** `intraday_orb`, `intraday_flag`, `swing_ep`, `swing_vcp` exist only as names in prose.
5. **No `harness/score.py`, no `config/weights.yaml`** — thresholds never meet signal values anywhere.
6. **`live/` has zero collected behavioural tests.** 16 modules, one import-smoke file. Two consolidation steps shipped a broken `live/` that stayed green. (There *are* 7 behavioural tests in `live/tests/test_level_flow.py`, but `pytest.ini` sets `testpaths = tests`, so they are never collected.)
7. **`live/regime/regime_pull.py` raises `NameError`.** Layer 1 is not runnable.
8. **`condition_codes.yaml` is actively misleading** — its own banner says the delivery carries no condition field at all, so these are "a vocabulary this codebase invented."
9. **Root `README.md` is substantially stale** — refers to trees that no longer exist and quotes "435 tests" against ~2,500. `CLAUDE.md` is current; the README is not.

**Security:** a **Databento API key is stored in plaintext** in three allow-rules in `D:\Dev\.claude\settings.local.json`. Every other rule reads it from the user environment, which is correct. `test_no_secrets.py` passes because it scans repo files and never sees `.claude/`. **Rotate the key and delete those three rules.**

---

## 10. Proposed additions — accepted and rejected

### Accepted

| Addition | Why it survives the tenets |
|---|---|
| **Layer I institutional context** (§5.4) | 9 rows, mostly free, each carrying source + lag; ships PROVISIONAL and cannot size for 60 sessions. |
| **Snapshot-tested refusal states** | Turns the core design conviction from prose into a failing test. Directly addresses "the read is the implementation" — five prior failures. |
| **Trials counter on screen** | Makes overfitting visible on the operational surface, not confined to a notebook. Direct consequence of the deflated-Sharpe result. |
| **Bayesian n-display per playbook** | Makes "not enough evidence yet" a first-class display state with a visibly narrowing interval. |
| **Rank composite + separate absolute gate** | Fixes rank compositing's manufactured "best candidate". Status inherits from the weaker. |
| **Return-segment declaration on every indicator** | Lou/Polk/Skouras sign inversion. Cheap; prevents a whole class of silent wrongness. |
| **Cue-response phrasing on the invalidation field** | Gollwitzer/Sheeran meta-analysis, d ≈ 0.65, 94 studies — the effect depends on specifying the *cue*, not just the action. A UI change, not a model. |
| **Risk headroom permanently displayed** | A kill switch first seen at trigger time has already failed. Coval & Shumway: morning losers took above-average afternoon risk 31.2% vs 27.0%, unprofitably. |
| **Threshold-scaled confirmation** | TT confirms only above a configured quantity. Universal confirmation trains dismissal. |
| **Override-rate measurement per warning class** | CPOE literature: override rates 46.2–96.2%. Any warning overridden >80% is mis-calibrated or should be deleted. Measuring it is itself the feature. |
| **Working orders shown at their price level on the levels rail** | MD Trader's `Work` column. Removes eye-correlation between two panels under time pressure. |
| **Session/basis label per row** | `RTH/ETH`, `PRE/AH/CLS`. Direct fix for "a well-formed value that answers a different question." |
| **Meta-labeling as the eventual ML shape** | Sizes only, never direction. Respects both human gates by construction. Trainable on hundreds, not millions. |
| **Volatility-targeted sizing in ATR units** | Boring, well-evidenced, needs no prediction at all. Cheapest Sharpe improvement available. |
| **Triple-barrier labeling** | Makes the log's labels match how you actually trade; prerequisite for meta-labeling. |

### Rejected

| Rejected | Reason |
|---|---|
| Dealer gamma / GEX | Inferred sign presented as observation. §5.4. |
| FINRA short volume | Disqualified by FINRA's own notice. §5.4. |
| Buyback blackout | p > 0.05 across all windows, 1994–2018. |
| HMM / Markov-switching regime label | ~4 transitions/year; regimes identified only up to relabeling; 218 parameters for 2 regimes × 8 variables. |
| ADX / Kaufman ER as a market switch | Ranked 11th–13th of 13; abstinence trap costing 4–6pp/yr. |
| Hurst exponent | Three estimation methods, three answers, one name — the exact pattern the tenets exist to catch. |
| Isotonic calibration (for now) | Needs ~1,000 samples. Platt has 2 parameters. |
| Gradient boosting on the trade log | Confident, uninterpretable, fits idiosyncrasy at this n. |
| Gap-fill percentages as published | Definition unstated; dominated by noise-sized gaps. |
| Order-book depth across the watchlist | IBKR caps `reqMktDepth` at 3 concurrent; depth on gappers is illusory. |
| Unusual-options-activity feeds | Unvalidatable, and would sit in Context looking like evidence. |
| A continuous 0–100 risk score | Hides staleness; invites trading a 62 differently from a 58. |
| Streamlit | The only display option that adds a process to babysit. |
| HTML as the running UI | Mockups are blueprints. Confirmed. |
| Auto-generated features | Cannot be pre-registered with a predicted direction. |

### Do-not-automate

Order transmission · `/iserver/questions/suppress` (deletes the broker's own gate) · reconciliation-corrective orders (real orders from a state you just proved you don't understand) · `reqGlobalCancel` as a general kill switch · stop widening or move-to-breakeven on a rule · re-entry after a stop-out (highest-risk moment behaviourally; needs *more* friction than the original entry, not less) · threshold re-fitting on live data · any automatic size increase after wins.

---

## 11. Open decisions — yours, not mine

Each of these changes what gets built, and none is a defensible-choice-and-move-on.

**Four of v1.0's seven were dissolved rather than answered** — §4.1 and §4.2 removed the thing that made them consequential. Recorded here because a dissolved question tends to come back as a new one:

| v1.0 | Status |
|---|---|
| 1. Layer 0 denominator arithmetic (11−1=10, not 9) | **Moot in the terminal.** Layer 0 is the cloud task's; nothing here consumes a denominator. Preserved in §12.1 |
| 2. Can a live Layer 0 veto fire mid-session with positions open? | **Moot.** No veto fires at all now (§4.2). Preserved in §12.1 as the hardest part of any Layer 0 revival |
| 6. Too-wide stop: refuse, or size down? | **Dissolved by §4.2.** The terminal does neither. §7b.2 |
| — | *(and the ≤1 ADR / 3×ATR question below survives, but only as a labelling question)* |

**Decided 2026-08-10:**

| Decision | Where it landed |
|---|---|
| **The regime surface is deleted.** Layer 0, the macro strip, Layer I **and Layer 1** are all produced by the Claude task. Four surfaces, not six; core drops to seven slices. The day record keeps only `regime_snapshot.ref` — *not rendered is not the same as not recorded* | §3.2 |
| **The ingest ledger lands in slice 009**, not later. Nothing can backfill it | §8.2b |
| **Risk stays a percentage of NLV; NLV is read live from IBKR**, never configured — size must compound with the account, and a fixed dollar risk would be the defect. Initial value set so 1R ≈ $500. **Frozen at session start with the live value beside it**, so size does not shrink under you as the day's losses accumulate | §7b.1 |
| **`daily_loss_usd: 2000` · `monthly_loss_usd: 5000`.** Both hard blocks. Note the ratio: **2.5 full daily stop-outs exhausts the month**, so the monthly limit binds well before any slow bleed reaches it — the month row therefore renders headroom in *days*, not only dollars | §7b.1 |
| **Day-context capture starts now** — a capture step joins slice 009 rather than waiting for a consumer | §12.7, plan slice 009 |
| **The overnight macro strip stays in the Claude task and does not render in the terminal.** The Δ-since-snapshot column drops with it — it bought drift at the cost of nine live quotes and a second place where the same nine numbers live | §5.5 |
| **Layer I is computed by the Claude task too.** All nine of its rows are EOD or weekly, so a live computation would produce an identical number at greater cost with a second chance to disagree | §5.4 |
| **Both are locked into a YAML snapshot** beside the prose — `frozen_at` written once, never updated; the terminal reads and renders, never recomputes. **Machine-readable from day one even though nothing consumes it yet**, because the eventual "did regime separate outcomes" test cannot be run retroactively over prose | §5.5a |
| **Daily and monthly loss limits are declared in US dollars**, not R or % of NLV. R is rendered alongside, computed from dollars. Deriving limits from R is a possible phase-2 refinement | §7b.1 |
| **A rolling-month limit exists and also blocks.** `HARD_BLOCKS` gains its second member — deliberately, as a visible diff in a named constant. It fires rarely and matters more: six ordinary red days never trip a daily limit once | §4.2, §7b.1 |
| **The daily block auto-resets overnight.** No explicit re-arm | §4.2 |
| **The block never covers `SELL` or `CLOSE`.** `BUY` and `SHORT` only. Confirmed | §4.2 |
| **The Layer I state machine is kept.** Built, logged, not rendered, on trial for 60 sessions | §5.4, §12.3 |
| **IBKR-vs-Databento capability is not terminal functionality** — it is a data-acquisition question, tracked separately from this spec's open list | §7.2, §12.9 |

**Decided 2026-08-09 — recorded here, folded into the spec above:**

| # | Decision | Where it landed |
|---|---|---|
| **Render layer** | **Settled: Python/Textual in Windows Terminal.** Removed from this list — it was carried forward as a "confirm" item in error. §2.3 states it; nothing re-opens it | §2.3 |
| **Databento** | **No subscription. Per-byte, traded tickers only** — a fraction of the cost, and it lands in the only sample where hit rate is measurable | §7.2 rewritten |
| **Phase 3** | **Stays halted.** Confirmed | §7.2, plan §5 |
| **Daily loss limit** | **Enforced.** The one hard block in the system. `HARD_BLOCKS = frozenset({"daily_loss_breached"})`, one call site, contents asserted by test | §4.2, §7b.1, §7b.4 |
| **Colour on failed rules** | **Renders.** Green inside a declared threshold, **amber outside it**, red for the one enforced block and for system refusals. It is readability, not enforcement — *"outside our suggestion"*, nothing more | §4.1 colour table |
| **Stop rule** | **Both.** ≤1×ADR for intraday-ORH entries, 3×ATR floor for daily-close entries, and **a hard refusal to apply either across timeframes** — a labelling rule, not a trade block | §6.4, §7b.2 |
| **Acknowledgement keystroke** | **Kept**, for the two remaining top-severity warn-rules. Its purpose is the override-rate record, not friction | §4.2 |

**Still open, and yours: nothing.** Every decision raised in this document has been made. What remains is verification and cleanup, tracked below so it is not mistaken for a decision waiting on you.

---

**Work items — not decisions:**

1. **Five concurrent `keepUpToDate` streams on one account are untested** (008b, deviation 3). IBKR limits *simultaneous open historical requests* separately from the request-rate budget, and 008b probed one stream in one process — so the pacing conclusion **holds for one symbol and is an inference for five.** **Test before the cadence is removed from a five-symbol console**, or the failure arrives on a morning with five names attached, which is the morning it matters. `cum_refresh_s` stays a working fallback meanwhile.

2. **Delete the Databento key from the working tree**, and **fix `test_no_secrets.py` so it would have caught it.** The key is rotated (2026-08-10) so the exposure is closed, but this is the **second** cleartext occurrence and the test that exists to catch it passed both times. **A secrets test that passes while a live key sits in a committed file manufactures confidence** — establish *which* failure it was (never scanned `requirements.txt`, or scanned and missed the pattern) rather than assuming, and confirm it **fails** against the old key before accepting that it passes.

3. **008b's window did not span the open** (deviation 1) — it ran 12:34–13:06, so the opening half-hour's update cadence is unmeasured. The ~5 s beat held across a 6× swing in per-minute volume within the window, which is suggestive that cadence is not volume-driven, **but the open was not observed.** Cheap to close on any morning.

4. **The workflow mock predates the last three decisions**: VWAP from 1-minute bars rather than tick, the `keepUpToDate` ~5 s refresh replacing the 120 s cadence, and one-symbol-per-process. Fold into the next mock pass.

5. **Mockups 03–08 predate** the four-colour grammar, the no-cache decision, the RVOL settlement and the number-formatting rule. Blueprints for slices 013+, not core.

6. **The prioritisation pass (§12.8) has not been run.** Superseded for now by the minimum-to-useful cut; run it when the next tier is scoped.

**Closed since the last list:** `keepUpToDate` viability, the 04:00 anchor seam (there is none), streaming bar-update semantics, the Databento key rotation, and every open decision.

---

## 12. Future version — deferred, not cancelled

Everything §4.1 and §4.2 removed, preserved with the criterion that brings it back. **Nothing here returns on judgement; each has a test.** The section exists so that removal does not become forgetting — the project's own recurring failure is a correct warning sitting in a file nobody opens, and a deleted feature with no record is the same failure in reverse.

### 12.1 Layer 0 in the terminal — the 14-row model

Preserved verbatim: market-wide, never ticker-dependent. **11 rows frozen at 08:00 ET, 3 read live and displayed beside the cached composite, never folded into it.** Four hard vetoes stored as a separate boolean array, never summed into the score. Rows 12 and 14 are the per-ticker tape functions (`first_bar_strength`, `drive_purity`, `orh_persistence`, `max_pullback_pct`, `vwap_breaks`) called on SPY/QQQ — all exist, all registered, never called on an index; the cheapest 2 of the 14. Row 10 (gap breadth) has no wired data path. Row 13 (TICK/ADD/RSP) has unverified IBKR availability.

**Two unresolved sub-problems travel with it**, and neither may be skipped on revival: the denominator arithmetic (Amendment 1 §A1.5 — removing row 10 from an 11-row card leaves 10, not 9; `mockup-02` inherited `6/9`), and **how bands rescale on a reduced denominator**, which is unspecified anywhere and biases every session toward the middle.

**Promote when:** the cloud task's prose read demonstrably fails — a specific, written instance of a morning where the prose was ambiguous and a scored row would have resolved it. Three such instances. Not "it would be nice to have the number."

### 12.2 The exposure dial `L0 × L1 → fraction of 1R`

**Promote when:** ≥100 logged trades with the regime cell recorded at stage time show median R separating across cells by more than the within-cell spread, on a declared holdout. Until then `risk_pct` is yours and the log records what you chose (§7b.1) — which is the data the test needs.

### 12.3 Layer I state name and desk action

`RISK-OFF` · `DEFENSIVE` · `NEUTRAL` · `CONSTRUCTIVE` · `FULL MOMENTUM` with their actions. Computed and logged from slice 013; not rendered.

**Promote when:** 60 sessions logged **and** realized R separates across states on a holdout **and** the decisive-row log shows more than two rows ever mattering. Two consecutive failures delete the state machine and keep the nine rows.

### 12.4 Grader letter grades and the band cuts

A+ ≥ 0.90 · A ≥ 0.80 · B ≥ 0.65 · C ≥ 0.50, per playbook.

**Promote when:** ≥150 logged trades allow each playbook's cuts to be fitted on its own data and the fit holds on its declared holdout. **Per playbook, not globally** — the six ladders disagreed definitionally, and a single readmission would recreate exactly that. Until then: dimension vector plus rank within today's watchlist (§6.3).

### 12.5 Detector polarity colouring

`_state_cell`'s TRUE/FALSE colouring with `BEAR` inversion, and `GroupScore`'s polarity argument. Deleted in code, not conditioned (§4.1).

**Promote when:** an individual detector's hit rate is measured against forward excursion on slice 017's replay and **separates outcomes on a declared holdout** — stated `on trades taken, n=…` — the tape corpus covers traded symbol-days only, so a detector is tested for **lift over the bar-derived base rate on the archived watchlist** (§7.2), never against a universe it never saw. Adjudicated in slice 018. Per detector — the whole point of reducing 22 to 11 was that they were not independent, and readmitting them as a set would re-manufacture the confirmation.

### 12.6 Stop modes attached to indicators

The five modes in §7b.2 all resolve to **price structure** — VWAP, a session extreme, a bar extreme, or a number you type. A later version adds stops that attach to an **indicator**:

| Deferred mode | Resolver |
|---|---|
| **Moving-average stops** | 9 / 20 EMA on the playbook's intraday timeframe; 10 / 20 / 50 SMA daily |
| **ATR band** | a multiple of ATR trailing from the extreme, evaluated on bar close |
| **VWAP deviation band** | 1σ / 2σ rather than a fixed offset |
| **Anchored VWAP** | anchored to the gap, the catalyst bar, or the base low |
| **Swing / fractal** | the last confirmed swing low, which needs a confirmed-swing definition |

**Why they are not in core, and it is not effort.** A moving average is not a level until it has been tested. §6b.1a already says this: every MA carries a **claim state** — `untested · claimed · lost · reclaimed` — with the crossing timestamp. **A stop at an untested 20-EMA is a stop at an arbitrary line that happens to be nearby**, and it will render identically to a stop at a level the market has defended three times. That is the project's signature defect wearing a stop's clothes.

So the dependency is real and ordered: **the MA claim-state machine must be built and running before an MA can be a stop resolver.** When it is, the mode arrives nearly free — the resolver returns the MA price *plus its claim state*, and the row renders `20-EMA 47.88 — claimed 09:41, held 2×` or refuses with `20-EMA untested today — not a level`.

**Promote when:** the claim-state machine ships (slice 012b) **and** the trade log shows at least 20 stops placed at structural levels that coincided with an MA, so there is something to compare against. Until then the price override covers the case manually, and the record shows you chose it.

**The offset (§7b.2) applies unchanged** — an indicator-attached stop still sits beyond its level by `stop_offset`, for the same reason.

### 12.7 Capture the whole day, including what the terminal never shows

**Write everything about a trading day into one store** — not only what the terminal renders, but the material that shaped the day from outside it: the pre-market macro read, the news that moved a name, the external dashboards you consulted, the calendar, the regime prose. Over time that store becomes the only place where *"which of these actually related to good outcomes"* can be asked at all.

**Tenet 7 is the licence: display is not storage.** Capture is already specified as a superset of display (§2.2, §4.3) — this extends the same principle past the terminal's own boundary. A hidden indicator is still recorded; so should be a news headline you read on another screen.

**Why capture belongs early even though the analysis is far away.** Capture is cheap and **irreversible if skipped** — you cannot go back and record what the tape felt like on a morning you did not record, and news and dashboard state are the least reconstructible data in the whole system. Analysis is expensive, gated, and can start at any time on a store that already exists. **The asymmetry is the entire argument**, and it is the same one behind pulling replay data on the day rather than when a question arises.

**What it must carry, or it is unusable later.** Every captured item declares **source · as-of · capture method · whether it was seen before or after the trading decision**. That last field is not optional: an article timestamped 10:14 that you read at 16:00 has no bearing on a 09:31 entry, and a store that cannot separate the two will manufacture hindsight relationships on its first query.

**The hard boundary, and it is the reason this sits in §12 rather than in core.** This store is precisely the apparatus for the thing the tenets forbid: mining a dataset for correlations with outcome. §10 already rejects *auto-generated features — cannot be pre-registered with a predicted direction*, and `phase-3-halted.md` is halted. So:

> **Capture is unconditionally permitted. Querying it against outcomes requires a pre-registration with a predicted direction, declared before the query runs.**

Nothing about building the store releases that gate, and the store must not ship with a general "find what correlates" surface — that is not a feature awaiting priority, it is a feature the tenets rule out in that shape.

**A naming point, because this project has been bitten by it repeatedly.** This is **not "Layer 2 work."** Layer 2 already means *your own breakout follow-through per playbook* (§5.3). Calling the capture store Layer 2 would put two different things behind one name, which is the failure Amendment 7 exists to stop. **It is a later-phase work item**, and it is named `day_context_store` here so it cannot be confused with a layer.

**Capture starts now — decided.** A capture step joins slice 009. Only the *analysis* waits for the trade log and a pre-registered question (§8.3's floor).

**The two things that make an early store worth having rather than rotting.** Write it **append-only, one file per session, with every item carrying `source · as-of · capture method · seen-before-or-after-the-decision`** — and **do not design a schema beyond that.** A rigid schema chosen now will be wrong; a timestamped append log of self-describing items cannot be, because re-interpreting it later is a read-side problem. **The failure mode to avoid is not a wrong schema, it is a store that silently stops being written to** — so the day record carries `context_captured: n items` and the review surface shows a session with zero as a gap, not as a quiet day.

### 12.11 Several symbols attached at once

Three tickers watched simultaneously. **The data budget already allows it** — 3 of 5 tick slots, 3 of 3 depth — so this is a rendering and record-shape change, not a capability one: `attached` becomes a list (§6b.1c), and the pane must show three symbols without shrinking any below legibility.

**The constraint is decided now and is not negotiable later: one process, never several.** Two processes means two writers on a slot ledger that only works with one, two client IDs on one pacing budget, and two day records for one session — which breaks `renderer(record)` as a pure function.

**Promote when:** the single-symbol pane has run for a month and `config/layout.yaml`'s history shows what you actually watch. **The real question is not feasibility but attention** — whether three symbols watched partially beats one watched properly — and that is answerable from usage rather than from argument.

### 12.8 The prioritisation pass — the next piece of work, not a deferral

Everything in §12 is *deferred with a criterion*. What does not yet exist is a **single ranked order across all of it**, and it is the next thing to produce: indicators, grader dimensions, stop modes, order-creation features, regime rows, detector components and backtesting each currently carry their own local ordering, and nothing reconciles them against one another.

**The axis, so the pass is fast when it runs.** Rank every candidate on three questions, in this order:

1. **Does anything downstream block on it?** The trade log blocks Layer 2, grader calibration, the similarity prior and every override-rate measurement — which is why it is core and early despite being unglamorous. Blockers outrank everything.
2. **Does it change a decision on a real trading morning?** Not "is it interesting" — does its absence cost you a trade or cost you money. Most of the corpus fails here, and that is the finding.
3. **Can it be built without fitting anything?** Anything requiring a fit is gated behind the log by construction, so it cannot be core no matter how valuable.

**The output is one table, not seven** — every candidate from every family in one order, with its family named, so the comparison that has never been made can be made: *is the fifth-best indicator worth more than the second stop mode?* Today those live in different documents and are never weighed against each other, which is how scope grows without anyone deciding.

**Run it once the inputs stop changing**, and treat the result as the reordering of `BUILD-PLAN.md` §2 rather than a new document.

### 12.9 Source decision layer — IBKR where free, Databento otherwise

Routes each (symbol-day, schema) to the cheaper adequate source. **Acceptance test is parity**: pull the same symbol-day from both, compare bar-for-bar, require agreement or an explained difference. Every stored symbol-day carries its source, so a mixed series can be decomposed.

**Promote when:** core has run against Databento long enough to be the reference, and open decision 6's IBKR capability test (§11) has an answer. **Not before** — a source layer built before there is a trusted reference has nothing to be tested against.

### 12.10 Any enforcement at all

**No criterion is offered.** §4.2 is a standing architectural rule, not a stage. If a future version enforces something, that is a deliberate reversal made by you in writing — not a threshold quietly crossed. The one item where the evidence genuinely argues the other way is the daily loss limit (§11.8), and it is listed as an open decision rather than a promotion criterion for exactly that reason.

---

## 13. Sources — the Drive and OneDrive entries are HUMAN-REACHABLE ONLY

**Read the qualification before the list.** Only the `Repo:` line is reachable from this
tree. **The Drive and OneDrive entries below resolve for Christoph, on his machine, and for
nobody and nothing else** — the Drive sync was removed on 2026-08-09, so no path on disk
points at them, and `tests/test_spec_pointers.py` deliberately excludes external and absolute
paths, which means it will never flag them however stale they become.

This is the exact mechanism that cost Layer 0: a source that reads as live, is cited like
every other source, and is reachable by one person. Cite them; do not plan work that assumes
a session can open them.

Repo: `D:\Dev\CLAUDE.md`, `momentum-harness/CLAUDE.md`, `docs/specs/`, `docs/observations/`, `handoff/`, `harness/config/preregistration.yaml` (v25).
Drive **(human-reachable only)**: 123 documents across three folders (see `DRIVE-ARCHIVE-LIST.md`).
OneDrive **(human-reachable only)**: `D:\chbichOneDrive\OneDrive\Documents\_Trading`, 425 files.
External research: Song & Szafir (VIS 2018) · Daniel & Moskowitz *Momentum Crashes* · Gao/Han/Li/Zhou *Market Intraday Momentum* (JFE 2018) · Lou/Polk/Skouras *A Tug of War* (JFE 2019) · Zarattini/Barbon/Aziz (SSRN 4729284) · Bailey & López de Prado *Deflated Sharpe* · Harvey/Liu/Zhu (RFS 2016) · Dawes (1979) · Kaminski & Lo *When Do Stop-Loss Rules Stop Losses?* · Coval & Shumway (JF 2005) · Gollwitzer & Sheeran (2006) · KC Fed RORO wp 24-12 · FINRA Information Notice 05/10/19 · State Street buyback study · Schwager & Coyle *Market Wizards: The Next Generation* (2026) · Databento, IBKR, Textual documentation.
