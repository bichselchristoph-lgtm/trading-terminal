# 036 — UAT for 060: B-001, panels rendering twice

**For Christoph. This is what closes B-001. Nothing else does.**

---

## Why it needs you

`060` found a real race — `_apply_fit()` checked the DOM for panels and then mounted, with two callers and no lock between them, so a resize landing mid-sequence let a second caller see the same empty frame and mount a second full set. Fixed with a lock.

**But the shape that reproduced it in test is not the shape you saw.** It reproduced with **two sessions sharing one process**, at `120×40` following `80×24`. Your screenshots were **one session at 209×54, then maximised**, and that shape came back clean in the size table.

**So the fix is well-argued and the evidence for it does not cover your case.** This UAT is the only thing that does.

**And it needs repetition.** The race fired roughly **one fresh process in six**. A single clean run is weak evidence — twelve clean trials would still come up about one time in nine by luck alone. **Five fresh starts, not one.**

---

## Expected, at every step

**Seven panels, one of each title:** `WATCHLIST` · `ATTACHED` · `TAPE` · `SIZING` · `RISK` · `HEALTH` · `PIPELINE`.

**Fourteen is the defect.** Two of every title.

---

## Run

**Between each run: close the terminal tab and open a fresh one.** A new `python` process in a reused tab is not the same test — the race lived in process startup.

### Run 1 — your working size

1. Fresh tab at **209×54**
2. Start the terminal
3. **Before attaching**, scroll to the bottom. Count panel sets.
4. Attach QQQ. Scroll to the bottom. Count.
5. Attach QQQ twice more. Count after each.

- [ ] Seven throughout
- [ ] Fourteen at some point — say which step

### Run 2 — the maximised case, your original capture

1. Fresh tab, **maximised**
2. Start, attach QQQ, scroll to the bottom, count

- [x ] Seven
- [ ] Fourteen

### Run 3 — resize mid-session

**This is the one that most directly exercises what was fixed** — the second caller into `_apply_fit()` was `Frame.on_resize`.

1. Fresh tab at 209×54, start, attach QQQ
2. **Maximise while it is running.** Count.
3. **Restore to 209×54.** Count.

- [ x] Seven throughout
- [ ] Fourteen — say at which resize

### Runs 4 and 5 — repeat Run 3

Fresh tab each time. **The rate matters more than any single result.**

- [ 7] Run 4 seven / fourteen
- [7 ] Run 5 seven / fourteen

### Run 6 — restart in the same tab

The original `c015` report said the symptom appeared after *"started terminal again"*. `060` offers a simpler explanation that needs nothing surviving a restart — worth one check.

1. Quit the app, start it again **in the same tab**, attach QQQ, count

- [x ] Seven
- [ ] Fourteen

---

## If a duplicate appears anywhere

**One observation matters more than the rest: is the second set reachable by scrolling inside the app, or only by dragging the terminal's own scrollbar?**

- [ ] App's own scrolling — it is in the render tree
- [ ] Only the terminal scrollbar — it is in the console buffer, and the fix addressed something else

**Screenshot it and note which run and step.**

---

## Verdict

- [ x] **Accepted.** Seven panels in all six runs. B-001 closes as fixed.
- [ ] **Not accepted.** Fourteen appeared — details above.

**If accepted**, B-001's row moves to fixed with `060` named, and the paste-ready cells come in chat.

**If not accepted**, the fix was for a real race that was not the one you are seeing, and both stay open — the race and the symptom.

christoph aug 22 2026
