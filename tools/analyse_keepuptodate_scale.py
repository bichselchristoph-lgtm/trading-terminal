"""Analysis for handoff task 021 -- reads the raw JSONL written by
tools/probe_keepuptodate_scale.py and answers the task's six questions.

Kept separate from the probe deliberately. The probe holds five live streams for
six hours; an exception in the arithmetic here would otherwise cost a session of
measurement that cannot be re-recorded.

Pure file reader: opens no socket, imports no broker library, takes no argument
that could reach one.

    C:\\venvs\\trading\\Scripts\\python.exe tools/analyse_keepuptodate_scale.py \\
        --out-dir records/probes/021

The one-stream baseline it compares against is 008b's measured median of 5.002 s
(AMZN, 2026-08-10, 12:34-13:06 ET, 376 updates). That number is a MEASUREMENT
FROM ANOTHER RUN, not a constant of the API -- it is carried here so the ratio
can be stated, and it is labelled everywhere it appears.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, time as dtime
from pathlib import Path
from statistics import mean, median

# 008b, AMZN, 2026-08-10 12:34-13:06 ET, one stream, 376 updates.
BASELINE_008B_MEDIAN_S = 5.002

# The task names five buckets, the first starting at 09:25, because it assumed a
# 09:25 start. This run connected at 09:12:57, so updates exist BEFORE the task's
# first boundary. A leading bucket is added rather than dropping them: the first
# version of this file had no such bucket and bucket_of() returned None for every
# pre-09:25 update, so 73 measured callbacks vanished and every bucket printed
# "no updates" while the totals showed otherwise. Anything unbucketed is now
# counted and reported -- see `unbucketed` below.
BUCKETS: list[tuple[str, dtime, dtime]] = [
    ("pre-09:25", dtime(0, 0), dtime(9, 25)),
    ("09:25-09:30", dtime(9, 25), dtime(9, 30)),
    ("09:30-10:00", dtime(9, 30), dtime(10, 0)),
    ("10:00-12:00", dtime(10, 0), dtime(12, 0)),
    ("12:00-15:30", dtime(12, 0), dtime(15, 30)),
    ("15:30-16:00", dtime(15, 30), dtime(16, 0)),
    ("16:00-close", dtime(16, 0), dtime(23, 59, 59)),  # the useRTH=False boundary
]


def stats(xs: list[float]) -> dict:
    if not xs:
        return {"n": 0, "min": None, "median": None, "mean": None, "max": None}
    return {
        "n": len(xs),
        "min": round(min(xs), 3),
        "median": round(median(xs), 3),
        "mean": round(mean(xs), 3),
        "max": round(max(xs), 3),
    }


def rank(xs: list[float]) -> list[float]:
    """Average ranks, ties shared -- needed for Spearman without scipy."""
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def pearson(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 3:
        return None
    mx, my = mean(xs), mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    if dx == 0 or dy == 0:
        return None
    return round(num / (dx * dy), 4)


def spearman(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 3:
        return None
    return pearson(rank(xs), rank(ys))


def bucket_of(t: dtime) -> str | None:
    for name, lo, hi in BUCKETS:
        if lo <= t < hi:
            return name
    return None


def load(path: Path) -> list[dict]:
    recs = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                recs.append(json.loads(line))
            except json.JSONDecodeError:
                # A run killed mid-write leaves one truncated final line. That is
                # a partial record, not a corrupt file -- drop it and say so.
                recs.append({"kind": "__truncated__"})
    return recs


def analyse_symbol(symbol: str, recs: list[dict]) -> dict:
    truncated = sum(1 for r in recs if r.get("kind") == "__truncated__")
    initial = next((r for r in recs if r.get("kind") == "initial"), None)
    rejected = next((r for r in recs if r.get("kind") == "rejected"), None)
    updates = [r for r in recs if r.get("kind") == "update"]

    by_bucket: dict[str, list[float]] = {name: [] for name, _, _ in BUCKETS}
    unbucketed = 0
    per_minute: dict[str, dict] = {}
    classes = {"APPEND_NEW_BAR": 0, "REVISE_IN_PLACE": 0, "NO_CHANGE": 0,
               "REPLACED_TIMESTAMP_WITHOUT_HASNEWBAR": 0}

    for u in updates:
        classes[u["classification"]] = classes.get(u["classification"], 0) + 1
        wall = datetime.fromisoformat(u["wall_et"])
        b = bucket_of(wall.time())
        gap = u.get("since_prev_s")
        if gap is not None:
            if b:
                by_bucket[b].append(float(gap))
            else:
                unbucketed += 1
        # Group by the FORMING minute the update referred to. Volume is the last
        # snapshot for that minute -- 008b established that the bar is revised in
        # place, so the final value is the minute's true volume and summing the
        # updates would overstate it ~6x.
        bt = u["bar_timestamp"]
        slot = per_minute.setdefault(bt, {"updates": 0, "volume": 0.0})
        slot["updates"] += 1
        slot["volume"] = float(u["bar"]["volume"])

    # Correlation is computed on REGULAR-SESSION minutes only. Pre-market minutes
    # have near-zero volume and would dominate the rank correlation with a
    # cluster that says nothing about the question being asked.
    rth = []
    for bt, v in per_minute.items():
        try:
            t = datetime.fromisoformat(bt).time()
        except ValueError:
            continue
        if dtime(9, 30) <= t < dtime(16, 0):
            rth.append((v["updates"], v["volume"]))
    upd = [float(a) for a, _ in rth]
    vol = [float(b) for _, b in rth]

    last_earliest = updates[-1].get("earliest") if updates else None
    return {
        "symbol": symbol,
        "accepted": bool(initial and initial.get("accepted")),
        "rejected": rejected,
        "truncated_lines": truncated,
        "initial": {
            "count": initial.get("count") if initial else None,
            "earliest": initial.get("earliest") if initial else None,
            "latest": initial.get("latest") if initial else None,
        },
        "final_earliest_seen": last_earliest,
        "anchor_held": bool(initial and last_earliest
                            and last_earliest == initial.get("earliest")),
        "total_updates": len(updates),
        "unbucketed_updates": unbucketed,
        "classifications": classes,
        "cadence_by_bucket": {k: stats(v) for k, v in by_bucket.items()},
        "cadence_overall": stats([g for v in by_bucket.values() for g in v]),
        "ratio_vs_008b_by_bucket": {
            k: (round(stats(v)["median"] / BASELINE_008B_MEDIAN_S, 2)
                if stats(v)["median"] else None)
            for k, v in by_bucket.items()
        },
        "volume_correlation_rth": {
            "minutes": len(rth),
            "pearson_updates_vs_volume": pearson(upd, vol),
            "spearman_updates_vs_volume": spearman(upd, vol),
        },
        "per_minute": per_minute,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--json", action="store_true", help="Dump the full result as JSON")
    args = p.parse_args(argv)

    out = Path(args.out_dir)
    summary_path = out / "021_summary.json"
    run_summary = json.loads(summary_path.read_text(encoding="utf-8")) \
        if summary_path.exists() else None

    results = []
    for path in sorted(out.glob("021_*_events.jsonl")):
        symbol = path.name[len("021_"):-len("_events.jsonl")]
        results.append(analyse_symbol(symbol, load(path)))

    run_recs = load(out / "021_run.jsonl") if (out / "021_run.jsonl").exists() else []
    drops = [r for r in run_recs if r.get("kind") == "disconnected"]
    reconnects = [r for r in run_recs if r.get("kind") == "connected"]
    api_errors = [r for r in run_recs if r.get("kind") == "api_error"]
    heartbeats = [r for r in run_recs if r.get("kind") == "heartbeat"]

    print("=" * 78)
    print("021 -- keepUpToDate at five streams")
    print("=" * 78)
    if run_summary:
        print(f"window   : {run_summary['started_et']} -> {run_summary['finished_et']} "
              f"({run_summary['observed_minutes']} min)")
        print(f"survived : {run_summary['survived_window']}  "
              f"api_errors={len(run_summary['api_errors'])}")
    else:
        print("NOTE: no 021_summary.json -- the run has not finished. Figures below are "
              "from the JSONL written so far.")
    if heartbeats:
        print(f"heartbeats: {len(heartbeats)}, last {heartbeats[-1]['wall_et']}")
    print(f"drops={len(drops)} reconnects={len(reconnects)} api_error_records={len(api_errors)}")

    print("\n-- acceptance and 04:00 anchor " + "-" * 46)
    for r in results:
        print(f"  {r['symbol']:<6} accepted={r['accepted']}  initial={r['initial']['count']} bars "
              f"earliest={r['initial']['earliest']}  anchor_held={r['anchor_held']} "
              f"(last seen {r['final_earliest_seen']})")

    print("\n-- cadence seconds by period (median, and x008b's 5.002s one-stream baseline) --")
    names = [b[0] for b in BUCKETS]
    print(f"  {'symbol':<7}" + "".join(f"{n:>16}" for n in names))
    for r in results:
        cells = []
        for n in names:
            s = r["cadence_by_bucket"][n]
            cells.append(f"{s['median']:.2f}/{r['ratio_vs_008b_by_bucket'][n]:.1f}x"
                         if s["median"] else "-")
        print(f"  {r['symbol']:<7}" + "".join(f"{c:>16}" for c in cells))

    stray = sum(r["unbucketed_updates"] for r in results)
    if stray:
        print(f"\n  !! {stray} updates fell outside every bucket and are NOT in the table "
              f"above. That is a gap in BUCKETS, not a property of the data.")

    print("\n-- full cadence detail " + "-" * 54)
    for r in results:
        print(f"  {r['symbol']}  total updates {r['total_updates']}  {r['classifications']}")
        for n in names:
            s = r["cadence_by_bucket"][n]
            if s["n"]:
                print(f"     {n:<12} n={s['n']:<5} min={s['min']:<8} median={s['median']:<8} "
                      f"mean={s['mean']:<8} max={s['max']}")
            else:
                print(f"     {n:<12} no updates")

    print("\n-- does cadence track print rate? (RTH minutes only) " + "-" * 24)
    for r in results:
        c = r["volume_correlation_rth"]
        print(f"  {r['symbol']:<6} minutes={c['minutes']:<5} "
              f"pearson={c['pearson_updates_vs_volume']}  "
              f"spearman={c['spearman_updates_vs_volume']}")

    if args.json:
        blob = {"run_summary": run_summary, "streams": results,
                "drops": drops, "reconnects": reconnects}
        dest = out / "021_analysis.json"
        dest.write_text(json.dumps(blob, indent=2, default=str), encoding="utf-8")
        print(f"\nwritten: {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
