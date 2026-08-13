"""Investigation script for handoff task 021 -- keepUpToDate at the open, at five
streams, for a full session.

Task 008b measured ONE keepUpToDate stream for 32 minutes mid-session and found a
median update cadence of 5.002 s. It left three deviations open, and they share a
window: the open was never observed, 32 minutes is not a session, and five
concurrent streams on one account were never tried. This script closes all three
in one run, and answers the question none of them could separately -- whether
cadence degrades when five streams share one account.

Five open requests, issued ONCE each. No re-request, no polling, no loop that
calls the API. The only repeated call is ib.sleep(), which pumps the event loop
and issues nothing.

NOTHING HERE SHIPS TO PRODUCTION. Read-only, no config written, no order path:
never imports tws_order, never calls reqExecutions, connects readonly=True.

Every callback is appended to a per-symbol JSONL and flushed as it arrives. A
six-hour run that buffered in memory and died at 15:50 would lose six hours.

    C:\\venvs\\trading\\Scripts\\python.exe tools/probe_keepuptodate_scale.py \\
        --port 7496 --client-id 121 --until 16:05 \\
        --symbols AAPL NVDA TSLA AMD SOFI \\
        --out-dir records/probes/021

Analysis is deliberately NOT done here. The run writes raw callbacks; bucketing,
cadence statistics and the volume correlation are computed afterwards from the
JSONL by tools/analyse_keepuptodate_scale.py, so a crash in the arithmetic cannot
cost a session of measurement.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, time as dtime
from pathlib import Path
from zoneinfo import ZoneInfo

from ib_async import IB, Stock

ET = ZoneInfo("America/New_York")

# ib_async's IB.RequestTimeout defaults to 0 (= wait forever). Same reasoning as
# 008b's probe, reimplemented rather than imported: this task must not create an
# import edge to the only repo that can place an order.
REQUEST_TIMEOUT_SECONDS = 30

# A heartbeat is written even when no callback arrives, so a silent stream is
# distinguishable from a dead process. 008b could not tell those apart because
# absence of output was its only symptom of both.
HEARTBEAT_SECONDS = 60


class ProbeError(Exception):
    """Connectivity or resolution failure -- never a finding."""


def now_et() -> datetime:
    return datetime.now(ET)


def stamp() -> str:
    return now_et().isoformat(timespec="milliseconds")


def snapshot(bar) -> dict:
    """The fields that would change if a bar were revised in place."""
    return {
        "date": str(bar.date),
        "open": float(bar.open),
        "high": float(bar.high),
        "low": float(bar.low),
        "close": float(bar.close),
        "volume": float(bar.volume),
        "average": float(bar.average),
        "barCount": int(bar.barCount),
    }


def parse_until(text: str) -> datetime:
    """'16:05' -> today's 16:05 ET. Rejects a time already past, because a
    deadline in the past would make the probe exit instantly and report a
    zero-length run as a completed one."""
    try:
        hh, mm = (int(x) for x in text.split(":"))
        target = now_et().replace(hour=hh, minute=mm, second=0, microsecond=0)
    except Exception as e:
        raise ProbeError(f"--until must look like 16:05, got {text!r}") from e
    if target <= now_et():
        raise ProbeError(f"--until {text} ET is already past (now {stamp()}).")
    return target


class Stream:
    """One symbol's open request and its event log."""

    def __init__(self, symbol: str, ordinal: int, out_dir: Path):
        self.symbol = symbol
        self.ordinal = ordinal          # 1-based: which request in issue order
        self.path = out_dir / f"021_{symbol}_events.jsonl"
        self.fh = open(self.path, "w", encoding="utf-8", buffering=1)
        self.accepted = False
        self.reject: dict | None = None
        self.bars = None
        self.updates = 0
        self.appends = 0
        self.revisions = 0
        self.no_change = 0
        self.anomalous = 0
        self.initial_earliest: str | None = None
        self.initial_count = 0
        self.last_seen: dict | None = None
        self.last_wall: datetime | None = None
        self.last_update_wall: datetime | None = None

    def emit(self, kind: str, **fields) -> None:
        self.fh.write(json.dumps({"kind": kind, "symbol": self.symbol,
                                  "wall_et": stamp(), **fields}, default=str) + "\n")
        self.fh.flush()

    def close(self) -> None:
        try:
            self.fh.close()
        except Exception:
            pass


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, required=True)
    p.add_argument("--client-id", type=int, required=True,
                   help="Distinct id, so this run is separable from anything else on the connection.")
    p.add_argument("--symbols", nargs="+", required=True)
    p.add_argument("--until", default="16:05", help="ET wall-clock stop time, e.g. 16:05")
    p.add_argument("--out-dir", required=True)
    args = p.parse_args(argv)

    deadline = parse_until(args.until)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = out_dir / "021_summary.json"
    run_log = open(out_dir / "021_run.jsonl", "w", encoding="utf-8", buffering=1)

    def log(kind: str, **fields) -> None:
        run_log.write(json.dumps({"kind": kind, "wall_et": stamp(), **fields}, default=str) + "\n")
        run_log.flush()

    ib = IB()
    api_errors: list[dict] = []
    conn_events: list[dict] = []

    def on_error(reqId, errorCode, errorString, contract):  # noqa: N803
        rec = {"req_id": int(reqId), "code": int(errorCode), "message": str(errorString),
               "contract": getattr(contract, "symbol", None)}
        api_errors.append({**rec, "wall_et": stamp()})
        log("api_error", **rec)
        print(f"[{stamp()}] API error {errorCode} ({rec['contract']}): {errorString}", flush=True)

    def on_disconnected():
        conn_events.append({"event": "disconnected", "wall_et": stamp()})
        log("disconnected")
        print(f"[{stamp()}] !!! DISCONNECTED", flush=True)

    def on_connected():
        conn_events.append({"event": "connected", "wall_et": stamp()})
        log("connected")
        print(f"[{stamp()}] reconnected", flush=True)

    try:
        ib.connect(args.host, args.port, clientId=args.client_id, timeout=15, readonly=True)
    except Exception as e:
        raise ProbeError(
            f"Could not connect to {args.host}:{args.port} (client_id={args.client_id}): {e}"
        ) from e
    if not ib.isConnected():
        raise ProbeError("Connection did not complete.")
    ib.RequestTimeout = REQUEST_TIMEOUT_SECONDS
    ib.errorEvent += on_error
    ib.disconnectedEvent += on_disconnected
    ib.connectedEvent += on_connected

    server_version = ib.client.serverVersion()
    started = now_et()
    print(f"[{stamp()}] connected read-only, server version {server_version}, "
          f"clientId={args.client_id}")
    log("connected_ok", server_version=server_version, client_id=args.client_id,
        symbols=args.symbols, until=deadline.isoformat(timespec="seconds"))

    streams: list[Stream] = []
    for i, sym in enumerate(args.symbols, start=1):
        streams.append(Stream(sym, i, out_dir))

    def make_handler(st: Stream):
        def on_update(bar_list, has_new_bar: bool) -> None:
            wall = now_et()
            cur = snapshot(bar_list[-1])
            prev = st.last_seen
            changed = sorted(k for k in cur if prev is None or cur[k] != prev.get(k)) \
                if (prev is None or cur != prev) else []
            same_ts = bool(prev) and cur["date"] == prev["date"]
            # The distinction that matters: an update carrying the SAME bar
            # timestamp with different values is an in-place revision of the
            # forming minute.
            classification = (
                "APPEND_NEW_BAR" if has_new_bar
                else "REVISE_IN_PLACE" if same_ts and changed
                else "NO_CHANGE" if same_ts
                else "REPLACED_TIMESTAMP_WITHOUT_HASNEWBAR"
            )
            st.updates += 1
            if classification == "APPEND_NEW_BAR":
                st.appends += 1
            elif classification == "REVISE_IN_PLACE":
                st.revisions += 1
            elif classification == "NO_CHANGE":
                st.no_change += 1
            else:
                st.anomalous += 1
            since = round((wall - st.last_wall).total_seconds(), 3) if st.last_wall else None
            st.emit(
                "update",
                seq=st.updates,
                has_new_bar=bool(has_new_bar),
                classification=classification,
                bar_timestamp=cur["date"],
                since_prev_s=since,
                changed_fields=changed,
                bar=cur,
                total_bars=len(bar_list),
                earliest=str(bar_list[0].date) if bar_list else None,
            )
            st.last_seen, st.last_wall, st.last_update_wall = cur, wall, wall
        return on_update

    # --- issue the five requests, once each, in order -------------------------
    for st in streams:
        try:
            qualified = ib.qualifyContracts(Stock(st.symbol, "SMART", "USD"))
            if len(qualified) != 1:
                raise ProbeError(f"{st.symbol!r} resolved to {len(qualified)} contracts.")
            contract = qualified[0]
            bars = ib.reqHistoricalData(
                contract,
                endDateTime="",
                durationStr="1 D",
                barSizeSetting="1 min",
                whatToShow="TRADES",
                useRTH=False,
                formatDate=1,
                keepUpToDate=True,
            )
        except (asyncio.TimeoutError, TimeoutError) as e:
            # Which ORDINAL failed is the finding: the fifth failing means a cap
            # lower than the documented 50 simultaneous requests.
            st.reject = {"reason": "timeout", "detail": f"{REQUEST_TIMEOUT_SECONDS}s", "error": str(e)}
            st.emit("rejected", ordinal=st.ordinal, **st.reject)
            log("stream_rejected", symbol=st.symbol, ordinal=st.ordinal, **st.reject)
            print(f"[{stamp()}] REJECTED #{st.ordinal} {st.symbol}: timeout", flush=True)
            continue
        except Exception as e:
            st.reject = {"reason": type(e).__name__, "error": str(e)}
            st.emit("rejected", ordinal=st.ordinal, **st.reject)
            log("stream_rejected", symbol=st.symbol, ordinal=st.ordinal, **st.reject)
            print(f"[{stamp()}] REJECTED #{st.ordinal} {st.symbol}: {e}", flush=True)
            continue

        st.bars = bars
        st.accepted = bars is not None and len(bars) > 0
        initial = [snapshot(b) for b in bars] if bars else []
        st.initial_count = len(initial)
        st.initial_earliest = initial[0]["date"] if initial else None
        st.last_seen = initial[-1] if initial else None
        st.last_wall = now_et()
        st.emit("initial", ordinal=st.ordinal, accepted=st.accepted, count=len(initial),
                earliest=st.initial_earliest,
                latest=initial[-1]["date"] if initial else None,
                con_id=int(contract.conId), exchange=contract.exchange)
        print(f"[{stamp()}] #{st.ordinal} {st.symbol:<6} ACCEPTED={st.accepted} "
              f"{len(initial)} bars, earliest {st.initial_earliest}", flush=True)
        bars.updateEvent += make_handler(st)

    accepted_streams = [s for s in streams if s.accepted]
    log("all_requests_issued", accepted=[s.symbol for s in accepted_streams],
        rejected=[s.symbol for s in streams if not s.accepted])
    if not accepted_streams:
        raise ProbeError("No stream accepted; nothing to observe.")

    print(f"[{stamp()}] observing {len(accepted_streams)} streams until "
          f"{deadline.isoformat(timespec='seconds')} ...", flush=True)

    # --- observe -------------------------------------------------------------
    next_heartbeat = now_et().timestamp() + HEARTBEAT_SECONDS
    while now_et() < deadline:
        ib.sleep(1)  # pumps the event loop; issues no request
        t = now_et()
        if t.timestamp() >= next_heartbeat:
            next_heartbeat = t.timestamp() + HEARTBEAT_SECONDS
            hb = {s.symbol: {
                "updates": s.updates,
                "silent_s": round((t - s.last_update_wall).total_seconds(), 1)
                if s.last_update_wall else None,
                "bars": len(s.bars) if s.bars is not None else None,
                "earliest": str(s.bars[0].date) if s.bars is not None and len(s.bars) else None,
            } for s in accepted_streams}
            log("heartbeat", connected=ib.isConnected(), streams=hb)
            print(f"[{t.isoformat(timespec='seconds')}] hb connected={ib.isConnected()} " +
                  "  ".join(f"{k}={v['updates']}({v['silent_s']}s)" for k, v in hb.items()),
                  flush=True)

    finished = now_et()

    # --- teardown ------------------------------------------------------------
    final: dict[str, dict] = {}
    for st in accepted_streams:
        final[st.symbol] = {
            "count": len(st.bars) if st.bars is not None else 0,
            "earliest": str(st.bars[0].date) if st.bars is not None and len(st.bars) else None,
            "latest": str(st.bars[-1].date) if st.bars is not None and len(st.bars) else None,
        }
        try:
            ib.cancelHistoricalData(st.bars)
        except Exception as e:
            log("cancel_failed", symbol=st.symbol, error=str(e))

    still_connected = ib.isConnected()
    # Everything after this point is teardown. Without the marker, our own
    # ib.disconnect() lands in conn_events and makes a clean run report itself as
    # having dropped -- which is what 008b's summary line got wrong.
    teardown_from = len(conn_events)
    ib.disconnect()
    spontaneous = conn_events[:teardown_from]

    summary = {
        "task": "021",
        "client_id": args.client_id,
        "host_port": f"{args.host}:{args.port}",
        "server_version": server_version,
        "symbols_requested": args.symbols,
        "started_et": started.isoformat(timespec="seconds"),
        "finished_et": finished.isoformat(timespec="seconds"),
        "observed_minutes": round((finished - started).total_seconds() / 60, 2),
        "request": {
            "durationStr": "1 D", "barSizeSetting": "1 min", "whatToShow": "TRADES",
            "useRTH": False, "formatDate": 1, "keepUpToDate": True, "endDateTime": "",
        },
        "streams": [
            {
                "symbol": s.symbol,
                "ordinal": s.ordinal,
                "accepted": s.accepted,
                "reject": s.reject,
                "initial_count": s.initial_count,
                "initial_earliest": s.initial_earliest,
                "final": final.get(s.symbol),
                "anchor_held": (
                    s.initial_earliest is not None
                    and final.get(s.symbol, {}).get("earliest") == s.initial_earliest
                ),
                "updates": s.updates,
                "appends": s.appends,
                "revisions_in_place": s.revisions,
                "no_change": s.no_change,
                "anomalous": s.anomalous,
                "events_file": str(s.path),
            }
            for s in streams
        ],
        "still_connected_at_end": still_connected,
        "spontaneous_connection_events": spontaneous,
        "survived_window": still_connected and not spontaneous,
        "connection_events": conn_events,
        "api_errors": api_errors,
    }
    with open(summary_path, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, default=str)
    for st in streams:
        st.close()
    log("finished", summary=str(summary_path))
    run_log.close()

    print(f"\n[{stamp()}] === SUMMARY ===")
    for s in summary["streams"]:
        print(f"  #{s['ordinal']} {s['symbol']:<6} accepted={s['accepted']} "
              f"updates={s['updates']} (append {s['appends']}, revise {s['revisions_in_place']}, "
              f"anomalous {s['anomalous']})  anchor_held={s['anchor_held']}  "
              f"earliest {s['initial_earliest']} -> {(s['final'] or {}).get('earliest')}")
    print(f"  observed        : {summary['observed_minutes']} min")
    print(f"  survived window : {summary['survived_window']} "
          f"(spontaneous drops: {spontaneous or 'none'})")
    print(f"  api errors      : {len(api_errors)}")
    print(f"  written         : {summary_path}")
    return 0


# Import must never open a socket. A prior incident had a module connect to live
# TWS at import, so a test collector walking the tree opened a live session.
if __name__ == "__main__":
    try:
        sys.exit(main())
    except ProbeError as exc:
        print(f"\nFAILED: {exc}", file=sys.stderr)
        sys.exit(2)
