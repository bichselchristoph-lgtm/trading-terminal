---
id: 094
title: OCA group surgery, ETH pass -- join-later works, cascade is immediate, GTC expiry is not exposed
type: task
class: admin
owner: claude-code
unblocks: the unattended-exit order construction (spec change belongs to the design session, after 095)
depends: none
touches: nothing in the tree -- measurements only, scratch in $env:TEMP
bugs: []
---

**Status** DONE

# 094 — done. Group surgery works outside the session, the cascade fires in about a quarter of a second, and nothing on a working GTC order carries its auto-expiry.

## Gate, and the conditions this ran under

**ET start 2026-08-26 05:57:44 EDT, Wednesday. Pre-market (04:00–09:30).** The session gate
passes: this is the ETH pass. First order at 06:00:05 ET, last read at 06:02:09 ET.

**Paper confirmed by both signals before the first order**, as required:

```
06:00:01 ET  gate  account=DUR964730 port=7497
06:00:01 ET  gate  paper confirmed by both signals (id prefix + port)
```

**A 093 file was looked for and does not exist.** `handoff/inbox/` holds 092, then 094 and 095
(both written 2026-08-26 11:40 local); there is no `093-*.md` on disk anywhere under `D:\Dev`.
The retraction is therefore a no-op here rather than a skip — recorded so the absence is on the
record rather than assumed.

## Deviation, stated rather than papered over

**Task 062 names no tradeable instrument.** 062 is *"`verify.ps1` §10 reports on `tws_order`"* —
its "test instrument" is a **measuring** instrument, not a ticker. `handoff/inbox/062-*.md` and
`handoff/done/062-*.md` contain no symbol, and a sweep of the inbox for one found nothing.

**Used `F`** — the instrument the terminal's own order tier already trades, ~$14, one share.
This is a substitution, not compliance with the task as written. It is defensible because OCA
group mechanics are a property of the order machinery, not of the symbol carrying them; if the
design session disagrees, the pass is cheap to repeat.

**"End state: flat" was scoped to `F`.** The account was read before the first order and, as it
happened, held nothing:

```
06:00:01 ET  before  positions as found: none
```

Provenance of that empty reading, since it would otherwise look odd against the prior day's
record: **Christoph closed NVDA and QQQ manually in TWS** shortly before this pass. The account
was not emptied by anything here. Had it held either position, the scoping would still have
applied: a measurement task does not authorise flattening a position it did not create.

## Price reference

Live NBBO **was** available in pre-market, so both references exist and both are recorded:

```
06:00:02 ET  ref  previous RTH close F = 13.95  (bar 2026-08-25, useRTH=True)
06:00:05 ET  ref  live NBBO in ETH: bid=13.96 ask=13.97 last=13.975 -- present
06:00:05 ET  ref  sell STP 6.97 (~50%), sell LMT 27.9 (~200%) -- both non-marketable by design
```

**The prices used were taken from the previous RTH close**, per the task. Nothing filled.

---

## M1-E — a sole-member group is accepted in ETH

**Observation.** Accepted. Not rejected, not queued. It reached `PreSubmitted` within a quarter
of a second and the explicit `ocaGroup` was echoed back on `openOrder`:

```
06:00:05.310 ET  status     id=6 ValidationError filled=0.0 oca='M094-A'
06:00:05.310 ET  error      id=6 code=2109 Order Event Warning:Attribute 'Outside Regular Trading
                            Hours' is ignored based on the order type and destination. PlaceOrder
                            is now being processed.
06:00:05.547 ET  openOrder  id=6 SELL STP tif=GTC oca='M094-A' type=3 lmt=0.0 aux=6.97
                            status=ValidationError
06:00:05.548 ET  status     id=6 PreSubmitted filled=0.0 oca='M094-A'
06:00:05.549 ET  openOrder  id=6 SELL STP tif=GTC oca='M094-A' type=3 lmt=0.0 aux=6.97
                            status=PreSubmitted
```

**Observation, unprompted and worth keeping.** `outsideRth=True` on a STP to SMART is **ignored**,
and IBKR says so out loud — warning **2109**. The order is still processed.

**Observation.** `status='ValidationError'` appears as a transient state *before* `PreSubmitted`,
carrying warning 2109. It is a warning surfaced as a status, not a rejection: the same order id
reached `PreSubmitted` 238ms later. **Inference:** any code that reads the first status it sees
and concludes "rejected" would be wrong here. Not verified beyond this instance.

## M2-E — join-later works, and the cascade is immediate

**Observation.** A new GTC sell LMT naming the **same group as an already-live order** was
accepted, and both orders then reported that group:

```
06:00:11.559 ET  openOrder  id=7 SELL LMT tif=GTC oca='M094-A' type=3 lmt=27.9 status=PendingSubmit
06:00:11.562 ET  status     id=7 Submitted filled=0.0 oca='M094-A'
06:00:17.314 ET  M2-E       STP oca='M094-A' status=PreSubmitted
06:00:17.314 ET  M2-E       LMT oca='M094-A' status=Submitted
```

**This is the measurement the task exists for. A new order can join a live order's `ocaGroup` at
creation, outside RTH.** Previously measured nowhere in this project.

**Observation — cascade timing.** The STP leg was cancelled at **06:00:17.314**. The sibling LMT,
which nothing cancelled directly, went `PendingCancel` at **06:00:17.547** and `Cancelled` at
**06:00:17.549**:

```
06:00:17.314 ET  status  id=6 PendingCancel filled=0.0 oca='M094-A'   <- the leg I cancelled
06:00:17.547 ET  status  id=7 PendingCancel filled=0.0 oca='M094-A'   <- the sibling
06:00:17.548 ET  status  id=6 Cancelled     filled=0.0 oca='M094-A'
06:00:17.549 ET  error   id=6 code=202 Order Canceled - reason:
06:00:17.549 ET  status  id=7 Cancelled     filled=0.0 oca='M094-A'
06:00:17.549 ET  error   id=7 code=202 Order Canceled - reason:
```

**The cascade fired in ~235ms, and it fired in pre-market.** It did **not** wait for the session.
Observation was continued for the full **75s** the task asked for; nothing further arrived.

**This answers the question 095 cannot.** There is no queued-cascade window in ETH — no interval
in which one leg is dead and the other still working. The state the construction exists to
prevent did not occur at this resolution.

**Inference, labelled as such:** 235ms is not zero, so a window exists in principle. Whether it
can be observed by a client, or whether anything could fill inside it, was not measured.

## M3-E — modify outside RTH is accepted, and does not disturb the sibling

**Observation.** Fresh group `M094-B`, both legs placed, limit leg re-priced 27.9 → 29.29 (still
non-marketable). Accepted, not queued:

```
06:01:43.032 ET  M3-E       before modify: STP id=8 ... oca='M094-B' aux=6.97 |
                            LMT id=9 ... oca='M094-B' lmt=27.9
06:01:43.276 ET  openOrder  id=9 SELL LMT tif=GTC oca='M094-B' type=3 lmt=29.29 status=Submitted
06:01:51.029 ET  M3-E       after modify: STP status=PreSubmitted oca='M094-B'
06:01:51.029 ET  M3-E       after modify: LMT status=Submitted oca='M094-B' lmt=29.29
```

**The stop leg was untouched, both orders still carried `M094-B`, and modification did not
cascade.** Cleanup by cancelling one leg removed both, again immediately:

```
06:01:51.030 ET  status  id=8 PendingCancel oca='M094-B'
06:01:51.262 ET  status  id=9 PendingCancel oca='M094-B'
06:01:51.264 ET  status  id=8 Cancelled     oca='M094-B'
06:01:51.293 ET  status  id=9 Cancelled     oca='M094-B'
06:02:01.040 ET  clean   after cancelling STP: LMT status=Cancelled (cascade check)
```

## M4 — nothing on a working GTC order carries its auto-expiry

**Observation.** Every field on the live GTC order and its status whose name touches date, expiry,
cancel, duration or time was read and printed. All of them are empty or sentinel:

```
06:01:51.029 ET  order.activeStartTime      = ''
06:01:51.029 ET  order.activeStopTime       = ''
06:01:51.029 ET  order.autoCancelDate       = ''
06:01:51.029 ET  order.autoCancelParent     = False
06:01:51.029 ET  order.conditionsCancelOrder= False
06:01:51.029 ET  order.continuousUpdate     = False
06:01:51.029 ET  order.duration             = 2147483647
06:01:51.029 ET  order.goodAfterTime        = ''
06:01:51.029 ET  order.goodTillDate         = ''
06:01:51.029 ET  order.manualOrderTime      = ''
```

`orderStatus` contributed only its own class constants (`Cancelled`, `PendingCancel`,
`ApiCancelled`, `ApiUpdate`) — string names, not dates.

**The absence is the finding, as the task instructed.** `ib_async` exposes **nothing** on a
working GTC order that carries or implies the quarter-end / 90-day / corporate-action expiry.
`goodTillDate` is empty on a GTC order — it is an input field for GTD, not a readback of when
IBKR intends to expire this one. `duration = 2147483647` is `INT_MAX`, the unset sentinel.

**Inference, labelled as such:** a client cannot learn a GTC order's expiry date from the order
feed. If the unattended construction depends on knowing it, that knowledge has to come from
somewhere other than the wire — or the design must not depend on it. **Not measured:** whether
the expiry is exposed anywhere else in the API at all.

---

## End state — by fresh read, not by absence of error

```
06:02:09.045 ET  end  FRESH read -- open orders on F: none
06:02:09.045 ET  end  FRESH read -- total open orders in account: 0
06:02:09.045 ET  end  positions: none
06:02:09.045 ET  end  F flat: True
```

`reqAllOpenOrders` was issued before the read, so this is the account's answer and not this
client's cache. **Flat, zero open orders, account-wide.** Nothing this task created outlived it.

## verify.ps1

**Ran 2026-08-26 12:02:36 +02:00 (06:02:36 ET), completed 12:05:59 +02:00.** Output written to
`handoff/verify-output.md`. No test count is quoted here, per the exit criteria.

Failures are named by the script itself. It classifies most as unchanged and four as new, all
four in `live/tests/` — `test_attach_is_reachable_by_key.py` and `test_launches_as_a_program.py`,
which correspond to the uncommitted `live/tui/app.py`, `live/attach/ibkr.py` and the untracked
`live/attach/accounts.py` in §2's status. **This task touched nothing in the tree**, so none of
them can be attributable to it; they are reported here as the state verify.ps1 found, not as a
result of this pass.

## No spec was edited

None. The reading of M1-E–M4 belongs to the design session, after 095. What follows is offered as
inference for that session and is **not** written into any spec by this task.

**Inference for the design session.** SECURITY-BRIEF §5.3 concluded that no IBKR construction
keeps a protective stop and a working exit mutually exclusive unattended. **M2-E is evidence
against that conclusion**, and it identifies where the earlier reasoning went wrong: the fatal
property measured on 2026-08-26 was never "OCA cascades on cancel" alone — it was that cascade
**combined with a DAY exit**, which IBKR cancels at the close, taking the GTC stop with it. Both
legs GTC removes the trigger. The cascade remains, but nothing routine fires it.

**What is measured:** join-later is accepted; the group is echoed on both legs; the cascade is
immediate rather than queued; modify does not cascade; all of it works outside RTH.
**What is not measured:** that a GTC exit survives an actual session close (needs a close),
and that `ocaType=3` reduces rather than cancels on a real fill (needs RTH — that is 095's M2-R
territory and the terminal's own open item). **A construction should not be adopted on this
pass alone.**

## Scratch

`%TEMP%\oca094\m094.py` and `%TEMP%\oca094\m094-log.txt`. Nothing was written to any repo except
this note.
