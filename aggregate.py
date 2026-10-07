#!/usr/bin/env python3
"""Turn the raw log CSVs into typical.json: for each garage, weekday and hour, the median free count.

Usage: aggregate.py <data-dir>
Reads <data-dir>/log/*.csv, writes <data-dir>/typical.json:
{
  "updated": "2026-10-07T11:40:00+02:00", "days": 12, "samples": 1700,
  "garages": { "motta": { "slots": [[[median, n], ... 24 hours] ... 7 weekdays (0 = Monday)],
                           "fullFrom": [hour or null per weekday] } }
}
A slot needs at least MIN_SAMPLES readings before the app shows it.
"""
import sys, pathlib, json, csv, datetime, statistics
from collections import defaultdict

MIN_SAMPLES = 3
CAPACITY = {"balestra": 426, "motta": 165, "castello": 242, "lac": 231, "campomarzio": 161, "bettydo": 96, "resega": 400}

def main():
    d = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "data")
    buckets = defaultdict(list)   # (garage, weekday, hour) -> [free, ...]
    days, samples = set(), 0
    for f in sorted((d / "log").glob("*.csv")):
        with f.open(encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                try:
                    ts = datetime.datetime.fromisoformat(row["ts"]); free = int(row["free"])
                except (KeyError, ValueError):
                    continue
                buckets[(row["garage"], ts.weekday(), ts.hour)].append(free)
                days.add(ts.date()); samples += 1
    garages = {}
    for gid, cap in CAPACITY.items():
        slots = [[None] * 24 for _ in range(7)]
        full_from = [None] * 7
        for wd in range(7):
            for h in range(24):
                v = buckets.get((gid, wd, h), [])
                if len(v) >= MIN_SAMPLES:
                    slots[wd][h] = [round(statistics.median(v)), len(v)]
            # first hour (from 06:00) where the garage is typically nearly full and stays so for the next hour too
            for h in range(6, 23):
                a, b = slots[wd][h], slots[wd][h + 1]
                if a and b and a[0] < cap * 0.1 and b[0] < cap * 0.1:
                    full_from[wd] = h; break
        garages[gid] = {"cap": cap, "slots": slots, "fullFrom": full_from}
    out = {"updated": datetime.datetime.now().astimezone().replace(microsecond=0).isoformat(),
           "days": len(days), "samples": samples, "garages": garages}
    (d / "typical.json").write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    print(f"{len(days)} days, {samples} samples -> typical.json")

if __name__ == "__main__":
    main()
