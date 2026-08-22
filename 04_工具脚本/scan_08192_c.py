# -*- coding: utf-8 -*-
import json
from collections import defaultdict
from pathlib import Path

def load(p):
    raw = json.loads(Path(p).read_text(encoding="utf-8"))
    data = raw["data"] if "data" in raw else raw
    rev = {str(v): k for k, v in data.get("nameSpaceMap", {}).items()}
    items = []
    for r in data["systemShopItems"]:
        item = r[0]
        nin = item.get("NIN", "")
        pref, name = nin.split(":", 1) if ":" in nin else ("", nin)
        ns = rev.get(pref, pref)
        items.append((f"{ns}:{name}", r[1], item))
    return data, items

d19, a = load(r"C:/Users/AI10/Desktop/ppcdata/01_配置明文/0819_decoded.json")
d92, b = load(r"C:/Users/AI10/Desktop/ppcdata/01_配置明文/08192_decoded.json")

sa, sb = {x[0] for x in a}, {x[0] for x in b}
print("0819", len(a), "08192", len(b))
print("added names", sorted(sb - sa))
print("removed names", sorted(sa - sb))

# enchant summary
ENCH = {
    0: "protection", 1: "fire_protection", 2: "feather_falling", 3: "blast_protection",
    4: "projectile_protection", 5: "thorns", 6: "respiration", 7: "depth_strider",
    8: "aqua_affinity", 9: "sharpness", 10: "smite", 11: "bane_of_arthropods",
    12: "knockback", 13: "fire_aspect", 14: "looting", 15: "efficiency",
    16: "silk_touch", 17: "unbreaking", 18: "fortune", 19: "power",
    20: "punch", 21: "flame", 22: "infinity", 23: "luck_of_the_sea",
    24: "lure", 25: "frost_walker", 26: "mending", 27: "binding",
    28: "vanishing", 29: "impaling", 30: "riptide", 31: "loyalty",
    32: "channeling", 33: "multishot", 34: "piercing", 35: "quick_charge",
    36: "soul_speed", 37: "swift_sneak", 38: "wind_burst", 39: "density",
    40: "breach",
}
MAX = {
    "protection": 4, "fire_protection": 4, "feather_falling": 4, "blast_protection": 4,
    "projectile_protection": 4, "thorns": 3, "respiration": 3, "depth_strider": 3,
    "aqua_affinity": 1, "sharpness": 5, "smite": 5, "bane_of_arthropods": 5,
    "knockback": 2, "fire_aspect": 2, "looting": 3, "efficiency": 5,
    "silk_touch": 1, "unbreaking": 3, "fortune": 3, "power": 5,
    "punch": 2, "flame": 1, "infinity": 1, "luck_of_the_sea": 3,
    "lure": 3, "frost_walker": 2, "mending": 1, "binding": 1,
    "vanishing": 1, "impaling": 5, "riptide": 3, "loyalty": 3,
    "channeling": 1, "multishot": 1, "piercing": 4, "quick_charge": 3,
    "soul_speed": 3, "swift_sneak": 3, "wind_burst": 3, "density": 5, "breach": 4,
}

by = defaultdict(list)
for r in d92["systemShopItems"]:
    item = r[0]
    nin = item.get("NIN", "")
    if not nin.endswith("enchanted_book"):
        continue
    ud = item.get("userData") or {}
    ench = ud.get("ench") or []
    if not ench:
        by[("generic", "vanilla_blank")].append(0)
        continue
    e = ench[0]
    eid = e.get("id", {}).get("__value__")
    lvl = e.get("lvl", {}).get("__value__")
    mod = (e.get("modEnchant") or {}).get("__value__")
    name = mod or ENCH.get(eid, f"id{eid}")
    by[name].append(lvl)

print("\n=== ENCHANT COVERAGE ===")
keep = []
drop = []
for name, lvls in sorted(by.items(), key=lambda x: str(x[0])):
    lvls = sorted(set(lvls))
    mx = MAX.get(name)
    print(f"  {str(name):24} listed={lvls} max={mx}")
    if name in ("generic",) or name == "vanilla_blank":
        continue
    if mx is None:
        # mod enchant
        if lvls:
            top = sorted(lvls)[-2:] if len(lvls) > 1 else lvls[-1:]
            keep.append((name, top, "mod, keep top2 of listed"))
            drop.append((name, [x for x in lvls if x not in top]))
        continue
    want = [mx] if mx == 1 else [mx - 1, mx]
    have_keep = [x for x in lvls if x in want]
    have_drop = [x for x in lvls if x not in want]
    keep.append((name, have_keep, f"want {want}"))
    if have_drop:
        drop.append((name, have_drop))

print("\nKEEP", len(keep))
for x in keep:
    print(" ", x)
print("\nDROP lows", drop)

print("\n=== WS items ===")
for r in d92["systemShopItems"]:
    item = r[0]
    nin = item.get("NIN", "")
    pref, name = nin.split(":", 1)
    rev = {str(v): k for k, v in d92["nameSpaceMap"].items()}
    if rev.get(pref) == "ws":
        print(name, r[1], r[6] if len(r) > 6 else "")

print("\n=== slime/string/flower unit prices ===")
rev = {str(v): k for k, v in d92["nameSpaceMap"].items()}
for r in d92["systemShopItems"]:
    item = r[0]
    nin = item.get("NIN", "")
    pref, name = nin.split(":", 1) if ":" in nin else ("", nin)
    ns = rev.get(pref, pref)
    if ns == "minecraft" and name in (
        "slime_ball", "string", "red_flower", "yellow_flower", "iron_ingot",
        "gold_ingot", "diamond", "netherite_ingot", "copper_ingot", "emerald",
        "leather", "iron_nugget", "gold_nugget",
    ):
        print(name, "c", item.get("count", 1), "buy", r[1], "sell", r[2])
