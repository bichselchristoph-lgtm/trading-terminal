---
id: 087
title: The repaint path — the age that reads 0s, the flicker, and the stream that dies unmarked
type: task
class: product
story: S038
epic: 4
owner: claude-code
depends: none
touches: the repaint path, the stream lifecycle, the ATTACHED header, the HEALTH stream rows
mockup: ATTACHED mockup — the context block and its states
uat: c047
bugs:
  - id: B-140
    action: close
    status: "Fixed. The age was always computed correctly at paint time; the bug was that nothing ever triggered a paint except a stream push, so a fully-stalled row froze at its last painted value forever. Fixed with a genuine periodic repaint (`REPAINT_INTERVAL_S = 1.0`, `self.set_interval` in `on_mount`), made affordable by B-141's fix — before that, every tick would have forced a full remount. Confirmed red (age stuck at 0/0/0/0 across 4 real seconds) with the timer disabled, green restored."
  - id: B-141
    action: close
    status: "Fixed. `_rerender()` called `_apply_fit(force=True)` unconditionally, and `force=True` meant an unconditional `frame.remove_children()` + `frame.mount(...)` — every landed value cleared and rebuilt the ENTIRE DOM under #frame. Fixed: `_apply_fit` now updates each already-mounted panel's own content via `Panel.update()` (Textual diffs this; it cannot diff a remove-then-mount) when the panel SET is unchanged, and only remounts on a genuine structural change (first mount, or a too-small transition). Confirmed red (a landed value forced 1 full remount) by temporarily forcing the old always-remount path, green restored."
  - id: B-143
    action: close
    status: "Fixed, both halves. HEALTH's stream rows now carry the same `stale Ns` marker the ATTACHED header uses, at the same STALE_THRESHOLD_S=20s, reusing `_stale_suffix` directly rather than a new vocabulary. A row that sits `pending` past a new, configured, UNFITTED bound (`config/pending.yaml`, `pending_timeout_s`, default 90s) now renders a named refusal (`Cell.absent`'s existing shape) instead of silent `pending` forever. Both confirmed red by temporarily disabling each in turn, green restored."
---

**Status** RUNNING

# 087 — one reading of the repaint path settles three defects

**This note needs to be pasted to chat.**

---

## A concurrent-session finding, stated first because it shaped how this task was worked

**Two peer sessions were active in this same working tree for the duration of this task**: `momentum-32` (idle/waiting, ~34 minutes old at the time this note was written) and `momentum-de` (busy, ~1 day old). `momentum-32` had left **substantial uncommitted, in-progress work for task 088** ("ADR% day boundary") sitting directly in `live/attach/attach.py` and `live/tui/app.py` — the SAME two files this task needed to edit, discovered via `git diff` showing `today_et`/"session not started" logic that had never been committed (`git log -S "today_et"` returns nothing).

**Consequence for how this task was executed, stated plainly:**
- Every edit in this task targeted precise, hand-verified anchor text, re-read immediately before editing, never a blind offset.
- `git stash` was **not used** for red-before-green verification — stashing the whole file would have swept up 088's uncommitted, untested, in-progress work along with this task's own changes, and popping it back is not guaranteed lossless under a live concurrent edit. Instead, each of the three fixes was verified red-before-green by a **targeted temporary revert of that fix alone** (commented out / short-circuited, tests run, then restored), leaving 088's own hunks completely untouched throughout. See the Tests section below for each.
- **The closing commit is scoped by hunk, not by whole file** — `attach.py`/`app.py` carry both sessions' uncommitted work, and only this task's own hunks are staged (`git add -p`), leaving 088's own work exactly as `momentum-32` left it, for that session to commit on its own.
- Two pre-existing test failures were observed during this task's own verification runs (`test_a_key_press_renders_the_context_block_not_only_the_symbol`, `test_an_explicit_failure_refuses_a_row_the_baseline_does_not`), both showing `ADR% used — (session not started)`. **Confirmed by direct reading, not fixed here**: `test_attach.py`'s `Fake.dailies()` fixture generates bars dated in June every year, which can never equal `today_et` (today's real ET calendar date) under 088's new day-boundary check — this is 088's own incomplete work interacting with fixtures nobody has updated for it yet, entirely unrelated to anything this task touched. `live/` suite: 217 passed (205 + 12 new), same 2 pre-existing failures, unchanged by this task.

---

## Part 0 — read, then measure, then fix, answered as read

**1. When is the freshness age computed?** `header_freshness()`'s arithmetic (`now() - last_update_at`) was always correct and computed fresh on every call. **The bug is that nothing called it except a stream push.** No `set_interval`/`call_later`/timer of any kind existed anywhere in `live/tui/` before this task (confirmed by grep across the whole module — zero matches). A push also resets `last_update_at = now()` immediately before triggering the one repaint that would show the age, so a healthy, actively-pushing stream always painted an age near 0s — explaining "the header read 0s continuously for a long time." Once the sector stream died and only the symbol stream kept pushing, the header (which reads the OLDER of the two stream ages) kept getting repainted by the symbol's own pushes, each time showing the sector's own genuinely-growing staleness — explaining how `stale 4994s/5010s/6014s` became visible at all despite no timer: the symbol stream's pushes were acting as an incidental repaint trigger for an unrelated row's staleness.

**2. How many repaint paths are there?** **Exactly one** — `_rerender()` → `_apply_fit(force=True)` → unconditional full remount — triggered from every independent callback site (every stream push, every role landing/error). Not two paths with one unnamed; one path whose trigger fires at whatever real-world cadence the underlying pushes happen to arrive at. **Measured live** (see below) rather than argued: the observed "5-10s" cadence (switching among several symbols) and "30s or so" cadence (one quiet symbol over 100 minutes) are the SAME mechanism at different real push rates, not two mechanisms.

**3. Does `_begin_attach` actually tear the outgoing streams down?** The code's own cancel loop (`for handle in self._streams: handle.cancel()`) does call through to the real `ib_async` `cancelHistoricalData` — confirmed by reading `ibkr.py`'s `cancelHistoricalDataStream`. Whether IBKR's own API genuinely stops the server-side subscription on every call is not independently verifiable from this machine without live TWS, but it does not matter for the VISIBLE symptom: `_apply_stream_update`'s generation guard runs BEFORE any repaint, so even a stream that somehow kept pushing past cancellation could never cause a visible repaint from a stale generation — confirmed empirically (see the measurement). Pinned as its own Teardown exit test regardless, since "the code says it does" and "it was observed" are different claims and the task asked for both.

**4. Why does a full-screen flicker occur at all on a framework that diffs?** **Found by direct reading, not inference**: `_apply_fit`'s panel-mounting branch was `if force or self.query("#too-small") or not self.query(Panel): await frame.remove_children(); await frame.mount(...)` — and `_rerender()` (the value-landing path, called from EVERY stream push and role landing) always passed `force=True`. Every single landed value cleared and rebuilt the entire `#frame` DOM tree, bypassing Textual's diffing entirely. `Panel.on_resize()` already had the correct pattern sitting right next to this (`self.update(self.body(w, h))`) — the fix reuses it.

**Nothing in these four reads contradicted the task file.**

---

## Measurement — before any fix, per §2's own instruction

**Does not need live TWS.** Flicker is a property of the repaint mechanism, not of market data — a controlled fake stream (5.0s push cadence, matching 008b's own measured median) exercises the real, unmodified `_apply_fit`/`_rerender` path end to end.

**Deliberately worst-case**: the fake's `cancel()` is a no-op — the stream keeps pushing forever after a switch, exactly the scenario Part 0 item 2's "streams accumulating" hypothesis worries about.

**One, two and four attaches, each run 60 real seconds, recorded separately, never averaged:**

```
1 attach:  remounts=10  intervals(s)=[5.0, 5.02, 5.25, 10.22, 5.02, 5.17, 5.05, 5.02, 7.25]
           median=5.05s  mean=5.89s
2 attaches: remounts=12  intervals(s)=[5.0, 5.02, 5.0, 5.02, 5.0, 5.02, 5.02, 5.0, 5.02, 5.06, 5.0]
           median=5.02s  mean=5.01s
4 attaches: remounts=12  intervals(s)=[5.02, 5.0, 5.02, 5.0, 5.02, 5.02, 5.0, 5.02, 5.0, 5.02, 5.0]
           median=5.02s  mean=5.01s
```

**Which hypothesis this supports: neither, and the measurement says why.** The interval does **not** shorten as attach count rises — it stays fixed at ~5.0-5.05s at 1, 2 and 4 attaches, even with prior generations' streams deliberately left alive and pushing in the background throughout. This refutes "streams accumulating." It is also not literally "a timer" — confirmed absent from the code directly. **The real cause, identified by the measurement's own instrumentation** (`Frame.remove_children`, `_apply_fit`'s own remount call site, spied directly): one remount per landed push, at the push's own cadence, unaffected by switch history — exactly Part 0 item 4's finding, empirically confirmed rather than merely argued.

---

## The three fixes

**B-140.** `REPAINT_INTERVAL_S = 1.0` (a UI-mechanics choice, not a fitted threshold — `header_freshness()` renders whole seconds, so 1Hz is the finest granularity that could ever be visible). `self.set_interval(REPAINT_INTERVAL_S, self._tick)` registered in `on_mount()`; `_tick()` calls `_rerender()`. Affordable only because of B-141's fix — before it, every tick would have forced a full remount, trading one flicker source for another.

**B-141.** `_apply_fit` now distinguishes a structural change (first mount, or entering/leaving the too-small refusal) from ordinary content-only repaints. Structural changes still remove-and-remount. Everything else updates each already-mounted `Panel`'s content in place via `Panel.update()`, reusing the existing widget's own current `content_size` — the exact pattern `Panel.on_resize()` already used for resize, extended to every OTHER repaint trigger. Every `Panel` now carries a stable `id=` (its `render_panels()` dict key) so a later repaint can find and update the SAME mounted widget rather than replacing it. The concurrency guarantee `force=True` used to provide (atomic decision under `_fit_lock`, closing a `060`/B-001-shaped race) is unchanged — the lock still serialises every caller; only the choice of WHAT to do once serialised got cheaper.

**B-143a.** HEALTH's stream rows now append `_stale_suffix(age)` — the exact function the ATTACHED header already uses, at the same `STALE_THRESHOLD_S`. No new vocabulary, per the task's own instruction.

**B-143b.** `config/pending.yaml`'s `pending_timeout_s` (90s, UNFITTED — see the file's own note: chosen comfortably past every live wall time 082 measured, 15-60s+, and far short of the hundred-minute stall this task exists to stop hiding). `Attached.metrics.attached_at` (set once, at stage-1 landing) is the clock a still-pending row measures itself against — `_pending_text(a, what)` renders plain `pending` within the bound, and `Cell.absent(f"no {what} in {int(bound)}s, unfitted").render()` past it, reusing the existing refusal grammar rather than inventing a screen state. Applied to all four pending-capable rows (RVOL own, RVOL sector, ADR% used, VWAP) — `Last $` is untouched, per its own existing "never pending" rule.

---

## Tests — seven exit categories, every fix confirmed red before green

`live/tests/test_087_repaint_path.py`, 12 tests, all self-built (B-136 — checked by the same AST import-inspection 083/084/086 already used).

- **Green ×3**: a landed value updates in place, not a full remount (spies `Frame.remove_children` directly — the exact call site the measurement identified); the age advances across ~3.5 real seconds with the stream frozen after its initial push; the age climbs 1s→4s monotonically over four real seconds with pushes arriving only once. The two age tests genuinely spend real wall-clock time — reading `header_freshness()` directly would prove only the arithmetic, which was never the bug.
- **Refusal ×4**: a dead HEALTH stream (25s silent) is marked `stale 25s`; a borderline-fresh one (19s) is not; a row pending past its (test-local, 1s) bound renders a named, unfitted refusal naming what did not arrive; a row within its bound still reads plain `pending`, and one with no attach clock at all (`attached_at is None`, the state every pre-087 test leaves it at) also reads plain `pending` rather than being misread as infinitely stale.
- **Teardown**: four attaches of the same symbol open four streams and cancel exactly three — `_begin_attach`'s existing cancel loop, pinned rather than trusted.
- **Colour ×2**: `stale` never appears off a fresh reading; it appears on exactly the half of a compound RVOL row whose OWN stream aged past threshold, never bleeding into the other half.
- **Fixture**: the AST check.

**Confirmed red before green for all four fix-specific behaviours** (B-140's timer, B-141's in-place path, B-143a's HEALTH marker, B-143b's pending bound), each via a targeted, temporary, immediately-reverted disable of that ONE mechanism — not `git stash`, for the concurrent-session reason stated above. Each showed the exact expected failure (age stuck at `[0, 0, 0, 0]`; "a landed value forced 1 full remount"; a dead stream missing its `stale 25s` marker; a timed-out row still reading bare `pending`), then was restored and reconfirmed green.

`live/` suite: 217 passed (205 before this task's own 12 additions), the same 2 pre-existing failures from 088's concurrent uncommitted work, unchanged.

---

## What you may NOT do — confirmed untouched

`ADR% used` — untouched by this task (088's own, uncommitted, concurrent work touches it; this task's diff has zero lines in that computation). `request_timeout_s` — untouched. No new screen state invented — HEALTH reuses the existing `stale Ns` marker verbatim; the pending bound reuses the existing `Cell.absent` refusal shape verbatim. Nothing 078/080/083 built was weakened — the `live/` suite's only two failures are attributable entirely to 088, confirmed by reading, not by this task's own changes.

---

## UAT

`christoph/open/047` — live, not performed here, per the task's own instruction.

---

## Closing sequence

`verify.ps1` runs as the last action, not pasted or summarised here. `export-handoff.ps1`/commit/push follow, scoped to this task's own files AND, within `live/attach/attach.py` and `live/tui/app.py` specifically, to this task's own HUNKS ONLY — `git add -p`, leaving task 088's own uncommitted, in-progress work in those same two files exactly as `momentum-32` left it, for that session to commit on its own. The tree continues to hold other unrelated synced content from Christoph/Drive, deliberately left untouched, per the same precedent 083/084/086 already recorded.

**This note needs to be pasted to chat.**
