---
id: 003
title: Layer 0 frozen/live split — spec landed, mockups to reconcile
status: READY
depends_on: []
touches_phase3: false
---

# TASK 003 — Reconcile the repo with Layer 0 Amendment 2

Two new files have landed from the design side. This task makes the rest of the
repo consistent with them. NO new Layer 0 code — Layer 0 stays unbuilt, and
making that visible is most of the point.

## What arrived (already in the tree, no action needed to create them)

- `docs/specs/layer0-amendment-2-frozen-vs-live.md`
- `docs/specs/mockups/mockup-05-live-context.html`

## The decision they record

Layer 0 has fourteen rows. ELEVEN are computed once at 08:00 ET and cached.
THREE are not — row 10 (gap breadth), row 12 (index instance of the tape
functions), row 13 (TICK/ADD/RSP). Those three change in real time during the
pre-market and early session.

Decision: the FROZEN ELEVEN produce the cached composite score. The LIVE THREE
display as current values ALONGSIDE it and are NOT folded into it. If the live
three are ever to move exposure, that is a recompute with a declared cadence,
never a silent refresh.

None of the fourteen is ticker-dependent. The split is frozen vs live, not
market-wide vs per-name. Layer 0 remains entirely market-wide.

## Work

1. `docs/specs/mockups/mockup-02-regime.html` currently renders Layer 0 as a
   computed score (`6 / 9  AMBER`, reduced denominator, vetoes). That is
   faithful to the SPEC and NOT to the CODE — zero of the fourteen rows are
   implemented. Edit it to:
   - replace the Layer 0 score block with the NOT BUILT refusal state, matching
     the wording used in `mockup-05-live-context.html`
   - keep the reduced-denominator explanation, but as a description of what the
     panel will show WHEN BUILT, not as a current reading
   - leave Layers 1 and 2 untouched — Layer 1 is real (`regime_pull.py`)
   Rationale, worth carrying in the edit comment: a rendered AMBER with no
   implementation behind it is the most dangerous state available, because it
   looks operational.

2. `docs/specs/mockups/mockup-README.md` — add sheet 05 to the table, and note
   that 05 sits between 03 and the attached-symbol block rather than after 04.
   Fix the cross-links so the sequence resolves.

3. The pending item "Layer 0 reduced-denominator scaling is unspecified and
   biases toward AMBER" should be CLOSED as not-applicable, with the reason
   recorded: there is no code to rescale. The 6/9 came from a model reading the
   Layer 0 document in a chat session and scoring the table by hand. Module C,
   the append-only log the Integration Spec calls the point of the build, does
   not exist, so no record of that reading survives. Re-open when `layer0.py`
   exists.

4. Register in `preregistration.yaml` COMPARISONS (not hypotheses — it does not
   predict, and it is settled by counting): the four hard vetoes are re-readings
   of rows 5, 6, 7 and 10 at different thresholds, so the veto array carries no
   information not already in those rows. Layer 0 has FOURTEEN inputs, not
   eighteen. Settlement: count sessions where a veto fires while the rest of the
   table is strong enough to outvote one -1. That is the veto's stated design
   intent and is now a countable claim.

5. Add the three Layer 0 source documents to the provenance registry that
   `test_provenance_resolves.py` checks, with `implemented: "NO"` and an
   implementation_status naming zero of fourteen. Quote the value — YAML 1.1
   parses bare NO as boolean False.

## NOT in this task

- Building `layer0.py`, `combine.py` or `intraday_tape.py`. Layer 0 stays
  unbuilt; the build was deliberately deferred behind the data synthesis.
- Deciding the row 10 veto question. Row 10 is live AND one of the four hard
  vetoes, so it can fire mid-session with positions already open. Two readings
  are stated in the amendment; neither should be inherited by default, and the
  second needs behaviour for open positions specified before it is built.
- Anything on the identification path. The `OFFICIAL` min_separation guard and
  the window widening are ahead of this in the queue and must land together.
