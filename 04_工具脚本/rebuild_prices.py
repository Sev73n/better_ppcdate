# -*- coding: utf-8 -*-
"""Rebuild PPCP systemShopItems prices per agreed plan."""
import json
import copy
import csv
import base64
import zlib
from pathlib import Path

ROOT = Path(r"C:/Users/AI10/AppData/Local/Temp/ppcp_decode")
DESK = Path(r"C:/Users/AI10/Desktop")
SELL_RATE = 0.625


def r2(x):
    return round(float(x) + 1e-12, 2)


def sell_of(buy, zero=False):
    if zero:
        return 0.0
    s = r2(buy * SELL_RATE)
    if s >= buy and buy > 0:
        s = r2(buy - 0.01) if buy > 0.01 else 0.0
    return s


def make_row(nin, count, buy, tag, sell_zero=False):
    buy = r2(buy)
    sell = sell_of(buy, zero=sell_zero)
    f12, f13, f14, f15 = 1, 0.2, 0.9, 0.1
    if count and count >= 16:
        f12 = min(count, 64)
        f13 = 0.0
    return [
        {
            "NIN": nin,
            "count": count if count is not None else 1,
            "durability": 0,
            "modEnchantData": [],
        },
        buy,
        sell,
        "",
        0,
        0,
        tag,
        False,
        "金币",
        "金币",
        0,
        1.0,
        f12,
        f13,
        f14,
        f15,
    ]


# buy, count, tag
VANILLA_BUY = {
    "cobblestone": (0.10, 64, "材料"),
    "dirt": (0.10, 64, "材料"),
    "sand": (1.00, 64, "材料"),
    "gravel": (1.00, 64, "材料"),
    "clay_ball": (2.00, 64, "材料"),
    "flint": (2.00, 64, "材料"),
    "snow": (0.50, 64, "材料"),
    "ice": (2.00, 64, "材料"),
    "packed_ice": (6.00, 64, "材料"),
    "blue_ice": (18.00, 64, "材料"),
    "obsidian": (40.00, 64, "材料"),
    "magma": (8.00, 64, "材料"),
    "glass": (2.00, 64, "材料"),
    "oak_log": (2.00, 64, "材料"),
    "birch_log": (2.00, 64, "材料"),
    "spruce_log": (2.00, 64, "材料"),
    "jungle_log": (2.00, 64, "材料"),
    "acacia_log": (2.00, 64, "材料"),
    "dark_oak_log": (2.00, 64, "材料"),
    "mangrove_log": (2.00, 64, "材料"),
    "cherry_log": (2.50, 64, "材料"),
    "bamboo": (1.00, 64, "材料"),
    "coal": (8.00, 64, "材料"),
    "charcoal": (6.00, 64, "材料"),
    "copper_ingot": (12.00, 64, "材料"),
    "iron_ingot": (36.00, 64, "材料"),
    "gold_ingot": (72.00, 64, "材料"),
    "redstone": (16.00, 64, "材料"),
    "lapis_lazuli": (28.00, 64, "材料"),
    "emerald": (120.00, 64, "材料"),
    "diamond": (200.00, 64, "材料"),
    "quartz": (10.00, 64, "材料"),
    "amethyst_shard": (8.00, 64, "材料"),
    "ancient_debris": (900.00, 1, "材料"),
    "netherite_scrap": (1080.00, 1, "材料"),
    "netherite_ingot": (4500.00, 1, "材料"),
    "bone": (2.00, 64, "材料"),
    "string": (3.00, 64, "材料"),
    "spider_eye": (4.00, 64, "材料"),
    "gunpowder": (6.00, 64, "材料"),
    "slime_ball": (8.00, 64, "材料"),
    "leather": (6.00, 64, "材料"),
    "feather": (2.00, 64, "材料"),
    "ink_sac": (3.00, 64, "材料"),
    "glow_ink_sac": (8.00, 64, "材料"),
    "blaze_rod": (80.00, 16, "材料"),
    "ghast_tear": (100.00, 16, "材料"),
    "magma_cream": (20.00, 64, "材料"),
    "ender_pearl": (48.00, 16, "材料"),
    "shulker_shell": (600.00, 1, "材料"),
    "phantom_membrane": (40.00, 16, "材料"),
    "echo_shard": (80.00, 16, "材料"),
    "nether_star": (8000.00, 1, "材料"),
    "heavy_core": (13140.00, 1, "材料"),
    "dragon_breath": (80.00, 16, "材料"),
    "heart_of_the_sea": (1200.00, 1, "材料"),
    "nautilus_shell": (40.00, 16, "材料"),
    "prismarine_shard": (6.00, 64, "材料"),
    "prismarine_crystals": (10.00, 64, "材料"),
    "glowstone_dust": (6.00, 64, "材料"),
    "rabbit_foot": (20.00, 16, "材料"),
    "rabbit_hide": (3.00, 64, "材料"),
    "honeycomb": (8.00, 64, "材料"),
    "resin_clump": (4.00, 64, "材料"),
    "wheat": (3.00, 64, "食物"),
    "wheat_seeds": (1.00, 64, "食物"),
    "carrot": (3.00, 64, "食物"),
    "potato": (3.00, 64, "食物"),
    "beetroot": (3.00, 64, "食物"),
    "beetroot_seeds": (1.00, 64, "食物"),
    "melon_seeds": (1.00, 64, "食物"),
    "pumpkin_seeds": (1.00, 64, "食物"),
    "melon_slice": (2.00, 64, "食物"),
    "pumpkin": (4.00, 64, "食物"),
    "sugar_cane": (2.00, 64, "食物"),
    "kelp": (0.50, 64, "食物"),
    "apple": (4.00, 64, "食物"),
    "sweet_berries": (2.00, 64, "食物"),
    "glow_berries": (3.00, 64, "食物"),
    "chorus_fruit": (8.00, 64, "食物"),
    "beef": (4.00, 64, "食物"),
    "porkchop": (4.00, 64, "食物"),
    "mutton": (4.00, 64, "食物"),
    "chicken": (3.50, 64, "食物"),
    "rabbit": (4.00, 64, "食物"),
    "cod": (3.00, 64, "食物"),
    "salmon": (3.50, 64, "食物"),
    "tropical_fish": (3.00, 64, "食物"),
    "pufferfish": (6.00, 64, "食物"),
    "rotten_flesh": (0.50, 64, "食物"),
    "egg": (2.00, 16, "食物"),
    "blue_egg": (3.00, 16, "食物"),
    "brown_egg": (3.00, 16, "食物"),
    "bread": (6.00, 64, "食物"),
    "cooked_beef": (6.00, 64, "食物"),
    "cooked_porkchop": (6.00, 64, "食物"),
    "cooked_mutton": (6.00, 64, "食物"),
    "cooked_chicken": (5.00, 64, "食物"),
    "water_bucket": (8.00, 1, "材料"),
    "lava_bucket": (20.00, 1, "材料"),
    "milk_bucket": (10.00, 1, "食物"),
    "axolotl_bucket": (300.00, 1, "其他"),
    "elytra": (13140.00, 1, "其他"),
    "totem_of_undying": (1800.00, 1, "其他"),
}

for d in [
    "white",
    "black",
    "gray",
    "light_gray",
    "brown",
    "red",
    "orange",
    "yellow",
    "lime",
    "green",
    "cyan",
    "light_blue",
    "blue",
    "purple",
    "magenta",
    "pink",
]:
    VANILLA_BUY[f"{d}_wool"] = (4.00, 64, "材料")
    VANILLA_BUY[f"{d}_dye"] = (2.00, 64, "材料")
    VANILLA_BUY[f"{d}_concrete_powder"] = (4.00, 64, "材料")

for f in [
    "poppy",
    "dandelion",
    "blue_orchid",
    "allium",
    "azure_bluet",
    "red_tulip",
    "orange_tulip",
    "white_tulip",
    "pink_tulip",
    "oxeye_daisy",
    "cornflower",
    "lily_of_the_valley",
    "lilac",
    "rose_bush",
    "peony",
    "sunflower",
    "torchflower",
    "pitcher_plant",
    "pink_petals",
    "wildflowers",
    "closed_eyeblossom",
    "open_eyeblossom",
    "cactus_flower",
]:
    VANILLA_BUY[f] = (2.00, 64, "材料")

SPAWN_EGGS = {}
for k in [
    "pig",
    "cow",
    "sheep",
    "chicken",
    "horse",
    "donkey",
    "mule",
    "wolf",
    "cat",
    "ocelot",
    "rabbit",
    "mooshroom",
    "parrot",
    "llama",
    "fox",
    "bee",
    "goat",
    "camel",
    "sniffer",
    "armadillo",
]:
    SPAWN_EGGS[k] = 200
for k in [
    "villager",
    "wandering_trader",
    "iron_golem",
    "snow_golem",
    "turtle",
    "dolphin",
    "panda",
    "polar_bear",
    "allay",
    "axolotl",
    "frog",
    "tadpole",
]:
    SPAWN_EGGS[k] = 600
for k in [
    "zombie",
    "husk",
    "drowned",
    "skeleton",
    "stray",
    "creeper",
    "spider",
    "cave_spider",
    "slime",
    "witch",
    "phantom",
    "silverfish",
    "endermite",
    "bogged",
    "breeze",
]:
    SPAWN_EGGS[k] = 1500
for k in [
    "blaze",
    "ghast",
    "magma_cube",
    "hoglin",
    "zoglin",
    "piglin",
    "piglin_brute",
    "zombified_piglin",
    "strider",
    "guardian",
    "elder_guardian",
    "shulker",
    "vex",
    "pillager",
    "vindicator",
]:
    SPAWN_EGGS[k] = 4000
for k in ["enderman", "evoker", "ravager", "warden", "wither_skeleton"]:
    SPAWN_EGGS[k] = 8000
for k in ["wither", "ender_dragon"]:
    SPAWN_EGGS[k] = 13140

DOLL_BUY = {}
for mob, egg_buy in SPAWN_EGGS.items():
    DOLL_BUY[f"kaleidoscope_doll_{mob}"] = r2(egg_buy * 0.5)
for special in [
    "kaleidoscope_doll_abert_cat",
    "kaleidoscope_doll_cr_019",
    "kaleidoscope_doll_tartaric_acid",
    "kaleidoscope_doll_ysbb",
]:
    DOLL_BUY[special] = 200.00
DOLL_BUY["kaleidoscope_doll_illusioner"] = 750.00


def cookery_labor_and_buy(name, old_buy):
    n = name
    l0 = {
        "manual": 1.00,
        "recipe_book": 1.00,
        "tomato_seed": 1.00,
        "lettuce_seed": 1.00,
        "chili_seed": 1.00,
        "wild_rice_seed": 1.00,
        "tomato": 4.00,
        "lettuce": 4.00,
        "red_chili": 4.00,
        "rice_panicle": 4.00,
        "oil": 5.00,
        "sashimi": 6.00,
        "caterpillar": 6.00,
        "raw_meatball": 6.00,
        "raw_cut_small_meats": 6.00,
        "raw_pork_belly": 6.00,
        "raw_cow_offal": 6.00,
        "raw_lamb_chops": 6.00,
    }
    if n in l0:
        return "L0", l0[n]

    equip_keys = (
        "teapot",
        "kitchenware",
        "basket",
        "trash",
        "enamel",
        "chopping",
        "steamer",
        "millstone",
        "shawarma",
        "stockpot",
        "stove",
        "stockpot_lid",
    )
    if any(x in n for x in equip_keys) or n.endswith("_pot") or n == "kaleidoscope_cookery_pot":
        return "L1", r2(max(old_buy, 20.00))

    if "dark_cuisine" in n or "suspicious" in n:
        return "L1", 6.00

    if any(x in n for x in ("blaze_", "golden_salad", "buddha", "nether_style", "end_style")):
        return "L3", r2(max(old_buy * 1.15, 60.00))

    if "rice_bowl" in n or n.endswith("_noodle") or n.endswith("_noodles"):
        return "L2", r2(max(old_buy, 45.00))

    teas = {
        "oolong",
        "biluochun",
        "tieguanyin",
        "sakura_fubuki",
        "flower_tea",
        "barley_tea",
    }
    if n.endswith("_tea") or n in teas:
        return "L1", r2(max(old_buy, 30.00))

    if n.startswith("cooked_") or n in (
        "fried_egg",
        "cooked_rice",
        "mantou",
        "dumpling",
        "meat_pie",
        "samsa",
        "baozi",
        "fruit_platter",
    ):
        return "L1", r2(max(old_buy, 8.00 if n.startswith("cooked_") else old_buy))

    if old_buy >= 15:
        return "L1", r2(max(old_buy, 20.00))
    return "L1", r2(old_buy)


def tavern_buy(name, old_buy):
    if name == "manual":
        return "L0", 1.00
    if name in ("grape", "green_grape", "gold_grape", "ice_grape", "grapevine"):
        return "L0", 3.00
    if name == "melon":
        return "L0", 4.00
    if name == "vinegar":
        return "L1", 8.00
    if name == "barrel":
        return "L1", 30.00
    if old_buy >= 100:
        return "L2", r2(max(old_buy, 100.00))
    return "L2", r2(old_buy)


def main():
    data = json.loads((ROOT / "ppcp_config_decoded.json").read_text(encoding="utf-8"))
    old_items = data["systemShopItems"]
    new_items = []
    report = []
    seen = set()

    def update_existing(row, buy, tag=None, sell_zero=False, count=None, action="update"):
        r = copy.deepcopy(row)
        old_b, old_s = r[1], r[2]
        r[1] = r2(buy)
        r[2] = sell_of(r[1], zero=sell_zero)
        if tag is not None:
            r[6] = tag
        if count is not None:
            r[0]["count"] = count
        if "count" not in r[0] or r[0]["count"] is None:
            r[0]["count"] = 1
        report.append((r[0]["NIN"], old_b, r[1], old_s, r[2], action))
        return r

    for row in old_items:
        nin = row[0]["NIN"]
        seen.add(nin)
        ns, name = nin.split(":", 1)

        if ns == "0":
            if name in VANILLA_BUY:
                buy, cnt, tag = VANILLA_BUY[name]
                new_items.append(update_existing(row, buy, tag=tag, count=cnt))
            else:
                new_items.append(update_existing(row, row[1], tag=row[6]))
        elif ns == "3":
            tier, buy = cookery_labor_and_buy(name, row[1])
            new_items.append(update_existing(row, buy, action=f"cookery-{tier}"))
        elif ns == "2":
            tier, buy = tavern_buy(name, row[1])
            new_items.append(update_existing(row, buy, action=f"tavern-{tier}"))
        elif ns == "1":
            buy = DOLL_BUY.get(name, r2(row[1]))
            new_items.append(update_existing(row, buy, count=1, action="doll"))
        else:
            new_items.append(update_existing(row, row[1]))

    for name, (buy, cnt, tag) in VANILLA_BUY.items():
        nin = f"0:{name}"
        if nin not in seen:
            new_items.append(make_row(nin, cnt, buy, tag))
            report.append((nin, None, r2(buy), None, sell_of(buy), "add-vanilla"))
            seen.add(nin)

    for mob, buy in sorted(SPAWN_EGGS.items(), key=lambda x: (x[1], x[0])):
        nin = f"0:{mob}_spawn_egg"
        if nin not in seen:
            new_items.append(make_row(nin, 1, buy, "其他", sell_zero=True))
            report.append((nin, None, r2(buy), None, 0.0, f"add-egg-{buy}"))
            seen.add(nin)

    data["systemShopItems"] = new_items
    data["ecoSystemData"]["noticeMsg"] = (
        "死亡会扣除所有金币（基金不受影响）｜价格体系重建：回收率0.625｜含刷怪蛋"
    )

    out_json = DESK / "ppcp_config_rebuilt.json"
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    out_json.write_text(payload, encoding="utf-8")
    (ROOT / "ppcp_config_rebuilt.json").write_text(payload, encoding="utf-8")

    anchors = {
        "sell_rate": SELL_RATE,
        "decimal_places": 2,
        "diamond_stack_buy": 200.0,
        "elytra_buy": 13140.0,
        "farm_spawn_egg_buy": 200.0,
        "labor": {"L0": 1.0, "L1": 1.5, "L2": 1.8, "L3": 2.0},
        "spawn_egg_tiers": {
            "T1": 200,
            "T2": 600,
            "T3": 1500,
            "T4": 4000,
            "T5": 8000,
            "T6": 13140,
        },
    }
    (DESK / "price_anchors.json").write_text(
        json.dumps(anchors, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    with open(DESK / "ppcp_price_diff.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["NIN", "old_buy", "new_buy", "old_sell", "new_sell", "action"])
        for row in report:
            w.writerow(row)

    bad = []
    for r in new_items:
        b, s = r[1], r[2]
        nin = r[0]["NIN"]
        if round(b, 2) != b or round(s, 2) != s:
            bad.append((nin, "not-2dp", b, s))
        if "_spawn_egg" in nin:
            if s != 0:
                bad.append((nin, "egg-sell", b, s))
        elif not (b > s >= 0):
            bad.append((nin, "buy<=sell", b, s))

    compact = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    share = "ppcpdata%" + base64.b64encode(zlib.compress(compact.encode("utf-8"), 9)).decode(
        "ascii"
    )
    (DESK / "ppcp_share_rebuilt.txt").write_text(share, encoding="utf-8")
    (ROOT / "ppcp_share_rebuilt.txt").write_text(share, encoding="utf-8")

    print(f"items: {len(old_items)} -> {len(new_items)}")
    print(f"added: {sum(1 for x in report if str(x[5]).startswith('add'))}")
    print(f"validation issues: {len(bad)}")
    for x in bad[:30]:
        print(" ", x)
    print(f"share length: {len(share)}")

    def show(nin):
        hits = [r for r in new_items if r[0]["NIN"] == nin]
        if hits:
            print(f"{nin}: buy={hits[0][1]} sell={hits[0][2]} count={hits[0][0].get('count')}")

    show("0:diamond")
    show("0:elytra")
    show("0:pig_spawn_egg")
    show("0:ender_dragon_spawn_egg")
    show("0:netherite_ingot")
    show("0:ancient_debris")
    show("0:cobblestone")
    show("1:kaleidoscope_doll_ender_dragon")
    show("1:kaleidoscope_doll_pig")
    show("3:sweet_and_sour_pork_rice_bowl")
    show("2:honey_wine")


if __name__ == "__main__":
    main()
