---
id: c045
title: UAT for 084 — the second attach of a symbol is fast
type: task
class: product
uat_for: 084
depends: 084
---

# c045 — UAT for 084

**Ten minutes. Best run during a regular session**, because the first attach is
the one that has to be slow for the test to mean anything.

## What changed

The reduced 20-session curve behind RVOL is now held in memory for the trading
day. **The first attach of a symbol fetches it; every attach after that does
not.**

## Steps

1. **Attach AMZN.** Note roughly how long `RVOL` sits on `pending` — expect
   fifteen to sixty seconds.
2. **Attach QQQ.** Then **attach AMZN again.**
3. **How long does `RVOL` sit on `pending` the second time?**

**The whole task is the difference between steps 1 and 3.** Expect the second
attach to land RVOL with `ADR% used`, in about two seconds.

## The questions

**A.** Is the second attach visibly faster on the RVOL row?
yes
**B. Are the numbers the same on both attaches?** Same symbol, same session,
same curve — they must be. **If the second attach shows different RVOL values
than the first, stop and report it immediately.** A cache serving a nearly-right
curve is worse than no cache: it is invisible and it lasts the whole session.
yes
**C.** Switching between three or four names as you normally would — **does the
terminal feel different to use?** This is the question the task was built for
and the only one that cannot be measured.
screen flickers every 5 to 10 seconds after a few attaches.
**D.** Anything odd after a long session — the panel slowing, memory climbing,
values that look stale rather than wrong.

## What is NOT being checked

**Cross-day caching.** Nothing is written to disk and nothing survives a
restart, deliberately: a split rescales historical volume, so a curve cached
yesterday would be silently wrong today for exactly the names most likely to be
worth trading.

**The sector reading's reliability.** B-138 — a separate problem with the two
large pulls contending, which caching reduces but does not fix.
not available as not RTH now. need to check later
Write your answers into this file's copy and retire it the usual way.
Signed-off by Christoph, Aug 24, 2026	