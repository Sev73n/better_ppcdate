# -*- coding: utf-8 -*-
"""Merge user 0807a share, set tools/armor to full remaining durability, fill gaps."""
from __future__ import annotations

import base64
import csv
import json
import zlib
from collections import Counter
from pathlib import Path

BASE = Path(r"C:/Users/AI10/Desktop/ppcdata")
USER = BASE / "06_用户自行导入" / "0807a.txt"
OUT_JSON = BASE / "01_配置明文" / "最终配置_rebuilt.json"
SELL = 0.625

MAX_DUR_PREFIX = {
    "wooden_": 59,
    "stone_": 131,
    "iron_": 250,
    "golden_": 32,
    "diamond_": 1561,
    "netherite_": 2031,
}
TOOL_SUFFIX = ("_sword", "_pickaxe", "_axe", "_shovel", "_hoe")
ARMOR = {
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
MISC = {
    "bow": 384,
    "crossbow": 464,
    "shield": 336,
    "trident": 250,
    "elytra": 432,
    "fishing_rod": 64,
    "carrot_on_a_stick": 25,
    "warped_fungus_on_a_stick": 100,
    "shears": 238,
    "flint_and_steel": 64,
    "brush": 64,
}
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
AUX_ITEMS = {"potion", "splash_potion", "lingering_potion", "tipped_arrow"}


def load_share(p: Path):
    t = p.read_text(encoding="utf-8").strip()
    if t.startswith("ppcpdata%"):
        return json.loads(zlib.decompress(base64.b64decode(t.split("%", 1)[1])))
    return json.loads(t)


def r2(x):
    return round(float(x) + 1e-12, 2)


def sell_of(buy):
    s = r2(buy * SELL)
    if s >= buy and buy > 0:
        s = r2(buy - 0.01) if buy > 0.01 else 0.0
    return s


def max_dur_for(name: str):
    if name in ARMOR:
        return ARMOR[name]
    if name in MISC:
        return MISC[name]
    for pref, d in MAX_DUR_PREFIX.items():
        if name.startswith(pref) and name.endswith(TOOL_SUFFIX):
            return d
    return None


def main():
    data = load_share(USER)
    rev = {str(v): k for k, v in data["nameSpaceMap"].items()}
    fwd = {k: str(v) for k, v in data["nameSpaceMap"].items()}
    mc = fwd["minecraft"]

    existing = set()
    for r in data["systemShopItems"]:
        pref, name = r[0]["NIN"].split(":", 1)
        existing.add(f"{rev.get(pref, pref)}:{name}")

    fixed = 0
    for r in data["systemShopItems"]:
        name = r[0]["NIN"].split(":", 1)[1]
        if name in AUX_ITEMS or name.endswith("_potion"):
            continue
        dmax = max_dur_for(name)
        if dmax is None:
            continue
        if r[0].get("durability") != dmax:
            fixed += 1
        r[0]["durability"] = dmax
        r[0].setdefault("modEnchantData", [])

    added = []

    def add_row(name, buy, count=64, tag="方块"):
        abs_id = f"minecraft:{name}"
        if abs_id in existing:
            return False
        buy = r2(buy)
        sell = sell_of(buy)
        f12 = min(count, 64) if count >= 16 else 1
        f13 = 0.0 if count >= 16 else 0.2
        data["systemShopItems"].append(
            [
                {
                    "NIN": f"{mc}:{name}",
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
        )
        existing.add(abs_id)
        added.append(name)
        return True

    for c in COLORS:
        add_row(f"{c}_stained_glass_pane", 2.0)
        add_row(f"{c}_carpet", 8.0)
    add_row("glass_pane", 1.0)

    for name, buy in [
        ("nether_brick", 2.0),
        ("red_nether_brick", 3.0),
        ("nether_brick_fence", 2.5),
        ("nether_brick_stairs", 2.5),
        ("nether_brick_slab", 1.2),
        ("nether_brick_wall", 2.5),
        ("red_nether_brick_stairs", 3.5),
        ("red_nether_brick_slab", 1.5),
        ("red_nether_brick_wall", 3.0),
        ("chiseled_nether_bricks", 3.0),
        ("cracked_nether_bricks", 2.0),
        ("polished_basalt", 1.5),
        ("smooth_basalt", 1.5),
        ("polished_blackstone", 1.5),
        ("polished_blackstone_bricks", 1.8),
        ("cracked_polished_blackstone_bricks", 1.5),
        ("chiseled_polished_blackstone", 2.0),
        ("polished_blackstone_stairs", 1.8),
        ("polished_blackstone_slab", 0.9),
        ("polished_blackstone_brick_stairs", 2.0),
        ("polished_blackstone_brick_slab", 1.0),
        ("polished_blackstone_brick_wall", 2.0),
        ("blackstone_stairs", 1.5),
        ("blackstone_slab", 0.8),
        ("blackstone_wall", 1.5),
        ("gilded_blackstone", 20.0),
        ("crimson_nylium", 3.0),
        ("warped_nylium", 3.0),
        ("crimson_stem", 2.0),
        ("warped_stem", 2.0),
        ("stripped_crimson_stem", 2.2),
        ("stripped_warped_stem", 2.2),
        ("crimson_hyphae", 2.0),
        ("warped_hyphae", 2.0),
        ("nether_gold_ore", 8.0),
        ("nether_quartz_ore", 6.0),
        ("crying_obsidian", 40.0),
        ("respawn_anchor", 200.0),
        ("magma_block", 3.0),
        ("end_stone_bricks", 5.0),
        ("end_stone_brick_stairs", 5.0),
        ("end_stone_brick_slab", 2.5),
        ("end_stone_brick_wall", 5.0),
        ("purpur_pillar", 6.0),
        ("purpur_stairs", 6.0),
        ("purpur_slab", 3.0),
    ]:
        add_row(name, buy)

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
        f"死亡扣30%｜工具满耐久｜森罗配方B"
    )

    OUT_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    share = "ppcpdata%" + base64.b64encode(
        zlib.compress(
            json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode(), 9
        )
    ).decode()
    (BASE / "分享码.txt").write_text(share, encoding="utf-8")
    (BASE / "05_原始备份" / "最终分享串_副本.txt").write_text(share, encoding="utf-8")
    (BASE / "06_用户自行导入" / "0807a_merged_full_dur.txt").write_text(
        share, encoding="utf-8"
    )

    rep = BASE / "03_对比报告" / "0807a对照与耐久修复.csv"
    with open(rep, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["kind", "id", "detail"])
        w.writerow(["durability_fixed_count", "", fixed])
        for a in added:
            w.writerow(["added_vanilla", a, ""])

    for want in [
        "diamond_sword",
        "iron_pickaxe",
        "elytra",
        "nether_brick",
        "red_carpet",
        "white_stained_glass_pane",
        "potion",
    ]:
        hits = []
        for r in data["systemShopItems"]:
            name = r[0]["NIN"].split(":", 1)[1]
            if name == want:
                hits.append((r[0].get("durability"), r[1], r[0].get("count")))
        print(want, hits[:3])
    print(
        f"fixed_dur={fixed} added={len(added)} total={total} share={len(share)}"
    )
    print("notice", data["ecoSystemData"]["noticeMsg"])


if __name__ == "__main__":
    main()
