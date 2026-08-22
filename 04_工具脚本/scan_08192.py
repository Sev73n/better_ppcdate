# -*- coding: utf-8 -*-
import base64, json, zlib
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(r"C:/Users/AI10/Desktop/ppcdata")
src = ROOT / "06_用户自行导入" / "08192.txt"
out = ROOT / "01_配置明文" / "08192_decoded.json"


def decode(s):
    s = s.strip()
    if "%" in s[:20]:
        s = s.split("%", 1)[1]
    pad = (-len(s)) % 4
    return json.loads(zlib.decompress(base64.b64decode(s + "=" * pad)))


raw = decode(src.read_text(encoding="utf-8"))
out.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
data = raw["data"] if isinstance(raw, dict) and "data" in raw else raw
rev = {str(v): k for k, v in data.get("nameSpaceMap", {}).items()}

print("NS", data.get("nameSpaceMap"))
print("tags", data.get("customItemTags"))
print("shop", len(data.get("systemShopItems", [])))

by_ns = Counter()
unpriced = []
rows = []
for r in data.get("systemShopItems", []):
    item = r[0] if isinstance(r[0], dict) else {}
    nin = item.get("NIN", "")
    pref, name = nin.split(":", 1) if ":" in nin else ("", nin)
    ns = rev.get(pref, pref)
    buy, sell = r[1] if len(r) > 1 else None, r[2] if len(r) > 2 else None
    tag = r[6] if len(r) > 6 else ""
    rec = r[7] if len(r) > 7 else None
    dur = item.get("durability", 0)
    count = item.get("count", 1)
    ench = item.get("modEnchantData")
    row = {
        "ns": ns, "name": name, "full": f"{ns}:{name}",
        "buy": buy, "sell": sell, "tag": tag, "rec": rec,
        "dur": dur, "count": count, "ench": ench,
        "keys": sorted(item.keys()),
    }
    rows.append(row)
    by_ns[ns] += 1
    if buy in (None, 0, 0.0) or tag in ("", None):
        unpriced.append(row)

print("BY_NS", dict(by_ns))
print("\n=== ALL NON-CORE NS ITEMS ===")
core = {"minecraft", "kaleidoscope_cookery", "kaleidoscope_tavern", "kaleidoscope_doll", "bricefire", "ws", "farmers_tale_nullgr"}
for x in rows:
    if x["ns"] not in core:
        print(f"{x['full']:55} buy={x['buy']!s:>8} sell={x['sell']!s:>8} tag={x['tag']!r:12} rec={x['rec']} d={x['dur']} c={x['count']} ench={x['ench']} keys={x['keys']}")

print("\n=== ENCHANTED BOOKS ===")
for x in rows:
    if "enchanted_book" in x["name"] or (x["ench"] and x["ench"] != []):
        print(f"{x['full']:40} buy={x['buy']} sell={x['sell']} d={x['dur']} c={x['count']} ench={x['ench']} tag={x['tag']!r} keys={x['keys']}")

print("\n=== ZERO/EMPTY TAG (sample all) ===")
c = 0
for x in rows:
    if x["buy"] in (0, 0.0) or not x["tag"]:
        print(f"{x['full']:55} buy={x['buy']} sell={x['sell']} tag={x['tag']!r} d={x['dur']} c={x['count']}")
        c += 1
print("unpriced-ish count", c)

print("\n=== NAME HINTS flower/cream/ring/necklace/armor/paste/ointment ===")
keys = ("flower", "cream", "ring", "necklace", "armor", "paste", "ointment", "gao", "nong", "amulet", "pendant", "charm", "plug", "insert", "trim", "bauble", "jewel")
for x in rows:
    n = x["name"].lower()
    if any(k in n for k in keys):
        print(f"{x['full']:55} buy={x['buy']} tag={x['tag']!r} d={x['dur']}")
