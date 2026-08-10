# LAYER 0 — AMENDMENT 2: Frozen score, live rows

Supersedes nothing. Adds a split the original Layer 0 spec did not distinguish.
Filed in the REPO (not only in Drive) because the governing Layer 0 documents
living outside the tree is precisely what let this layer go unbuilt and
unnoticed. See `test_provenance_resolves.py`.

## The finding

Layer 0 is described as "computed once at 08:00 ET and cached for the session".
That is true of eleven of its fourteen rows. It is NOT true of three:

- row 10 — gap breadth (names / sectors gapping)
- row 12 — index instance of the tape functions
- row 13 — TICK / ADD / RSP

These are pre-market and early-session readings that CHANGE IN REAL TIME. Cached
at 08:00 and displayed unchanged, they show values that have since moved. A
stale number that looks current is the same failure class as the rest of this
project's catalogue.

None of the fourteen is ticker-dependent. Layer 0 remains entirely market-wide;
the split is FROZEN vs LIVE, not market vs name.

## The decision

FROZEN ELEVEN produce the cached score. The composite Layer 0 reading is
computed once at 08:00 from rows 1-9, 11 and 14, and does not move during the
session. Its denominator is whatever Amendment 1's exclusion rule leaves.

LIVE THREE display as CURRENT VALUES alongside that score. They are shown, not
folded into it. The panel therefore carries one frozen composite and three
values that update.

Consequence, stated so it cannot be quietly reversed: if the live three are ever
to move exposure, that is a RECOMPUTE WITH A DECLARED CADENCE, not a silent
refresh. "Computed once at 08:00" and "responds to live rows" cannot both be
true of one number. Whichever is chosen must be visible in the panel.

## Display placement

A separate section, positioned:

    ranked watchlist
    -> LIVE SESSION CONTEXT   (the three live rows)
    -> attached-symbol block  (levels, rules, tape, context, predictions)

Market-wide but time-varying, so it sits between day-level context and per-name
detail. The existing pre-market zone is marked "frozen at open"; these rows need
the opposite marking — still updating, with a last-updated time.

## OPEN — row 10 is a veto row

Single-theme breadth is one of Layer 0's four hard vetoes AND is in the live
group. So it can fire MID-SESSION, after positions are open.

That is a different object from a veto evaluated once pre-market: it means
exposure can be withdrawn while you are already positioned. Not decided here.
The two readings are:

- veto is evaluated ONCE at 08:00 with the frozen score, and the live display of
  row 10 is context only; or
- veto is live, and tripping it mid-session is an exposure event with defined
  behaviour for open positions.

The second needs that behaviour specified before it is built. Neither should be
inherited by default.

## Related finding, recorded here so it is not re-derived

The four hard vetoes are re-readings of rows 5, 6, 7 and 10 at different
thresholds. They are not four additional inputs. Layer 0 has FOURTEEN inputs,
not eighteen, and a veto firing is correlated with those rows already scoring
-1. The veto array's marginal value is confined to sessions where the rest of
the table outvotes one -1 — which is its stated design intent, but that is now a
countable claim rather than an assumption. Belongs in the comparisons section of
`preregistration.yaml`: it does not predict, and it is settled by counting.

## Status

Layer 0 is SPEC'd and UNBUILT. `layer0.py`, `combine.py` and `intraday_tape.py`
do not exist; zero of the fourteen rows are implemented as Layer 0 inputs. The
build was deliberately deferred behind the data synthesis — this is not
neglect. But the terminal mockup renders Layer 0 as a scored, vetoing,
exposure-driving layer, which is faithful to the spec and NOT to the code.

Until it is built, the panel must not display a Layer 0 score as though it were
computed. A rendered AMBER with no implementation behind it is the most
dangerous state available, because it looks operational.

## Source documents (Drive)

- Regime Read Template — Layer 0: Overnight / Pre-Market Risk-On Read (the
  14-row table; origin document)
- Signal Tool Integration Spec — Layer 0, Intraday Tape, Dashboard (defines
  layer0.py, combine.py, intraday_tape.py)
- Dashboard Spec — Amendment 1: Layer 0 Session Context (exclusion rule; the
  9 denominator)
