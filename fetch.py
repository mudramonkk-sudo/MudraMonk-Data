import os, json, datetime, urllib.request, urllib.parse
T = os.environ["UPSTOX_TOKEN"]
K = {
 "NSE_INDEX|Nifty 50": "Nifty 50",
 "BSE_INDEX|SENSEX": "Sensex",
 "NSE_INDEX|Nifty Bank": "Bank Nifty",
 "NSE_EQ|INE002A01018": "Reliance",
 "NSE_EQ|INE040A01034": "HDFC Bank",
 "NSE_EQ|INE467B01029": "TCS",
 "NSE_EQ|INE009A01021": "Infosys",
 "NSE_EQ|INE090A01021": "ICICI Bank",
}
url = "https://api.upstox.com/v2/market-quote/quotes?instrument_key=" + urllib.parse.quote(",".join(K))
req = urllib.request.Request(url, headers={"Accept": "application/json", "Authorization": "Bearer " + T})
d = json.load(urllib.request.urlopen(req, timeout=30))["data"]
tok = {v.get("instrument_token"): v for v in d.values()}
items = []
for k, n in K.items():
    v = tok.get(k)
    if not v:
        continue
    p = v.get("last_price")
    ch = v.get("net_change")
    pct = None
    if p and ch is not None and p != ch:
        pct = round(ch * 100 / (p - ch), 2)
    items.append({"n": n, "p": p, "ch": ch, "pct": pct})
if not items:
    raise SystemExit("no data")
ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
out = {"updated": datetime.datetime.now(ist).strftime("%d %b %Y, %I:%M %p IST"), "items": items}
json.dump(out, open("prices.json", "w"))
