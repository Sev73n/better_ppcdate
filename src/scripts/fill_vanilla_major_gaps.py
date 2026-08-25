# -*- coding: utf-8 -*-
"""
Fill major vanilla building gaps + unify family prices.

Anchors (stack buy unless noted):
  cobble 0.10 → stone 0.20 → stone_bricks 0.30
  sand 1 → glass 2 → stained_glass 3; pane ≈ half
  wool 4 → carpet ≈ 2/3; concrete 5; terracotta 1.2 → glazed 3.5
  plank 0.60 (cherry/nether 0.80); stairs×1.5 slab×0.55 fence×1.2
  sell = buy × 0.625
  4/9 compact ore-blocks: unit×n×1.1, count=1 (anti-arbitrage)
"""
from __future__ import annotations

import base64
import csv
import json
import zlib
from collections import Counter
from pathlib import Path

BASE = Path(r"C:/Users/AI10/Desktop/ppcdata")
CFG = BASE / "01_配置明文" / "最终配置_rebuilt.json"
SHARE_IN = BASE / "分享码.txt"
SELL = 0.625

COLORS = [
    "white",
    "orange",
    "magenta",
    "light_blue",
    "yellow",
    "lime",
    "pink",
    "gray",
    "light_gray",
    "cyan",
    "purple",
    "blue",
    "brown",
    "green",
    "red",
    "black",
]
WOODS_OVERWORLD = [
    "oak",
    "spruce",
    "birch",
    "jungle",
    "acacia",
    "dark_oak",
    "mangrove",
    "cherry",
    "pale_oak",
]
WOODS_NETHER = ["crimson", "warped"]
WOODS_ALL = WOODS_OVERWORLD + ["bamboo"] + WOODS_NETHER

# remaining durability for tools (PPCP field)
MAX_DUR = {
    "elytra": 432,
    "bow": 384,
    "crossbow": 464,
    "shield": 336,
    "trident": 250,
    "fishing_rod": 64,
    "shears": 238,
    "flint_and_steel": 64,
    "brush": 64,
}
for mat, d in [
    ("wooden", 59),
    ("stone", 131),
    ("iron", 250),
    ("golden", 32),
    ("diamond", 1561),
    ("netherite", 2031),
]:
    for t in ("sword", "pickaxe", "axe", "shovel", "hoe"):
        MAX_DUR[f"{mat}_{t}"] = d
ARMOR_DUR = {
    "leather_helmet": 55,
    "leather_chestplate": 80,
    "leather_leggings": 75,
    "leather_boots": 65,
    "chainmail_helmet": 165,
    "chainmail_chestplate": 240,
    "chainmail_leggings": 225,
    "chainmail_boots": 195,
    "iron_helmet": 165,
    "iron_chestplate": 240,
    "iron_leggings": 225,
    "iron_boots": 195,
    "golden_helmet": 77,
    "golden_chestplate": 112,
    "golden_leggings": 105,
    "golden_boots": 91,
    "diamond_helmet": 363,
    "diamond_chestplate": 528,
    "diamond_leggings": 495,
    "diamond_boots": 429,
    "netherite_helmet": 407,
    "netherite_chestplate": 592,
    "netherite_leggings": 555,
    "netherite_boots": 481,
    "turtle_helmet": 275,
}
MAX_DUR.update(ARMOR_DUR)


def r2(x):
    return round(float(x) + 1e-12, 2)


def sell_of(buy):
    s = r2(buy * SELL)
    if s >= buy and buy > 0:
        s = r2(buy - 0.01) if buy > 0.01 else 0.0
    return s


def load_share(p: Path):
    t = p.read_text(encoding="utf-8").strip()
    if t.startswith("ppcpdata%"):
        return json.loads(zlib.decompress(base64.b64decode(t.split("%", 1)[1])))
    return json.loads(t)


def plank_of(w: str) -> float:
    if w in ("crimson", "warped", "cherry"):
        return 0.80
    if w == "pale_oak":
        return 0.70
    if w == "bamboo":
        return 0.55
    return 0.60


def main():
    data = load_share(SHARE_IN)
    rev = {str(v): k for k, v in data["nameSpaceMap"].items()}
    fwd = {k: str(v) for k, v in data["nameSpaceMap"].items()}
    mc = fwd["minecraft"]

    # name -> row
    by_name = {}
    for r in data["systemShopItems"]:
        pref, name = r[0]["NIN"].split(":", 1)
        if rev.get(pref) == "minecraft":
            by_name[name] = r

    prices = {}  # name -> (buy, count, tag)
    report = []

    def setp(name, buy, count=64, tag="方块"):
        buy = r2(buy)
        prices[name] = (buy, count, tag)

    def stone_family(base_name, base_buy, variants):
        """variants: list of (name, mult) relative to base stack buy."""
        setp(base_name, base_buy)
        for n, m in variants:
            setp(n, base_buy * m)

    def shaped(base_buy, stairs=True, slab=True, wall=False, fence=False):
        out = []
        if stairs:
            out.append(("stairs", 1.50))
        if slab:
            out.append(("slab", 0.55))
        if wall:
            out.append(("wall", 1.20))
        if fence:
            out.append(("fence", 1.20))
        return out

    # ----- stone / deepslate / sandstone -----
    setp("cobblestone", 0.10)
    setp("stone", 0.20)
    setp("stone_bricks", 0.30)
    setp("smooth_stone", 0.35)
    setp("cracked_stone_bricks", 0.35)
    setp("chiseled_stone_bricks", 0.40)
    setp("mossy_cobblestone", 0.25)
    setp("mossy_stone_bricks", 0.40)
    for n, m in [
        ("cobblestone_stairs", 1.5),
        ("cobblestone_slab", 0.55),
        ("cobblestone_wall", 1.2),
        ("stone_stairs", 1.5),
        ("stone_brick_stairs", 1.5),
        ("stone_brick_slab", 0.55),
        ("stone_brick_wall", 1.2),
        ("mossy_cobblestone_stairs", 1.5),
        ("mossy_cobblestone_slab", 0.55),
        ("mossy_cobblestone_wall", 1.2),
        ("mossy_stone_brick_stairs", 1.5),
        ("mossy_stone_brick_slab", 0.55),
        ("mossy_stone_brick_wall", 1.2),
    ]:
        base = 0.10 if "cobble" in n and "mossy_stone" not in n else 0.30
        if n.startswith("mossy_cobblestone"):
            base = 0.25
        if n.startswith("mossy_stone"):
            base = 0.40
        if n.startswith("stone_stairs"):
            base = 0.20
        if "stone_brick" in n:
            base = 0.30
        setp(n, base * (1.5 if "stairs" in n else 0.55 if "slab" in n else 1.2))

    for rock, base in [("andesite", 0.20), ("diorite", 0.20), ("granite", 0.20)]:
        setp(rock, base)
        setp(f"polished_{rock}", base * 1.5)
        setp(f"{rock}_stairs", base * 1.5)
        setp(f"{rock}_slab", base * 0.55)
        setp(f"{rock}_wall", base * 1.2)
        setp(f"polished_{rock}_stairs", base * 1.5 * 1.5)
        setp(f"polished_{rock}_slab", base * 1.5 * 0.55)

    setp("deepslate", 0.30)
    setp("cobbled_deepslate", 0.25)
    setp("polished_deepslate", 0.40)
    setp("deepslate_bricks", 0.45)
    setp("deepslate_tiles", 0.45)
    setp("chiseled_deepslate", 0.50)
    setp("cracked_deepslate_bricks", 0.48)
    setp("cracked_deepslate_tiles", 0.48)
    for prefix, base in [
        ("cobbled_deepslate", 0.25),
        ("polished_deepslate", 0.40),
        ("deepslate_brick", 0.45),
        ("deepslate_tile", 0.45),
    ]:
        setp(f"{prefix}_stairs", base * 1.5)
        setp(f"{prefix}_slab", base * 0.55)
        setp(f"{prefix}_wall", base * 1.2)

    setp("tuff", 0.30)
    setp("polished_tuff", 0.40)
    setp("tuff_bricks", 0.45)
    setp("chiseled_tuff", 0.50)
    setp("chiseled_tuff_bricks", 0.55)
    for prefix, base in [
        ("tuff", 0.30),
        ("polished_tuff", 0.40),
        ("tuff_brick", 0.45),
    ]:
        setp(f"{prefix}_stairs", base * 1.5)
        setp(f"{prefix}_slab", base * 0.55)
        setp(f"{prefix}_wall", base * 1.2)

    setp("calcite", 0.50)
    setp("dripstone_block", 0.40)
    setp("sandstone", 1.20)
    setp("smooth_sandstone", 1.50)
    setp("cut_sandstone", 1.40)
    setp("chiseled_sandstone", 1.60)
    for n, b, m in [
        ("sandstone_stairs", 1.20, 1.5),
        ("sandstone_slab", 1.20, 0.55),
        ("sandstone_wall", 1.20, 1.2),
        ("red_sandstone", 1.50, 1.0),
        ("smooth_red_sandstone", 1.80, 1.0),
        ("cut_red_sandstone", 1.70, 1.0),
        ("chiseled_red_sandstone", 1.90, 1.0),
        ("red_sandstone_stairs", 1.50, 1.5),
        ("red_sandstone_slab", 1.50, 0.55),
        ("red_sandstone_wall", 1.50, 1.2),
    ]:
        setp(n, b * m if m != 1.0 else b)

    setp("bricks", 2.00)  # Java
    setp("brick_block", 2.00)  # Bedrock alias
    setp("brick_stairs", 3.00)
    setp("brick_slab", 1.10)
    setp("brick_wall", 2.40)
    setp("mud", 0.30)
    setp("packed_mud", 0.50)
    setp("mud_bricks", 1.50)
    setp("mud_brick_stairs", 2.25)
    setp("mud_brick_slab", 0.83)
    setp("mud_brick_wall", 1.80)

    setp("prismarine", 26.40)  # 4×shard 6 ×1.1; stairs/bricks stay convenience
    setp("prismarine_bricks", 10.00)
    setp("dark_prismarine", 10.00)
    setp("prismarine_stairs", 12.00)
    setp("prismarine_slab", 4.40)
    setp("prismarine_wall", 9.60)
    setp("prismarine_brick_stairs", 15.00)
    setp("prismarine_brick_slab", 5.50)
    setp("dark_prismarine_stairs", 15.00)
    setp("dark_prismarine_slab", 5.50)

    # ----- wood -----
    for w in WOODS_ALL:
        p = plank_of(w)
        setp(f"{w}_planks", p)
        setp(f"{w}_stairs", p * 1.5)
        setp(f"{w}_slab", p * 0.55)
        setp(f"{w}_fence", p * 1.2)
        setp(f"{w}_fence_gate", p * 1.5, 16)
        setp(f"{w}_door", p * 2.5, 16)
        setp(f"{w}_trapdoor", p * 2.0, 16)
        setp(f"{w}_button", max(0.5, p * 0.8), 16)
        setp(f"{w}_pressure_plate", p * 1.2, 16)
        setp(f"{w}_sign", p * 2.0 + 0.20, 16)
        setp(f"{w}_hanging_sign", p * 3.0 + 0.40, 16)
        if w in WOODS_OVERWORLD:
            setp(f"{w}_log", 2.00 if w != "cherry" else 2.40)
            setp(f"{w}_wood", 2.20 if w != "cherry" else 2.60)
            setp(f"stripped_{w}_log", 2.20 if w != "cherry" else 2.60)
            setp(f"stripped_{w}_wood", 2.40 if w != "cherry" else 2.80)
            setp(f"{w}_leaves", 1.00)
            setp(f"{w}_sapling", 2.00)
            setp(f"{w}_boat", 8.00, 1, "其他")
            setp(f"{w}_chest_boat", 15.00, 1, "其他")
        if w in WOODS_NETHER:
            setp(f"{w}_stem", 2.40)
            setp(f"stripped_{w}_stem", 2.60)
            setp(f"{w}_hyphae", 2.40)
            setp(f"stripped_{w}_hyphae", 2.60)
            setp(f"{w}_nylium", 3.00)
            setp(f"{w}_fungus", 2.00)
            setp(f"{w}_roots", 1.50)
    setp("nether_wart_block", 4.00)
    setp("warped_wart_block", 4.00)
    setp("bamboo_block", 1.80)
    setp("bamboo_mosaic", 0.70)
    setp("bamboo_mosaic_stairs", 1.05)
    setp("bamboo_mosaic_slab", 0.39)

    # ----- color family -----
    for c in COLORS:
        setp(f"{c}_wool", 4.00)
        setp(f"{c}_carpet", 3.00)  # ≈ wool×2/3 + tiny labor (was wrongly 8)
        setp(f"{c}_concrete", 5.00)
        setp(f"{c}_concrete_powder", 4.00)
        setp(f"{c}_terracotta", 1.50)
        setp(f"{c}_glazed_terracotta", 3.50)
        setp(f"{c}_stained_glass", 3.00)
        setp(f"{c}_stained_glass_pane", 1.50)
        setp(f"{c}_bed", 8.00, 1, "其他")
        setp(f"{c}_candle", 6.00, 16, "其他")
        setp(f"{c}_banner", 6.00, 16, "其他")
        setp(f"{c}_shulker_box", 1400.00, 1, "其他")
    setp("terracotta", 1.00)
    setp("glass", 2.00)
    setp("glass_pane", 1.00)
    setp("tinted_glass", 8.00)
    setp("candle", 5.00, 16, "其他")
    setp("white_candle", 6.00, 16, "其他")  # already in loop
    # generic bed / carpet / stained aliases
    setp("bed", 8.00, 1, "其他")
    setp("carpet", 3.00)
    setp("stained_glass", 3.00)
    setp("stained_glass_pane", 1.50)

    # ----- coral -----
    for c in ["tube", "brain", "bubble", "fire", "horn"]:
        setp(f"{c}_coral_block", 6.00)
        setp(f"{c}_coral", 4.00, 16)
        setp(f"{c}_coral_fan", 4.00, 16)
        setp(f"dead_{c}_coral_block", 2.00)
        setp(f"dead_{c}_coral", 1.50, 16)
        setp(f"dead_{c}_coral_fan", 1.50, 16)

    # ----- copper (ingot 12 is per-item; count is stack size, NOT a price divisor) -----
    cu = 12.0
    cu_block = r2(9 * cu * 1.1)  # 118.8
    cut = r2(cu_block / 4 * 1.1)  # 32.67
    stages = ("", "exposed_", "weathered_", "oxidized_")

    def copper8(base):
        return [f"{s}{base}" for s in stages] + [f"waxed_{s}{base}" for s in stages]

    for n in [
        "copper_block",
        "exposed_copper",
        "weathered_copper",
        "oxidized_copper",
        "waxed_copper",
        "waxed_exposed_copper",
        "waxed_weathered_copper",
        "waxed_oxidized_copper",
    ] + copper8("copper_golem_statue") + copper8("chiseled_copper"):
        setp(n, cu_block, 1)
    for n in copper8("cut_copper") + copper8("copper_grate"):
        setp(n, cut, 1)
    for n in copper8("cut_copper_stairs"):
        setp(n, r2(cut * 1.5), 1)
    for n in copper8("cut_copper_slab"):
        setp(n, r2(cut * 0.55), 1)
    for n in copper8("copper_bulb"):
        setp(n, r2((3 * cu + 80 + 16) * 1.1), 1, "其他")
    for n in copper8("copper_door"):
        setp(n, r2(6 * cu), 1, "其他")
    for n in copper8("copper_trapdoor"):
        setp(n, r2(4 * cu), 1, "其他")
    for n in copper8("copper_chest"):
        setp(n, r2((8 * cu + 8) * 1.1), 1, "其他")
    setp("raw_copper_block", r2(9 * 10.0 * 1.1), 1)

    # ----- quartz / misc compact decorative -----
    q_unit = 10.0 / 64.0
    q_block_unit = r2(4 * q_unit * 1.1)  # 0.69
    # sell as stacks of 16 for UX (unit preserved)
    setp("quartz_block", r2(q_block_unit * 16), 16)
    setp("smooth_quartz", r2(q_block_unit * 16 * 1.1), 16)
    setp("chiseled_quartz_block", r2(q_block_unit * 16 * 1.15), 16)
    setp("quartz_bricks", r2(q_block_unit * 16 * 1.15), 16)
    setp("quartz_pillar", r2(q_block_unit * 16 * 1.1), 16)
    setp("quartz_stairs", r2(q_block_unit * 1.5 * 16), 16)
    setp("quartz_slab", r2(q_block_unit * 0.55 * 16), 16)
    setp("smooth_quartz_stairs", r2(q_block_unit * 1.1 * 1.5 * 16), 16)
    setp("smooth_quartz_slab", r2(q_block_unit * 1.1 * 0.55 * 16), 16)
    setp("hay_block", r2(9 * 3.0 * 1.1), 16)  # 29.7; wheat is 3 per item
    setp("bone_block", 12.00, 16)
    setp("honeycomb_block", r2(4 * 8.0 * 1.1), 16)  # 35.2; honeycomb is 8 per item
    setp("dried_kelp_block", 6.00, 16)

    # ----- nether/end touch-ups -----
    setp("nether_brick", 2.00)
    setp("red_nether_brick", 3.00)
    setp("nether_brick_fence", 2.40)
    setp("nether_brick_stairs", 3.00)
    setp("nether_brick_slab", 1.10)
    setp("nether_brick_wall", 2.40)
    setp("red_nether_brick_stairs", 4.50)
    setp("red_nether_brick_slab", 1.65)
    setp("red_nether_brick_wall", 3.60)
    setp("chiseled_nether_bricks", 3.00)
    setp("cracked_nether_bricks", 2.00)
    setp("polished_basalt", 1.50)
    setp("smooth_basalt", 1.50)
    setp("polished_blackstone", 1.50)
    setp("polished_blackstone_bricks", 1.80)
    setp("chiseled_polished_blackstone", 2.00)
    setp("cracked_polished_blackstone_bricks", 1.50)
    setp("blackstone_stairs", 1.50)
    setp("blackstone_slab", 0.55)
    setp("blackstone_wall", 1.20)
    setp("polished_blackstone_stairs", 2.25)
    setp("polished_blackstone_slab", 0.83)
    setp("polished_blackstone_wall", 1.80)
    setp("polished_blackstone_brick_stairs", 2.70)
    setp("polished_blackstone_brick_slab", 0.99)
    setp("polished_blackstone_brick_wall", 2.16)
    setp("gilded_blackstone", 20.00)
    setp("crying_obsidian", 40.00)
    setp("respawn_anchor", 200.00, 1, "其他")
    setp("end_stone", 3.00)
    setp("end_stone_bricks", 4.00)
    setp("end_bricks", 4.00)  # bedrock alias — was 5/4 sell-broken
    setp("end_stone_brick_stairs", 6.00)
    setp("end_brick_stairs", 6.00)
    setp("end_stone_brick_slab", 2.20)
    setp("end_stone_brick_wall", 4.80)
    setp("end_rod", 20.00, 16, "其他")  # was 64/64; blaze+pearl craft band
    setp("purpur_block", 6.00)
    setp("purpur_pillar", 6.50)
    setp("purpur_stairs", 9.00)
    setp("purpur_slab", 3.30)
    setp("chorus_flower", 8.00, 16)
    setp("end_crystal", 300.00, 1, "其他")  # sell 187.5 < ghast+eye+glass mats

    # ----- redstone / nature small gaps -----
    setp("iron_bars", 12.00, 64, "材料")
    setp("chain", 8.00, 64, "材料")
    setp("scaffolding", 2.00, 64, "材料")
    setp("item_frame", 6.00, 16, "其他")
    setp("glow_item_frame", 12.00, 16, "其他")
    setp("chiseled_bookshelf", 25.00, 16, "其他")
    setp("crafter", 80.00, 1, "其他")
    setp("grass_block", 1.00)
    setp("podzol", 2.00)
    setp("mycelium", 3.00)
    setp("coarse_dirt", 0.50)
    setp("rooted_dirt", 1.00)
    setp("dirt_path", 0.80)
    setp("azalea", 3.00, 16)
    setp("flowering_azalea", 4.00, 16)
    setp("dead_bush", 0.50, 16)
    setp("fern", 0.50, 16)
    setp("large_fern", 1.00, 16)
    setp("short_grass", 0.30, 16)
    setp("tall_grass", 0.60, 16)
    setp("cobweb", 8.00, 16)
    setp("amethyst_cluster", 20.00, 16)
    setp("budding_amethyst", 80.00, 16)
    setp("furnace_minecart", 50.00, 1, "其他")

    # apply
    added = 0
    updated = 0
    for name, (buy, count, tag) in sorted(prices.items()):
        sell = sell_of(buy)
        if name in by_name:
            r = by_name[name]
            old = (r[1], r[2], r[0].get("count"))
            r[1] = buy
            r[2] = sell
            r[0]["count"] = count
            r[0].setdefault("modEnchantData", [])
            # keep / fix durability for durable goods
            if name in MAX_DUR:
                r[0]["durability"] = MAX_DUR[name]
            elif "durability" not in r[0]:
                r[0]["durability"] = 0
            # tag slot
            if len(r) > 6 and isinstance(r[6], str) and r[6] in (
                "方块",
                "材料",
                "其他",
                "食物",
                "",
            ):
                r[6] = tag
            if old != (buy, sell, count):
                updated += 1
                report.append((name, "update", old[0], buy, count, tag))
        else:
            f12 = min(count, 64) if count >= 16 else 1
            f13 = 0.0 if count >= 16 else 0.2
            row = [
                {
                    "NIN": f"{mc}:{name}",
                    "count": count,
                    "durability": MAX_DUR.get(name, 0),
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
            data["systemShopItems"].append(row)
            by_name[name] = row
            added += 1
            report.append((name, "add", "", buy, count, tag))

    # notice
    counts = Counter()
    for r in data["systemShopItems"]:
        counts[rev.get(r[0]["NIN"].split(":", 1)[0])] += 1
    total = len(data["systemShopItems"])
    mc_n = counts.get("minecraft", 0)
    cook = counts.get("kaleidoscope_cookery", 0)
    tav = counts.get("kaleidoscope_tavern", 0)
    doll = counts.get("kaleidoscope_doll", 0)
    ice = counts.get("bricefire", 0)
    extra = total - mc_n - cook - tav - doll - ice
    data.setdefault("ecoSystemData", {})["noticeMsg"] = (
        f"仅金币｜原版{mc_n}｜森罗厨{cook}+酒{tav}+偶{doll}｜冰火{ice}｜其他{extra}｜合计{total}｜"
        f"死亡扣30%｜建筑阶梯定价｜工具满耐久"
    )

    CFG.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    share = "ppcpdata%" + base64.b64encode(
        zlib.compress(
            json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode(), 9
        )
    ).decode()
    (BASE / "分享码.txt").write_text(share, encoding="utf-8")
    (BASE / "05_原始备份" / "最终分享串_副本.txt").write_text(share, encoding="utf-8")

    rep = BASE / "03_对比报告" / "原版大块缺口补齐与调价.csv"
    with open(rep, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "action", "old_buy", "new_buy", "count", "tag"])
        w.writerows(report)

    rationale = BASE / "02_定价锚点与说明" / "原版建筑阶梯定价说明.txt"
    rationale.write_text(
        f"""原版建筑向定价说明（本次补齐后）

一、全局
- 货币：仅金币；回收 sell = buy × 0.625（禁止 sell≥buy）
- 建筑块默认 ×64 上架；门/按钮/船/铜块等例外见 count
- 锚点不变：圆石堆 0.10｜钻石堆 200｜鞘翅 13140

二、石材阶梯（堆价）
- 圆石 0.10 → 石头 0.20 → 石砖/平滑石 0.30~0.35
- 安山岩/闪长岩/花岗岩 0.20，磨制 ×1.5
- 深板岩：圆深板岩 0.25 → 深板岩 0.30 → 磨制 0.40 → 砖/瓦 0.45
- 变种：台阶 ×0.55｜楼梯 ×1.5｜墙 ×1.2（相对对应基材堆价）
- 砂岩从沙 1.0 抬升：砂岩 1.2 → 切割/平滑/錾制 1.4~1.6
- 红砖堆 2.0；泥砖 1.5；海晶 8 / 砖与暗海晶 10

三、木材阶梯
- 木板 0.60（樱/下界菌岩板 0.80，苍白橡 0.70，竹板 0.55）
- 原木 ~2.0；去皮略贵；树叶 1；树苗 2
- 楼梯×1.5｜台阶×0.55｜栅栏×1.2｜栅栏门×1.5
- 门×2.5 / 活板门×2.0（×16）；告示牌/悬挂告示牌按板+棒

四、玻璃 / 羊毛 / 混凝土 / 陶瓦
- 玻璃 2，玻璃板 1；染色玻璃 3，染色板 1.5（玻璃+染料档）
- 羊毛 4；地毯 3（≈2/3 羊毛，纠正手动的 8）
- 混凝土 5，粉末 4；陶瓦 1.0~1.5；带釉陶瓦 3.5（烧制+染料）
- 旗帜 6、蜡烛 5~6（蜂蜡/线+染料档）；床保持 8

五、铜 / 石英（防合成套利）
- 铜锭堆 12 → 铜块单价 = 9×(12/64)×1.1 ≈ 1.86（count=1）
- 切制/氧化/涂蜡同价或略高 5%，避免「买块拆锭」或「氧化刷差价」
- 石英堆 10 → 石英块按 4 合 1×1.1，再×16 上架方便购买

六、珊瑚 / 末地
- 珊瑚块 6；活珊瑚/扇 4；死亡减半档
- 末地石 3 → 末地石砖 4；末地烛 20（焰棒+珍珠带，不再 64/64 坏回收）
- 紫珀 6；重生锚 200；末影水晶 500

七、本次统计
- 新增 {added}｜调价/对齐 {updated}｜原版合计 {mc_n}｜全店 {total}
- 分享码已写入 Desktop/ppcdata/分享码.txt
""",
        encoding="utf-8",
    )

    print(f"added={added} updated={updated} mc={mc_n} total={total}")
    print("notice", data["ecoSystemData"]["noticeMsg"])
    for s in [
        "cobblestone",
        "stone_bricks",
        "oak_planks",
        "white_carpet",
        "white_stained_glass_pane",
        "copper_block",
        "quartz_block",
        "end_rod",
        "end_bricks",
        "nether_brick",
        "tube_coral",
        "black_glazed_terracotta",
        "pale_oak_planks",
        "deepslate_bricks",
    ]:
        r = by_name.get(s)
        if r:
            print(
                f"  {s:28} buy={r[1]:8} sell={r[2]:8} c={r[0].get('count')}"
            )


if __name__ == "__main__":
    main()
