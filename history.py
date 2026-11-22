"""Index chart data for the Mudra Monk app -> history.json

Separate from fetch.py so the website's prices.json / stocks.json are never touched.
1D  = today's 5-minute closes (Upstox intraday candles)
1W / 1M / 1Y = daily closes (Upstox historical candles, last ~400 days)
"""
import datetime
import json
import os
import urllib.parse
import urllib.request

T = os.environ["UPSTOX_TOKEN"].strip()
H = {"Accept": "application/json", "Authorization": "Bearer " + T, "User-Agent": "Mozilla/5.0"}
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
now = datetime.datetime.now(IST)

INDICES = {
    "Nifty 50": "NSE_INDEX|Nifty 50",
    "Sensex": "BSE_INDEX|SENSEX",
    "Bank Nifty": "NSE_INDEX|Nifty Bank",
}


def get(url):
    req = urllib.request.Request(url, headers=H)
    return json.load(urllib.request.urlopen(req, timeout=40)).get("data", {}).get("candles", [])


def intraday(key):
    k = urllib.parse.quote(key, safe="")
    try:
        return get(f"https://api.upstox.com/v3/historical-candle/intraday/{k}/minutes/5")
    except Exception as e:  # older API as fallback
        print("v3 intraday failed", key, repr(e)[:120])
        rows = get(f"https://api.upstox.com/v2/historical-candle/intraday/{k}/1minute")
        return rows[::5] if rows else rows


def daily(key):
    k = urllib.parse.quote(key, safe="")
    to = now.date().isoformat()
    frm = (now.date() - datetime.timedelta(days=400)).isoformat()
    try:
        return get(f"https://api.upstox.com/v3/historical-candle/{k}/days/1/{to}/{frm}")
    except Exception as e:
        print("v3 daily failed", key, repr(e)[:120])
        return get(f"https://api.upstox.com/v2/historical-candle/{k}/day/{to}/{frm}")


old = {}
if os.path.exists("history.json"):
    try:
        old = json.load(open("history.json")).get("indices", {})
    except Exception:
        old = {}

out = {}
for name, key in INDICES.items():
    rec = dict(old.get(name, {}))
    # candles: [timestamp, open, high, low, close, volume, oi] — newest first
    try:
        c = intraday(key)
        if c:
            pts = sorted((r[0][11:16], round(r[4], 2)) for r in c)  # ("09:15", close)
            rec["d1"] = [list(p) for p in pts]
            rec["d1_date"] = c[0][0][:10]
    except Exception as e:
        print("intraday failed", name, repr(e)[:200])
    try:
        c = daily(key)
        if c:
            rec["daily"] = [[r[0][:10], round(r[4], 2)] for r in sorted(c, key=lambda r: r[0])]
    except Exception as e:
        print("daily failed", name, repr(e)[:200])
    if rec:
        out[name] = rec
    print(name, "1D pts", len(rec.get("d1", [])), "daily pts", len(rec.get("daily", [])))

if out:
    json.dump({"updated": now.strftime("%d %b %Y, %I:%M %p IST"), "indices": out},
              open("history.json", "w"), separators=(",", ":"))
    print("history.json written")
else:
    print("no history data; history.json unchanged")
