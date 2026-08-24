---
id: 089
title: Complete 084's owed live measurement, now that TWS is up
type: task
class: admin
unblocks: 084's UAT (christoph/open/045) and B-138's closure
story: none
owner: claude-code
depends: 084
touches: nothing in live/ or core/ — a measurement report only
bugs:
  - id: B-138
    action: close
    status: "Closed for the specific case 084's cache targets: the repeated-request cost of re-attaching a WARM symbol within one session. Measured live (client_id=84, real TWS, QQQ): the own-curve request's wall time dropped from 1.95s (first attach, a real fetch, 7800 bars received) to 0.00s (second attach, bars_received=None — confirming no wire request was made at all, a genuine cache hit, not merely a fast one). Total keypress-to-RVOL-landed time dropped 2.48s to 1.48s (a 1.00s reduction) — less than the full 1.95s because other stage-2 work (rth_dailies, the price stream) runs concurrently and is unaffected by this task, so the cache's own saving is partially masked by the slowest OTHER concurrent role rather than fully exposed in the total. Not closed in full: the cache does not help a COLD symbol a session has never attached before, which is 082's own separate, still-open finding about pacing contention under load."
---

**Status** DONE

# 089 — 084's live measurement, completed

**This note needs to be pasted to chat.**

---

## The measurement

Same harness `084`'s own note already described (`084_cache_measure.py`,
never committed, `client_id=84`, real TWS): attach QQQ, wait out IBKR's
same-symbol historical cooldown on `rth_dailies` (084 does not cache that
role), attach QQQ again, report keypress-to-`RVOL`-landed wall time for both
plus the own-role `RequestMetrics.wall_s`/`bars_received`.

```
FIRST attach:  own-request wall_s=1.95s   bars_received=7800   keypress-to-RVOL-landed=2.48s
cooldown clear after 13s
SECOND attach: own-request wall_s=0.00s   bars_received=None   keypress-to-RVOL-landed=1.48s
```

**The number 084 existed to produce**: the own-curve request dropped from
**1.95s to 0.00s**, with `bars_received=None` on the second attach confirming
no wire request was made at all — a real cache hit, not merely a fast
response. Total attach time dropped 2.48s → 1.48s (1.00s), a smaller delta
than the full 1.95s because other, concurrent stage-2 work is unaffected by
this task and partially masks the saving in the TOTAL figure — the own-role
figure is the honest one to read for what 084 actually changed.

**RVOL itself refused on both attaches** (`unavailable='no bars today'`) —
this is the after-hours condition already noted earlier in this session
("its after-hours trading, not much volume expected"), not a caching
defect: the price stream's own numerator was empty at the time of this run,
independent of which curve (cached or freshly fetched) fed it. Because RVOL
never landed a real value on either attach, this run could not additionally
confirm the rendered VALUE is bit-for-bit identical across both attaches —
that identity property is already covered separately by
`test_084_rvol_curve_cache.py::test_identity_the_cached_curve_is_the_first_fetch_not_a_fresh_recompute`,
against a fixture built specifically to make a stale value detectable.

---

## What was not touched

No production file. No test file. `handoff/done/084-for-code-task-rvol-curve-cache.md`
— already exported, deliberately left exactly as it was.

---

## UAT

`christoph/open/045-for-christoph-task-uat-084-curve-cache.md` can now be
meaningfully performed — the speedup it presumably asks about is quoted
above.

---

## Closing sequence

`verify.ps1` runs as the last action, not pasted or summarised here.
`export-handoff.ps1`/commit/push follow, scoped to this task's own two
files only.

**This note needs to be pasted to chat.**
