#!/usr/bin/env python3
"""Build the list of public EV charging sites around Lugano from the federal open data (ich-tanke-strom.ch).

Usage: chargers.py <out.json> [--js]
Downloads the BFE static EVSE data (about 20 MB), keeps the stations in the Lugano area,
groups charge points that stand together into one site and writes a small JSON file:
{"updated": "...", "sites": [{"id","n","a","lat","lng","op","kw","acc","e":[evse ids]}]}
With --js it prints the same list as a JavaScript constant for pasting into index.html.
The app reads the live free/occupied status separately, straight from the BFE status feed.
"""
import sys, json, gzip, math, re, datetime, urllib.request

DATA = "https://data.geo.admin.ch/ch.bfe.ladestellen-elektromobilitaet/data/oicp/ch.bfe.ladestellen-elektromobilitaet.json"
BOX = (45.972, 8.905, 46.040, 8.995)  # lat min, lng min, lat max, lng max: Lugano and the first ring of neighbours
GROUP_M = 40

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "lugano-parking/1.0", "Accept-Encoding": "gzip"})
    b = urllib.request.urlopen(req, timeout=120).read()
    return json.loads(gzip.decompress(b) if b[:2] == b"\x1f\x8b" else b)

def dist(a, b):
    k = math.pi / 180
    x = (b[1] - a[1]) * k * math.cos((a[0] + b[0]) / 2 * k); y = (b[0] - a[0]) * k
    return 6371000 * math.hypot(x, y)

def nice_name(raw, op, street):
    raw = (raw or "").strip()
    # Codes like "N2-201902-001-D0" or "23322229 14447.1A" are not names: fall back to operator and street.
    if not raw or not re.search(r"[A-Za-z]{3}", raw) or re.match(r"^[A-Z0-9][A-Z0-9\-\. ]+$", raw):
        return f"{op} · {street}" if street else op
    raw = re.sub(r"^\S+ (GmbH|AG|SA|Sagl) ", "", raw)  # "IONITY GmbH IONITY Lugano Sud" -> "IONITY Lugano Sud"
    raw = re.sub(r"\s+\d+$", "", raw)            # "Emil Frey Noranco 7" -> "Emil Frey Noranco"
    raw = re.sub(r"\s*\|\s*Via .*$", "", raw)     # "Migros | Lugano | Via Pretorio 1" -> "Migros | Lugano"
    return raw.replace(" | ", " · ")

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "chargers.json"
    d = fetch(DATA)
    pts = []
    for op in d.get("EVSEData", []):
        opname = (op.get("OperatorName") or "").strip()
        for r in op.get("EVSEDataRecord") or []:
            try:
                la, lo = map(float, r["GeoCoordinates"]["Google"].split())
            except Exception:
                continue
            if not (BOX[0] < la < BOX[2] and BOX[1] < lo < BOX[3]):
                continue
            kw = max([float(f.get("power") or 0) for f in (r.get("ChargingFacilities") or [])] or [0])
            acc = r.get("Accessibility") or ""
            if kw == 0 and acc.startswith("Restricted"):
                continue  # dealer-only points with no data are no use to drivers
            a = r.get("Address") or {}
            names = r.get("ChargingStationNames") or []
            pts.append({"id": r["EvseID"], "lat": la, "lng": lo, "op": opname, "kw": kw, "acc": acc,
                        "street": (a.get("Street") or "").strip(), "city": (a.get("City") or "").strip(),
                        "name": names[0]["value"] if names else ""})
    sites = []
    for p in sorted(pts, key=lambda p: (p["op"], p["lat"])):
        nm = nice_name(p["name"], p["op"], p["street"])
        s = next((s for s in sites if s["op"] == p["op"] and (dist((s["lat"], s["lng"]), (p["lat"], p["lng"])) < GROUP_M
                  or (s["n"] == nm and dist((s["lat"], s["lng"]), (p["lat"], p["lng"])) < 250))), None)
        if not s:
            s = {"op": p["op"], "lat": p["lat"], "lng": p["lng"], "kw": 0, "acc": p["acc"], "e": [],
                 "n": nm, "a": ", ".join(x for x in (p["street"], p["city"]) if x)}
            sites.append(s)
        s["e"].append(p["id"]); s["kw"] = max(s["kw"], p["kw"])
    for i, s in enumerate(sorted(sites, key=lambda s: (s["lat"], s["lng"]))):
        s["id"] = f"c{i}"; s["lat"] = round(s["lat"], 5); s["lng"] = round(s["lng"], 5)
        # OICP "Free publicly accessible" means open to everyone (not free of charge); "Restricted" means customers or members only.
        s["acc"] = "restricted" if s["acc"].startswith("Restricted") else "public"
        s["kw"] = int(s["kw"]) if s["kw"] == int(s["kw"]) else s["kw"]
    sites.sort(key=lambda s: s["id"])
    keys = ["id", "n", "a", "lat", "lng", "op", "kw", "acc", "e"]
    sites = [{k: s[k] for k in keys} for s in sites]
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
    if "--js" in sys.argv:
        print("const CHARGERS_TS=" + json.dumps(now) + ";")
        print("const CHARGERS=[\n" + ",\n".join(" " + json.dumps(s, ensure_ascii=False, separators=(",", ":")) for s in sites) + "\n];")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"updated": now, "sites": sites}, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(sites)} sites, {sum(len(s['e']) for s in sites)} charge points", file=sys.stderr)

if __name__ == "__main__":
    main()
