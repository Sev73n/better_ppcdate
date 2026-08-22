# -*- coding: utf-8 -*-
"""Re-scan 08192 for colorful cream / rings / necklaces."""
import base64, json, zlib
from collections import Counter
from pathlib import Path

ROOT = Path(r"C:/Users/AI10/Desktop/ppcdata")
src = ROOT / "06_用户自行导入" / "08192.txt"


def decode(s):
    s = s.strip()
    if "%" in s[:20]:
        s = s.split("%", 1)[1]
    pad = (-len(s)) % 4
    return json.loads(zlib.decompress(base64.b64decode(s + "=" * pad)))


raw = decode(src.read_text(encoding="utf-8"))
data = raw["data"] if isinstance(raw, dict) and "data" in raw else raw
rev = {str(v): k for k, v in data.get("nameSpaceMap", {}).items()}
print("NS MAP", json.dumps(data.get("nameSpaceMap"), ensure_ascii=False, indent=2))
print("shop", len(data.get("systemShopItems", [])))

HINT = (
    "flower", "cream", "ring", "neck", "armor", "paste", "ointment", "gao",
    "amulet", "pendant", "charm", "jewel", "dye", "color", "colour", "wax",
    "slime", "jiezhi", "xianglian", "duocai", "moe", "girl", "niang",
    "bracelet", "earring", "locket", " circlet", "band", "finger",
    "salve", "balm", "grease", "oint", "cosmetic", "makeup",
    "ore", "ingot",
)


def key(item):
    nin = item.get("NIN", "")
    pref, name = nin.split(":", 1) if ":" in nin else ("", nin)
    return rev.get(pref, pref), name, f"{rev.get(pref, pref)}:{name}"


print("\n=== buy=200 sell=10 ===")
print("\n=== buy=200 any sell ===")
print("\n=== sell=10 any ===")

c200_10 = []
c200 = []
s10 = []
zero_not_book = []
hint_hits = []
by_ns = Counter()

for r in data["systemShopItems"]:
    item, buy, sell = r[0], r[1], r[2]
    ns, name, full = key(item)
    by_ns[ns] += 1
    tag = r[6] if len(r) > 6 else ""
    rec = {
        "full": full, "buy": buy, "sell": sell, "tag": tag,
        "keys": list(item.keys()), "item": item,
        "count": item.get("count", 1),
    }
    if buy == 200 and sell == 10:
        c200_10.append(rec)
    if buy == 200:
        c200.append(rec)
    if sell == 10:
        s10.append(rec)
    if buy in (0, 0.0) and "enchanted_book" not in name:
        zero_not_book.append(rec)
    low = name.lower()
    if any(h in low for h in HINT):
        hint_hits.append(rec)

print("BY_NS", dict(by_ns))

print("\n=== EXACT 200/10 (%d) ===" % len(c200_10))
for x in c200_10:
    print(x["full"], "tag=", x["tag"], "c=", x["count"], "keys=", x["keys"])

print("\n=== buy=200 (%d) ===" % len(c200))
for x in c200:
    print(f"{x['full']:55} sell={x['sell']:8} tag={x['tag']!r:10} c={x['count']}")

print("\n=== sell=10 (%d) ===" % len(s10))
for x in s10:
    print(f"{x['full']:55} buy={x['buy']:8} tag={x['tag']!r:10}")

print("\n=== ZERO BUY not book (%d) ===" % len(zero_not_book))
for x in zero_not_book:
    print(f"{x['full']:55} sell={x['sell']} tag={x['tag']!r} keys={x['keys']}")

print("\n=== HINT HITS (%d) ===" % len(hint_hits))
for x in hint_hits:
    print(f"{x['full']:55} buy={x['buy']} sell={x['sell']} tag={x['tag']!r}")
