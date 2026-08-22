# -*- coding: utf-8 -*-
"""Compare 08192 vs 08193; find 123/123 marker and jewelry cluster."""
import base64, json, zlib
from pathlib import Path

ROOT = Path(r"C:/Users/AI10/Desktop/ppcdata")


def decode(p):
    s = Path(p).read_text(encoding="utf-8").strip()
    if "%" in s[:20]:
        s = s.split("%", 1)[1]
    pad = (-len(s)) % 4
    raw = json.loads(zlib.decompress(base64.b64decode(s + "=" * pad)))
    return raw["data"] if isinstance(raw, dict) and "data" in raw else raw


def rows(data):
    rev = {str(v): k for k, v in data.get("nameSpaceMap", {}).items()}
    out = []
    for i, r in enumerate(data["systemShopItems"]):
        item = r[0]
        nin = item.get("NIN", "")
        pref, name = nin.split(":", 1) if ":" in nin else ("", nin)
        ns = rev.get(pref, f"?{pref}")
        out.append({
            "i": i,
            "ns": ns,
            "name": name,
            "full": f"{ns}:{name}",
            "buy": r[1],
            "sell": r[2],
            "tag": r[6] if len(r) > 6 else "",
            "item": item,
            "nin": nin,
            "keys": list(item.keys()),
        })
    return out


d92 = decode(ROOT / "06_用户自行导入" / "08192.txt")
d93 = decode(ROOT / "06_用户自行导入" / "08193.txt")
a, b = rows(d92), rows(d93)

print("08192", len(a), "NS", list(d92.get("nameSpaceMap", {})))
print("08193", len(b), "NS", list(d93.get("nameSpaceMap", {})))
print("NS added", set(d93.get("nameSpaceMap", {})) - set(d92.get("nameSpaceMap", {})))
print("NS removed", set(d92.get("nameSpaceMap", {})) - set(d93.get("nameSpaceMap", {})))

# 123/123
print("\n=== 123 buy or sell ===")
for x in b:
    if x["buy"] == 123 or x["sell"] == 123:
        print(json.dumps({k: x[k] for k in ("i", "full", "buy", "sell", "tag", "nin", "keys")}, ensure_ascii=False))
        print("  item", json.dumps(x["item"], ensure_ascii=False)[:800])

# name diffs
sa, sb = {x["full"] for x in a}, {x["full"] for x in b}
print("\n=== added names", len(sb - sa), "===")
for n in sorted(sb - sa):
    xs = [x for x in b if x["full"] == n]
    for x in xs:
        print(f"  + {x['full']:50} buy={x['buy']} sell={x['sell']} tag={x['tag']!r} keys={x['keys']}")

print("\n=== removed names", len(sa - sb), "===")
for n in sorted(sa - sb):
    print("  -", n)

# same name, price changed
from collections import defaultdict
pa = defaultdict(list)
pb = defaultdict(list)
for x in a:
    pa[x["full"]].append((x["buy"], x["sell"], x["tag"]))
for x in b:
    pb[x["full"]].append((x["buy"], x["sell"], x["tag"]))

print("\n=== price/tag changed (same name) ===")
for k in sorted(set(pa) & set(pb)):
    if pa[k] != pb[k]:
        print(f"  {k}")
        print(f"    92 {pa[k]}")
        print(f"    93 {pb[k]}")

# dump nearby items around 123 marker
print("\n=== neighbors of 123 marker ===")
for x in b:
    if x["buy"] == 123 or x["sell"] == 123:
        i = x["i"]
        for y in b[max(0, i - 8): i + 9]:
            mark = " <<<" if y["i"] == i else ""
            print(f"  [{y['i']:4}] {y['full']:50} {y['buy']}/{y['sell']}{mark}")

# also dump new ns items
new_ns = set(d93.get("nameSpaceMap", {})) - set(d92.get("nameSpaceMap", {}))
if new_ns:
    print("\n=== items in new namespaces ===")
    for x in b:
        if x["ns"] in new_ns:
            print(f"  {x['full']:50} buy={x['buy']} sell={x['sell']} tag={x['tag']!r}")

# save decoded
(ROOT / "01_配置明文" / "08193_decoded.json").write_text(
    json.dumps({"data": d93}, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("\nwrote 08193_decoded.json")
