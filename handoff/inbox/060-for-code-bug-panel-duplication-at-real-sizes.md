---
task: 060
class: product
depends: 059
touches: live/tests/test_panels_render_once.py, live/tui/app.py, live/render.py
---

# 060 — B-001 continued: run the discriminator at real dimensions

**If `handoff/inbox/060-for-code-bug-panel-duplication-at-real-sizes.md` exists in your tree and `handoff/done/060-*.md` does not, this task is for you. Otherwise stop reading and ignore this message.**

---

## 0. Where 059 left it

`059` ruled out candidate A **at one size**. `live/tests/test_panels_render_once.py` drove the real app through Textual's pilot across mount, three repeated attaches, `_rerender()` and a refused attach, and the render tree never held more than one panel per title.

**Textual's pilot defaults to 80×24.** Christoph's terminal is **209×54**, and the capture that shows the duplication is **maximised — roughly 316×37**, wider *and shorter* than his working size.

**So the finding is: the render tree is clean at 80×24.** It is not yet a finding about any size the terminal is actually used at. **That is `B-012`'s shape exactly** — a layout claim verified against a width the product never runs at.

---

## 1. Part 1 — answer the question file, then set it ANSWERED

`handoff/questions/059-panel-duplication-cause.md`. **Do not edit the question file's body. Set `ANSWERED` on it and cite this task.** The answers:

**Q — is the app running in Textual inline mode?** *(the design session's own question, checked first because it needed nobody)*

**No, and it is ruled out.** Christoph ran:

```
Get-ChildItem D:\Dev\momentum -Recurse -Filter *.py |
  Select-String -Pattern 'inline\s*=|alt_screen|\.run\(|run_async\('
```

One hit outside tests: `live\tui\app.py:923` — `MomentumApp(record=record, layout=layout, md=broker.md).run()`. **No `inline=`, no `alt_screen` anywhere in the tree.** Textual's default is the alternate screen.

**Q — is the same terminal tab reused across runs, and how is the app stopped?**

**Held, deliberately, and here is why.** In Christoph's two captures **both copies of the panel set read `lag 945m`, `as of 2026-08-21 19:59:00`, and `attached 11:44` — identical to the digit.** Lag is computed at paint time. Two separate runs would have to have attached inside the same minute *and* produced the same lag to match. **Both copies almost certainly come from one run**, which makes leftovers-from-a-previous-run a weak explanation regardless of how the app is stopped.

**If Part 2 and Part 3 both come back clean, these two questions become live again and this task stops rather than guessing.**

---

## 2. Part 2 — a contradiction that must be resolved before anything else

**`app.py:923` says the app takes the alternate screen. Christoph's captures show a scrollbar at the right edge of the window — in the empty first frame as well as the attached one.**

**An application holding the alternate screen produces no terminal scrollback, so no scrollbar.** One of these two readings is wrong and it is cheap to find out which.

**Establish at runtime — not from the source — whether the alternate screen is actually entered.** Whether the driver emits the enter-alt-screen sequence, what `App` reports about its own mode once running, whichever route the installed Textual version makes available.

- **Alt screen is entered → the scrollbar is Textual's own**, drawn inside the app, and the duplication is inside the render tree after all. Go to Part 3.
- **Alt screen is not entered → that is the defect**, and Part 3 becomes confirmation rather than search. A plain `.run()` that does not take the screen is a well-formed call answering a different question.

**Report which, as an observation.** Do not record a cause you have not read.

---

## 3. Part 3 — re-run the four tests across real sizes

**Parameterize `test_panels_render_once.py` over the pilot's terminal size.** At minimum:

| Size | Why |
|---|---|
| **80×24** | the current default — the only size 059 covered |
| **120×40** | existing pinned snapshot width |
| **209×54** | **Christoph's actual terminal** |
| **240×70** | existing pinned snapshot width |
| **~316×37** | **approximately the maximised capture. Measure it rather than trusting this number** — it is estimated from pixel counts, not read from the terminal |

**Report a table: size against panel-instance count.** That table is the deliverable of this part whether or not anything reproduces.

**Two hypotheses, and the table separates them:**

- **Width-conditional** — duplicates appear as columns grow. The fix is in the layout path.
- **Height-conditional** — duplicates appear when the viewport is **shorter than the content**. The maximised capture is roughly **37 rows against a working height of 54**, and in Christoph's captures the second panel set begins immediately after `PIPELINE`, which is where the first set ends. **A scroll region rendering its content twice would look exactly like this**, and `B-005` (no fold indicator) and `B-011` (the too-small guard measures the window, not the tile) are its neighbours.

**Do not assume which. Read the table.**

---

## 4. Part 4 — the fix, only if Part 2 or Part 3 found something

**If a cause was read:** fix it, and add a test at the size that reproduced. **Seen red first** — revert, watch it fail, restore, watch it pass.

**Assert the rule, not the current output.** Count panel instances against the expected set. `B-029` is what happens otherwise.

**If nothing reproduces at any size and the alternate screen is confirmed entered:** **stop.** Write the table into `OBSERVATIONS.md`, record that the render tree is clean at five sizes, and state in the done-note that Christoph's two questions from Part 1 are now the blocking facts. **Do not fix anything speculatively** — `059` forbade it and so does this.

---

## 5. Scope

**In scope, narrowly:** adding 209×54 to *this test file's* sizes.

**Not in scope:** `B-012` generally — the snapshot suite's pinned widths stay as they are. `B-002`, `B-005`, `B-009`, `B-010`, `B-011`, `B-091`. The three files the last sync reported as differing from Drive (`040`, `043`, `052`) — those are Christoph's, separately.

---

## 6. Exit tests

**Green.**
- The size table exists and covers all five sizes.
- The alternate-screen question in Part 2 is answered from runtime, not from source.
- Any new test was **seen red** before green.
- The existing suite stays green at its three pinned widths.

**Refusal.**
- At whichever size reproduces — or at 209×54 if none does — **attach a bad symbol.** The panels render their refusals **once**.
- **The empty first frame**, no data at all: every panel a named refusal, one instance each. **Christoph's empty capture already carries the scrollbar, so this case is load-bearing.**

**UAT — Christoph.**
- Run at 209×54, attach QQQ, and **scroll to the bottom of the app.** Count the panel sets.
- Then maximise and do the same. **Report whether the duplicate is reachable by the app's own scrolling or only by the terminal's scrollbar** — that single observation separates a render-tree defect from a console defect better than anything in this task.

---

## 7. Closing

**Scratch in `$env:TEMP`, never the repo.**

**The closing sequence, from the main checkout: sync, work, verify, export, push.** `verify.ps1` runs as the last action and **is not pasted or summarised.** The done-note states that it ran and when, and **quotes no test count.**
