# -*- coding: utf-8 -*-
"""Reprice kaleidoscope cookery/tavern to labor plan C: L1=3, L2=4, L3=5.
Keep materials, empty_cup, kitchen/bar furniture & tools at low fixed prices.
"""
import json
import base64
import zlib
from pathlib import Path

BASE = Path(r"C:/Users/AI10/Desktop/ppcdata")
CFG = BASE / "01_配置明文" / "最终配置_rebuilt.json"
SELL = 0.625

# Plan C
L0, L1, L2, L3 = 1.0, 3.0, 4.0, 5.0

MAT = {
    "seed": 1.00,
    "crop": 4.00,
    "oil": 5.00,
    "raw_meat": 6.00,
    "flour": 5.00,
    "dough": 8.00,
    "simple_mat": 10.00,
    "bowl_mat": 10.00,
    "special_mat": 10.00,
    "tea_mat": 10.00,
    "soup_mat": 10.00,
    "equip": 30.00,
    "knife_iron": 80.00,
    "knife_gold": 120.00,
    "knife_diamond": 400.00,
    "knife_netherite": 2000.00,
}


def r2(x):
    return round(float(x) + 1e-12, 2)


def sell_of(buy):
    s = r2(buy * SELL)
    if s >= buy and buy > 0:
        s = r2(buy - 0.01) if buy > 0.01 else 0.0
    return s


def cookery_price(name: str) -> tuple[str, float, int]:
    n = name
    if n == "empty_cup":
        return "L0", 10.00, 16
    if n.endswith("_seed") or n in ("manual", "recipe_book", "recipe_item"):
        return "L0", MAT["seed"], 64
    if n in (
        "tomato",
        "lettuce",
        "red_chili",
        "green_chili",
        "rice_panicle",
        "rice",
        "wild_rice",
        "caterpillar",
        "sashimi",
        "oil",
    ):
        return "L0", MAT["crop"] if n != "oil" else MAT["oil"], 64
    if n in ("flour",):
        return "L0", MAT["flour"], 64
    if n in (
        "raw_dough",
        "raw_noodles",
        "stuffed_dough_food",
        "raw_zongzi",
        "raw_bamboo_tube_rice",
    ):
        return "L0", MAT["dough"], 64
    if n.startswith("raw_"):
        return "L0", MAT["raw_meat"], 64

    # equipment / decor — fixed, no dish labor
    if any(
        x in n
        for x in (
            "stove",
            "pot",
            "stockpot",
            "chopping",
            "millstone",
            "steamer",
            "shawarma",
            "teapot",
            "trash",
            "enamel",
            "kitchenware",
            "fruit_basket",
            "scarecrow",
            "oil_pot",
            "oil_block",
            "straw",
            "chili_ristra",
            "strung",
            "transmutation",
            "cook_stool",
            "chair_",
            "table_",
        )
    ):
        return "EQ", MAT["equip"], (
            1 if ("stove" in n or "millstone" in n or "stockpot" in n) else 16
        )
    if "kitchen_knife" in n or n in ("kitchen_shovel", "sickle"):
        if "netherite" in n:
            return "EQ", MAT["knife_netherite"], 1
        if "diamond" in n:
            return "EQ", MAT["knife_diamond"], 1
        if "gold" in n:
            return "EQ", MAT["knife_gold"], 1
        return "EQ", MAT["knife_iron"], 1
    if "farmer_" in n or "straw_hat" in n:
        return "EQ", 40.00, 1

    if any(
        x in n
        for x in (
            "blaze_",
            "golden_salad",
            "buddha",
            "nether_style",
            "end_style",
            "pan_seared_knight",
            "stargazy",
            "sweet_and_sour_ender",
            "chorus_fried",
            "fondant_spider",
        )
    ):
        base = 20.00 if ("blaze_" in n or "golden_salad" in n or "buddha" in n) else 12.00
        return "L3", r2(base * L3), 64
    if "dark_cuisine" in n or "suspicious" in n:
        return "L1", r2(8.00 * L1), 64  # 24

    if (
        "rice_bowl" in n
        or n.endswith("_noodle")
        or n.endswith("_noodles")
        or n
        in (
            "egg_fried_rice",
            "hot_dry_noodles",
            "laba_congee",
            "donkey_burger",
        )
    ):
        return "L2", r2(MAT["bowl_mat"] * L2), 64
    if n.endswith("_plate") or n.endswith("_platter"):
        return "L2", r2(MAT["simple_mat"] * L2), 16
    if n.endswith("_tea") or n in (
        "oolong",
        "biluochun",
        "tieguanyin",
        "sakura_fubuki",
        "flower_tea",
        "barley_tea",
    ):
        return "L1", r2(MAT["tea_mat"] * L1), 16
    if "soup" in n or "stew" in n or "borscht" in n or "congee" in n:
        return "L1", r2(MAT["soup_mat"] * L1), 64

    if n.startswith("cooked_") or n in (
        "fried_egg",
        "cooked_rice",
        "mantou",
        "baozi",
        "dumpling",
        "samsa",
        "meat_pie",
        "qingtuan",
        "zongzi",
        "bamboo_tube_rice",
        "sticky_candy",
        "sticky_rice_cake",
        "shengjian_mantou",
    ):
        return "L1", r2(MAT["raw_meat"] * L1), 64

    return "L1", r2(MAT["simple_mat"] * L1), 64


def tavern_price(name: str) -> tuple[str, float, int]:
    n = name
    if n in ("manual",):
        return "L0", 1.00, 1
    if any(
        x in n
        for x in (
            "grape",
            "grapevine",
            "trellis",
            "crop",
            "juice",
            "bucket",
            "vinegar",
            "empty_",
            "water_bottle",
            "honey_bottle",
            "pressing",
            "wild_grape",
        )
    ):
        if "juice" in n:
            return "L1", r2(6.00 * L1), 16  # 18
        if "bucket" in n:
            return "L1", r2(8.00 * L1), 16  # 24
        return "L0", 3.00 if ("grape" in n or "vine" in n) else 5.00, 64

    if any(
        x in n
        for x in (
            "sofa",
            "stool",
            "cabinet",
            "counter",
            "lamp",
            "rack",
            "table",
            "holder",
            "chalkboard",
            "sandwich",
            "stepladder",
            "string_lights",
            "incense",
            "painting",
            "tap",
            "shaker",
            "glassware",
        )
    ):
        return "EQ", 35.00, 16
    if n in ("barrel", "bar_cabinet", "glass_bar_cabinet", "cellar_cabinet"):
        return "EQ", 40.00, 16
    if n == "melon":
        return "L0", 40.00, 16
    if n == "emerald":
        return "L2", 150.00, 16

    spirits_l3 = {
        "molotov",
        "nether_special",
        "sculk_special",
        "dragon_breath_bottle",
        "miners_star",
    }
    spirits_l2_hi = {
        "honey_wine",
        "madame_shexiang",
        "sunset_glow",
        "rum",
        "whiskey",
        "vodka",
    }
    # finished drinks: clean C — mat basket × labor
    if (
        n in spirits_l3
        or n in spirits_l2_hi
        or "wine" in n
        or "cocktail" in n
        or n
        in {
            "wine",
            "rum",
            "whiskey",
            "vodka",
            "brandy",
            "champagne",
            "sherry",
            "glowflower_brew",
            "luminous_bride",
            "red_queen",
            "mother_snow",
            "polaris_sweet_white",
            "carignan",
            "riesling_dry_white",
            "sauvignon_blanc_dry_white",
            "bloody_mary",
            "mojito",
            "godfather",
            "screwdriver",
            "white_lady",
            "mystery_cocktail",
            "signature_cocktail",
            "grasshopper",
            "depth_charge",
            "brass_heart",
            "xp_bottle",
            "potion_bottle",
            "allium_garden",
            "plum_wine",
            "sakura_wine",
            "ice_wine",
            "sweet_berry_wine",
        }
    ):
        if n in spirits_l3:
            return "L3", r2(60.00 * L3), 16  # 300
        if n in spirits_l2_hi:
            return "L2", r2(50.00 * L2), 16  # 200
        return "L2", r2(40.00 * L2), 16  # 160

    return "EQ", 40.00, 16


def main():
    data = json.loads(CFG.read_text(encoding="utf-8"))
    rev = {str(v): k for k, v in data["nameSpaceMap"].items()}
    changed = []
    for r in data["systemShopItems"]:
        pref, name = r[0]["NIN"].split(":", 1)
        mod = rev.get(pref, pref)
        if mod == "kaleidoscope_cookery":
            tier, buy, count = cookery_price(name)
        elif mod == "kaleidoscope_tavern":
            tier, buy, count = tavern_price(name)
        else:
            continue
        buy = r2(buy)
        old_buy, old_sell = r[1], r[2]
        r[1] = buy
        r[2] = sell_of(buy)
        if r[0].get("count") is None:
            r[0]["count"] = count
        if old_buy != buy or old_sell != r[2]:
            changed.append((f"{mod}:{name}", tier, old_buy, buy, r[2]))

    # notice refresh counts
    from collections import Counter

    counts = Counter()
    for r in data["systemShopItems"]:
        pref = r[0]["NIN"].split(":", 1)[0]
        counts[rev.get(pref, pref)] += 1
    mc = counts.get("minecraft", 0)
    cook = counts.get("kaleidoscope_cookery", 0)
    tav = counts.get("kaleidoscope_tavern", 0)
    doll = counts.get("kaleidoscope_doll", 0)
    ice = counts.get("bricefire", 0)
    total = len(data["systemShopItems"])
    data["ecoSystemData"]["noticeMsg"] = (
        f"仅金币｜原版{mc}｜森罗厨{cook}+酒{tav}+偶{doll}｜冰火{ice}｜合计{total}｜"
        f"死亡扣30%｜森罗人工C档×3/4/5"
    )

    CFG.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    share = "ppcpdata%" + base64.b64encode(
        zlib.compress(
            json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode(), 9
        )
    ).decode()
    (BASE / "分享码.txt").write_text(share, encoding="utf-8")
    (BASE / "05_原始备份" / "最终分享串_副本.txt").write_text(share, encoding="utf-8")

    # update anchors file
    anchors_path = BASE / "02_定价锚点与说明" / "price_anchors.json"
    try:
        anchors = json.loads(anchors_path.read_text(encoding="utf-8"))
    except Exception:
        anchors = {}
    anchors["labor"] = {"L0": 1.0, "L1": 3.0, "L2": 4.0, "L3": 5.0}
    anchors["labor_note"] = "方案C：原料≈10 → 成品30/40/50；空杯/厨具/家具不加人工"
    anchors_path.write_text(
        json.dumps(anchors, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    report = BASE / "03_对比报告" / "森罗人工C档调价.csv"
    import csv

    with open(report, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "tier", "old_buy", "new_buy", "new_sell"])
        for row in changed:
            w.writerow(row)

    print(f"changed {len(changed)} / share {len(share)}")
    # samples
    samples = [
        "empty_cup",
        "barley_tea",
        "flower_tea",
        "egg_fried_rice",
        "donkey_burger",
        "sweet_and_sour_pork_rice_bowl",
        "pan_seared_knight_steak",
        "sakura_wine",
        "glowflower_brew",
        "rum",
        "molotov",
        "grape_juice",
        "empty_bottle",
        "black_sofa",
    ]
    shown = {s: None for s in samples}
    for a, tier, ob, nb, nsell in changed:
        short = a.split(":", 1)[1]
        if short in shown:
            shown[short] = (tier, ob, nb, nsell)
    # also print unchanged samples of interest
    for r in data["systemShopItems"]:
        pref, name = r[0]["NIN"].split(":", 1)
        mod = rev.get(pref, pref)
        if name in samples and shown.get(name) is None:
            shown[name] = ("(unchanged?)", r[1], r[1], r[2])
    for s in samples:
        print(f"  {s}: {shown[s]}")


if __name__ == "__main__":
    main()
