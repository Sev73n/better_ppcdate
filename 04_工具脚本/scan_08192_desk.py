# -*- coding: utf-8 -*-
import json
from pathlib import Path

raw = json.loads(Path(r"C:/Users/AI10/Desktop/ppcdata/01_配置明文/08192_decoded.json").read_text(encoding="utf-8"))
data = raw["data"] if "data" in raw else raw
rev = {str(v): k for k, v in data.get("nameSpaceMap", {}).items()}

def key(item):
    nin = item.get("NIN", "")
    pref, name = nin.split(":", 1) if ":" in nin else ("", nin)
    return f"{rev.get(pref, pref)}:{name}"

want_ns = {"ihzao", "create", "ysm_maid", "breath_maid", "farmer_delight_nullgr", "farmers_tale_nullgr", "ws", "doll"}
print("=== listed new-mod items ===")
for r in data["systemShopItems"]:
    item, buy, sell = r[0], r[1], r[2]
    k = key(item)
    ns = k.split(":", 1)[0]
    if ns in want_ns:
        tag = r[6] if len(r) > 6 else ""
        print(f"{k:48} buy={buy:8} sell={sell:8} tag={tag} keys={list(item.keys())}")

print("\n=== materials ===")
names = {
    "slime_ball", "slime", "string", "leather", "iron_ingot", "gold_ingot",
    "copper_ingot", "diamond", "netherite_ingot", "emerald", "iron_nugget",
    "gold_nugget", "raw_iron", "raw_gold", "raw_copper", "coal", "redstone",
    "lapis_lazuli", "quartz", "amethyst_shard", "experience_bottle",
    "enchanted_book", "book", "anvil", "paper", "wheat", "cabbage",
    "iron_nugget", "stick", "oak_planks", "andesite", "calcite",
}
for r in data["systemShopItems"]:
    item, buy, sell = r[0], r[1], r[2]
    k = key(item)
    name = k.split(":", 1)[1]
    if name in names or "flower" in name or "dye" in name:
        if k.startswith("minecraft:"):
            print(f"{k:42} c={item.get('count',1):3} buy={buy} sell={sell}")

print("\n=== tavern paintings prices ===")
for r in data["systemShopItems"]:
    item, buy, sell = r[0], r[1], r[2]
    k = key(item)
    if "painting" in k:
        print(f"{k:70} buy={buy} sell={sell}")
