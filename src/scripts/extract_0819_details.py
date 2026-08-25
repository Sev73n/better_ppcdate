# -*- coding: utf-8 -*-
import json
from collections import Counter
from pathlib import Path

p = Path(r"C:/Users/AI10/Desktop/ppcdata/01_配置明文/0819_decoded.json")
raw = json.loads(p.read_text(encoding="utf-8"))
data = raw["data"]
rev = {str(v): k for k, v in data["nameSpaceMap"].items()}

NEW_NS = {"ihzao", "ysm_maid", "breath_maid", "create"}
rows = []
for r in data["systemShopItems"]:
    item = r[0]
    nin = item.get("NIN", "")
    pref, name = nin.split(":", 1) if ":" in nin else ("", nin)
    ns = rev.get(pref, pref)
    buy, sell = r[1], r[2]
    tag = r[6] if len(r) > 6 else ""
    rec = r[7] if len(r) > 7 else None
    dur = item.get("durability", 0)
    count = item.get("count", 1)
    rows.append({
        "ns": ns, "name": f"{ns}:{name}", "buy": buy, "sell": sell,
        "tag": tag, "recycle": rec, "dur": dur, "count": count,
        "ratio": (sell / buy) if buy else None,
    })

print("=== NEW MOD ITEMS ===")
for x in rows:
    if x["ns"] in NEW_NS:
        print(f"{x['name']:45} buy={x['buy']:8} sell={x['sell']:8} tag={x['tag']!r:8} rec={x['recycle']} d={x['dur']} c={x['count']}")

print("\n=== RECYCLE ON ===")
for x in rows:
    if x["recycle"]:
        print(f"{x['name']:45} buy={x['buy']} sell={x['sell']} tag={x['tag']}")

print("\n=== EMPTY TAG ===")
for x in rows:
    if not x["tag"]:
        print(f"{x['name']:45} buy={x['buy']} sell={x['sell']} rec={x['recycle']}")

print("\n=== ZERO BUY ===")
for x in rows:
    if x["buy"] in (0, 0.0):
        print(f"{x['name']:45} buy={x['buy']} sell={x['sell']} tag={x['tag']}")

print("\n=== ZERO SELL (sample by ns) ===")
c = Counter()
for x in rows:
    if x["sell"] in (0, 0.0):
        c[x["ns"]] += 1
print(dict(c))
zeros = [x for x in rows if x["sell"] in (0, 0.0)]
for x in zeros[:40]:
    print(f"{x['name']:45} buy={x['buy']} tag={x['tag']} rec={x['recycle']}")
print(f"... total zero sell {len(zeros)}")

print("\n=== HIGH BUY TOP 15 ===")
for x in sorted(rows, key=lambda z: z["buy"] or 0, reverse=True)[:15]:
    print(f"{x['name']:45} buy={x['buy']} sell={x['sell']} tag={x['tag']}")

print("\n=== LUCKY DRAW FULL ===")
print(json.dumps(data["luckyDraws"], ensure_ascii=False, indent=2))

print("\n=== FUND COIN ===")
print(data["customCoinTypes"])

print("\n=== TAG COUNTS ===")
print(Counter(x["tag"] or "<empty>" for x in rows))
