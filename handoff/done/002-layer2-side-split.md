---
id: 002
title: Layer 2 follow-through — split by side, and check it survives a non-breakout playbook
status: READY
depends_on: []
touches_phase3: false
---

# TASK 002 — Layer 2 follow-through: side split now, playbook shape deferred

Two related items. The first is a measurement question answerable today. The
second is a genuine deferral with a stated trigger, filed here rather than left
as a comment — per the `test_deferred_work.py` convention.

## PART A — Split the counter by side (DO NOW)

Layer 2 currently reads e.g. `breakout follow-through 9 / 20 (45%) AMBER` for
`intraday_orb`. The user trades breakouts BOTH long and short under that one
playbook id.

If the counter pools sides, 9/20 could be 7/12 long and 2/8 short — two
populations inside one number, and the AMBER that comes out of it is an average
of a regime that is working and one that is not. That is the same shape as the
three RVOLs and the two curves: one name covering measurements that are not the
same measurement.

Do:

1. Determine whether the current counter pools long and short. Read it; do not
   assume from the playbook id.
2. If it pools, split it: report follow-through per side, and keep the combined
   figure only if both sides are shown alongside it.
3. The exposure grid consumes Layer 2. Decide explicitly which figure drives it
   — the side matching the candidate under consideration is the obvious answer,
   but state it rather than letting it fall out of the code.
4. `n below the calibration floor` already applies to the pooled figure.
   Splitting HALVES each n, so both sides will be further below the floor. That
   is correct and must stay visible: two honestly-unfitted numbers beat one
   averaged number that looks better sampled than it is.

Do NOT treat a side difference as a finding. With n this small it is an
observation at most. If it looks large, that is a candidate for
`docs/observations/`, not a conclusion.

## PART B — Non-breakout playbook shape (DEFERRED)

The Layer 2 metric is "breakout follow-through". It is per-playbook already, so
it is correct as long as every playbook it runs for is breakout-shaped.

Current playbooks: `intraday_orb`, `intraday_flag`, `swing_ep`, `swing_vcp`,
plus the ETF playbook (Amdt 2). All breakout-shaped, so no action needed.

TRIGGER: adding a playbook whose follow-through is not breakout-shaped — a
range or mean-reversion playbook being the obvious case. For that shape,
"did the breakout follow through" is not merely a worse metric, it is a
question about a thing that does not occur in the setup. The Layer 2 concept
would need its own definition per playbook, declared the way `lookback` and the
VWAP price source are declared: required, no default, so a new playbook cannot
inherit a metric that does not apply to it by omission.

BLOCKS: nothing today. Registered so that adding such a playbook trips this
rather than silently reusing a breakout metric.

## Why this is an artifact and not a comment

Three warnings written in-repo were correct and read past: the UNVERIFIED banner
in `condition_codes.yaml`, the module docstring naming NOII as the better source
for auction type and window, and the `_to_merge/README` note. Each would have
saved real time. A note nobody is forced to read is indistinguishable from no
note, which is what `tests/test_deferred_work.py` now enforces.
