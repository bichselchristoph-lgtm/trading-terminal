**Status** WRITTEN · **Type** UAT · **Date** 2026-08-11 · **For** Christoph
**Slice** `S009` — the TUI frame, the refusal grammar, and a thin day record
**Done-note** `handoff/done/S009-tui-frame-and-refusal-grammar.md`

# 003 — Read the empty screen

---

## What this is

The first thing in this project that can be looked at rather than read about.

`S009` built the frame and the refusal vocabulary **before any panel has data**. The app boots on an empty day record, and every surface renders a named refusal — no crashes, no blanks, no zeros.

**That is not a degraded mode. It is the ordinary first frame of every session**, and the reason it is worth a screen is the conviction this whole project is built on: *a panel that renders a value with nothing behind it is worse than a panel that renders nothing.* Layer 0 rendered as an operational reading when none of its fourteen rows existed in code. It looked authoritative.

## The criterion

**Whether every refusal is understandable without asking anyone what it means.**

Not whether it looks nice. Not whether the layout pleases you. If a cell says something you have to ask about, that cell has failed, and it is worth more to this project than any cell that reads well.

You wrote most of this vocabulary. **That works against you here** — you will read `unfitted` and know what it means because you chose the word. The question is whether the *screen* tells you, not whether you already know.

## How to run it

Launch the TUI in `D:\Dev\momentum` with no data at all — no day record, no IBKR connection, nothing attached. Claude Code can tell you the exact command; it is not recorded here because the entry point may have changed.

**Do it in a real Windows Terminal at the size you actually trade at.** Then try it much narrower and much wider. The snapshot suite covers 80×24, 120×40 and 240×70, but a suite passing is not the same as a screen being readable.

## What to look at

**Every cell that is not a number.** For each one: does it say what is missing, and why?

**The panel borders.** The right-hand end of every top border carries provenance — source, as-of time, or safety state. Does it tell you what you would need to know about where that panel's content comes from?

**The bottom of a panel with more content than fits.** *"Nothing more here"* and *"more below"* must not look the same. Does a scrolled panel say `3–14 of 31` and `+7 more ↓`, and did you notice it without being told to look?

**The colours.** There should be no green anywhere at all, and no red except `[ STOPPED — DAILY LIMIT ]`. If anything reads as a verdict — *this is good, this is bad, this is safe* — that is a §4.1 violation and it is worth naming.

**Make the window too small.** It should state `window too small` and render **zero** panels, never a silently clipped one.

## What to report

**Every refusal you had to think about**, quoted exactly as it renders. Those are the findings.

**Anything you expected to see and did not.** The frame is deliberately thin — the day record carries only `schema_version · session_date · generated_at · attached[] · tickets[] · health · regime_snapshot{ref, frozen_at}`. If something is missing because its slice has not been built, that is correct. **Say so anyway**, because the gap between what you expect on screen and what the record can carry is worth knowing now rather than at `S011`.

**Anything that looked authoritative.** That is the failure this slice exists to prevent, and it is the one you are best placed to catch.

## What this UAT is not asking

Not whether the layout is right — that is `config/layout.yaml` and it is meant to change.
Not whether panels are missing — most are, by design.
Not whether it is fast, pretty, or finished.

---

**Report in chat.** The result file for `christoph/done/` follows from what you say.
