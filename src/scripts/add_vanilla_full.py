# -*- coding: utf-8 -*-
"""Add comprehensive vanilla shop coverage to PPCP config."""
import json
import base64
import zlib
import csv
from pathlib import Path

BASE = Path(r"C:/Users/AI10/Desktop/ppcdata")
CFG = BASE / "01_配置明文" / "最终配置_rebuilt.json"
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


def make_row(name, count, buy, tag):
    buy = r2(buy)
    sell = sell_of(buy)
    f12 = min(count, 64) if count >= 16 else 1
    f13 = 0.0 if count >= 16 else 0.2
    return [
        {
            "NIN": f"0:{name}",
            "count": count,
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
        0.9,
        0.1,
    ]


A = {
    "plank": 0.60,
    "stick": 0.20,
    "coal": 8.00,
    "copper": 12.00,
    "iron": 36.00,
    "gold": 72.00,
    "redstone": 16.00,
    "lapis": 28.00,
    "emerald": 120.00,
    "diamond": 200.00,
    "netherite": 4500.00,
}


def add(catalog, name, buy, count=64, tag="材料"):
    catalog[name] = (r2(buy), count, tag)


catalog = {}

for n, p in [
    ("stone", 0.20),
    ("stone_bricks", 0.30),
    ("smooth_stone", 0.35),
    ("cobbled_deepslate", 0.25),
    ("deepslate", 0.30),
    ("andesite", 0.20),
    ("diorite", 0.20),
    ("granite", 0.20),
    ("calcite", 0.50),
    ("tuff", 0.30),
    ("dripstone_block", 0.40),
    ("moss_block", 2.00),
    ("mud", 0.30),
    ("packed_mud", 0.50),
    ("terracotta", 1.00),
    ("white_concrete", 5.00),
    ("glass_pane", 1.00),
    ("tinted_glass", 8.00),
    ("sandstone", 1.20),
    ("red_sand", 1.20),
    ("red_sandstone", 1.50),
    ("soul_sand", 2.00),
    ("soul_soil", 2.00),
    ("netherrack", 0.50),
    ("basalt", 1.00),
    ("blackstone", 1.00),
    ("end_stone", 3.00),
    ("purpur_block", 6.00),
    ("prismarine", 8.00),
    ("dark_prismarine", 10.00),
    ("sea_lantern", 20.00),
    ("glowstone", 12.00),
    ("shroomlight", 10.00),
    ("ochre_froglight", 15.00),
    ("pearlescent_froglight", 15.00),
    ("verdant_froglight", 15.00),
]:
    add(catalog, n, p, 64, "材料")

for c in [
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
    add(catalog, f"{c}_concrete", 5.00, 64, "材料")
    add(catalog, f"{c}_terracotta", 1.20, 64, "材料")
    add(catalog, f"{c}_stained_glass", 3.00, 64, "材料")

woods = [
    "oak",
    "birch",
    "spruce",
    "jungle",
    "acacia",
    "dark_oak",
    "mangrove",
    "cherry",
    "bamboo",
    "crimson",
    "warped",
]
for w in woods:
    plank = 0.80 if w in ("crimson", "warped", "cherry") else A["plank"]
    add(catalog, f"{w}_planks", plank, 64, "材料")
    add(catalog, f"{w}_stairs", r2(plank * 1.5), 64, "材料")
    add(catalog, f"{w}_slab", r2(plank * 0.6), 64, "材料")
    add(catalog, f"{w}_fence", r2(plank * 1.2), 64, "材料")
    add(catalog, f"{w}_door", r2(plank * 2.5), 16, "材料")
    add(catalog, f"{w}_trapdoor", r2(plank * 2.0), 16, "材料")
    add(catalog, f"{w}_sign", r2(plank * 2.0 + A["stick"]), 16, "材料")
    if w not in ("crimson", "warped", "bamboo"):
        add(catalog, f"{w}_boat", 8.00, 1, "其他")
        add(catalog, f"{w}_chest_boat", 15.00, 1, "其他")

add(catalog, "stick", A["stick"], 64, "材料")
add(catalog, "crafting_table", 5.00, 16, "其他")
add(catalog, "chest", 8.00, 16, "其他")
add(catalog, "barrel", 10.00, 16, "其他")
add(catalog, "ladder", 2.00, 64, "材料")
add(catalog, "bookshelf", 20.00, 16, "材料")
add(catalog, "item_frame", 6.00, 16, "其他")
add(catalog, "glow_item_frame", 12.00, 16, "其他")
add(catalog, "painting", 8.00, 16, "其他")
add(catalog, "flower_pot", 3.00, 16, "其他")

ores = {
    "coal_ore": 10.00,
    "deepslate_coal_ore": 12.00,
    "iron_ore": 30.00,
    "deepslate_iron_ore": 36.00,
    "raw_iron": 30.00,
    "gold_ore": 60.00,
    "deepslate_gold_ore": 70.00,
    "raw_gold": 60.00,
    "copper_ore": 10.00,
    "deepslate_copper_ore": 12.00,
    "raw_copper": 10.00,
    "diamond_ore": 220.00,
    "deepslate_diamond_ore": 240.00,
    "emerald_ore": 140.00,
    "deepslate_emerald_ore": 150.00,
    "lapis_ore": 32.00,
    "deepslate_lapis_ore": 36.00,
    "redstone_ore": 18.00,
    "deepslate_redstone_ore": 20.00,
    "nether_gold_ore": 40.00,
    "nether_quartz_ore": 12.00,
}
for n, p in ores.items():
    add(catalog, n, p, 64, "材料")

for n, mult, base in [
    ("iron_block", 9, A["iron"]),
    ("gold_block", 9, A["gold"]),
    ("diamond_block", 9, A["diamond"]),
    ("emerald_block", 9, A["emerald"]),
    ("copper_block", 9, A["copper"]),
    ("netherite_block", 9, A["netherite"]),
    ("coal_block", 9, A["coal"]),
    ("lapis_block", 9, A["lapis"]),
    ("redstone_block", 9, A["redstone"]),
    ("raw_iron_block", 9, 30.00),
    ("raw_gold_block", 9, 60.00),
    ("raw_copper_block", 9, 10.00),
    ("quartz_block", 4, 10.00),
    ("amethyst_block", 4, 8.00),
]:
    add(catalog, n, r2(mult * base * 1.1), 1 if base >= 30 else 16, "材料")

add(catalog, "iron_nugget", r2(A["iron"] / 9), 64, "材料")
add(catalog, "gold_nugget", r2(A["gold"] / 9), 64, "材料")

for n, p in [
    ("wooden_pickaxe", 3.00),
    ("wooden_axe", 3.00),
    ("wooden_shovel", 1.50),
    ("wooden_hoe", 2.00),
    ("wooden_sword", 2.50),
    ("stone_pickaxe", 5.00),
    ("stone_axe", 5.00),
    ("stone_shovel", 2.00),
    ("stone_hoe", 3.00),
    ("stone_sword", 3.00),
]:
    add(catalog, n, p, 1, "其他")

tools = {
    "iron_pickaxe": 120.00,
    "iron_axe": 120.00,
    "iron_shovel": 50.00,
    "iron_hoe": 80.00,
    "iron_sword": 90.00,
    "golden_pickaxe": 150.00,
    "golden_sword": 120.00,
    "diamond_pickaxe": 650.00,
    "diamond_axe": 650.00,
    "diamond_shovel": 250.00,
    "diamond_hoe": 450.00,
    "diamond_sword": 450.00,
    "netherite_pickaxe": 5200.00,
    "netherite_axe": 5200.00,
    "netherite_shovel": 4800.00,
    "netherite_hoe": 5000.00,
    "netherite_sword": 5000.00,
    "bow": 40.00,
    "crossbow": 80.00,
    "arrow": 2.00,
    "spectral_arrow": 6.00,
    "shield": 80.00,
    "trident": 2000.00,
    "mace": 8000.00,
    "flint_and_steel": 40.00,
    "shears": 70.00,
    "fishing_rod": 20.00,
    "carrot_on_a_stick": 25.00,
    "warped_fungus_on_a_stick": 30.00,
    "brush": 50.00,
    "spyglass": 100.00,
}
for n, p in tools.items():
    cnt = 64 if n in ("arrow", "spectral_arrow") else 1
    add(catalog, n, p, cnt, "其他" if cnt == 1 else "材料")

armor = {
    "leather_helmet": 30.00,
    "leather_chestplate": 50.00,
    "leather_leggings": 40.00,
    "leather_boots": 25.00,
    "iron_helmet": 180.00,
    "iron_chestplate": 320.00,
    "iron_leggings": 280.00,
    "iron_boots": 160.00,
    "golden_helmet": 250.00,
    "golden_chestplate": 450.00,
    "golden_leggings": 400.00,
    "golden_boots": 220.00,
    "diamond_helmet": 1000.00,
    "diamond_chestplate": 1600.00,
    "diamond_leggings": 1400.00,
    "diamond_boots": 800.00,
    "netherite_helmet": 6000.00,
    "netherite_chestplate": 9000.00,
    "netherite_leggings": 8000.00,
    "netherite_boots": 5500.00,
    "turtle_helmet": 400.00,
    "chainmail_helmet": 120.00,
    "chainmail_chestplate": 200.00,
    "chainmail_leggings": 180.00,
    "chainmail_boots": 100.00,
}
for n, p in armor.items():
    add(catalog, n, p, 1, "其他")

redstone = {
    "redstone_torch": (5.00, 64),
    "repeater": (25.00, 16),
    "comparator": (40.00, 16),
    "piston": (50.00, 16),
    "sticky_piston": (80.00, 16),
    "observer": (60.00, 16),
    "hopper": (180.00, 1),
    "dropper": (40.00, 16),
    "dispenser": (50.00, 16),
    "lever": (3.00, 16),
    "stone_button": (1.00, 16),
    "oak_button": (1.00, 16),
    "stone_pressure_plate": (2.00, 16),
    "oak_pressure_plate": (2.00, 16),
    "light_weighted_pressure_plate": (80.00, 16),
    "heavy_weighted_pressure_plate": (80.00, 16),
    "daylight_detector": (50.00, 16),
    "target": (30.00, 16),
    "note_block": (15.00, 16),
    "rail": (8.00, 64),
    "powered_rail": (40.00, 64),
    "detector_rail": (25.00, 64),
    "activator_rail": (25.00, 64),
    "minecart": (40.00, 1),
    "chest_minecart": (50.00, 1),
    "hopper_minecart": (220.00, 1),
    "furnace_minecart": (60.00, 1),
    "tnt_minecart": (80.00, 1),
    "tnt": (30.00, 64),
    "redstone_lamp": (25.00, 16),
    "tripwire_hook": (10.00, 16),
    "trapped_chest": (20.00, 16),
    "lightning_rod": (40.00, 16),
    "sculk_sensor": (80.00, 16),
    "calibrated_sculk_sensor": (200.00, 16),
}
for n, (p, cnt) in redstone.items():
    tag = "其他" if "minecart" in n or n == "hopper" else "材料"
    add(catalog, n, p, cnt, tag)

stations = {
    "furnace": 20.00,
    "blast_furnace": 120.00,
    "smoker": 40.00,
    "brewing_stand": 100.00,
    "cauldron": 80.00,
    "anvil": 400.00,
    "chipped_anvil": 250.00,
    "damaged_anvil": 120.00,
    "grindstone": 30.00,
    "smithing_table": 50.00,
    "fletching_table": 20.00,
    "cartography_table": 30.00,
    "loom": 20.00,
    "composter": 10.00,
    "stonecutter": 40.00,
    "lectern": 40.00,
    "beacon": 10000.00,
    "enchanting_table": 900.00,
    "ender_chest": 800.00,
    "respawn_anchor": 600.00,
    "lodestone": 500.00,
    "conduit": 2500.00,
    "jukebox": 220.00,
    "bell": 150.00,
}
for n, p in stations.items():
    add(catalog, n, p, 1, "其他")

brew = {
    "nether_wart": (15.00, 64, "材料"),
    "blaze_powder": (15.00, 64, "材料"),
    "glass_bottle": (2.00, 16, "材料"),
    "fermented_spider_eye": (12.00, 64, "材料"),
    "glistering_melon_slice": (80.00, 64, "食物"),
    "golden_carrot": (90.00, 64, "食物"),
    "golden_apple": (600.00, 1, "食物"),
    "enchanted_golden_apple": (8000.00, 1, "食物"),
    "sugar": (2.00, 64, "食物"),
    "turtle_scute": (80.00, 64, "材料"),
    "breeze_rod": (100.00, 16, "材料"),
    "slime_block": (80.00, 16, "材料"),
    "honey_bottle": (12.00, 16, "食物"),
    "honey_block": (40.00, 16, "材料"),
    "experience_bottle": (50.00, 16, "其他"),
}
for n, (p, cnt, tag) in brew.items():
    add(catalog, n, p, cnt, tag)

foods = {
    "cooked_cod": 5.00,
    "cooked_salmon": 6.00,
    "baked_potato": 4.00,
    "cookie": 3.00,
    "pumpkin_pie": 12.00,
    "cake": 40.00,
    "mushroom_stew": 10.00,
    "rabbit_stew": 20.00,
    "suspicious_stew": 15.00,
    "dried_kelp": 1.00,
    "beetroot_soup": 8.00,
    "cooked_rabbit": 6.00,
    "bread": 6.00,
}
for n, p in foods.items():
    add(catalog, n, p, 1 if n == "cake" else 64, "食物")

crops = {
    "torchflower_seeds": 8.00,
    "pitcher_pod": 8.00,
    "cactus": 2.00,
    "brown_mushroom": 3.00,
    "red_mushroom": 3.00,
    "crimson_fungus": 4.00,
    "warped_fungus": 4.00,
    "chorus_flower": 20.00,
    "vine": 2.00,
    "lily_pad": 3.00,
    "sea_pickle": 4.00,
    "hanging_roots": 2.00,
    "spore_blossom": 10.00,
    "big_dripleaf": 6.00,
    "small_dripleaf": 4.00,
    "glow_lichen": 2.00,
    "moss_carpet": 1.00,
}
for n, p in crops.items():
    add(catalog, n, p, 64, "食物" if "seed" in n or n == "pitcher_pod" else "材料")

travel = {
    "saddle": (200.00, 1, "其他"),
    "ender_eye": (80.00, 16, "其他"),
    "compass": (50.00, 1, "其他"),
    "clock": (80.00, 1, "其他"),
    "empty_map": (20.00, 16, "其他"),
    "recovery_compass": (400.00, 1, "其他"),
    "lead": (30.00, 16, "其他"),
    "name_tag": (150.00, 1, "其他"),
    "goat_horn": (120.00, 1, "其他"),
    "firework_rocket": (8.00, 64, "其他"),
    "fire_charge": (10.00, 64, "材料"),
    "bucket": (40.00, 1, "材料"),
    "powder_snow_bucket": (20.00, 1, "材料"),
    "cod_bucket": (40.00, 1, "其他"),
    "salmon_bucket": (40.00, 1, "其他"),
    "tropical_fish_bucket": (50.00, 1, "其他"),
    "pufferfish_bucket": (60.00, 1, "其他"),
    "tadpole_bucket": (40.00, 1, "其他"),
    "snowball": (1.00, 64, "材料"),
    "bone_meal": (1.00, 64, "材料"),
    "paper": (2.00, 64, "材料"),
    "book": (10.00, 16, "材料"),
    "writable_book": (15.00, 16, "其他"),
    "enchanted_book": (300.00, 1, "其他"),
    "torch": (1.00, 64, "材料"),
    "soul_torch": (3.00, 64, "材料"),
    "lantern": (40.00, 16, "其他"),
    "soul_lantern": (50.00, 16, "其他"),
    "campfire": (15.00, 16, "其他"),
    "soul_campfire": (20.00, 16, "其他"),
    "end_crystal": (500.00, 1, "其他"),
    "popped_chorus_fruit": (10.00, 64, "食物"),
    "shulker_box": (1400.00, 1, "其他"),
    "white_shulker_box": (1400.00, 1, "其他"),
    "sponge": (80.00, 16, "材料"),
    "wet_sponge": (80.00, 16, "材料"),
    "trial_key": (200.00, 1, "其他"),
    "ominous_trial_key": (600.00, 1, "其他"),
    "ominous_bottle": (150.00, 16, "其他"),
    "wind_charge": (20.00, 64, "其他"),
    "wolf_armor": (400.00, 1, "其他"),
}
for n, (p, cnt, tag) in travel.items():
    add(catalog, n, p, cnt, tag)

for c in [
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
    add(catalog, f"{c}_shulker_box", 1400.00, 1, "其他")


def main():
    data = json.loads(CFG.read_text(encoding="utf-8"))
    have = {
        r[0]["NIN"].split(":", 1)[1]
        for r in data["systemShopItems"]
        if r[0]["NIN"].startswith("0:")
    }

    added = []
    skipped = []
    for name, (buy, count, tag) in sorted(catalog.items()):
        if name in have:
            skipped.append(name)
            continue
        data["systemShopItems"].append(make_row(name, count, buy, tag))
        added.append((name, buy, count, tag))
        have.add(name)

    data["ecoSystemData"]["noticeMsg"] = (
        "死亡会扣除所有金币（基金不受影响）｜价格重建0.625｜原版全面覆盖｜含刷怪蛋"
    )

    payload = json.dumps(data, ensure_ascii=False, indent=2)
    CFG.write_text(payload, encoding="utf-8")

    compact = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    share = "ppcpdata%" + base64.b64encode(
        zlib.compress(compact.encode("utf-8"), 9)
    ).decode("ascii")
    (BASE / "分享码.txt").write_text(share, encoding="utf-8")
    (BASE / "05_原始备份" / "最终分享串_副本.txt").write_text(share, encoding="utf-8")

    rep = BASE / "03_对比报告" / "原版补全清单.csv"
    with open(rep, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["item", "buy", "count", "tag"])
        for row in added:
            w.writerow(row)

    # refresh intro snippet
    intro = BASE / "02_定价锚点与说明" / "简介.txt"
    text = intro.read_text(encoding="utf-8") if intro.exists() else ""
    if "原版全面覆盖" not in text:
        text += "\n\n【更新】已补全原版工作站/红石/工具甲/建筑/酿造等常用物，便于原版内容覆盖。\n"
        intro.write_text(text, encoding="utf-8")

    bad = []
    for r in data["systemShopItems"]:
        b, s = r[1], r[2]
        nin = r[0]["NIN"]
        if "_spawn_egg" in nin:
            if s != 0:
                bad.append(nin)
        elif not (b > s >= 0):
            bad.append(nin)

    mc = sum(1 for r in data["systemShopItems"] if r[0]["NIN"].startswith("0:"))
    print(f"added {len(added)}, skipped existing {len(skipped)}")
    print(f"total shop items {len(data['systemShopItems'])}, vanilla {mc}")
    print(f"validation bad {len(bad)}")
    print(f"share len {len(share)}")
    for check in [
        "brewing_stand",
        "furnace",
        "hopper",
        "nether_wart",
        "golden_apple",
        "diamond_pickaxe",
        "oak_planks",
        "shulker_box",
        "beacon",
        "rail",
        "enchanting_table",
        "netherite_chestplate",
    ]:
        hit = [r for r in data["systemShopItems"] if r[0]["NIN"] == f"0:{check}"]
        if hit:
            print(f"  {check}: buy={hit[0][1]} sell={hit[0][2]} x{hit[0][0]['count']}")
        else:
            print(f"  {check}: MISSING")


if __name__ == "__main__":
    main()
