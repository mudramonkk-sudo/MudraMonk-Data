import os, json, gzip, datetime, urllib.request, urllib.parse, urllib.error
T = os.environ["UPSTOX_TOKEN"].strip()
UA = {"User-Agent": "Mozilla/5.0"}
H = {"Accept": "application/json", "Authorization": "Bearer " + T, "User-Agent": "Mozilla/5.0"}

def quotes(keys):
    url = "https://api.upstox.com/v2/market-quote/quotes?instrument_key=" + urllib.parse.quote(",".join(keys))
    req = urllib.request.Request(url, headers=H)
    return json.load(urllib.request.urlopen(req, timeout=40))["data"]

def pct(v):
    p = v.get("last_price")
    ch = v.get("net_change")
    if p and ch is not None and p != ch:
        return round(ch * 100 / (p - ch), 2)
    return None

ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
stamp = datetime.datetime.now(ist).strftime("%d %b %Y, %I:%M %p IST")

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
try:
    d = quotes(list(K))
except urllib.error.HTTPError as e:
    print("HTTP", e.code, e.read().decode()[:600])
    raise SystemExit(1)
tok = {v.get("instrument_token"): v for v in d.values()}
items = []
for k, n in K.items():
    v = tok.get(k)
    if not v:
        continue
    p = pct(v)
    if p is None:
        p = 0.0
    items.append({"n": n, "p": v.get("last_price"), "ch": v.get("net_change"), "pct": p})
if not items:
    print("no matching data:", list(d.keys())[:10])
    raise SystemExit(1)
out = {"updated": stamp, "items": items}

SYMS = set(["RELIANCE","HDFCBANK","ICICIBANK","INFY","TCS","BHARTIARTL","ITC","SBIN","LT","HINDUNILVR","KOTAKBANK","AXISBANK","BAJFINANCE","BAJAJFINSV","MARUTI","M&M","SUNPHARMA","NTPC","POWERGRID","ONGC","TATASTEEL","TITAN","ULTRACEMCO","ASIANPAINT","NESTLEIND","WIPRO","HCLTECH","TECHM","JSWSTEEL","HINDALCO","COALINDIA","ADANIENT","ADANIPORTS","GRASIM","CIPLA","DRREDDY","APOLLOHOSP","EICHERMOT","HEROMOTOCO","BAJAJ-AUTO","TRENT","BEL","INDIGO","ETERNAL","JIOFIN","SHRIRAMFIN","SBILIFE","HDFCLIFE","TATACONSUM","MAXHEALTH","INDUSINDBK","TMPV","TMCV","TATAMOTORS","VEDL","BANKBARODA","PNB","DMART","HAL","ADANIPOWER"])
ACR = set(["HDFC","ICICI","IDFC","ITC","ONGC","NTPC","BSE","NSE","TCS","HCL","SBI","LIC","UPL","IRCTC","IRFC","REC","PNB","GAIL","BEL","HAL","NMDC","SAIL","IOC","BPCL","HPCL","JSW","ABB","IFCI","IDBI","DLF","KEC","MRF","CESC","NHPC","SJVN","RVNL","BHEL","TVS","LTIMINDTREE","LTI","PVR","UCO"])
SMALL = set(["of","and","the","in","for"])

def nice(s):
    w = s.replace("&", " and ").split()
    r = []
    for x in w:
        lx = x.lower()
        if lx == "ltd" or lx == "ltd.":
            r.append("Ltd")
        elif lx in SMALL:
            r.append(lx)
        elif x in ACR:
            r.append(x)
        elif x.isalpha():
            if len(x) <= 4:
                if not any(c in "AEIOUaeiou" for c in x):
                    r.append(x.upper())
                else:
                    r.append(x.capitalize())
            else:
                r.append(x.capitalize())
        else:
            r.append(x.capitalize())
    return " ".join(r)

def vtxt(vol):
    if vol >= 10000000:
        return str(round(vol / 10000000, 2)) + " crore shares"
    return str(round(vol / 100000, 2)) + " lakh shares"

try:
    req = urllib.request.Request("https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz", headers=UA)
    ins = json.loads(gzip.decompress(urllib.request.urlopen(req, timeout=120).read()))
    ref = {}
    for r in ins:
        if r.get("segment") == "NSE_EQ":
            if r.get("instrument_type") == "EQ":
                ref[r["instrument_key"]] = [r.get("name") or r.get("trading_symbol"), r.get("trading_symbol")]
    print("equity instruments", len(ref))
    keys = list(ref)
    rows = []
    bad = 0
    for i in range(0, len(keys), 100):
        try:
            q = quotes(keys[i:i + 100])
        except Exception as e:
            bad += 1
            print("batch failed", i, repr(e)[:150])
            continue
        for v in q.values():
            info = ref.get(v.get("instrument_token"))
            if not info:
                continue
            ltp = v.get("last_price")
            if not ltp:
                continue
            p = pct(v)
            if p is None:
                p = 0.0
            oh = v.get("ohlc") or {}
            vol = v.get("volume") or 0
            rows.append([nice(info[0]), info[1].replace("&", "and"), ltp, round(v.get("net_change") or 0, 2), p, oh.get("open"), oh.get("high"), oh.get("low"), vol, info[1]])
    print("stock rows", len(rows), "failed batches", bad)
    if len(rows) > 300:
        slim = [r[:9] for r in rows]
        json.dump({"updated": stamp, "s": slim}, open("stocks.json", "w"), separators=(",", ":"))
    big = [r for r in rows if r[9] in SYMS]
    if len(big) >= 10:
        gain = sorted(big, key=lambda r: r[4], reverse=True)[:5]
        lose = sorted(big, key=lambda r: r[4])[:5]
        act = sorted(big, key=lambda r: r[8], reverse=True)[:5]
        out["g"] = [[r[0], r[1], r[2], r[4], vtxt(r[8])] for r in gain]
        out["l"] = [[r[0], r[1], r[2], r[4], vtxt(r[8])] for r in lose]
        out["v"] = [[r[0], r[1], r[2], r[4], vtxt(r[8])] for r in act]
    print("movers pool", len(big))
except Exception as e:
    print("stocks failed:", repr(e)[:300])

json.dump(out, open("prices.json", "w"))
print("ok", len(items), "movers" if "g" in out else "no movers", "stocks.json" if os.path.exists("stocks.json") else "no stocks file")
