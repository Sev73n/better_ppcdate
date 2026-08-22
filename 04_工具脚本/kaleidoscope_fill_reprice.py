# -*- coding: utf-8 -*-
"""补全森罗厨房/酒馆 ID（官方源），并按人工 1.8~2.3 倍重定价。"""
import json
import base64
import zlib
import csv
import copy
from pathlib import Path

BASE = Path(r"C:/Users/AI10/Desktop/ppcdata")
CFG = BASE / "01_配置明文" / "最终配置_rebuilt.json"
SELL = 0.625

# 权威来源：
# 厨房: GitHub KaleidoscopeMods/KaleidoscopeCookery tags/items/cookery_mod_items.json
# 酒馆: GitHub KaleidoscopeMods/KaleidoscopeTavern assets/.../lang/en_us.json


def r2(x):
    return round(float(x) + 1e-12, 2)


def sell_of(buy, zero=False):
    if zero:
        return 0.0
    s = r2(buy * SELL)
    if s >= buy and buy > 0:
        s = r2(buy - 0.01) if buy > 0.01 else 0.0
    return s


def make_row(ns, name, count, buy, tag):
    buy = r2(buy)
    return [
        {
            "NIN": f"{ns}:{name}",
            "count": count,
            "durability": 0,
            "modEnchantData": [],
        },
        buy,
        sell_of(buy),
        "",
        0,
        0,
        tag,
        False,
        "金币",
        "金币",
        0,
        1.0,
        min(count, 64) if count >= 16 else 1,
        0.0 if count >= 16 else 0.2,
        0.9,
        0.1,
    ]


# ---- labor multipliers (user: mats 10 -> dish 18~23) ----
L0, L1, L2, L3 = 1.0, 1.80, 2.00, 2.30

# material proxy costs (per shop listing stack where applicable)
MAT = {
    "seed": 1.00,
    "crop": 4.00,
    "oil": 5.00,
    "raw_meat": 6.00,
    "flour": 5.00,
    "dough": 8.00,
    "rice": 4.00,
    "simple_mat": 10.00,  # 用户例：原料约10 → L1=18
    "bowl_mat": 10.00,  # → L2=20
    "special_mat": 10.00,  # 基础高难 → L3=23；下面再对极特殊抬价
    "tea_mat": 10.00,
    "soup_mat": 10.00,
    "equip": 30.00,
    "knife_iron": 80.00,
    "knife_gold": 120.00,
    "knife_diamond": 400.00,
    "knife_netherite": 2000.00,
}


def cookery_price(name: str) -> tuple[str, float, int]:
    """Return (tier, buy, count)."""
    n = name
    # L0
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
    if n in ("raw_dough", "raw_noodles", "stuffed_dough_food", "raw_zongzi", "raw_bamboo_tube_rice"):
        return "L0", MAT["dough"], 64
    if n.startswith("raw_"):
        return "L0", MAT["raw_meat"], 64

    # equipment / decor
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
            "empty_cup",
            "transmutation",
            "cook_stool",
            "chair_",
            "table_",
        )
    ):
        return "L1", MAT["equip"], 1 if "stove" in n or "millstone" in n or "stockpot" in n else 16
    if "kitchen_knife" in n or n == "kitchen_shovel" or n == "sickle":
        if "netherite" in n:
            return "L1", MAT["knife_netherite"], 1
        if "diamond" in n:
            return "L1", MAT["knife_diamond"], 1
        if "gold" in n:
            return "L1", MAT["knife_gold"], 1
        return "L1", MAT["knife_iron"], 1
    if "farmer_" in n or "straw_hat" in n:
        return "L1", 40.00, 1

    # L3 specialty
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
        # 高难：原料篮子按 20 估 → ×2.3 ≈ 46；烈焰等再略抬
        base = 20.00 if "blaze_" in n or "golden_salad" in n or "buddha" in n else 12.00
        return "L3", r2(base * L3), 64
    if "dark_cuisine" in n or "suspicious" in n:
        return "L1", 8.00, 64

    # L2 multi-step
    if "rice_bowl" in n or n.endswith("_noodle") or n.endswith("_noodles") or n in (
        "egg_fried_rice",
        "hot_dry_noodles",
        "laba_congee",
        "donkey_burger",
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

    # cooked intermediates
    if n.startswith("cooked_") or n in ("fried_egg", "cooked_rice", "mantou", "baozi", "dumpling", "samsa", "meat_pie", "qingtuan", "zongzi", "bamboo_tube_rice", "sticky_candy", "sticky_rice_cake", "shengjian_mantou"):
        return "L1", r2(MAT["raw_meat"] * L1), 64

    # default stir-fry / meal L1
    return "L1", r2(MAT["simple_mat"] * L1), 64


def tavern_price(name: str) -> tuple[str, float, int]:
    n = name
    if n in ("manual",):
        return "L0", 1.00, 1
    # crops / juice L0-L1
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
            return "L1", r2(6.00 * L1), 16
        if "bucket" in n:
            return "L1", r2(8.00 * L1), 16
        return "L0", 3.00 if "grape" in n or "vine" in n else 5.00, 64
    # furniture
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
        return "L1", 35.00, 16
    if n in ("barrel", "bar_cabinet", "glass_bar_cabinet", "cellar_cabinet"):
        return "L1", 40.00, 16
    # cocktails / spirits L2-L3
    spirits = {
        "wine",
        "rum",
        "whiskey",
        "vodka",
        "brandy",
        "champagne",
        "sherry",
        "ice_wine",
        "plum_wine",
        "sakura_wine",
        "honey_wine",
        "sweet_berry_wine",
        "glowflower_brew",
        "luminous_bride",
        "madame_shexiang",
        "sunset_glow",
        "miners_star",
        "red_queen",
        "mother_snow",
        "polaris_sweet_white",
        "carignan",
        "riesling_dry_white",
        "sauvignon_blanc_dry_white",
        "molotov",
        "bloody_mary",
        "mojito",
        "godfather",
        "screwdriver",
        "white_lady",
        "mystery_cocktail",
        "signature_cocktail",
        "grasshopper",
        "depth_charge",
        "nether_special",
        "sculk_special",
        "brass_heart",
        "dragon_breath_bottle",
        "xp_bottle",
        "potion_bottle",
        "allium_garden",
    }
    if n in spirits or "wine" in n or "cocktail" in n:
        base = 100.00
        if n in ("molotov", "nether_special", "sculk_special", "dragon_breath_bottle", "miners_star"):
            return "L3", r2(120.00 * L3 / 2), 16  # ~138
        if n in ("honey_wine", "madame_shexiang", "sunset_glow", "rum", "whiskey", "vodka"):
            return "L2", r2(110.00 * L2 / 1.5), 16
        return "L2", r2(base * L2 / 1.5), 16
    if n in ("emerald",):  # mod drink-like; keep separate
        return "L2", 150.00, 16
    return "L1", 40.00, 16


# Official cookery list (short ids)
COOKERY_ADD = [
    "apple_platter",
    "bamboo_tube_rice",
    "baozi_plate",
    "berry_platter",
    "chair_acacia",
    "chair_bamboo",
    "chair_birch",
    "chair_cherry",
    "chair_crimson",
    "chair_dark_oak",
    "chair_jungle",
    "chair_mangrove",
    "chair_oak",
    "chair_spruce",
    "chair_warped",
    "chili_ristra",
    "chorus_fruit_platter",
    "cook_stool_acacia",
    "cook_stool_bamboo",
    "cook_stool_birch",
    "cook_stool_cherry",
    "cook_stool_crimson",
    "cook_stool_dark_oak",
    "cook_stool_jungle",
    "cook_stool_mangrove",
    "cook_stool_oak",
    "cook_stool_spruce",
    "cook_stool_warped",
    "diamond_kitchen_knife",
    "donkey_burger",
    "egg_fried_rice",
    "empty_cup",
    "farmer_boots",
    "farmer_chest_plate",
    "farmer_leggings",
    "flour",
    "gold_kitchen_knife",
    "hot_dry_noodles",
    "iron_kitchen_knife",
    "kitchen_shovel",
    "laba_congee",
    "netherite_kitchen_knife",
    "oil_block",
    "oil_pot",
    "qingtuan",
    "qingtuan_plate",
    "raw_bamboo_tube_rice",
    "raw_dough",
    "raw_noodles",
    "raw_zongzi",
    "recipe_item",
    "rice",
    "scarecrow",
    "shengjian_mantou_plate",
    "sickle",
    "steamer",
    "sticky_candy",
    "sticky_candy_plate",
    "sticky_rice_cake",
    "sticky_rice_cake_plate",
    "straw_block",
    "straw_hat",
    "straw_hat_flower",
    "strung_mushrooms",
    "stuffed_dough_food",
    "table_acacia",
    "table_bamboo",
    "table_birch",
    "table_cherry",
    "table_crimson",
    "table_dark_oak",
    "table_jungle",
    "table_mangrove",
    "table_oak",
    "table_spruce",
    "table_warped",
    "tomato_platter",
    "transmutation_lunch_bag",
    "watermelon_platter",
    "wild_rice",
    "zongzi",
    "zongzi_plate",
]

# From tavern en_us.json — skip nothing critical; furniture colors included for coverage
TAVERN_SKIP = set()  # could skip nothing
TAVERN_ALL = Path(
    r"C:/Users/AI10/.cursor/projects/C-Users-AI10-AppData-Local-Temp-520ff681-de2a-4719-bc33-8e3778664937/agent-tools/d430177f-853a-4f61-a1ff-f62523c94b05.txt"
)


def load_tavern_ids():
    import re

    text = TAVERN_ALL.read_text(encoding="utf-8")
    lang = json.loads(text) if text.strip().startswith("{") else json.loads(re.search(r"\{[\s\S]*\}", text).group(0))
    ids = []
    for k in lang:
        m = re.match(r"(?:item|block)\.kaleidoscope_tavern\.(.+)", k)
        if m:
            ids.append(m.group(1))
    return sorted(set(ids) - TAVERN_SKIP)


def normalize_cookery_name(n: str) -> str:
    if n.startswith("kaleidoscope_cookery_"):
        return n[len("kaleidoscope_cookery_") :]
    return n


def main():
    data = json.loads(CFG.read_text(encoding="utf-8"))
    have3 = set()
    have2 = set()
    for r in data["systemShopItems"]:
        ns, n = r[0]["NIN"].split(":", 1)
        if ns == "3":
            have3.add(normalize_cookery_name(n))
        elif ns == "2":
            have2.add(n)

    added = []
    # reprice existing cookery + tavern
    for r in data["systemShopItems"]:
        ns, n = r[0]["NIN"].split(":", 1)
        if ns == "3":
            nn = normalize_cookery_name(n)
            tier, buy, cnt = cookery_price(nn)
            r[1] = r2(buy)
            r[2] = sell_of(buy)
            if r[0].get("count") is None:
                r[0]["count"] = cnt
        elif ns == "2":
            tier, buy, cnt = tavern_price(n)
            r[1] = r2(buy)
            r[2] = sell_of(buy)

    # add missing cookery
    for name in COOKERY_ADD:
        if name in have3:
            continue
        tier, buy, cnt = cookery_price(name)
        data["systemShopItems"].append(make_row("3", name, cnt, buy, "森罗物语（厨房）"))
        added.append(("3:" + name, buy, cnt, tier, "cookery"))
        have3.add(name)

    # add missing tavern
    for name in load_tavern_ids():
        if name in have2:
            continue
        tier, buy, cnt = tavern_price(name)
        data["systemShopItems"].append(make_row("2", name, cnt, buy, "森罗物语（酒馆）"))
        added.append(("2:" + name, buy, cnt, tier, "tavern"))
        have2.add(name)

    data["ecoSystemData"]["noticeMsg"] = (
        "死亡会扣除所有金币（基金不受影响）｜森罗人工1.8~2.3｜原版+铜器时代｜基岩ID已校对"
    )

    payload = json.dumps(data, ensure_ascii=False, indent=2)
    CFG.write_text(payload, encoding="utf-8")
    share = "ppcpdata%" + base64.b64encode(
        zlib.compress(json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8"), 9)
    ).decode("ascii")
    (BASE / "分享码.txt").write_text(share, encoding="utf-8")
    (BASE / "05_原始备份" / "最终分享串_副本.txt").write_text(share, encoding="utf-8")

    with open(BASE / "03_对比报告" / "森罗补全与调价.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["NIN", "buy", "count", "tier", "source"])
        for row in added:
            w.writerow(row)

    # sample check
    samples = [
        "3:tomato",
        "3:sweet_and_sour_pork",
        "3:sweet_and_sour_pork_rice_bowl",
        "3:blaze_lamb_chop",
        "3:flour",
        "3:iron_kitchen_knife",
        "2:wine",
        "2:bar_cabinet",
        "2:mojito",
    ]
    print(f"added {len(added)}, total items {len(data['systemShopItems'])}, share {len(share)}")
    idx = {r[0]["NIN"]: r for r in data["systemShopItems"]}
    # also resolve prefixed
    for s in samples:
        ns, n = s.split(":")
        hit = idx.get(s)
        if not hit and ns == "3":
            hit = idx.get(f"3:kaleidoscope_cookery_{n}")
        print(s, (hit[1], hit[2]) if hit else "MISSING")

    # explain mats 10 example
    print("example mats10 -> L1", r2(10 * L1), "L2", r2(10 * L2), "L3", r2(10 * L3))

    note = BASE / "02_定价锚点与说明" / "简介.txt"
    t = note.read_text(encoding="utf-8")
    if "人工1.8" not in t:
        t += (
            "\n【森罗调价】料理人工：原料×1.8（单步）/×2.0（盖饭多步）/×2.3（高难特产）；"
            "例：原料约10 → 成品约18/20/23。物品ID补全来源：官方 GitHub cookery_mod_items 标签 + 酒馆 lang。\n"
        )
        note.write_text(t, encoding="utf-8")


if __name__ == "__main__":
    main()
