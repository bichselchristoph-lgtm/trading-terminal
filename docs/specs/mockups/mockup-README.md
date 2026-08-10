# MOCKUPS — read this first

## These are BLUEPRINTS. There is no web app.

The files named `mockup-*.html` are DESIGN DRAWINGS of a PowerShell terminal
dashboard. They are HTML because HTML is a convenient way to draw an annotated
console panel and pin margin notes beside it — not because anything renders in a
browser at runtime.

If you open one, you are looking at a drawing of console output, not at the
product. Nothing imports them. Nothing serves them. There is no frontend to
build or maintain, and no build step that consumes them.

This note exists because a folder of HTML files inside a repo reads like a web
frontend. It is not one.

## Why the running dashboard is a terminal

Decided deliberately, not by default:

- In-place redraw in a console needs no web server, no browser, and no render
  stack. That satisfies the RENDER PATH NEVER BLOCKS ON WRITE rule trivially
  rather than by careful engineering.
- It sits next to the Python harness and Claude Code, in the same window the
  rest of the work happens in.
- Fewer moving parts between a market event and it appearing on screen.

Specific panels may graduate to a richer UI later if the visuals justify it.
Nothing in the design forces that, and nothing is waiting on it.

## The four sheets

| File | Stage | Shows |
|---|---|---|
| `mockup-01-ingest.html` | Watchlist ingest | CSV drop, filename and provenance verification, the two hard refusals, the staleness AGE flag |
| `mockup-02-regime.html` | Regime read | Layers 0 / 1 / 2, the exposure grid, reduced denominator named, downgrades-only, half-size discipline |
| `mockup-03-watchlist.html` | Ranked watchlist | All 31 names ranked and none dropped, unfitted status everywhere, attached-symbol live context |
| `mockup-04-size-stage.html` | Size, stage, reconcile | Two-input sizing, four stop modes, untransmitted staged order, reconcile, the FROZEN breach state |

Read them in order; each links to the next.

## What each sheet is really demonstrating

Every one of them shows WHAT REFUSAL LOOKS LIKE. That is the point of the set.
A dashboard that only draws the happy path teaches you nothing about how the
system behaves when a file is malformed, a data source is missing, a sample is
too small, or a safety wall is breached — which is exactly when the display
matters most.

So each sheet gives screen space to:

- absence shown AS absence (`n/a` with a reason, never a zero)
- unfitted claims labelled unfitted rather than dressed as probabilities
- named missing inputs and stated denominators
- refusals that say what to do next, not just that something failed

## When these become wrong

They are SPECS, so they are wrong when the system changes — a renamed field, a
new stop mode, a changed refusal message. If you change behaviour these sheets
describe, update the sheet in the same pass or delete it. A stale blueprint
beside a governing spec makes a reader distrust both.

They are NOT wrong merely because the terminal looks slightly different in
practice; they specify content and behaviour, not pixel layout.

## Related

- `../REPO_CONSOLIDATION_PLAN.md` — repo structure
- `../../observations/` — parked findings, different lifetime, different rules
- The END-TO-END WORKFLOW doc indexes these sheets against the 12-stage spine
  and the two human gates (what to trade, whether to send).
