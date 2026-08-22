# -*- coding: utf-8 -*-
import base64, json, zlib
from pathlib import Path

src = Path(r"C:/Users/AI10/Desktop/ppcdata/06_用户自行导入/08192.txt")
s = src.read_text(encoding="utf-8").strip()
if "%" in s[:20]:
    s = s.split("%", 1)[1]
raw = json.loads(zlib.decompress(base64.b64decode(s + "=" * 4)))
data = raw["data"] if "data" in raw else raw

print("TOP KEYS", list(raw.keys()) if isinstance(raw, dict) else type(raw))
print("DATA KEYS", list(data.keys()))

rev = {str(v): k for k, v in data.get("nameSpaceMap", {}).items()}

# row shape
r0 = data["systemShopItems"][0]
print("ROW LEN", len(r0))
for i, x in enumerate(r0):
    print(f"  r[{i}]", type(x).__name__, json.dumps(x, ensure_ascii=False)[:200] if not isinstance(x, dict) else list(x.keys()))

# all extra data keys that might hold display names
for k, v in data.items():
    if k == "systemShopItems":
        continue
    t = type(v).__name__
    extra = ""
    if isinstance(v, (list, dict)):
        extra = f" len={len(v)}"
    print(f"FIELD {k:30} {t}{extra}")

print("\n=== ALL bricefire ===")
print("\n=== ALL farmer / tale ===")

for r in data["systemShopItems"]:
    item = r[0]
    nin = item.get("NIN", "")
    pref, name = nin.split(":", 1) if ":" in nin else ("", nin)
    ns = rev.get(pref, pref)
    if ns in ("bricefire", "farmer_delight_nullgr", "farmers_tale_nullgr", "doll", "kaleidoscope_doll"):
        print(f"{ns}:{name:40} buy={r[1]} sell={r[2]}")

# dump any string fields in items that aren't NIN
print("\n=== item keys besides NIN/count/durability/modEnchantData ===")
extra_keys = set()
for r in data["systemShopItems"]:
    extra_keys |= set(r[0].keys())
print(extra_keys)

# items with userData that are NOT enchanted books
print("\n=== non-book userData ===")
for r in data["systemShopItems"]:
    item = r[0]
    if "userData" not in item:
        continue
    nin = item.get("NIN", "")
    if "enchanted_book" in nin:
        continue
    print(nin, r[1], r[2], json.dumps(item.get("userData"), ensure_ascii=False)[:300])

# custom tags
print("\n=== customItemTags ===")
print(json.dumps(data.get("customItemTags"), ensure_ascii=False)[:2000])
