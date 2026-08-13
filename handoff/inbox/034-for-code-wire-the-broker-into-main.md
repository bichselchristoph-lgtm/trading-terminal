---
id: 034
title: Wire IBKRMarketData into main() so attaching QQQ reaches a real feed
type: product
owner: claude-code
depends: 032
---

**Status** WRITTEN

**If `handoff/inbox/034-for-code-wire-the-broker-into-main.md` exists in your tree, this is for
you. If it does not, stop reading and ignore this message.**

# 034 — Attach reaches a broker

**`032` made the key press reachable. This makes it do something.** Today pressing `a` and
typing QQQ renders *"no market data — the app connects to no broker in this slice"*, because
`main()` passes no `md`.

**`live/attach/ibkr.py` — 203 lines, `IBKRMarketData`, the only module in the tree that touches
a broker — is imported by nothing at all, not even a test.** That is the fourth instance of the
green-suite-unreachable-feature pattern and the strictest of them. **This task ends it.**

**The exit test is Christoph's:** attach QQQ, compare the context block against his own charts.
That is `christoph/open/013`, which has never once been performable.

---

## READ FIRST — a live process is on the account

**Task `021` is running right now**, five `keepUpToDate` streams, `clientId=121`, until 16:05 ET.

- **Use a different `clientId`.** A collision disconnects one of them, and `021` is a six-hour
  measurement that cannot be re-run today.
- **IBKR pacing is per account, not per connection.** Every request this task issues comes out
  of the same budget `021` is spending. **Attaching one symbol is a handful of historical
  requests and is fine; a loop that polls is not.**
- **Do not stop, restart or reconnect anything belonging to `021`.**

---

## Part 1 — The connection is configured, never defaulted

`config/ibkr.yaml`. **`SPEC.md` §4.4: every setting in config, once, required, no default.**

```yaml
host:       "127.0.0.1"
port:       7496              # TWS live. 7497 is paper — they are different accounts
client_id:  7                 # REQUIRED. Must differ from every other live connection
connect_timeout_s:  10
```

**`client_id` carries a note saying a collision silently disconnects the other client** — that
is a fact about the API, not a preference, and the next person to pick a number needs to know
it. **Prefix anything that is a broker constraint rather than a choice with
`constraint:ibkr`**, with the `note` field the convention requires, because
`grep 'constraint:ibkr' config/` is the broker-migration checklist.

**Read-only.** Only `tws_order` places orders. **State in the done-note exactly what enforces
that on this connection** — if it is TWS's global read-only setting rather than anything in this
code, say so plainly and call it a convention (rule 14). **Do not claim an enforcement that is
not in the tree.**

---

## Part 2 — `main()` constructs it and hands it to the app

The app takes a `MarketData`. `main()` builds an `IBKRMarketData` from config and passes it in.
**The attach binding is unchanged** — it already calls `attach(symbol, md, origin="typed")`.

**The HEALTH panel already has the rows for this** — `sources`, `last seen`, `frames/ticks` —
and they currently render `(no feed connected)`. **They should now say what is actually true.**
A panel that has been refusing correctly since S009 gets its first real value.

---

## Part 3 — TWS absent is a rendered refusal, never an exit

**`SPEC.md` §4.2, and this is the part most likely to be got wrong.** If TWS is not running, or
the port is wrong, or the connection times out:

- **The app still launches.** Every panel renders.
- **HEALTH says which host and port failed, and why.** Not "error", not a traceback.
- **Attaching then renders a refusal naming the connection**, not a stack trace.

**A launcher that exits when TWS is down is a refusal the user cannot read** — the same defect
`029` fixed, arriving through a different door. **Demonstrate it: run with the port set to
something closed, quote what renders.**

---

## Part 4 — What the context block must carry

Every value in the block carries **source, as-of time, and lag** (`SPEC.md` §3 and the third
tenet). **A value with no stamp beside a value with one is the defect this project is named
for.**

**Two standing data rules apply and both were earned the hard way:**

- **Assert the bar count you asked for.** IBKR returned 204 bars against 205 requested, with no
  error and no flag. **A window that cannot be computed over the length it was defined for
  renders `unavailable`, never over a shorter lookback.**
- **No price from a snapshot endpoint alone.** `get_price_snapshot` returned empty objects for
  eight instruments in one run while the bar feed answered normally for all of them. **A
  degraded supplier looks exactly like a quiet market.**

**Do not add indicators.** Whatever `attach()` and `_context_block()` already compute is the
scope. **If the context block turns out to need something not yet built, that is a finding for
the done-note, not work to do here.**

---

## Part 5 — The tests

**Extend `live/tests/test_attach_is_reachable_by_key.py`. Do not write a third reachability
suite** — two sessions already wrote two, and folding them into one was the resolution.

1. **A key press against a fake that returns real-shaped data renders *values*, not a
   refusal.** Today's suite proves the panel changes; this proves it changes to something with
   content. **Seen red first** against `main()` as it stands.
2. **Connection failure renders a named refusal and the app survives** — Part 3.
3. **No network in the suite.** `IBKRMarketData` is constructed against a fake transport;
   nothing in `pytest` opens a socket. **Assert it** — the same guard `021`'s analyser has.

**Do not extend `test_attach.py`.** It tests `attach()` as a function and that separation is
what made `032`'s independent verification possible.

---

## Part 6 — Then Christoph attaches QQQ

**Write `christoph/open/015-for-christoph-attach-qqq-against-your-charts.md`?** **No — do not
write into `christoph/`.** The design session authors it. **Say in the done-note that `013` is
now performable**, and name what he should compare.

---

## Done when

- `python -m live.tui.app` connects, and HEALTH renders the connection rather than
  `(no feed connected)`.
- Pressing `a`, typing `QQQ`, enter renders a context block with stamped values.
- **With TWS closed, the app still launches and HEALTH says why.** Quoted.
- The three tests exist, the first two seen red first.
- `021` was not disturbed — say so, with the `clientId` you used.

---

## Deliverable

`handoff/done/034-for-code-wire-the-broker-into-main.md`:

1. The rendered context block for QQQ, quoted as it appears at 209 × 54.
2. The TWS-closed refusal, quoted.
3. The two reds, quoted.
4. **What enforces read-only on this connection**, and whether it is code or convention.
5. **Anything the context block needed that is not built** — a finding, not work.
6. **What you could not do**, and why. Empty is suspicious.
7. `verify.ps1` run at `<time>`. Do not quote its output.

---

**Work in a worktree, not the shared checkout. Remove it when the task completes.**
