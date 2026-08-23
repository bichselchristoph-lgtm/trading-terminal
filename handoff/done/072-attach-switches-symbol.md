---
id: 072
title: Attaching a second symbol accumulated instead of replacing the first — and the first fix broke a different, older rule
type: task
class: product
story: S037
epic: 4
owner: claude-code
unblocks: NOTHING
depends: none
touches: the attach path, the ATTACHED renderer, the attach tests
bugs:
  - id: NEW
    action: raise
    status: "Defect A, confirmed reproduced live before any fix (see Part 0): attaching a symbol DIFFERENT from the one already attached did not replace it — `_begin_attach`/`_finish_attach` only ever cleared an entry from `record.attached` matching the SAME symbol being (re-)attached, so a different symbol's entry accumulated instead. `SPEC.md` §12.11 ('Several symbols attached at once') is explicit this is deferred ('Promote when: the single-symbol pane has run for a month'), so today's correct behaviour is at most one entry, ever. Fixed: a successful attach now clears `record.attached` unconditionally before appending. Defect B (nothing said so) resolved as a consequence — with at most one entry possible, there is nothing left to render silently alongside it."
  - id: NEW
    action: raise
    status: "A regression found WHILE fixing Defect A, not before it: the first version of the fix cleared `record.attached` unconditionally the moment a new attach BEGAN (in `_begin_attach`), which loses the previously-attached symbol permanently if the new attach then FAILS — nothing re-adds it. This directly violates the older, already-tested `SPEC.md` §4.2 rule ('a failed attach must not blank a symbol that is working') and was caught by re-running the existing unresolvable-second-symbol reproduction, not by a new test. Corrected: `record.attached` is left untouched by `_begin_attach`; the on-screen blank during an in-flight attach is now enforced in `render_panels` (it does not render `at` while `record.attaching`/`record.attach_queued` is set), and `record.attached` is only ever cleared on a SUCCESSFUL attach."
---

**Status** RUNNING

# 072 — done. Attach did not switch symbols; fixed, and the fix's own first draft broke an older rule before landing.

**This note needs to be pasted to chat.**

---

## Part 0 — reproduced first, against the real `MomentumApp`/`attach()` path

**Not inferred from reading the code — run, with output captured before any
fix existed.** `live.tests.test_attach.Fake.resolve()` ignores its `symbol`
argument and always returns one hardcoded contract, which is exactly why
this had nothing to catch it: every existing test that attaches "two
different symbols" was actually attaching the same contract twice under two
different labels. Built `TwoSymbolFake` (now `live/tests/
test_072_attach_switches_symbol.py`) that resolves each symbol to its own
contract, then drove the real `MomentumApp` via a Textual pilot.

**1. Attach QQQ, then AMZN — recorded before any fix:**
```
record.attached symbols: ['QQQ', 'AMZN']
----BODY----
+- ATTACHED ---------------------------------------------------------  +
  QQQ  attached 10:23:23
              2 of 21 rows unavailable (flagged, not an error)
    ADR% used 24.9% ▓▓▓▓▓░░░░░░░░░░░░░░░ of $2.01 ADR20 RTH
    RVOL rel  1.0×  · avg 1.0×  · cum 30,000 sh
    VWAP      $101.00  · +$0.00
  AMZN  attached 10:23:23
              4 of 21 rows unavailable (flagged, not an error)
    ADR% used 24.9% ▓▓▓▓▓░░░░░░░░░░░░░░░ of $2.01 ADR20 RTH
  8 of 10 · +2 more ↓
```
**QQQ never left. AMZN's own block was correctly built and appended below
it**, and the panel had grown past its viewport ("+2 more ↓"). This matches
the report exactly once read carefully: QQQ genuinely was still there, and
a new timestamp genuinely had appeared on the panel — it belonged to
AMZN's own, correctly-labelled row, one screen-scroll below where the
report's attention had stopped.

**2. Does the attach coroutine run for the second symbol at all?** Yes —
confirmed by AMZN's own row carrying real, correctly-computed values. This
was never a stuck worker or a silent no-op.

**3. Does contract resolution succeed for AMZN?** Yes, in the scenario
above (a resolvable second symbol). Separately reproduced the unresolvable
case (`ZZZZNOPE`): resolution correctly fails, `attach_refusal` is set, and
— pre-fix — QQQ's OWN entry was untouched (this half was already correct;
see the regression below for how the FIRST fix attempt broke it anyway).

**4. Does anything write a new attach timestamp on a path that does not
also set the symbol?** No — `Attached` objects are constructed fresh
(`Attached(symbol=..., since=..., ...)`) in exactly one place
(`_finish_attach`'s success branch) and never mutated field-by-field
afterward. `test_since_is_never_written_independently_of_symbol` asserts
this structurally (greps for any `.since =` assignment outside that one
constructor call — none exists).

**5. Third symbol / re-attach QQQ after AMZN — is this specific to AMZN?**
No. `QQQ → AMZN → QQQ` reproduced the same accumulation
(`record.attached` became `['AMZN', 'QQQ']`) — general to any second,
distinct symbol, not an AMZN-specific fault.

---

## Root cause

`_begin_attach(symbol)` and `_finish_attach`'s success branch both filtered
`record.attached` on `a.symbol != symbol` — clearing an entry only when
RE-attaching the SAME symbol. A DIFFERENT symbol's entry was never touched,
so it accumulated. `SPEC.md` §12.11 settles which behaviour is correct:
"Several symbols attached at once" is explicitly **deferred** — "Promote
when: the single-symbol pane has run for a month" — so `record.attached`
must hold at most one entry today, and every mockup for this panel (v1.0
through v1.2) draws exactly one symbol, never several.

---

## The fix, and the regression its first draft introduced

**First attempt:** clear `record.attached` unconditionally in
`_begin_attach`, the instant a new attach begins. This passed the
accumulation reproduction — but re-running the UNRESOLVABLE-second-symbol
scenario (already covered by existing behaviour, not a new test) showed
QQQ **disappearing entirely** the moment `ZZZZNOPE` was typed, because
`_begin_attach` now wiped the record before knowing whether the new attach
would succeed, and none of `_finish_attach`'s failure branches ever put it
back. This is a direct violation of the older, load-bearing `SPEC.md` §4.2
rule already quoted in the surrounding code: *"A failed attach must not
blank a symbol that is working."*

**Corrected fix**, landed:
- `_begin_attach` no longer touches `record.attached` at all — only
  `attach_refusal`/`attach_queued` (cleared) and `attaching` (set).
- `render_panels` now renders `record.attached` **only when neither
  `record.attaching` nor `record.attach_queued` is set** — the
  "no stale value on screen while a gather is in flight" property (S037
  criterion 2) is enforced at the SCREEN, not by destroying the RECORD.
- `_finish_attach`'s success branch clears `record.attached` fully (not by
  symbol-filter) before appending the new entry — the only place the
  record is ever cleared, and only on success.
- Failure branches (`worker_refusal`, `not result.attached`) touch neither
  `record.attached` nor its timestamp — whatever was there survives a
  failed attempt intact, per §4.2.

**Defect B ("nothing said so") also gets a small, additive fix**: when a
symbol remains attached and the MOST RECENT attach attempt refused, the
panel's caption now reads `attach refused` instead of staying bare (071's
"bare when landed" rule is specifically for "nothing to report"; a refused
re-attach is something to report). The refusal line itself keeps the
existing, already-tested `Cell.absent()` grammar rather than adopting the
task's own illustrative wording ("could not attach —") verbatim — one-off
phrasing on a single row would break the closed refusal vocabulary every
other row on the panel already follows.

**Not built: the task's compact "QQQ remains attached — attached
09:19:07" single-line illustration for the refusal case.** The fixed
behaviour keeps QQQ's FULL context block visible (all four rows), which
the task's own exit criteria explicitly allow — "the previously attached
symbol is either absent or shown as previously attached with its own
timestamp" — and is more useful to a trader than collapsing it to one
line. Flagged as a deliberate choice between two sanctioned outcomes, not
an oversight.

---

## Tests — all four of §5, plus the mid-flight case, each seen red first

New file: `live/tests/test_072_attach_switches_symbol.py`, five tests.
Verified genuinely RED against the real pre-072 `live/tui/app.py` via `git
stash push --keep-index -- live/tui/app.py`, not narrated:

1. `test_attach_a_then_b_the_panel_renders_only_b` — RED
   (`['QQQ', 'AMZN']` where only `['AMZN']` is correct).
2. `test_attach_a_then_unresolvable_refuses_and_keeps_a_intact` — RED (no
   `attach refused` caption pre-fix; this specific assertion is a new
   requirement, not a regression check).
3. `test_attach_a_then_b_then_a_again` — RED (`['AMZN', 'QQQ']`).
4. `test_since_is_never_written_independently_of_symbol` — RED (the
   structural assertion for `record.attached = []` existing anywhere
   failed pre-fix, since no unconditional clear existed yet).
5. `test_no_stale_symbol_renders_while_a_different_one_is_in_flight` — RED,
   and **this is the closest thing to a byte-for-byte reproduction of the
   original report**: QQQ's full block rendered alongside the `ATTACHING
   AMZN` caption, mid-gather.

`git stash pop` restored the fix afterward. All five green against the
current code; `live/` suite in full: **168 passed** (was 163 after `071`).

---

## Test results

`live/` in full: **168 passed, 0 failed**. Full repo suite not yet re-run
in this task at time of writing this note (running as part of the closing
sequence, see below) — will report any change to the 12 pre-existing,
unrelated failures `070`/`071` already carried forward.

---

## Closing sequence

`verify.ps1`, `export-handoff.ps1`, commit, push — run after this note,
from the main checkout, scoped to this task's own files only. The working
tree still carries the same unrelated concurrent changes noted in `071`'s
own closing section (Christoph's `christoph/done`/`christoph/open`
retirements, and now also `073`, a fresh unrelated inbox item pulled in by
the same `sync.ps1` run that fetched `072`) — none of it swept into this
commit.
