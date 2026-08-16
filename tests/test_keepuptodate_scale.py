"""021's probe and its analysis, proved without a broker connection.

The probe holds five live streams for six hours against a session that cannot be
re-recorded, so the parts that can be tested offline are tested offline: the
deadline parser, the bar snapshot, and every line of the analysis arithmetic.

**The rule under test, in one line: no measured callback may be silently
dropped.** The first version of the analysis had exactly that defect -- its
buckets began at 09:25 because the task's method assumed a 09:25 start, the run
actually connected at 09:12:57, and `bucket_of()` returned None for every
pre-open update. Seventy-three measured callbacks vanished and the table printed
"no updates" while the totals printed otherwise. `test_no_update_is_unbucketed`
and `test_whole_run_window_is_bucketed` exist for that, and would have caught it.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, time as dtime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from tools.probe_keepuptodate_scale import (  # noqa: E402
    ProbeError, parse_until, snapshot,
)
from tools.analyse_keepuptodate_scale import (  # noqa: E402
    BASELINE_008B_MEDIAN_S, BUCKETS, DEAD_STREAM_AFTER_S, analyse_symbol,
    bucket_of, grid_adherence, liveness, load, p95, pearson, spearman, stats,
)

ET = ZoneInfo("America/New_York")


class StubBar:
    """Only the fields ib_async's BarData exposes that a revision can move."""

    def __init__(self, date, o, h, l, c, v, avg, n):  # noqa: E741
        self.date, self.open, self.high, self.low = date, o, h, l
        self.close, self.volume, self.average, self.barCount = c, v, avg, n


# --------------------------------------------------------------------------
# the probe
# --------------------------------------------------------------------------

def test_parse_until_returns_today_at_that_et_time():
    # Only meaningful before 23:58 local ET; the run window is a trading day.
    now = datetime.now(ET)
    later = (now + timedelta(minutes=90)).replace(second=0, microsecond=0)
    got = parse_until(later.strftime("%H:%M"))
    assert got.tzinfo is not None
    assert (got.hour, got.minute) == (later.hour, later.minute)
    assert got.date() == now.date()


def test_parse_until_refuses_a_time_already_past():
    """A deadline in the past makes the observe loop exit instantly, and the
    probe would then report a zero-length run as a completed one."""
    past = (datetime.now(ET) - timedelta(hours=1)).strftime("%H:%M")
    with pytest.raises(ProbeError) as exc:
        parse_until(past)
    assert "already past" in str(exc.value)


@pytest.mark.parametrize("bad", ["16", "sixteen-oh-five", "", "16:05:00", "25:99x"])
def test_parse_until_refuses_malformed_input(bad):
    with pytest.raises(ProbeError):
        parse_until(bad)


def test_snapshot_captures_every_field_a_revision_can_move():
    """008b measured that average, barCount, close, high, low and volume are all
    revised in place while open is not. If snapshot() stopped carrying one of
    them, a revision would read as NO_CHANGE and the cadence count would fall
    silently."""
    bar = StubBar("2026-08-13 09:31:00-04:00", 1.0, 2.0, 0.5, 1.5, 900.0, 1.25, 7)
    got = snapshot(bar)
    assert got == {
        "date": "2026-08-13 09:31:00-04:00", "open": 1.0, "high": 2.0, "low": 0.5,
        "close": 1.5, "volume": 900.0, "average": 1.25, "barCount": 7,
    }
    assert set(got) >= {"average", "barCount", "close", "high", "low", "volume"}


def test_importing_the_probe_connects_to_no_broker_port():
    """preregistration records a prior incident where a module connected to live
    TWS at import, so a test collector walking the tree opened a live session.

    The assertion is narrowed to the four BROKER ports rather than to sockets in
    general, and the narrowing is the honest version: importing ib_async builds
    an asyncio event loop, and on Windows that calls socket.socketpair(), which
    is a loopback connect. A blanket 'no socket' assertion fails on that and
    would have to be deleted -- catching nothing -- whereas this one still fires
    on the incident it exists for.
    """
    code = (
        "import asyncio, socket, sys\n"
        "BROKER = {7496, 7497, 4001, 4002}\n"
        "_real = socket.socket.connect\n"
        "def guard(self, addr, *a, **k):\n"
        "    port = addr[1] if isinstance(addr, tuple) and len(addr) > 1 else None\n"
        "    if port in BROKER:\n"
        "        raise AssertionError('import connected to broker port %r' % (port,))\n"
        "    return _real(self, addr, *a, **k)\n"
        "socket.socket.connect = guard\n"
        # 054 Part 2 / 040 Part 0 (OBS-040). "socket.socket.connect" ALONE IS
        # NOT ENOUGH: on Windows asyncio runs a ProactorEventLoop, and
        # "loop.create_connection" reaches the socket through "ConnectEx"
        # without ever calling the method above -- measured by 034
        # (live/tests/test_launches_as_a_program.py), whose two-part guard
        # this mirrors. Patched on "BaseEventLoop" so it covers the selector
        # and proactor loops both.
        "_real_create = asyncio.base_events.BaseEventLoop.create_connection\n"
        "async def guard_create(self, protocol_factory, host=None, port=None, **k):\n"
        "    if port in BROKER:\n"
        "        raise AssertionError('import connected to broker port %r' % (port,))\n"
        "    return await _real_create(self, protocol_factory, host, port, **k)\n"
        "asyncio.base_events.BaseEventLoop.create_connection = guard_create\n"
        ""
        f"sys.path.insert(0, {str(REPO)!r})\n"
        "import tools.probe_keepuptodate_scale\n"
        "import tools.analyse_keepuptodate_scale\n"
        "print('clean')\n"
    )
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "clean" in r.stdout

    # Positive control: the same guard, against a module that DOES dial 7496.
    # Without this the test above passes just as well when the guard is broken,
    # and a green vacuous test is worse than no test.
    proof = code.replace(
        "import tools.probe_keepuptodate_scale\n"
        "import tools.analyse_keepuptodate_scale\n",
        "socket.socket().connect(('127.0.0.1', 7496))\n",
    )
    r2 = subprocess.run([sys.executable, "-c", proof], capture_output=True, text=True)
    assert r2.returncode != 0
    assert "import connected to broker port 7496" in r2.stderr

    # Second positive control, 054 Part 2 / 040 Part 0. The one above dials
    # SYNCHRONOUSLY and would pass just as well against the pre-054 guard,
    # which only patched "socket.socket.connect" -- exactly the version that
    # measurably let a live TWS connection through in 034 (OBS-040). This one
    # dials through "asyncio.base_events.BaseEventLoop.create_connection",
    # ib_async's own path, and must be caught by the SAME exception.
    proof_async = code.replace(
        "import tools.probe_keepuptodate_scale\n"
        "import tools.analyse_keepuptodate_scale\n",
        "async def _dial():\n"
        "    loop = asyncio.get_event_loop()\n"
        "    await loop.create_connection(asyncio.Protocol, '127.0.0.1', 7496)\n"
        "asyncio.run(_dial())\n",
    )
    r3 = subprocess.run([sys.executable, "-c", proof_async], capture_output=True, text=True)
    assert r3.returncode != 0, (
        "an asyncio connection to a broker port was NOT refused by the guard -- "
        "the exact hole OBS-040 measured. stdout:\n" + r3.stdout)
    assert "import connected to broker port 7496" in r3.stderr, r3.stderr


# --------------------------------------------------------------------------
# bucketing -- the regression that motivated this file
# --------------------------------------------------------------------------

@pytest.mark.parametrize("t,expected", [
    (dtime(4, 0), "pre-09:25"),
    (dtime(9, 12, 57), "pre-09:25"),      # the actual connect time of the 021 run
    (dtime(9, 24, 59), "pre-09:25"),
    (dtime(9, 25), "09:25-09:30"),
    (dtime(9, 29, 59), "09:25-09:30"),
    (dtime(9, 30), "09:30-10:00"),
    (dtime(9, 59, 59), "09:30-10:00"),
    (dtime(10, 0), "10:00-12:00"),
    (dtime(11, 59), "10:00-12:00"),
    (dtime(12, 0), "12:00-15:30"),
    (dtime(15, 29), "12:00-15:30"),
    (dtime(15, 30), "15:30-16:00"),
    (dtime(15, 59, 59), "15:30-16:00"),
    (dtime(16, 0), "16:00-close"),
    (dtime(16, 5), "16:00-close"),
])
def test_bucket_boundaries_are_half_open_and_exhaustive(t, expected):
    assert bucket_of(t) == expected


def test_whole_run_window_is_bucketed():
    """Every minute from the 04:00 anchor to the 16:05 stop lands somewhere. The
    defect this catches is a hole between buckets, which loses measurements
    without any error."""
    t = datetime(2026, 8, 13, 4, 0)
    end = datetime(2026, 8, 13, 16, 5)
    holes = []
    while t <= end:
        if bucket_of(t.time()) is None:
            holes.append(t.time().isoformat())
        t += timedelta(minutes=1)
    assert holes == [], f"unbucketed minutes: {holes[:10]}"


def test_buckets_do_not_overlap():
    """An overlap would double-count a gap into two periods."""
    for i, (name_a, lo_a, hi_a) in enumerate(BUCKETS):
        for name_b, lo_b, hi_b in BUCKETS[i + 1:]:
            assert hi_a <= lo_b or hi_b <= lo_a, f"{name_a} overlaps {name_b}"


# --------------------------------------------------------------------------
# arithmetic
# --------------------------------------------------------------------------

def test_stats_on_a_known_list():
    assert stats([1.0, 2.0, 3.0, 10.0]) == {
        "n": 4, "min": 1.0, "median": 2.5, "mean": 4.0, "p95": 10.0, "max": 10.0}


def test_stats_of_nothing_is_none_not_zero():
    """Zero would read as 'measured, and it was zero'."""
    assert stats([]) == {"n": 0, "min": None, "median": None, "mean": None,
                         "p95": None, "max": None}


def test_p95_is_nearest_rank_so_every_value_it_returns_really_happened():
    """An interpolated p95 would report a silence nobody measured, and the tail
    is the entire reason for quoting it."""
    xs = [float(i) for i in range(1, 101)]          # 1..100
    assert p95(xs) == 95.0
    assert p95([1.0]) == 1.0
    assert p95([]) is None
    # Nearest-rank never invents a value between observations.
    assert p95([1.0, 2.0, 100.0]) in (1.0, 2.0, 100.0)


def test_max_catches_a_lone_burst_that_p95_is_blind_to():
    """The reason this exists, and a caveat on how to read the table.

    Nineteen 5 s gaps and one 59.2 s hole -- AMZN's 09:19 shape. The median says
    5. So does p95: at n=20 the nearest-rank 95th is the 19th value, and a
    1-in-20 event sits above it. **Only max sees a single hole.** p95 starts
    reporting the tail once it happens twice in twenty. Both are quoted because
    they answer different questions -- p95 is the recurring tail, max is the
    worst thing that actually happened."""
    s = stats([5.0] * 19 + [59.2])
    assert s["median"] == 5.0
    assert s["p95"] == 5.0        # blind, by construction
    assert s["max"] == 59.2       # the one that catches it

    twice = stats([5.0] * 18 + [59.2, 59.2])
    assert twice["p95"] == 59.2   # two in twenty, and p95 reports it


def test_grid_adherence_separates_skipped_ticks_from_a_slower_beat():
    """The distinction the measurement turns on. A stream sitting on 5, 10 and
    15 s is keeping a 5 s beat and skipping ticks; one sitting on 7 s has a
    different beat. Both have a median above 5 and only this tells them apart."""
    skipping = grid_adherence([5.0, 10.0, 5.0, 15.0, 5.0])
    assert skipping["on_grid_pct"] == 100.0
    assert skipping["ticks_skipped_histogram"] == {1: 3, 2: 1, 3: 1}

    off_grid = grid_adherence([7.0, 7.2, 6.8, 7.1])
    assert off_grid["on_grid_pct"] == 0.0


def test_grid_adherence_of_nothing_is_none_not_a_hundred_percent():
    g = grid_adherence([])
    assert g["counted"] == 0 and g["on_grid_pct"] is None


def test_correlation_signs():
    up = [1.0, 2.0, 3.0, 4.0, 5.0]
    down = [5.0, 4.0, 3.0, 2.0, 1.0]
    assert pearson(up, up) == 1.0
    assert pearson(up, down) == -1.0
    assert spearman(up, [1.0, 4.0, 9.0, 16.0, 25.0]) == 1.0   # monotone, not linear
    assert pearson(up, [1.0] * 5) is None                      # no variance, not 0.0
    assert spearman([1.0, 2.0], [1.0, 2.0]) is None            # too few points


def test_spearman_shares_ranks_for_ties():
    assert spearman([1.0, 1.0, 2.0, 3.0], [1.0, 1.0, 2.0, 3.0]) == 1.0


# --------------------------------------------------------------------------
# end to end on synthetic callbacks
# --------------------------------------------------------------------------

def _records() -> list[dict]:
    """Two forming minutes at 09:31 and 09:32, revised then appended -- the shape
    008b measured. 09:31 is restated three times: 100 -> 400 -> 900 shares."""
    def upd(wall, bar_ts, vol, cls, has_new, gap, earliest="2026-08-13 04:00:00-04:00"):
        return {"kind": "update", "symbol": "TEST", "wall_et": wall,
                "classification": cls, "has_new_bar": has_new,
                "bar_timestamp": bar_ts, "since_prev_s": gap,
                "changed_fields": ["close", "volume"], "earliest": earliest,
                "bar": {"date": bar_ts, "open": 1.0, "high": 1.0, "low": 1.0,
                        "close": 1.0, "volume": float(vol), "average": 1.0,
                        "barCount": 1}}
    return [
        {"kind": "initial", "symbol": "TEST", "wall_et": "2026-08-13T09:12:57-04:00",
         "accepted": True, "count": 313, "earliest": "2026-08-13 04:00:00-04:00",
         "latest": "2026-08-13 09:12:00-04:00"},
        upd("2026-08-13T09:13:02-04:00", "2026-08-13 09:13:00-04:00", 50, "REVISE_IN_PLACE", False, 5.0),
        upd("2026-08-13T09:31:05-04:00", "2026-08-13 09:31:00-04:00", 100, "APPEND_NEW_BAR", True, 4.0),
        upd("2026-08-13T09:31:11-04:00", "2026-08-13 09:31:00-04:00", 400, "REVISE_IN_PLACE", False, 6.0),
        upd("2026-08-13T09:31:16-04:00", "2026-08-13 09:31:00-04:00", 900, "REVISE_IN_PLACE", False, 5.0),
        upd("2026-08-13T09:32:03-04:00", "2026-08-13 09:32:00-04:00", 200, "APPEND_NEW_BAR", True, 7.0),
    ]


def test_per_minute_volume_replaces_it_does_not_accumulate():
    """The finding 008b leads with. 09:31 is restated 100 -> 400 -> 900; its true
    volume is 900, not 1,400. Getting this wrong overstated volume 5.94x there,
    and RVOL's denominator with it."""
    r = analyse_symbol("TEST", _records())
    assert r["per_minute"]["2026-08-13 09:31:00-04:00"] == {"updates": 3, "volume": 900.0}
    assert r["per_minute"]["2026-08-13 09:32:00-04:00"] == {"updates": 1, "volume": 200.0}


def test_no_update_is_unbucketed():
    """The regression this file was written for. The 09:13 update precedes the
    task's first named bucket; before the fix it was dropped without a word."""
    r = analyse_symbol("TEST", _records())
    assert r["unbucketed_updates"] == 0
    assert r["cadence_by_bucket"]["pre-09:25"]["n"] == 1
    bucketed = sum(b["n"] for b in r["cadence_by_bucket"].values())
    assert bucketed == r["total_updates"]


def test_worst_rth_silence_is_the_largest_gap_with_the_moment_it_ended():
    """A median of 5 s can sit on top of a 40 s hole, and the hole is what a stop
    level waits for. The worst gap is reported with its wall clock so it can be
    quoted rather than only counted."""
    r = analyse_symbol("TEST", _records())
    w = r["worst_rth_silence"]
    assert w["silence_s"] == 7.0                      # the 09:32 gap, not the 6.0 at 09:31
    assert w["ended_at"] == "2026-08-13T09:32:03-04:00"
    assert w["bucket"] == "09:30-10:00"


def test_a_pre_open_hole_never_becomes_the_rth_headline():
    """AMZN went 59.2 s dark at 09:19, before the open. The console does not
    trade then, so that must not be reported as the session's worst silence."""
    recs = _records()
    recs[1]["since_prev_s"] = 59.2                    # the 09:13 pre-market update
    r = analyse_symbol("TEST", recs)
    assert r["worst_rth_silence"]["silence_s"] == 7.0
    assert r["cadence_by_bucket"]["pre-09:25"]["max"] == 59.2


def test_worst_rth_silence_is_none_when_nothing_traded_in_session():
    """None, not 0.0 -- zero would read as 'measured, and it was never dark'."""
    recs = [r for r in _records() if r["kind"] != "update" or "09:13" in r["wall_et"]]
    assert analyse_symbol("TEST", recs)["worst_rth_silence"] is None


def test_a_connected_socket_is_not_a_delivering_stream():
    """The finding this run turned on, pinned so it cannot be softened later.

    At 15:22:15 every stream stopped delivering; the run ran to 16:05:00 with the
    socket up and reported survived_window=True. 42.75 minutes of a session that
    cannot be re-recorded went unmeasured while the connection flag said fine."""
    lv = liveness("2026-08-13T15:22:15-04:00", "2026-08-13T16:05:00-04:00")
    assert lv["silent_tail_s"] == 2565.0
    assert lv["delivering_at_end"] is False


def test_a_stream_still_beating_at_the_end_reads_as_delivering():
    lv = liveness("2026-08-13T16:04:57-04:00", "2026-08-13T16:05:00-04:00")
    assert lv["silent_tail_s"] == 3.0
    assert lv["delivering_at_end"] is True


def test_dead_stream_threshold_clears_the_worst_legitimate_silence():
    """59.999 s was the widest real gap measured -- pre-market, quietest symbol.
    The threshold must sit above it or a quiet pre-open stream reads as dead."""
    assert DEAD_STREAM_AFTER_S > 60.0
    assert liveness("2026-08-13T09:19:00-04:00",
                    "2026-08-13T09:20:00-04:00")["delivering_at_end"] is True


def test_liveness_is_unknown_not_alive_when_the_run_has_not_ended():
    """None, not True. An unfinished run must not report its streams healthy."""
    lv = liveness("2026-08-13T15:22:15-04:00", None)
    assert lv["delivering_at_end"] is None and lv["silent_tail_s"] is None


def test_last_update_is_carried_out_of_the_events(tmp_path):
    r = analyse_symbol("TEST", _records())
    assert r["first_update_et"] == "2026-08-13T09:13:02-04:00"
    assert r["last_update_et"] == "2026-08-13T09:32:03-04:00"


def test_classifications_and_anchor_are_reported():
    r = analyse_symbol("TEST", _records())
    assert r["accepted"] is True
    assert r["total_updates"] == 5
    assert r["classifications"]["APPEND_NEW_BAR"] == 2
    assert r["classifications"]["REVISE_IN_PLACE"] == 3
    assert r["anchor_held"] is True


def test_anchor_reported_broken_when_the_window_slides():
    """A sliding window is the documented unknown keepUpToDate was probed for.
    If the earliest bar moves off 04:00, this must say so."""
    recs = _records()
    recs[-1]["earliest"] = "2026-08-13 09:30:00-04:00"
    r = analyse_symbol("TEST", recs)
    assert r["anchor_held"] is False


def test_ratio_is_stated_against_the_008b_baseline():
    r = analyse_symbol("TEST", _records())
    med = r["cadence_by_bucket"]["09:30-10:00"]["median"]
    assert r["ratio_vs_008b_by_bucket"]["09:30-10:00"] == round(med / BASELINE_008B_MEDIAN_S, 2)
    assert BASELINE_008B_MEDIAN_S == 5.002


def test_correlation_uses_regular_session_minutes_only():
    """Pre-market minutes are near-zero volume and would dominate the rank
    correlation with a cluster that says nothing about the question."""
    r = analyse_symbol("TEST", _records())
    assert r["volume_correlation_rth"]["minutes"] == 2   # 09:31 and 09:32, not 09:13


def test_a_truncated_final_line_is_counted_not_fatal(tmp_path):
    """A run killed mid-write leaves one partial record. Losing the whole file
    to it would discard a session of measurement that cannot be re-recorded."""
    p = tmp_path / "021_TEST_events.jsonl"
    with open(p, "w", encoding="utf-8") as fh:
        for rec in _records():
            fh.write(json.dumps(rec) + "\n")
        fh.write('{"kind": "update", "symbol": "TE')   # died here
    recs = load(p)
    r = analyse_symbol("TEST", recs)
    assert r["truncated_lines"] == 1
    assert r["total_updates"] == 5
