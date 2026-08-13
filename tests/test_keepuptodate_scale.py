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
    BASELINE_008B_MEDIAN_S, BUCKETS, analyse_symbol, bucket_of, load,
    pearson, spearman, stats,
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
        "import socket, sys\n"
        "BROKER = {7496, 7497, 4001, 4002}\n"
        "_real = socket.socket.connect\n"
        "def guard(self, addr, *a, **k):\n"
        "    port = addr[1] if isinstance(addr, tuple) and len(addr) > 1 else None\n"
        "    if port in BROKER:\n"
        "        raise AssertionError('import connected to broker port %r' % (port,))\n"
        "    return _real(self, addr, *a, **k)\n"
        "socket.socket.connect = guard\n"
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
        "n": 4, "min": 1.0, "median": 2.5, "mean": 4.0, "max": 10.0}


def test_stats_of_nothing_is_none_not_zero():
    """Zero would read as 'measured, and it was zero'."""
    assert stats([]) == {"n": 0, "min": None, "median": None, "mean": None, "max": None}


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
