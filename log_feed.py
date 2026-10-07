#!/usr/bin/env python3
"""Fetch the Città di Lugano garage feed once and append one line per garage to today's CSV.

Usage: log_feed.py <data-dir>
Writes <data-dir>/log/YYYY-MM-DD.csv with lines: iso_timestamp,garage_id,free
Timestamps are in Europe/Zurich so the day files line up with local days.
"""
import re, sys, pathlib, urllib.request, datetime
from zoneinfo import ZoneInfo

FEED = "https://www.lugano.ch/vivere-lugano/muoversi-lugano/posteggi/content/0.html?ajax=true&ajaxAction=map"
# feed name -> garage id used in the app
NAMES = {"Balestra": "balestra", "Motta": "motta", "Piazza Castello": "castello", "LAC": "lac",
         "Campo Marzio": "campomarzio", "Bettydo": "bettydo", "Resega": "resega"}
PATTERN = re.compile(r'<h5 class="mb-2">([^<]+)</h5>[\s\S]*?Posteggi liberi</strong><br>\s*(\d+)')

def main():
    out_dir = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "data")
    req = urllib.request.Request(FEED, headers={"User-Agent": "lugano-parking-logger/1.0 (+github pages app)"})
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    now = datetime.datetime.now(ZoneInfo("Europe/Zurich")).replace(microsecond=0)
    rows = []
    for m in PATTERN.finditer(html):
        name = m.group(1).split(" - ")[0].strip()
        gid = NAMES.get(name)
        if gid:
            rows.append(f"{now.isoformat()},{gid},{int(m.group(2))}")
    if len(rows) < 3:
        print("feed looked wrong, nothing logged", file=sys.stderr)
        sys.exit(1)
    log_dir = out_dir / "log"
    log_dir.mkdir(parents=True, exist_ok=True)
    f = log_dir / f"{now:%Y-%m-%d}.csv"
    new = not f.exists()
    with f.open("a", encoding="utf-8") as fh:
        if new:
            fh.write("ts,garage,free\n")
        fh.write("\n".join(rows) + "\n")
    print(f"logged {len(rows)} garages at {now:%H:%M}")

if __name__ == "__main__":
    main()
