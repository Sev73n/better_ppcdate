# -*- coding: utf-8 -*-
"""Close remaining convert loops + fill NetEase Copper Age / pale garden / happy ghast gaps.

Building stairs/discs/sherds convenience prices are left alone.
Oxidation/wax variants of the same copper piece share one price (axe-scrape arb).
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
SHARE = BASE / "分享码.txt"
SELL = 0.625
PREMIUM = 1.1
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
STAGES = ("", "exposed_", "weathered_", "oxidized_")


def r2(x):
    return round(float(x) + 1e-12, 2)


def sell_of(buy, zero=False):
    if zero:
        return 0.0
    s = r2(buy * SELL)
    if s >= buy and buy > 0:
        s = r2(buy - 0.01) if buy > 0.01 else 0.0
    return s


def eight(base: str) -> list[str]:
    """4 oxidation + 4 waxed. clean unwaxed = base, clean waxed = waxed_{base}."""
    return [f"{s}{base}" for s in STAGES] + [f"waxed_{s}{base}" for s in STAGES]


def load_cfg():
    return json.loads(CFG.read_text(encoding="utf-8"))


def write_share(data):
    CFG.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    share = "ppcpdata%" + base64.b64encode(
        zlib.compress(
            json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode(), 9
        )
    ).decode()
    SHARE.write_text(share, encoding="utf-8")
    (BASE / "05_原始备份" / "最终分享串_副本.txt").write_text(share, encoding="utf-8")
    return share


def index_mc(data):
    rev = {str(v): k for k, v in data["nameSpaceMap"].items()}
    fwd = {k: str(v) for k, v in data["nameSpaceMap"].items()}
    rows = {}
    for r in data["systemShopItems"]:
        pref, name = r[0]["NIN"].split(":", 1)
        if rev.get(pref) != "minecraft":
            continue
        rows[name] = r
    return rows, rev, fwd


def set_price(row, buy, report, name, reason):
    old = float(row[1])
    buy = r2(buy)
    if abs(old - buy) < 0.005 and abs(float(row[2]) - sell_of(buy)) < 0.005:
        return
    row[1] = buy
    row[2] = sell_of(buy)
    report.append((name, "reprice", old, buy, row[2], reason))


def main():
    data = load_cfg()
    rows, rev, fwd = index_mc(data)
    mc = fwd["minecraft"]
    report = []
    added = 0

    def add(name, buy, count=1, tag="方块", sell_zero=False, reason="add"):
        nonlocal added
        if name in rows:
            return False
        buy = r2(buy)
        item = {"NIN": f"{mc}:{name}", "durability": 0, "modEnchantData": []}
        if count is not None:
            item["count"] = count
        f12 = min(count or 1, 64) if (count or 1) >= 16 else 1
        f13 = 0.0 if (count or 1) >= 16 else 0.2
        row = [
            item,
            buy,
            sell_of(buy, zero=sell_zero),
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
        rows[name] = row
        added += 1
        report.append((name, reason, "", buy, row[2], f"add {tag} c={count}"))
        return True

    def price(name, buy, reason):
        if name in rows:
            set_price(rows[name], buy, report, name, reason)
        else:
            add(name, buy, 1, "方块", reason=reason)

    # ----- 1) close convert loops -----
    cu = float(rows["copper_ingot"][1]) if "copper_ingot" in rows else 12.0
    block = r2(9 * cu * PREMIUM)  # 118.8
    cut = r2(block / 4 * PREMIUM)  # 32.67
    stairs = r2(cut * 1.5)
    slab = r2(cut * 0.55)
    bulb = r2((3 * cu + 80 + 16) * PREMIUM)  # 3 ingot + blaze + redstone
    door = r2(6 * cu)
    trap = r2(4 * cu)
    chest_p = r2((8 * cu + 8) * PREMIUM)
    bars = 20.0
    chain = 15.0
    lantern = 45.0
    rod = 40.0

    # full-block tier (scrape/wax must not change value)
    block_ids = [
        "copper_block",
        "exposed_copper",
        "weathered_copper",
        "oxidized_copper",
        "waxed_copper",
        "waxed_exposed_copper",
        "waxed_weathered_copper",
        "waxed_oxidized_copper",
    ] + eight("copper_golem_statue")
    for n in block_ids:
        if n in rows:
            price(n, block, "copper-block-tier")
        else:
            add(n, block, 1, "方块", reason="copper-block-tier")

    for n in eight("cut_copper") + eight("copper_grate"):
        if n in rows:
            price(n, cut, "copper-cut/grate")
        else:
            add(n, cut, 1, "方块", reason="copper-cut/grate")

    # stonecutter 1 block → 1 chiseled
    for n in eight("chiseled_copper"):
        if n in rows:
            price(n, block, "copper-chiseled=block")
        else:
            add(n, block, 1, "方块", reason="copper-chiseled=block")

    for n in eight("cut_copper_stairs"):
        if n in rows:
            price(n, stairs, "copper-stairs")
        else:
            add(n, stairs, 1, "方块", reason="copper-stairs")
    for n in eight("cut_copper_slab"):
        if n in rows:
            price(n, slab, "copper-slab")
        else:
            add(n, slab, 1, "方块", reason="copper-slab")

    for n in eight("copper_bulb"):
        if n in rows:
            price(n, bulb, "copper-bulb")
        else:
            add(n, bulb, 1, "其他", reason="copper-bulb")
    for n in eight("copper_door"):
        if n in rows:
            price(n, door, "copper-door")
        else:
            add(n, door, 1, "其他", reason="copper-door")
    for n in eight("copper_trapdoor"):
        if n in rows:
            price(n, trap, "copper-trapdoor")
        else:
            add(n, trap, 1, "其他", reason="copper-trapdoor")
    for n in eight("copper_chest"):
        if n in rows:
            price(n, chest_p, "copper-chest")
        else:
            add(n, chest_p, 1, "其他", reason="copper-chest")
    for n in eight("copper_bars"):
        if n in rows:
            price(n, bars, "copper-bars-unify")
        else:
            add(n, bars, 64, "材料", reason="copper-bars-unify")
    for n in eight("copper_chain"):
        if n in rows:
            price(n, chain, "copper-chain-unify")
        else:
            add(n, chain, 64, "材料", reason="copper-chain-unify")
    for n in eight("copper_lantern"):
        if n in rows:
            price(n, lantern, "copper-lantern-unify")
        else:
            add(n, lantern, 16, "其他", reason="copper-lantern-unify")
    for n in eight("lightning_rod"):
        if n in rows:
            price(n, rod, "lightning-rod-unify")
        else:
            add(n, rod, 16, "其他", reason="lightning-rod-unify")

    # magma: Bedrock id is magma; magma_block may also exist
    magma_buy = r2(4 * 20.0 * PREMIUM)  # 88
    for n in ("magma", "magma_block"):
        if n in rows:
            price(n, magma_buy, "4x magma_cream x1.1")

    if "end_crystal" in rows:
        price("end_crystal", 300.0, "sell<ghast+eye+glass mats")

    if "hay_block" in rows:
        wheat = float(rows["wheat"][1]) if "wheat" in rows else 3.0
        price("hay_block", r2(9 * wheat * PREMIUM), "9x wheat x1.1")
    if "honeycomb_block" in rows:
        hc = float(rows["honeycomb"][1]) if "honeycomb" in rows else 8.0
        price("honeycomb_block", r2(4 * hc * PREMIUM), "4x honeycomb x1.1")
    if "packed_ice" in rows:
        ice = float(rows["ice"][1]) if "ice" in rows else 2.0
        packed = r2(9 * ice * PREMIUM)
        price("packed_ice", packed, "9x ice x1.1")
        if "blue_ice" in rows:
            price("blue_ice", r2(9 * packed * PREMIUM), "9x packed_ice x1.1")
    if "prismarine" in rows:
        shard = float(rows["prismarine_shard"][1]) if "prismarine_shard" in rows else 6.0
        price("prismarine", r2(4 * shard * PREMIUM), "4x shard x1.1")
    if "anvil" in rows:
        price("anvil", 1000.0, "between iron-block craft and convenience")

    # ----- 2) NetEase Copper Age / pale garden / happy ghast fills -----
    add("pale_oak_shelf", 12.0, 16, "方块")
    add("stripped_bamboo_block", 1.8, 64, "方块")

    for c in COLORS:
        add(f"{c}_harness", 60.0, 1, "其他")
    add("bundle", 25.0, 1, "其他")
    for c in COLORS:
        add(f"{c}_bundle", 25.0, 1, "其他")

    add("dried_ghast", 80.0, 1, "方块")
    add("happy_ghast_spawn_egg", 2500.0, 1, "刷怪蛋", sell_zero=True)

    # resin family from clump=4
    add("resin_brick", 6.0, 64, "材料")
    add("resin_bricks", 26.4, 16, "方块")
    add("resin_block", 39.6, 16, "方块")
    add("chiseled_resin_bricks", 26.4, 16, "方块")
    add("resin_brick_stairs", 39.6, 16, "方块")
    add("resin_brick_slab", 14.52, 16, "方块")
    add("resin_brick_wall", 31.68, 16, "方块")
    add("creaking_heart", 80.0, 1, "方块")
    add("creaking_spawn_egg", 1500.0, 1, "刷怪蛋", sell_zero=True)
    add("pale_moss_block", 3.0, 64, "方块")
    add("pale_moss_carpet", 2.0, 64, "方块")
    add("pale_hanging_moss", 2.0, 64, "方块")

    add("armadillo_scute", 50.0, 16, "材料")
    add("sniffer_egg", 400.0, 1, "其他", sell_zero=True)
    add("beehive", 25.0, 16, "方块")
    add("small_amethyst_bud", 8.0, 16, "方块")
    add("medium_amethyst_bud", 12.0, 16, "方块")
    add("large_amethyst_bud", 16.0, 16, "方块")
    add("pointed_dripstone", 2.0, 64, "方块")
    for s in ("flow", "guster", "scrape"):
        add(f"{s}_pottery_sherd", 100.0, 16, "材料")
    add("firefly_bush", 2.0, 64, "方块")
    add("bush", 1.0, 64, "方块")
    add("leaf_litter", 1.0, 64, "方块")
    add("short_dry_grass", 1.0, 64, "方块")
    add("tall_dry_grass", 1.5, 64, "方块")
    add("music_disc_tears", 80.0, 1, "其他")
    add("music_disc_lava_chicken", 80.0, 1, "其他")
    add("frogspawn", 8.0, 16, "方块")
    add("turtle_egg", 40.0, 1, "其他", sell_zero=True)

    # ----- leftover vanilla that NetEase Copper Age definitely has -----
    add("bamboo_raft", 8.0, 1, "其他")
    add("bamboo_chest_raft", 15.0, 1, "其他")
    add("bee_nest", 20.0, 16, "方块")
    add("leather_horse_armor", 40.0, 1, "装备")
    add("iron_horse_armor", 200.0, 1, "装备")
    add("golden_horse_armor", 150.0, 1, "装备")
    add("diamond_horse_armor", 800.0, 1, "装备")
    add("mangrove_propagule", 2.0, 64, "方块")
    add("mangrove_roots", 2.0, 64, "方块")
    add("muddy_mangrove_roots", 3.0, 64, "方块")
    add("nether_sprouts", 1.0, 64, "方块")
    add("twisting_vines", 2.0, 64, "方块")
    add("weeping_vines", 2.0, 64, "方块")
    add("carved_pumpkin", 4.0, 64, "方块")
    add("jack_o_lantern", 8.0, 16, "方块")
    add("brown_mushroom_block", 6.0, 64, "方块")
    add("red_mushroom_block", 6.0, 64, "方块")
    add("mushroom_stem", 6.0, 64, "方块")
    add("suspicious_sand", 15.0, 16, "方块")
    add("suspicious_gravel", 15.0, 16, "方块")
    add("reinforced_deepslate", 200.0, 1, "方块")
    add("iron_door", 80.0, 16, "其他")
    add("iron_trapdoor", 50.0, 16, "其他")
    add("bowl", 1.0, 64, "其他")
    add("web", 8.0, 16, "方块")
    add("seagrass", 1.0, 64, "方块")
    add("waterlily", 3.0, 64, "方块")
    add("lodestone_compass", 80.0, 1, "其他")
    add("undyed_shulker_box", 1400.0, 1, "其他")
    add("cut_sandstone_slab", 0.77, 64, "方块")
    add("smooth_sandstone_slab", 0.83, 64, "方块")
    add("normal_stone_slab", 0.11, 64, "方块")
    add("stone_slab", 0.11, 64, "方块")
    add("prismarine_bricks_stairs", 15.0, 64, "方块")
    # Bedrock aliases (same price as Java / already-listed names)
    add("noteblock", 15.0, 16, "其他")
    add("stonecutter_block", 40.0, 1, "其他")
    add("quartz_ore", 12.0, 64, "方块")
    add("dirt_with_roots", 1.0, 64, "方块")
    add("grass_path", 0.8, 64, "方块")
    add("deadbush", 0.5, 16, "方块")
    add("slime", 79.2, 1, "方块")
    add("wooden_door", 1.5, 16, "其他")
    add("frog_spawn", 8.0, 16, "方块")

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
    notice = (
        f"仅金币｜原版{mc_n}｜森罗厨{cook}+酒{tav}+偶{doll}｜冰火{ice}｜其他{extra}｜合计{total}｜"
        f"死亡扣30%｜刷怪蛋不可回收｜药水aux待核｜铜器时代已补"
    )
    data.setdefault("ecoSystemData", {})["noticeMsg"] = notice

    share = write_share(data)

    (BASE / "02_定价锚点与说明" / "简介.txt").write_text(
        f"""分享码简介（当前版）

【货币】仅金币
【数量】原版{mc_n}｜森罗厨{cook}+酒{tav}+偶{doll}｜冰火{ice}｜其他{extra}｜合计{total}
【本轮】关铜氧化/岩浆/末地水晶/干草等循环｜铁砧1000｜补铜器时代+苍园+乐魂挽具收纳袋
【注意】建筑楼梯/唱片/陶片维持便利价；刷怪蛋不可回收
【公告】{notice}
""",
        encoding="utf-8",
    )

    csv_path = BASE / "03_对比报告" / "铜器时代补齐与循环修复.csv"
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "action", "old_buy", "new_buy", "sell", "reason"])
        w.writerows(report)

    # ----- verify -----
    rows, _, _ = index_mc(data)
    lines = []
    lines.append(f"added={added} repriced={sum(1 for r in report if r[1]=='reprice')} mc={mc_n} total={total} share={len(share)}")

    def buy(n):
        return float(rows[n][1]) if n in rows else None

    def sellp(n):
        return float(rows[n][2]) if n in rows else None

    checks = []
    # diamond uncraft
    if "diamond_block" in rows and "diamond" in rows:
        profit = 9 * sellp("diamond") - buy("diamond_block")
        checks.append(("diamond uncraft", profit, profit < 0))
    # copper scrape: buy exposed, sell as copper_block
    if "exposed_copper" in rows and "copper_block" in rows:
        same = abs(buy("exposed_copper") - buy("copper_block")) < 0.01
        profit = sellp("copper_block") - buy("exposed_copper")
        checks.append(("copper scrape same-price", 0 if same else 1, same))
        checks.append(("copper scrape sell-block", profit, profit < 0))
    if "waxed_oxidized_copper" in rows:
        checks.append(
            (
                "waxed oxidized = block",
                buy("waxed_oxidized_copper") - buy("copper_block"),
                abs(buy("waxed_oxidized_copper") - buy("copper_block")) < 0.01,
            )
        )
    if "magma" in rows and "magma_cream" in rows:
        profit = 4 * sellp("magma_cream") - buy("magma")
        checks.append(("magma uncraft", profit, profit < 0))
    if "end_crystal" in rows:
        # ghast tear 80 + eye 100 + 7 glass ~14 ≈ 194
        checks.append(("end_crystal sell<194", sellp("end_crystal") - 194, sellp("end_crystal") < 194))
    if "hay_block" in rows and "wheat" in rows:
        checks.append(("hay uncraft", 9 * sellp("wheat") - buy("hay_block"), 9 * sellp("wheat") < buy("hay_block")))
    if "honeycomb_block" in rows and "honeycomb" in rows:
        checks.append(
            (
                "honeycomb uncraft",
                4 * sellp("honeycomb") - buy("honeycomb_block"),
                4 * sellp("honeycomb") < buy("honeycomb_block"),
            )
        )
    if "packed_ice" in rows and "ice" in rows:
        checks.append(("packed_ice uncraft", 9 * sellp("ice") - buy("packed_ice"), 9 * sellp("ice") < buy("packed_ice")))
    if "blue_ice" in rows and "packed_ice" in rows:
        checks.append(
            (
                "blue_ice uncraft",
                9 * sellp("packed_ice") - buy("blue_ice"),
                9 * sellp("packed_ice") < buy("blue_ice"),
            )
        )
    if "prismarine" in rows and "prismarine_shard" in rows:
        checks.append(
            (
                "prismarine uncraft",
                4 * sellp("prismarine_shard") - buy("prismarine"),
                4 * sellp("prismarine_shard") < buy("prismarine"),
            )
        )
    checks.append(("anvil=1000", buy("anvil") - 1000 if buy("anvil") else 999, buy("anvil") == 1000))

    must_have = [
        "dried_ghast",
        "happy_ghast_spawn_egg",
        "white_harness",
        "black_harness",
        "bundle",
        "red_bundle",
        "copper_golem_statue",
        "waxed_copper_chest",
        "pale_oak_shelf",
        "creaking_heart",
        "armadillo_scute",
        "music_disc_tears",
        "flow_pottery_sherd",
        "bamboo_raft",
        "leather_horse_armor",
        "diamond_horse_armor",
        "iron_door",
        "bee_nest",
    ]
    for n in must_have:
        checks.append((f"has {n}", 0 if n in rows else 1, n in rows))

    ok = True
    for label, val, passed in checks:
        mark = "OK" if passed else "FAIL"
        if not passed:
            ok = False
        lines.append(f"  [{mark}] {label}: {val}")

    txt = BASE / "03_对比报告" / "铜器时代补齐与循环修复.txt"
    txt.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    if not ok:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
