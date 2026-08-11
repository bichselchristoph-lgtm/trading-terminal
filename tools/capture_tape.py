"""Live tape capture for task 012 — QQQ, 2026-08-11.

**STANDALONE. Imports nothing from `live/`.** `live/tape/` remains un-adopted and
undecided, and this must not become an adoption by accident.

**CAPTURES RAW ONLY.** No buy/sell classification, no delta, no aggregation, no
resampling. The classification rule is not settled — `live/tape/rolling_flow.py`
uses Lee-Ready with a tick-test fallback, `live/tape/tape_reader.py` uses a
five-way quote-relative taxonomy — and a capture that computes is a capture that
cannot be recomputed under a different rule.

Every trade line therefore carries **the bid and ask in force at that moment plus
the quote's own timestamp**, so trades stay classifiable even if the quote file
is lost, and a later reader can see *which* quote a classification would have
used instead of guessing.

    python tools/capture_tape.py --port 7496 --symbol QQQ --until 16:00

Three streams, one JSONL each, under `records/tape/`. Not committed — the files
are large and their retention is a separate decision.
"""
from __future__ import annotations

import argparse
import json
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from ib_async import IB, Stock

ET = ZoneInfo("America/New_York")
REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "records" / "tape"

FLUSH_EVERY = 100
HEARTBEAT_S = 60
#: A trade timestamp further than this from the system clock, while the market
#: is open, means the stream is not live. Logged loudly rather than silently
#: tolerated -- a historical replay that looks like a live session is the same
#: failure shape as a 16:53 read that looks like an 05:00 read.
SKEW_WARN_S = 5.0
SKEW_LOUD_S = 30.0

#: 012a Phase B. The quote stamped on each trade is NOT verified to be the
#: consolidated NBBO, and at-bid/at-ask classification run against a
#: non-consolidated quote answers a different question than the same rule run
#: against a consolidated one. Nothing in the file said which -- this names it.
#:
#: MEASURED, not assumed: on 2026-08-11 at 05:10 ET the API reported
#: marketDataType=1 (live) with bidExchange='KQZ' and askExchange='PZ' -- three
#: venues quoting the bid and two the ask at one instant. So the quote is a
#: multi-venue aggregate. Whether that aggregate equals the SIP/NBBO is NOT
#: something the API reports, and this label deliberately does not claim it.
#: Christoph states the L1 line is "US Real-Time Non Consolidated Streaming
#: Quotes"; that is his statement, recorded as such in the sidecar, not an API
#: verification.
QUOTE_BASIS = "ibkr_l1_multivenue_aggregate_not_verified_nbbo"

#: 012a Phase B, second half: the provenance of every classification anyone
#: derives from these files. Written once into each stream and to a sidecar.
#:
#: EVERY ENTRY IS LABELLED BY SOURCE. The API exposes no market-data-subscription
#: tag -- accountValues() returns monetary tags only -- so the subscription set
#: is Christoph's statement and is marked as such. Conflating "he told me" with
#: "the API reported it" is the error 012a exists to correct.
PROVENANCE = {
    "subscriptions_stated_by_christoph": [
        "NASDAQ TotalView-OpenView",
        "full North America subscription set (incl. NYSE ArcaBook, Cboe BZX Depth)",
        "US Real-Time Non Consolidated Streaming Quotes (L1)",
    ],
    "subscriptions_source": "Christoph, via task 012a — NOT reported by the API",
    "api_reported": {
        "market_data_type": "1 (live) — from Ticker.marketDataType",
        "bid_ask_exchange_sample": "bidExchange='KQZ', askExchange='PZ' at 05:10 ET 2026-08-11",
        "depth_venue_probe": {
            "ISLAND": "refused, code 10089, feed named NASDAQ.NMS/DEEP",
            "NASDAQ": "refused, code 10089, feed named NASDAQ.NMS/DEEP",
            "ARCA": "served, 9x9 levels at 05:07 ET",
        },
    },
    "quote_basis": QUOTE_BASIS,
    "note": (
        "Depth refusals are recorded as codes and their face meaning. No inference "
        "about the account is attached to them; see 012a's refusal exit test."
    ),
}


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt is not None else None


class Stream:
    """Append-only JSONL sink. Flushes every FLUSH_EVERY records -- a crash must
    not cost the session."""

    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self.fh = open(path, "a", encoding="utf-8")
        self.count = 0
        self.since_flush = 0
        self.first_ts: str | None = None
        self.last_ts: str | None = None

    def write(self, rec: dict) -> None:
        self.fh.write(json.dumps(rec, default=str) + "\n")
        self.count += 1
        self.since_flush += 1
        ts = rec.get("ts") or rec.get("ts_event")
        if ts:
            self.first_ts = self.first_ts or str(ts)
            self.last_ts = str(ts)
        if self.since_flush >= FLUSH_EVERY:
            self.fh.flush()
            self.since_flush = 0

    def note(self, kind: str, **fields) -> None:
        """A non-data record -- gap, start, stop. Written into the stream itself
        so the file is self-describing."""
        self.fh.write(json.dumps({"_record": kind, "wall_utc": iso(now_utc()), **fields}) + "\n")
        self.fh.flush()

    def close(self) -> None:
        self.fh.flush()
        self.fh.close()

    def size(self) -> int:
        return self.path.stat().st_size if self.path.exists() else 0


class Capture:
    def __init__(self, ib: IB, symbol: str, day: str, want_depth: bool):
        self.ib = ib
        self.symbol = symbol
        self.want_depth = want_depth
        self.trades = Stream(OUT_DIR / f"{symbol}-{day}-trades.jsonl")
        self.quotes = Stream(OUT_DIR / f"{symbol}-{day}-quotes.jsonl")
        self.depth = Stream(OUT_DIR / f"{symbol}-{day}-depth.jsonl") if want_depth else None

        #: The quote in force. Every trade is stamped from this.
        self.quote = {"bid": None, "ask": None, "bidSize": None, "askSize": None,
                      "bidExch": None, "askExch": None, "ts": None}
        self.trades_without_quote = 0
        self.first_no_quote: str | None = None
        self.last_no_quote: str | None = None

        self.gaps: list[dict] = []
        self.disconnected_at: datetime | None = None
        self.printed = 0
        self.max_skew = 0.0
        self.skew_breaches = 0
        self.hb_counts: list[int] = []
        self.stop = False

    # ---- streams --------------------------------------------------------

    def on_pending(self, tickers) -> None:
        for t in tickers:
            self._quote_update(t)
            self._trade_updates(t)
            self._depth_update(t)

    def _quote_update(self, t) -> None:
        bid, ask = t.bid, t.ask
        if bid is None or ask is None or bid != bid or ask != ask:   # NaN-safe
            return
        if (bid, ask, t.bidSize, t.askSize) == (
            self.quote["bid"], self.quote["ask"], self.quote["bidSize"], self.quote["askSize"]
        ):
            return
        ts = iso(t.time or now_utc())
        # bidExchange/askExchange are the per-quote venue attribution -- a
        # multi-character value means several venues are at that price. This is
        # the evidence behind QUOTE_BASIS, recorded per line rather than once,
        # so a later reader can see which venues were quoting at that instant.
        self.quote = {"bid": bid, "ask": ask, "bidSize": t.bidSize, "askSize": t.askSize,
                      "bidExch": getattr(t, "bidExchange", None),
                      "askExch": getattr(t, "askExchange", None), "ts": ts}
        self.quotes.write({"ts": ts, "bid": bid, "ask": ask,
                           "bid_size": t.bidSize, "ask_size": t.askSize,
                           "bid_exchange": self.quote["bidExch"],
                           "ask_exchange": self.quote["askExch"],
                           "quote_basis": QUOTE_BASIS})

    def _trade_updates(self, t) -> None:
        for tick in getattr(t, "tickByTicks", []) or []:
            price = getattr(tick, "price", None)
            if price is None:
                continue
            ts = getattr(tick, "time", None)
            attrib = getattr(tick, "tickAttribLast", None)
            rec = {
                "ts": iso(ts),
                "price": price,
                "size": getattr(tick, "size", None),
                "exchange": getattr(tick, "exchange", None),
                "special_conditions": getattr(tick, "specialConditions", None),
                # THE field decision: the quote in force, with its own stamp.
                "bid": self.quote["bid"],
                "ask": self.quote["ask"],
                "bid_size": self.quote["bidSize"],
                "ask_size": self.quote["askSize"],
                "quote_ts": self.quote["ts"],
                "bid_exchange": self.quote["bidExch"],
                "ask_exchange": self.quote["askExch"],
                "quote_basis": QUOTE_BASIS,
                "past_limit": getattr(attrib, "pastLimit", None) if attrib else None,
                "unreported": getattr(attrib, "unreported", None) if attrib else None,
            }
            if self.quote["ts"] is None:
                self.trades_without_quote += 1
                self.first_no_quote = self.first_no_quote or rec["ts"]
                self.last_no_quote = rec["ts"]
            self.trades.write(rec)
            self._check_skew(ts)
            if self.printed < 5:
                self.printed += 1
                print(f"  TRADE {self.printed}: {rec['ts']}  {rec['price']} x {rec['size']}  "
                      f"bid {rec['bid']} / ask {rec['ask']}  ({rec['exchange']})", flush=True)

    def _depth_update(self, t) -> None:
        if not self.depth:
            return
        bids = getattr(t, "domBids", None)
        asks = getattr(t, "domAsks", None)
        if not bids and not asks:
            return
        self.depth.write({
            "ts": iso(now_utc()),
            "bids": [{"price": l.price, "size": l.size, "mm": l.marketMaker} for l in (bids or [])],
            "asks": [{"price": l.price, "size": l.size, "mm": l.marketMaker} for l in (asks or [])],
        })

    def _check_skew(self, ts) -> None:
        if not isinstance(ts, datetime):
            return
        skew = abs((now_utc() - ts).total_seconds())
        self.max_skew = max(self.max_skew, skew)
        if skew > SKEW_LOUD_S:
            self.skew_breaches += 1
            print(f"  !!!! SKEW {skew:.1f}s — trade timestamp is far from system clock. "
                  f"This may not be a live stream.", flush=True)

    # ---- connection -----------------------------------------------------

    def on_disconnect(self) -> None:
        self.disconnected_at = now_utc()
        print(f"  !!!! DISCONNECTED at {iso(self.disconnected_at)}", flush=True)

    def on_connect(self) -> None:
        if not self.disconnected_at:
            return
        gap = {"gap_start": iso(self.disconnected_at), "gap_end": iso(now_utc())}
        self.gaps.append(gap)
        # Never resume silently: an unmarked gap is indistinguishable from a
        # quiet market. Written into EVERY stream, because a reader of one file
        # must not have to consult another to learn it has a hole.
        for s in (self.trades, self.quotes, self.depth):
            if s:
                s.note("GAP", **gap)
        print(f"  reconnected; gap recorded {gap}", flush=True)
        self.disconnected_at = None

    # ---- reporting ------------------------------------------------------

    def heartbeat(self) -> None:
        self.hb_counts.append(self.trades.count)
        print(f"[{datetime.now(ET):%H:%M:%S} ET] trades={self.trades.count} "
              f"quotes={self.quotes.count} depth={self.depth.count if self.depth else '-'} "
              f"last_trade={self.trades.last_ts} connected={self.ib.isConnected()} "
              f"max_skew={self.max_skew:.1f}s gaps={len(self.gaps)}", flush=True)

    def summary(self) -> dict:
        out = {"symbol": self.symbol, "gaps": self.gaps,
               "trades_without_quote_stamp": self.trades_without_quote,
               "first_trade_without_quote": self.first_no_quote,
               "last_trade_without_quote": self.last_no_quote,
               "max_skew_seconds": round(self.max_skew, 2),
               "skew_breaches_over_30s": self.skew_breaches,
               "streams": {}}
        for name, s in (("trades", self.trades), ("quotes", self.quotes), ("depth", self.depth)):
            if s:
                out["streams"][name] = {"records": s.count, "first_ts": s.first_ts,
                                        "last_ts": s.last_ts, "bytes": s.size(),
                                        "path": str(s.path)}
        return out


def probe_depth(ib: IB, contract) -> tuple[bool, str]:
    """0e: does reqMktDepth work on this symbol, and on which exchange? Probed,
    never assumed, and NOTHING is signed up for -- a refusal here is an answer."""
    # Order matters, and the first version of this list was wrong. It tried
    # SMART, NASDAQ, ISLAND only and reported "no depth" -- but SMART returns
    # 10092 (not supported for this security type/exchange) and NASDAQ returns
    # 10089 (needs TotalView, which this account lacks), and neither of those
    # says anything about the venues that DO serve it. ARCA and BATS both
    # returned a live book on 2026-08-11 at 04:38 ET with no extra subscription.
    #
    # ARCA first on one observation only: 240x240 at 720.38/720.46 against BATS
    # 60x50 at 720.37/720.59. That is a single pre-market snapshot, not a rule.
    for exch in ("ARCA", "BATS", "NASDAQ", "SMART"):
        c = Stock(contract.symbol, exch, "USD")
        try:
            q = ib.qualifyContracts(c)
            if not q:
                continue
            t = ib.reqMktDepth(q[0], numRows=5)
            ib.sleep(4)
            ok = bool(t.domBids or t.domAsks)
            ib.cancelMktDepth(q[0])
            if ok:
                return True, exch
        except Exception as e:
            print(f"  depth probe on {exch}: {type(e).__name__}: {e}", flush=True)
    return False, ""


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, required=True)
    p.add_argument("--client-id", type=int, default=11)
    p.add_argument("--symbol", default="QQQ")
    p.add_argument("--until", default="16:00", help="ET wall-clock stop, HH:MM")
    p.add_argument("--probe-depth-only", action="store_true",
                   help="run 0e's depth probe and exit, writing nothing")
    args = p.parse_args(argv)

    ib = IB()
    # readonly=True. A capture has no business being able to place an order, and
    # in this workspace only tws_order may. Found during the 0e probe, which
    # connected read-write and sat through two order-request timeouts on
    # startup -- a capture that can trade is a capture one typo away from doing so.
    ib.connect(args.host, args.port, clientId=args.client_id, timeout=15, readonly=True)
    ib.RequestTimeout = 30
    print(f"connected {args.host}:{args.port} clientId={args.client_id} "
          f"server={ib.client.serverVersion()}", flush=True)

    qualified = ib.qualifyContracts(Stock(args.symbol, "SMART", "USD"))
    if len(qualified) != 1:
        print(f"FAILED: {args.symbol} resolved to {len(qualified)} contracts", file=sys.stderr)
        return 2
    contract = qualified[0]
    print(f"contract: {contract}", flush=True)

    have_depth, depth_exch = probe_depth(ib, contract)
    print(f"0e depth on {args.symbol}: {'YES via ' + depth_exch if have_depth else 'NO'}", flush=True)
    if args.probe_depth_only:
        ib.disconnect()
        return 0

    day = datetime.now(ET).strftime("%Y-%m-%d")
    cap = Capture(ib, args.symbol, day, have_depth)
    ib.pendingTickersEvent += cap.on_pending
    ib.disconnectedEvent += cap.on_disconnect
    ib.connectedEvent += cap.on_connect

    # LIVE VERIFICATION 1: this is reqTickByTickData, NOT reqHistoricalTicks.
    print("live-check 1: calling IB.reqTickByTickData(contract, 'AllLast') "
          "— not reqHistoricalTicks", flush=True)
    ib.reqTickByTickData(contract, "AllLast")
    ib.reqMktData(contract, "233", False, False)   # 233 verified to populate bid/askExchange
    if have_depth:
        dc = ib.qualifyContracts(Stock(args.symbol, depth_exch, "USD"))[0]
        ib.reqMktDepth(dc, numRows=10)
    for s in (cap.trades, cap.quotes, cap.depth):
        if s:
            s.note("START", symbol=args.symbol, client_id=args.client_id,
                   depth_exchange=depth_exch or None, provenance=PROVENANCE)
    (OUT_DIR / f"{args.symbol}-{day}-provenance.json").write_text(
        json.dumps({**PROVENANCE, "depth_exchange_used": depth_exch or None,
                    "symbol": args.symbol, "day": day}, indent=2), encoding="utf-8")

    hh, mm = (int(x) for x in args.until.split(":"))
    stop_at = datetime.now(ET).replace(hour=hh, minute=mm, second=0, microsecond=0)
    print(f"capturing until {stop_at:%H:%M} ET", flush=True)

    def _sigint(*_):
        cap.stop = True
    signal.signal(signal.SIGINT, _sigint)

    last_hb = time.monotonic()
    try:
        while not cap.stop and datetime.now(ET) < stop_at:
            ib.sleep(1)
            if time.monotonic() - last_hb >= HEARTBEAT_S:
                cap.heartbeat()
                last_hb = time.monotonic()
    finally:
        # Cancel EVERY subscription explicitly. Do not rely on disconnect to
        # release them -- a line still held is a line task 013 cannot use.
        for fn, arg in ((ib.cancelTickByTickData, (contract, "AllLast")),
                        (ib.cancelMktData, (contract,))):
            try:
                fn(*arg)
                print(f"  cancelled {fn.__name__}", flush=True)
            except Exception as e:
                print(f"  cancel {fn.__name__} failed: {e}", flush=True)
        if have_depth:
            try:
                ib.cancelMktDepth(dc)
                print("  cancelled cancelMktDepth", flush=True)
            except Exception as e:
                print(f"  cancel depth failed: {e}", flush=True)

        for s in (cap.trades, cap.quotes, cap.depth):
            if s:
                s.note("STOP")
                s.close()
        summary = cap.summary()
        summary["heartbeat_trade_counts"] = cap.hb_counts
        summary["monotonic_increase_across_3_heartbeats"] = (
            len(cap.hb_counts) >= 3 and all(
                b > a for a, b in zip(cap.hb_counts[-3:], cap.hb_counts[-2:])))
        (OUT_DIR / f"{args.symbol}-{day}-summary.json").write_text(
            json.dumps(summary, indent=2, default=str), encoding="utf-8")
        print("\n=== SUMMARY ===")
        print(json.dumps(summary, indent=2, default=str))
        ib.disconnect()
        print(f"disconnected; clientId {args.client_id} released", flush=True)
    return 0


# Import must never open a socket.
if __name__ == "__main__":
    sys.exit(main())
