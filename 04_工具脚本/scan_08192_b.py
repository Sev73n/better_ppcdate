# -*- coding: utf-8 -*-
import json
from collections import Counter
from pathlib import Path

data = json.loads(Path(r"C:/Users/AI10/Desktop/ppcdata/01_配置明文/08192_decoded.json").read_text(encoding="utf-8"))["data"]
rev = {str(v): k for k, v in data["nameSpaceMap"].items()}

print("=== ENCHANT BOOKS userData ===")
books = []
for r in data["systemShopItems"]:
    item = r[0]
    nin = item.get("NIN", "")
    pref, name = nin.split(":", 1) if ":" in nin else ("", nin)
    ns = rev.get(pref, pref)
    if ns == "minecraft" and name == "enchanted_book":
        ud = item.get("userData")
        books.append((r[1], r[2], ud, item))
        print(json.dumps({"buy": r[1], "sell": r[2], "userData": ud, "keys": list(item.keys())}, ensure_ascii=False)[:400])

print("book count", len(books))

print("\n=== SEARCH ring/neck/cream/paste/girl/moe/ointment/gao/jewelry ===")
for r in data["systemShopItems"]:
    item = r[0]
    nin = item.get("NIN", "")
    blob = json.dumps(item, ensure_ascii=False).lower()
    if any(k in blob or k in nin.lower() for k in (
        "ring", "neck", "cream", "paste", "ointment", "gao", "jewel", "amulet",
        "girl", "moe", "nyan", "more_mob", "moremob", "anthrop", "loli",
        "pendant", "bracelet", "slime",
    )):
        pref, name = nin.split(":", 1) if ":" in nin else ("", nin)
        ns = rev.get(pref, pref)
        print(f"{ns}:{name} buy={r[1]} keys={list(item.keys())} item={json.dumps(item, ensure_ascii=False)[:240]}")

print("\n=== MINECRAFT NEW vs typical (zero buy, not book) ===")
for r in data["systemShopItems"]:
    item = r[0]
    nin = item.get("NIN", "")
    pref, name = nin.split(":", 1) if ":" in nin else ("", nin)
    ns = rev.get(pref, pref)
    if ns == "minecraft" and r[1] in (0, 0.0) and name != "enchanted_book":
        print(f"  {name} keys={list(item.keys())} {json.dumps(item, ensure_ascii=False)[:200]}")

print("\n=== cookery/tavern extras (0 price or new-looking) ===")
for r in data["systemShopItems"]:
    item = r[0]
    nin = item.get("NIN", "")
    pref, name = nin.split(":", 1) if ":" in nin else ("", nin)
    ns = rev.get(pref, pref)
    if ns.startswith("kaleidoscope") and r[1] in (0, 0.0):
        print(f"  {ns}:{name}")

print("\n=== armor prices vanilla ===")
for r in data["systemShopItems"]:
    item = r[0]
    nin = item.get("NIN", "")
    pref, name = nin.split(":", 1) if ":" in nin else ("", nin)
    ns = rev.get(pref, pref)
    if ns == "minecraft" and any(x in name for x in ("helmet", "chestplate", "leggings", "boots")) and "horse" not in name:
        print(f"{name}|c{item.get('count',1)} buy={r[1]} sell={r[2]}")
