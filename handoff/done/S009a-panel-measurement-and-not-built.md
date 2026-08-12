---
id: S009a
title: The panel is never measured against the space it is given
status: RUNNING — stays RUNNING until this note reaches the design session
owner: claude-code
ran: 2026-08-12, 05:40 → 06:20 ET
tree: D:\Dev\momentum
---

# S009a — the panel measured against its tile, and the twelve stages declared

**Status** RUNNING

**Parts 1, 2 and 3 are complete. Part 4 ran and returned an answer, but not the
answer the task asked for** — it was written for after 16:00 ET on the 11th and
ran at 06:05 ET on the 12th, so the post-session question is untouched. See §4.

> **This note has to be pasted into chat.** Writing it is not reporting it. On
> 2026-08-11 `012a` and `013` both wrote correct done-notes that never reached
> the design session, which went on holding a stale `RUNNING` for both.

---

## The number that made all of it fail

**Christoph's terminal is `209 x 54`**, measured with `$Host.UI.RawUI.WindowSize`
at the size and font he trades at:

```
Width Height
----- ------
  209     54
```

Three tiles across 209 columns, minus 2 columns of `padding: 0 1` per tile,
gives each panel **~67 columns. `BOX_WIDTH` is 71.**

**Four columns. That is the entire caption-wrap defect**, and it is why a suite
of 80, 120 and 240 could not see it: **80 and 240 straddled 209 without covering
it.** The task called this *"a well-formed suite answering a different
question"*, and the measurement confirms it exactly — nothing was subtly wrong,
the panel was simply four columns wider than the space it had, every time, on
every panel.

`209 x 54` is now the **primary snapshot width**, with that reason recorded
beside it in `WIDTHS`.

---

## Part 1 — the three width defects

One root cause, fixed once. `Panel.body(width, height)` now takes both
dimensions; `on_resize` feeds it `content_size`; **every width-dependent thing —
border, caption, body rows, pinned separator — is computed from what the tile
actually got.** `BOX_WIDTH` survives as *the width the panel is designed at and
every canonical snapshot is taken at*, and is no longer the width it renders at.

### 1a — the caption-fitting rule, and which end gives way

**THE CAPTION GIVES WAY. THE TITLE NEVER DOES.**

The title is what identifies which tile you are looking at. You can still ask
what the as-of stamp said; you cannot ask which panel asked it. So the
provenance truncates from its right and **renders the loss** as `…`, and the
ellipsis is charged to the width budget so the marker cannot itself overflow.

At `209` nothing truncates at all — every caption fits in 67 columns with room
to spare. The rule matters at `80`, where each tile gets 24:

```
┌─ ATTACHED ─ not att… ┐          # 24 columns, caption cut, title and corner intact
┌─ WATCHLIST ─ no ing… ┐
```

**A defect I introduced and then caught, worth recording because it is the same
shape as the one being fixed.** The first version budgeted the caption at
`width - left - 3` while `box_top` actually spends 4 (one rule character, two
spaces, one corner). The line came out **one column over**, and the final
guarantee-fit then truncated the *border* instead of the caption:

```
┌─ ATTACHED ─ not atta……          # two ellipses, and no ┐ at all
```

That is the caption giving way twice and the border giving way once — a double
truncation. Fixed to `- 4`, and **the same `+4` had to be mirrored in
`min_width`**, or the derived minimum would admit a width at which the caption
is cut below its own stub.

### 1b — the body

Every line passes through `fit()`.
`test_no_line_ever_exceeds_the_width_it_was_given` sweeps **widths 22–120 across
all seven panels** and asserts no rendered line exceeds the width it was handed.
That is the assertion `S009` had no way to make: `_body()` took no width, so
there was nothing to compare against.

The pinned separator was `(BOX_WIDTH - 4)` regardless of tile — that is the
stray `--` you saw under SIZING and RISK. It is now `width - 4`.

### 1c — the guard, and the per-tile minimum

**This was the real bug.** `S009` compared the *window* against a fixed `60×16`.
A 1920 window split three ways satisfies `60×16` while every tile is starved, so
**the guard could not fire at the size that actually broke** — and what rendered
was the silently clipped panel §4e forbids.

Replaced with a per-tile check whose minimum is **derived from each panel's own
content**:

| panel | min_width | min_height |
|---|---:|---:|
| WATCHLIST | **23** | 3 |
| ATTACHED | 22 | 3 |
| PIPELINE | 22 | 3 |
| SIZING | 20 | 5 |
| HEALTH | 20 | 5 |
| TAPE | 18 | 3 |
| RISK | 18 | 5 |

**Shipped layout requires `75 x 11`**, driven by `3 tiles x 23 cols for
WATCHLIST + 2 padding` — a string the refusal message carries, so it names the
tile that ran out rather than only the window.

**How it is derived rather than fixed.** Two things may not give way:

1. **Title + a provenance stub.** §4d makes an unstamped panel the `[ STALE ]`
   anti-state, so a border with no legible caption is not a narrower panel, it
   is a different and worse one. `PROVENANCE_STUB = 6`.
2. **Every pinned row's label.** §4e's band exists so a failed rule survives
   scrolling; a pinned row cut past its label is a failed rule rendering as
   punctuation. **The label boundary is derived from the row itself** — the text
   before the first run of two or more spaces, which is how every pinned row in
   the module separates name from value.

`test_the_minimum_is_derived_from_each_panel_and_not_a_fixed_number` lengthens a
title and lengthens a pinned label and asserts the minimum moves. A fixed number
would not.

**The regression is pinned as the comparison that failed.** `BELOW_MINIMUM =
(74, 24)` **clears `60×16` in both dimensions** — so the old guard passed it and
let three starved tiles render, and the new one refuses.
`test_the_guard_measures_the_tile_and_not_the_window` asserts that fixture
property explicitly, so the test cannot quietly stop demonstrating the defect.

### The same defect in the dimension nobody looked at

`viewport` was fixed at 8. A panel handed six lines rendered nine and let the
layout clip the surplus **with no trace** — §4e's *"nothing more here" versus
"more below"* failing in the direction the rule was written for. The viewport is
now measured from the height given, so a short tile reports `+N more ↓` itself.

---

## Part 2 — the pinned widths

`WIDTHS` in `live/tests/test_tui_measured_against_its_tile.py`, each carrying
its reason, per *"do not add a width without a reason recorded next to it"*:

| size | tile | why |
|---|---:|---|
| **209 × 54** | **67** | **Christoph's working terminal.** Measured, not derived from 1920 pixels — font size decides columns and only the terminal knows. The width the suite missed |
| 80 × 24 | 24 | the floor, inherited. Also the **tightest passing case**: 24 against the 23 WATCHLIST needs — one column of slack |
| 240 × 70 | 78 | the ceiling, inherited |
| 74 × 24 | 22 | **one column below the derived minimum.** Refusal A: the too-small state renders and zero panels do |

`test_every_width_records_why_it_is_here` fails on a width whose reason is under
30 characters, so the list cannot grow by guessing.

**Snapshots are taken at the TILE width, not at `BOX_WIDTH`.** `S009`'s were all
at the design width, which is precisely why they could not see this: the thing
that broke was the *difference* between design width and tile width, and nothing
sampled it. Three new files — `tile-80x24.txt`, `tile-209x54.txt`,
`tile-240x70.txt`. **No existing snapshot was weakened or deleted;
`empty-record.txt` was regenerated only because the PIPELINE panel is new.**

---

## Part 3 — the twelve stages, and what the compact form cost

All twelve are declared in `config/layout.yaml` under a new `stages:` block, and
render as **one PIPELINE panel, one row per stage**, in a third tile row:

```
┌─ PIPELINE ─────────────────────────────────────── 1 of 12 built ┐
   1 ingest      [ NOT BUILT · S013 ]
   2 regime      → HEALTH panel
   3 indicators  [ NOT BUILT · S010 ]
   4 rank        [ NOT BUILT · S014 ]
   5 [HUMAN]     your decision - correctly not a slice
   6 size        [ NOT BUILT · S011 ]
   7 stage       [ NOT BUILT · S017 ]
   8 [HUMAN]     your decision - correctly not a slice
   9 manage      [ NOT BUILT ] (slice not assigned)
  10 reconcile   [ NOT BUILT · S015 ]
  11 journal     [ NOT BUILT · S015 ]
  12 archive     [ NOT BUILT · S013 ]
  12 of 12 · end
```

**At 209 × 54 all twelve rows render**: three tile rows of 18 lines each, so the
panel's measured viewport is 16 against 12 stages.

### What the compact form cost

**Chosen:** one panel, one row per stage, taking an ordinary `1fr` row like every
other tile.

**Cost 1 — no per-stage provenance.** A stage row has no border of its own, so
it cannot carry a source or an as-of stamp. The moment a stage is *built*, its
row can say `built` and nothing else; the real content needs a real panel. **So
every future slice that fills a stage must also graduate it out of PIPELINE and
leave the row pointing at the new panel** — the way `regime` already points at
HEALTH. If that is forgotten, a built stage renders as one line of nothing.

**Cost 2 — at the 80-column floor it is unreadable.** 24 columns per tile
truncates every stage row at `[ NOT …`, so at the floor the panel says *twelve
stages exist* and cannot say *which slice fills which*. It is honest — the
truncation renders — but it is not useful. At the working width this does not
arise.

**Cost 3 — vertical space is now shared three ways instead of two.** The two
tile rows dropped from ~27 lines each to ~18 at 209 × 54. Nothing is clipped, and
the measured viewport means any future crowding reports itself rather than
silently cutting. `test_the_pipeline_panel_does_not_crowd_out_the_built_ones`
pins `min_height == 3`, so the panel can never demand space from SIZING or RISK.

**Rejected:** a three-by-four grid of short cells (6 lines total). It cannot
carry *"`NOT BUILT` with the slice that will fill it"*, which the task requires,
without a legend — and a legend is a second thing to read.

### Refusal C — distinguishable without colour

`[ NOT BUILT · S010 ]` is a **bracketed badge**; `— (no account snapshot)` is an
**em-dash and a parenthesised reason**. *The machinery does not exist* against
*the machinery exists and the input is missing.* The test reduces both to their
character classes and asserts the shapes differ, so the distinction cannot
degrade into wording. **No colour is involved anywhere.**

### `regime` is not a stage that is coming

Declared as `renders: HEALTH` and asserted **not** to render `NOT BUILT`, per
`SPEC.md` §3.2. `test_regime_is_not_a_not_built_panel` pins it.

### A finding: `manage` has no slice, anywhere

**`BUILD-PLAN.md` §3–4 contains no slice that builds position management.**
Reconciliation appears inside `S017`'s eleven pre-send checks and `S015`'s
execution pull; journal is in `S015`'s title; nothing covers managing an open
position. It renders `[ NOT BUILT ] (slice not assigned)` rather than carrying an
invented number — **a plausible slice id would be read later as a record**, which
is this project's canonical defect.

**Two attributions are my reading of slice titles, not statements the plan
makes**, and should be checked: `indicators → S010` (*"Attach a symbol, and the
context block"*) and `reconcile → S015` (*"Execution pull, trade log, and
review"*). The other seven quote a slice title that names the stage directly.

The loader refuses a stage making more than one claim about its state
(`built_by` / `slice` / `human` / `renders`), because the second would be
silently lost behind the first.

---

## Part 4 — the depth probe, and what it does NOT establish

Ran **2026-08-12 at 06:05 ET** (server time `10:05:59 UTC`), `readonly=True`,
`clientId 21`. **`clientId 11` was not reused.** `numRows=10`, one venue at a
time, each cancelled before the next. **No subscription was changed and nothing
was signed up for.**

| venue | qualified to | result |
|---|---|---|
| **ISLAND** | `conId=320227571 exchange=NASDAQ primary=NASDAQ` | **0 bids, 0 asks.** `10089`, then `310` |
| **NASDAQ** | `conId=320227571 exchange=NASDAQ primary=NASDAQ` | **0 bids, 0 asks.** `10089`, then `310` |
| **ARCA** | `conId=320227571 exchange=ARCA primary=NASDAQ` | **8 bid levels, 9 ask levels. Zero error events** |

```
code 10089  Requested market data requires additional subscription for API.
            See link in 'Market Data Connections' dialog for more details.
            QQQ NASDAQ.NMS/DEEP
code 310    Can't find the subscribed market depth with tickerId:7
```

```
BID 0 723.03 x 320    ASK 0 723.12 x 280
BID 1 723.02 x 220    ASK 1 723.10 x 200
BID 2 722.97 x  80    ASK 2 723.33 x  40
BID 3 722.36 x  51    ASK 3 723.72 x  83
BID 4 722.01 x  53    ASK 4 723.75 x 350
BID 5 722.00 x4015    ASK 5 723.97 x  41
BID 6 723.04 x 200    ASK 6 723.98 x  59
BID 7 723.00 x  40    ASK 7 723.09 x 300
                      ASK 8 723.11 x 301
```
`marketMaker` is empty on every row.

**The 10089 is unchanged in code and in message from `012a`'s 05:07 ET result.**

**What this does not establish, stated because the temptation is the whole
lesson of `012a`:** nothing here says whether the affirmation was applied,
propagated, or took effect. The probe returns a refusal code and its literal
text. Any statement about the account's entitlement state is an inference, and I
am not making one.

**`ISLAND` and `NASDAQ` are not two probes.** `qualifyContracts` collapsed
`ISLAND` to `exchange=NASDAQ` — **identical `conId`, identical response**. The
task's three-venue sequence returned **two** distinct answers. So the question
*"if ISLAND now serves the book, tomorrow's 016 takes TotalView instead of
ARCA"* did not get a separate ISLAND answer to fail on.

### Post-session availability: NOT ANSWERED

The task gates part 4 on *"after 16:00 ET, once 012's capture has closed"*. The
capture closed 2026-08-11 at 16:00 ET and was reported; this ran the **next
morning at 06:05 ET**. **So the post-session question is untouched and stays
open.**

What it does give is a cleaner control than intended, **stated as an
observation**: `012a` at 05:07 ET and this at 06:05 ET are the same pre-market
window either side of the affirmation, same instrument, same venues — and the
answer did not move. **Whether depth behaves differently after the close is
still unknown, and one probe at 16:30 would settle it.**

### An observation on the ARCA book that may matter to the capture

**The rows came back out of price order.** Best bid by price is `723.04` at
**index 6**; index 0 is `723.03`. Asks likewise — `723.09` at index 7 beats
`723.12` at index 0. **`domBids[0]` was not the best bid at this instant.**
Positional DOM rows updating in place would explain it.

**Why it matters:** `012` captured 2,149,968 ARCA depth records, and any consumer
that assumes index 0 is the top of book would be wrong. **What would settle it:**
check whether `tools/capture_tape.py` recorded the row *position* alongside
price. If it did, the capture is fine and only the consumer is at risk; if it did
not, the ordering cannot be reconstructed. **I did not check, and I did not touch
`records/tape/`** — the task forbids it and the retention position is still
Christoph's.

**Book thinness pre-market:** 8 and 9 levels against a requested 10, with a
4,015-share resting bid at the round `722.00` dominating everything above it.

---

## Exit tests

| Test | Result |
|---|---|
| **Green** | `3 failed, 125 passed in 128.27s`. Two pre-existing, **one caused by this note and owed to the design session** — named below |
| **Refusal A** | **PASS** — `test_refusal_a_below_the_per_tile_minimum_no_panel_renders`. At 74×24 the too-small state renders and `query(Panel)` is empty. This is the case that shipped broken |
| **Refusal B** | **PASS** — `test_refusal_b_a_long_caption_is_truncated_and_the_loss_is_visible`. Border exactly the width given, title intact, ellipsis present, original caption absent |
| **Refusal C** | **PASS** — `test_refusal_c_not_built_and_data_absent_differ_without_colour`. Badge vs em-dash, asserted at character-class level |
| **UAT** | **Christoph — and it is OWED A FILE.** Re-run at 1920×1080 maximized and at the small size that broke. `tests/test_uat_has_a_file.py` is **red until `christoph/open/NNN-s009a-*.md` exists** declaring `**Slice** S009a`. The design session authors it; Claude Code never writes to `christoph/` |

### The suite, verbatim

```
FAILED tests/test_regime_snapshot_path.py::test_no_legacy_regime_snapshot_path
FAILED tests/test_spec_pointers.py::test_claude_md_pointers_resolve
FAILED tests/test_uat_has_a_file.py::test_every_declared_uat_exists_as_a_file
3 failed, 125 passed in 128.27s (0:02:08)
```

**Against `012`'s baseline of `2 failed, 102 passed`: +23 passed, +1 failure.**
The new file contributes 24 tests; one of them is the third failure below, which
is not a defect. `live/tests` alone: **52 passed, 0 failed.**

**None of the three is `test_uat_has_a_file`'s five historical notes.**

**3 · `test_every_declared_uat_exists_as_a_file` — CAUSED BY THIS NOTE, AND IT IS
THE TEST WORKING.** `015` built it so a UAT named in a done-note's exit table
must exist as a file Christoph will open. This note's exit table names one, and
**nothing in `christoph/` declares `**Slice** S009a`** — so it is red:

```
S009a-panel-measurement-and-not-built.md  ->  needs a file declaring **Slice**/**Task** S009a
```

**I have not cleared it, and must not.** `CLAUDE.md`'s handoff table marks
`christoph/open/` as *"Never write here"*, written by chat. **The design session
authors the UAT file and Christoph saves it.** This is the seventh-instance
pattern `015` exists to catch, firing on the first note written after it: a UAT
that lives only inside a done-note sits in a folder nobody opens again.

**It is red until that file exists. That is the intended behaviour, exactly like
`test_open_questions.py`.**

**The other two are pre-existing and unrelated:**

1. `test_no_legacy_regime_snapshot_path` — `christoph/done/006-h8-snapshot-path-fills.md:12`
   cites `claude/regime-snapshots/`. A historical citation in a folder the test
   does not exempt. Same shape as the `RE-SUPPLY.md` case H11 fixed by rewording.
   Reported in `012`'s note; unchanged.
2. `test_claude_md_pointers_resolve` — `CLAUDE.md:159` names `` `done/` ``, which
   does not resolve from the repo root; it means `christoph/done/`. **New since
   CLAUDE.md v1.1.** This is the *"path is wrong"* branch of the test's own
   message, not the *"widen the exclusion list"* branch. One word, but the file's
   version-history rule makes it a v1.2, so it was not touched.

---

## Divergences from what was on disk

**1 · Part 4 could not answer the question it was written to ask.** It is gated
on *"after 16:00 ET"* and ran at 06:05 ET the following morning. Reported as what
it is rather than relabelled.

**2 · The three-venue probe returned two answers.** `qualifyContracts` collapses
`ISLAND` into `NASDAQ`. Not a divergence I chose; worth knowing before `016`
plans around ISLAND as a distinct venue.

**3 · The 80-column floor now has one column of slack, not three.** Deriving the
minimum honestly put WATCHLIST at 23 against the 24 a tile gets at 80. It passes,
but **80 is now the tightest case in the suite**, and any panel title longer than
`WATCHLIST` will push the requirement past it. Left as-is: the floor was
inherited from `S009` §5 and dropping it is not this task's call.

**4 · `test_a_too_small_window_says_so_rather_than_clipping` still calls
`too_small_message(40, 10, 60, 16)` directly.** Those arguments no longer come
from anywhere in the app — the fixed `60×16` is gone. The test is not wrong: it
checks the *message*, which still narrows to one meaning. But the numbers in it
now read as a live minimum and are not one. **Not changed, because the task says
do not weaken an existing test** — flagged so the next reader is not misled.

**5 · `christoph/` has `012b-uat-basis-correction.md` in both `open/` and
`done/`.** Consistent with copy-verify-retire mid-flight, so probably just
unfinished rather than wrong. Not touched — `HANDOFF-PROTOCOL.md` §"christoph/"
says Christoph performs all three steps and no Claude writes to either folder.

**6 · Nothing was adopted, and no module from `live/` was adopted.**
`SPEC.md`, `BUILD-PLAN.md`, `REGIME-PROMPT.md` and `HANDOFF-PROTOCOL.md` are
untouched. The probe script lives in the session scratchpad, not in the tree —
it is a one-shot probe, and putting it in `tools/` would require a provenance
companion and a behavioural test for something that will not run again.

---

## Files

| file | change |
|---|---|
| `live/tui/app.py` | `fit()`, `_label()`, width/height-aware `Panel.body()`, `min_width()`, `min_height()`, `on_resize()`, caption rule in `box_top()`, `pipeline_panel()`, per-tile guard in `required()`/`compose()`. `MIN_COLS`/`MIN_ROWS` removed |
| `live/tui/grammar.py` | `Cell.not_built(reason, slice_id)` — the badge now names the slice |
| `live/tui/layout.py` | `Stage` dataclass, one-claim validation, `Layout.stages` |
| `config/layout.yaml` | `pipeline` component; `stages:` block with all twelve |
| `live/tests/test_tui_measured_against_its_tile.py` | **new**, 24 tests |
| `live/tests/snapshots/tile-{80x24,209x54,240x70}.txt` | **new** |
| `live/tests/snapshots/empty-record.txt` | regenerated — PIPELINE added, nothing else changed |

**Nothing in `live/tests/test_tui_frame.py` was weakened, deleted or edited.**

---

**Paste this into chat. `S009a` stays `RUNNING` until it lands there.**
