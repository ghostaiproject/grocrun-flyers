"""Weekly flyer archive for GrocRun (run by .github/workflows/flyer-archive.yml).

Pulls every grocery flyer for POSTAL from Flipp and merges its priced items into
archive_seed.json.gz in this repo; GrocRun copies it into its APK assets: the app merges it into its
own deal archive once per new "v", so new installs get past-week prices for compares.
Row = [merchant, name, price, pct, validFrom, validTo, priceText]. Keeps ~400 days, max CAP rows.
"""
import datetime, gzip, json, os, sys, unicodedata, urllib.request

BASE = "https://backflipp.wishabi.com/flipp"
PC = (os.environ.get("POSTAL") or "H2X1Y4").replace(" ", "")  # secret if set, else public downtown Montreal code
STORES = ["maxi", "super c", "iga", "metro", "walmart", "provigo", "adonis", "inter-marche", "intermarche", "costco"]
OUT = os.environ.get("OUT", "archive_seed.json.gz")
CAP = 50000


def get(u):
    r = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (Linux; Android 14) GrocRun/1.0", "Accept": "application/json"})
    return json.load(urllib.request.urlopen(r, timeout=40))


def fold(s):
    return "".join(c for c in unicodedata.normalize("NFD", s or "") if unicodedata.category(c) != "Mn").lower()


def key(r):
    return f"{r[0].lower()}|{fold(r[1])}|{r[2]}|{r[5][:10]}"


old = {"v": "", "rows": []}
if os.path.exists(OUT):
    with gzip.open(OUT, "rt", encoding="utf-8") as f:
        old = json.load(f)

flyers = [f for f in get(f"{BASE}/flyers?locale=fr&postal_code={PC}").get("flyers", [])
          if any(s in fold(f.get("merchant")) for s in STORES)]
print(f"{len(flyers)} flyers:", sorted({f.get('merchant') for f in flyers}))
new = []
for fl in flyers:
    try:
        items = get(f"{BASE}/flyers/{fl['id']}").get("items") or []
    except Exception as e:
        print("skip", fl.get("merchant"), e)
        continue
    for o in items:
        name = (o.get("name") or "").strip()
        p = o.get("price")
        try:
            price = round(float(p), 2)
        except (TypeError, ValueError):
            continue
        if not name or price <= 0:
            continue
        d = o.get("discount")
        new.append([fl.get("merchant") or "", name, price, int(d) if isinstance(d, (int, float)) and d > 0 else 0,
                    o.get("valid_from") or fl.get("valid_from") or "", o.get("valid_to") or fl.get("valid_to") or "", str(p), o.get("id")])
# "2/5$" deals (v5.4.1): the flyer list only gives 5.00; the item page's pre_price_text says "2/".
# Round prices are the likely ones: check those, store the price of ONE and priceText "2/5.0".
import re
from concurrent.futures import ThreadPoolExecutor
def _pre(item_id):
    try:
        return (get(f"{BASE}/items/{item_id}").get("item") or {}).get("pre_price_text") or ""
    except Exception:
        return ""
cand = [i for i, r in enumerate(new) if r[7] and (round(r[2] * 100) % 25 == 0 or round(r[2] * 100) % 100 in (33, 66, 67))]
with ThreadPoolExecutor(8) as ex:
    pres = list(ex.map(lambda i: _pre(new[i][7]), cand))
split = 0
for i, pre in zip(cand, pres):
    m = re.match(r"\s*(\d{1,2})\s*(/|pour\b|for\b)", pre, re.I)
    n = int(m.group(1)) if m else 1
    if 2 <= n <= 20:
        tot = new[i][2]
        new[i][2] = round(tot / n, 2)
        new[i][6] = f"{n}/{tot}"
        split += 1
new = [r[:7] for r in new]
print(len(new), "priced items pulled,", split, "2-for deals split")
if not new:
    sys.exit("nothing pulled, seed left as is")

seen, rows = set(), []
cut = (datetime.date.today() - datetime.timedelta(days=400)).isoformat()
for r in old["rows"] + new:
    k = key(r)
    if k in seen or (r[5][:10] and r[5][:10] < cut):
        continue
    seen.add(k)
    rows.append(r)
added = len(rows) - len([r for r in old["rows"] if r[5][:10] >= cut or not r[5]])
rows.sort(key=lambda r: r[5][:10])
rows = rows[-CAP:]
if added <= 0 and len(rows) == len(old["rows"]):
    print("no new rows")
    sys.exit(0)
v = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M")
os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
with gzip.open(OUT, "wt", encoding="utf-8") as f:
    json.dump({"v": v, "rows": rows}, f, ensure_ascii=False, separators=(",", ":"))
print(f"seed {v}: {len(rows)} rows (+{added}), {os.path.getsize(OUT) // 1024} KB")
