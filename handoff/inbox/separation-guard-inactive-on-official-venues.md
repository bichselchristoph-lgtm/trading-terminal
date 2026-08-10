# separation-guard-inactive-on-official-venues

Found 2026-08-08 while discharging `auction_anchoring.verification`. Not the
thing that check was looking for.

## What

`core/identify.py` applies `min_separation` only when the instrument's
`AuctionPresence` is `INCIDENTAL`:

```python
if presence is AuctionPresence.INCIDENTAL and separation < p.min_separation:
```

XNAS and XNYS are declared `OFFICIAL` in `core/config/venue_capabilities.yaml`,
which is **92% of the phase-3 sample**. On all of it, the largest off-book
print in the window is accepted as the cross with no size check.

## Why the justification does not hold

The code's stated reason: *"An official cross is known to exist, so the largest
off-book print in the window is it."*

The statistics check falsifies the premise. On 8 XNYS sessions the venue
**published an official closing price** while the only off-book prints carrying
that price were a median 1.2x the session median — one was 0.0x. A cross
happened by the venue's own account, and no cross-sized print for it exists
near the anchor in the trades delivery. So "official venue" does not imply "a
cross-sized print is in this window", and the largest print in the window can be
an ordinary one.

Today this is latent: with a 15s window those sessions fail to identify, which
is the right outcome. It becomes live the moment the window is widened — the
open result (real crosses at up to 31.5s) is a genuine reason to widen, and
widening is exactly what removes the only thing currently preventing the 8
coincidental closes from being labelled crosses.

## What it is not

Not a bug in `min_separation` (5.0 is fine) and not a reason to leave the window
at 15s. It is a missing guard on a path that has never been exercised hard.

## Options — RESOLVED 2026-08-08, order inverted

The original order was written before any of the three were tested. Testing
option 1 killed options 1 and 2 and promoted option 3, which was ranked last.

### 1 and 2 are DEAD — size cannot be the guard here at ANY level

Option 1 guessed the cost of applying `min_separation` on OFFICIAL venues was
"likely zero, verify before assuming". Measured across all 3,477 classified
roles: **32 sit below 5.0x (0.92%)**. Not zero, so the guess was wrong — but the
number is small enough that it looked like an acceptable price.

It is not, and the reason is not the size of the cost. `statistics` was pulled
for all 28 affected sessions ($0.35) and each of the 32 checked against the
venue's published official price:

| verdict | n | separations |
|---|---|---|
| REAL cross | 30 | 1.64x – 4.99x |
| COINCIDENCE | 2 | 1.07x, 1.85x |

**The distributions overlap.** A coincidence at 1.85x sits above two real
crosses at 1.64x and 1.65x. Any floor low enough to keep the real crosses
admits the coincidence; any floor high enough to exclude the coincidence
discards real crosses. Option 2 — a separate, lower floor for OFFICIAL venues —
fails for the same reason, because there is no level that separates them.

This is the third time an identification rule has died this way in this project:
size-and-side (16.2% FN, distributions overlap), paired-quantity (band from QQQ
met 0.51 on thin ARCX), and now size separation on OFFICIAL venues. The shape is
always the same and is worth recognising earlier next time: a statistic that
separates cleanly on the instrument it was derived from, overlapping on one it
was not. `min_separation: 5.0` came from QQQ. Tenet 6.

Also note where the real crosses go: **down to 1.64x**, below the 2.48x floor at
which size-alone bottomed out on QQQ. The premise that a cross is always
conspicuously large does not hold on thin single names.

### 3 is the only survivor — and it just demonstrated itself

Price match against the `statistics` schema was ranked last for cost. But it is
the method that produced the table above: it separated 30 real from 2
coincidental with no threshold at all, on exactly the population where size
overlaps. And on the already-classified rows it returned **133 of 133 confirmed,
zero mismatches**.

Its objection stands — identification would depend on a second purchased schema
— but the objection was priced at a guess. `statistics` is `ALL_SYMBOLS` per
venue-day and costs roughly **$0.005 per venue-day**; the 28 sessions here cost
$0.35 in total. Pricing across the whole phase-3 sample is running.

### What this changes

Not just the guard. If `statistics` is bought for the whole sample, auction
identification stops being *inferred* — from an anchor, a window and a size
ratio, each of which had to be derived and defended — and becomes *verified*
against the venue's own published price on every row. Every constant that was
fitted on QQQ and carried across becomes a fallback for rows the direct check
cannot cover, rather than the primary rule.

That also settles `imbalance_lag_seconds` without widening anything on faith:
with the official price known, the window stops being load-bearing.

### Two wrong rows found

`OMCL 2024-08-01 open` (1.07x) and `ITCI 2025-01-10 open` (1.85x) are currently
classified as crosses and are not. Two of 3,477 — but they are in the 18,410
records now, and they only surfaced because a floor they fell below prompted a
look.

### Cost of acting

`signal_version` bump on every auction-dependent signal and a rebuild of the
18,410 records. Do it once, together with the `imbalance_lag_seconds` decision —
not as two rebuilds.

Registered: `preregistration.yaml` -> `auction_anchoring.verification`
