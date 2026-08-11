# S009 — The TUI frame, the refusal grammar, and a thin day record

**Status** DONE · **Date** 2026-08-11 · **Type** build slice + spec amendment
**Runs in** `D:\Dev\momentum`. No TWS, no market data, nothing under `records/tape/`. **Safe alongside the capture.**
**Start after** `013c` has reported. Not before — it edits `handoff/` and `docs/specs/`, and two writers in one tree is how today's confusion started.

> Read this cold. The session that wrote it cannot answer questions.
> **This is the first thing in this project Christoph can look at.** Everything before it was plumbing.

---

## Why

Ten months of specification, four mockup sets, and no panel has ever rendered. This slice ends that.

**It is deliberately the slice with no data behind it.** `009` in `BUILD-PLAN.md` builds the frame and the refusal vocabulary before any panel has content to argue about. The app boots on an **empty day record** and every surface renders as a named refusal — no crashes, no blanks, no zeros.

That makes it the one slice whose acceptance test is the project's core conviction, stated as a runnable thing: *a panel that renders a value with nothing behind it is worse than a panel that renders nothing.* Layer 0 rendered as an operational reading when none of its fourteen rows existed. A snapshot test is the version of that warning which fails.

---

## Part 1 — Amend `BUILD-PLAN.md` in place

**Edits to the file on disk. Do not re-author it and do not accept a replacement from outside the tree** — `RE-SUPPLY.md` exists for exactly this, and `BUILD-PLAN.md` already carries tree-side repairs that a re-supply would silently undo.

**Four repo-facing facts are wrong. Change only these; touch no slice content.**

**1a — Slice numbers collide with handoff task numbers.** `BUILD-PLAN.md` assigns 008–020 to slices. `handoff/inbox/012-*.md` is already the live tape capture, and `handoff/inbox/013-*.md` is the protocol adoption. **BUILD-PLAN's 012 is *tape playbook binding* and today's 012 is *tape capture*** — adjacent subject, different work, same identifier. Someone will read one's done-note as the other's.

**Slices take the prefix `S`: `S008` … `S020`.** Handoff tasks keep bare numbers. Amend the §2 plan block and every slice heading. **The slice contents do not change and must not be rewritten** — this is a renumbering, not a revision.

**1b — The plan names the wrong repo.** §1 says Claude Code builds in `D:\Dev`, cites `momentum-harness/CLAUDE.md` as the handoff authority, and §2.1 of `SPEC.md` names `momentum-harness/` as the umbrella repo. **The build repo is `D:\Dev\momentum`.** `momentum-harness` is archived at `1afcecf` and carries a STOP section. Correct the references in `BUILD-PLAN.md` only; **leave `SPEC.md` alone** — it is a larger change and belongs to its own task.

**1c — The handoff convention has moved.** §1 and §2a describe writing task files into an inbox and a done-note out. That is now `docs/specs/HANDOFF-PROTOCOL.md`, with five states, the copy-and-keep rule, and `handoff/accepted/`. **Point at it rather than restating it** — a convention described in two places diverges.

**1d — "Existing numbering runs to 007, so this plan starts at 008."** True of `momentum-harness`. Under the `S` prefix the sentence is moot; remove or correct it.

**Record in `ADOPTION-LOG.md` or the done-note** — whichever the gate requires for an in-tree spec edit — that this was a repo-facing correction with no slice content changed.

---

## Part 2 — The decision to run `S009` before `S008`

`BUILD-PLAN.md` says **no slice starts while the previous one is un-accepted**, and lists `S008` first.

**`S009` goes first, and this is a decision rather than an oversight.** Record it in the amendment.

`S008` makes `live/` testable — 16 imported files, zero collected behavioural tests, and **an adoption decision nobody has made.** `S009` needs none of it. Deferring the first visible panel behind an unmade decision about an imported tree is how Layer 0 stayed unbuilt while fully specified.

**State in the amendment that `S008` is not cancelled and not descoped**, only reordered, and that its four defects — `condition_codes.yaml`, the session-defined-twice bug, the missing behavioural tests, `regime_pull.py` — remain owed.

---

## Part 3 — One per-module adoption, and it is the first

`BUILD-PLAN.md` step 3 says to port `live/render.py`'s `Result` model into the grammar **unchanged**: `state: Optional[bool]`, `na_reason`, `degraded`, `degraded_reason`. *"It is already right; do not redesign it."*

`live/` is un-adopted in this tree. **Adopt `live/render.py` alone, through the gate, as the first per-module adoption.** Not the tree — the module.

- Origin is `imported`, so **refusal 4 applies**: the companion must record the explicit decision, naming this task and the reason.
- **Refusal 2 applies**: a behavioural test, not an import smoke test. The `Result` model has four fields with meaning — a test must show that `state=None` with an `na_reason` renders differently from `state=False`, and that `degraded` survives a round trip.
- **If adopting the whole module drags in imports that pull the rest of `live/` behind it, stop and say so.** Do not adopt a second module to satisfy the first. Re-author the `Result` model into `grammar.py` instead, note that you did, and record `live/render.py` as still un-adopted. **A cascade through the gate is worse than a re-authored 30-line dataclass.**

---

## Part 4 — Build

Per `BUILD-PLAN.md` §009. All new code, natively authored in this tree — **only part 3 is an adoption.**

**4a — `live/tui/grammar.py`.** The three-axis refusal vocabulary from `SPEC.md` §4 as typed values: `Freshness` (live · aged · stale · frozen-at-HH:MM), `Presence` (present · absent · not-yet-computed), `Confidence` (full · degraded · refused · unfitted), and a `Cell` that renders them.

**This is the only place a value becomes a string.** A cell that is fresh, present and full-confidence renders as a plain number; **any deviation renders differently and renders the reason.**

The canonical vocabulary, from `SPEC.md` §4: `unfitted` · `n/a — <reason>` · `untested` · `partial` · `unavailable (<reason>)` · `absent, not zero` · `superseded` · `flagged, not an error` · `reduced denominator` · `NOT BUILT` · `STALE` · `FROZEN` · `warming` · `no-source`.

**Presence renders `—`, never `0.00`.** That is tenet 2 at the only layer that can enforce it.

**4b — `live/tui/app.py`.** Textual, **pinned version**. A **tiled** layout, not switchable screens: watchlist, attached symbol and tape across the top; sizing, risk and health along the bottom. Nothing hidden, nothing switched. `Ctrl+Tab` rotates focus and **is the entire navigation surface**. `Ctrl+P` palette for the long tail.

**One property must not be traded away**: `renderer(record)` is a **pure function of the day record**, with no panel reaching around it to compute anything. Everything downstream leans on it, and retrofitting it later costs ten times as much.

**4c — The thin day record.** `schema_version · session_date · generated_at · attached[] · tickets[] · health · regime_snapshot{ref, frozen_at}`, plus one number per session for the monthly P&L accumulator.

**`regime_snapshot` is a pointer, not rows.** There is no `layer_0`, no `layer_1`, no `layer_i`, and no `exposure` field. **A field that does not exist cannot be rendered by accident**, which is `SPEC.md` §4.1 enforced one layer below the screen. Do not add them "for later".

**4d — Panel chrome and provenance.** Box borders normalised to a fixed width — the mockups were 69–71 chars against a 71-char border, invisible in HTML and visibly broken in a console. **Account for ambiguous-width `·` and `—`.** ASCII-safe fallback when `SSH_CONNECTION` is set.

**The right-hand end of every top border carries provenance**: source, as-of time, sample window, or safety state. `computed 08:00 ET` · `IBKR · 07 Aug` · `not transmitted` · `updates · last 09:47:12`. **A live panel with no update stamp is the `[ STALE ]` anti-state.**

**4e — Scrolling with pinned rows.** Panels scroll independently. Risk rows, limit rows, the health bar, any failed rule and any active refusal are **sticky**.

A panel with content below the fold **says so** — `3–14 of 31` in the caption, `+7 more ↓` at the edge. ***"Nothing more here"* and *"more below"* must not render identically.** This is the sixth instance of a correct warning nobody was instructed to read: a limit breach at row 19 of a 12-row viewport is indistinguishable from no breach.

`window too small` narrows to mean **only** that the pinned rows do not fit.

**4f — `config/layout.yaml`, committed and load-bearing.** One line per component: `id`, `slot` (an ordinal, not a boolean), `visible`, and a **required `reason` on any change**. The renderer reads it; nothing else does.

**Enforce by test: a hidden component still computes and still writes to the day record.** Otherwise only visible components accumulate evidence and the inference is circular — tenet 7, *display is not storage*. **No auto-reordering, ever**: a system that both measures your preference and shapes it destroys the measurement.

**4g — The health bar, permanently visible.** Source states, last-seen ages, and the ticks-received-versus-frames-painted ratio.

**4h — Colour, and what it may never say.** No verdict colour anywhere (`SPEC.md` §4.1). No letter grades, no state names, no detector polarity colouring. **`_state_cell`'s polarity argument is deleted, not conditioned.**

Blue is a fact about config, never about the market. **Green renders nowhere** — it is reserved for a fitted signal measured against a pre-registered outcome, and nothing in this system is fitted. Dim-inverse for refusals: absence is not failure. **Red-inverse is reserved for exactly one badge, `[ STOPPED — DAILY LIMIT ]`.** `[ HALF SIZE ]` does not exist; it was a verdict.

**Status encoding is by position and typography, never colour alone** — it must survive 16-colour degradation over SSH.

---

## Part 5 — Snapshot tests

`pytest-textual-snapshot`, pinned. **Three widths: 80×24, 120×40, 240×70.** A layout correct at 120 columns and broken at 240 fails silently on the machine actually used.

**Scroll position is part of the snapshot.** One test drives a failed rule into a panel scrolled to the bottom and asserts it is still visible via the pinned band. **Without that test the pinning rule is prose.**

**The canonical snapshot is the refusal test: empty record → every panel shows a named refusal.** Any future change that turns one of those into `0.00` goes red. A too-small terminal renders a stated `window too small`, never a silently clipped panel.

---

## Do not

- Do not re-author `BUILD-PLAN.md`, or edit slice content while renumbering.
- Do not touch `SPEC.md`, `REGIME-PROMPT.md`, or `HANDOFF-PROTOCOL.md`.
- Do not adopt any module beyond `live/render.py`, and stop if it cascades.
- Do not add `layer_0`, `layer_1`, `layer_i`, or `exposure` to the day record.
- Do not render green anywhere, or red outside the one enumerated badge.
- Do not connect to TWS, read `records/tape/`, or touch anything belonging to `012`.
- Do not build window management, screen-switching, or drag-and-drop.

---

## Exit tests

| Test | Who | What |
|---|---|---|
| **Green** | Claude Code | Full `pytest`. The app boots on an empty day record and every surface renders as a refusal — **no crashes, no blanks, no zeros.** Snapshot suite green at all three widths. |
| **Refusal A** | Claude Code | **This slice is the refusal test.** Empty record → every panel shows a named refusal, captured as the canonical snapshot. |
| **Refusal B** | Claude Code | Change one refusal cell to render `0.00` and confirm the snapshot goes red. Revert. **A snapshot suite that does not fail on this has not been wired.** |
| **Refusal C** | Claude Code | Drive a failed rule into a panel scrolled to the bottom; assert it is still visible in the pinned band. |
| **Refusal D** | Claude Code | Set a component `visible: false` in `config/layout.yaml`; confirm it still computes and still writes to the day record. |
| **UAT** | Christoph | **Run it with no data at all. Read the empty screen and say whether every refusal is understandable without asking anyone what it means.** That is the acceptance criterion — not that it looks nice. Write the UAT record to `christoph/`. |

## Done-note must state

- Every `BUILD-PLAN.md` edit, quoted, and confirmation that no slice content changed.
- Whether `live/render.py` was adopted or the `Result` model re-authored, and why.
- The full refusal vocabulary as implemented, and any `SPEC.md` §4 term you could not render.
- The three snapshot widths, and what differed between them.
- Anything in `SPEC.md` §4 or §3.0a that **could not be built as written** — this is the first time these sections meet a compiler, and a spec that survives contact unchanged is unusual enough to be suspicious.
- **Anything in this task that diverged from what was on disk.**
