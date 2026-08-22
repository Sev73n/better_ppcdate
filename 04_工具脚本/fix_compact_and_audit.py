# -*- coding: utf-8 -*-
"""Restore compact-block prices (per-item, do not divide by count), then audit gaps/arb."""
from __future__ import annotations

import base64
import csv
import json
import zlib
from collections import defaultdict
from pathlib import Path

BASE = Path(r"C:/Users/AI10/Desktop/ppcdata")
CFG = BASE / "01_配置明文" / "最终配置_rebuilt.json"
SELL = 0.625
PREMIUM = 1.1

# 仅回写曾被「买价/count」误伤的压缩块
FIX_COMPACT = [
    ("diamond_block", "diamond", 9),
    ("emerald_block", "emerald", 9),
    ("gold_block", "gold_ingot", 9),
    ("iron_block", "iron_ingot", 9),
    ("coal_block", "coal", 9),
    ("lapis_block", "lapis_lazuli", 9),
    ("redstone_block", "redstone", 9),
    ("copper_block", "copper_ingot", 9),
    ("netherite_block", "netherite_ingot", 9),
    ("raw_iron_block", "raw_iron", 9),
    ("raw_gold_block", "raw_gold", 9),
    ("raw_copper_block", "raw_copper", 9),
    ("slime_block", "slime_ball", 9),
    ("quartz_block", "quartz", 4),
    ("amethyst_block", "amethyst_shard", 4),
    ("honey_block", "honey_bottle", 4),
]

# 审计用：可逆压缩/合成
AUDIT_COMPACT = FIX_COMPACT + [
    ("hay_block", "wheat", 9),
    ("bone_block", "bone_meal", 9),
    ("dried_kelp_block", "dried_kelp", 9),
    ("honeycomb_block", "honeycomb", 4),
    ("snow", "snowball", 4),
    ("clay", "clay_ball", 4),
    ("bricks", "brick", 4),
    ("nether_brick", "netherbrick", 4),
    ("glowstone", "glowstone_dust", 4),
    ("magma", "magma_cream", 4),
    ("melon_block", "melon", 9),
    ("prismarine", "prismarine_shard", 4),
]


def r2(x):
    return round(float(x) + 1e-12, 2)


def sell_of(buy):
    s = r2(buy * SELL)
    if s >= buy and buy > 0:
        s = r2(buy - 0.01) if buy > 0.01 else 0.0
    return s


def load_cfg():
    return json.loads(CFG.read_text(encoding="utf-8"))


def index_mc(data):
    rev = {str(v): k for k, v in data["nameSpaceMap"].items()}
    rows = {}
    dups = defaultdict(list)
    for r in data["systemShopItems"]:
        pref, name = r[0]["NIN"].split(":", 1)
        ns = rev.get(pref, pref)
        if ns != "minecraft":
            continue
        dur = r[0].get("durability", 0)
        key = (name, dur)
        dups[name].append(r)
        rows[key] = r
        rows.setdefault(name, r)
    return rows, dups, rev


def first(rows, *names):
    for n in names:
        if n in rows:
            return n, rows[n]
    return None, None


def buy_of(row):
    return float(row[1])


def sellp(row):
    return float(row[2])


def fix_compact(data):
    rows, _, _ = index_mc(data)
    report = []
    for block, ing, n in FIX_COMPACT:
        bname, br = first(rows, block, "brick_block" if block == "bricks" else "", "magma_block" if block == "magma" else "")
        iname, ir = first(rows, ing, "nether_brick" if ing == "netherbrick" else "")
        if not br or not ir:
            report.append((block, ing, None, None, "skip_missing"))
            continue
        old = buy_of(br)
        new = r2(n * buy_of(ir) * PREMIUM)
        br[1] = new
        br[2] = sell_of(new)
        report.append((bname, iname, old, new, f"{n}x{buy_of(ir)}x{PREMIUM}"))
    return report


def write_share(data):
    CFG.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    share = "ppcpdata%" + base64.b64encode(
        zlib.compress(json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode(), 9)
    ).decode()
    (BASE / "分享码.txt").write_text(share, encoding="utf-8")
    (BASE / "05_原始备份" / "最终分享串_副本.txt").write_text(share, encoding="utf-8")
    return len(share)


def catalog_missing():
    colors = [
        "white", "orange", "magenta", "light_blue", "yellow", "lime", "pink",
        "gray", "light_gray", "cyan", "purple", "blue", "brown", "green", "red", "black",
    ]
    woods = [
        "oak", "spruce", "birch", "jungle", "acacia", "dark_oak",
        "mangrove", "cherry", "pale_oak", "bamboo", "crimson", "warped",
    ]
    cat = defaultdict(list)

    def add(group, *names):
        cat[group].extend(names)

    for c in colors:
        add(
            "彩色方块",
            f"{c}_wool", f"{c}_carpet", f"{c}_concrete", f"{c}_concrete_powder",
            f"{c}_terracotta", f"{c}_glazed_terracotta", f"{c}_stained_glass",
            f"{c}_stained_glass_pane", f"{c}_bed", f"{c}_candle", f"{c}_shulker_box",
            f"{c}_banner", f"{c}_dye",
        )
    add("彩色方块", "terracotta", "glass", "glass_pane", "candle", "shulker_box")

    for w in woods:
        add(
            "木材",
            f"{w}_planks", f"{w}_stairs", f"{w}_slab", f"{w}_fence", f"{w}_fence_gate",
            f"{w}_door", f"{w}_trapdoor", f"{w}_button", f"{w}_pressure_plate",
            f"{w}_sign", f"{w}_hanging_sign", f"{w}_shelf",
        )
        if w not in ("crimson", "warped", "bamboo"):
            add("木材", f"{w}_log", f"{w}_wood", f"stripped_{w}_log", f"stripped_{w}_wood", f"{w}_leaves", f"{w}_sapling")
            add("船", f"{w}_boat", f"{w}_chest_boat")
        if w in ("crimson", "warped"):
            add("木材", f"{w}_stem", f"stripped_{w}_stem", f"{w}_hyphae", f"stripped_{w}_hyphae", f"{w}_nylium", f"{w}_fungus", f"{w}_roots")
    add("木材", "bamboo_block", "bamboo_mosaic", "bamboo_mosaic_stairs", "bamboo_mosaic_slab", "stripped_bamboo_block")

    add(
        "1.21试炼风潮",
        "mace", "breeze_rod", "wind_charge", "heavy_core",
        "trial_key", "ominous_trial_key", "ominous_bottle",
        "bolt_armor_trim_smithing_template", "flow_armor_trim_smithing_template",
        "flow_banner_pattern", "guster_banner_pattern",
        "flow_pottery_sherd", "guster_pottery_sherd", "scrape_pottery_sherd",
        "crafter", "vault", "trial_spawner", "ominous_bottle",
        "copper_bulb", "copper_grate", "copper_door", "copper_trapdoor",
        "chiseled_copper", "exposed_copper_bulb", "weathered_copper_bulb", "oxidized_copper_bulb",
        "waxed_copper_bulb", "tuff_bricks", "chiseled_tuff", "chiseled_tuff_bricks",
        "polished_tuff", "tuff_stairs", "tuff_slab", "tuff_wall",
        "polished_tuff_stairs", "polished_tuff_slab", "polished_tuff_wall",
        "tuff_brick_stairs", "tuff_brick_slab", "tuff_brick_wall",
    )
    add(
        "1.21.4苍白花园",
        "pale_oak_log", "pale_oak_wood", "stripped_pale_oak_log", "stripped_pale_oak_wood",
        "pale_oak_planks", "pale_oak_stairs", "pale_oak_slab", "pale_oak_fence",
        "pale_oak_fence_gate", "pale_oak_door", "pale_oak_trapdoor", "pale_oak_button",
        "pale_oak_pressure_plate", "pale_oak_sign", "pale_oak_hanging_sign",
        "pale_oak_leaves", "pale_oak_sapling", "pale_oak_boat", "pale_oak_chest_boat",
        "pale_moss_block", "pale_moss_carpet", "pale_hanging_moss",
        "closed_eyeblossom", "open_eyeblossom", "creaking_heart",
        "resin_clump", "resin_brick", "resin_bricks", "chiseled_resin_bricks",
        "resin_brick_stairs", "resin_brick_slab", "resin_brick_wall",
        "creaking_spawn_egg",
    )
    add(
        "1.21.6+新内容",
        "dried_ghast", "happy_ghast_spawn_egg", "harness",
        "white_harness", "orange_harness", "magenta_harness", "light_blue_harness",
        "yellow_harness", "lime_harness", "pink_harness", "gray_harness",
        "light_gray_harness", "cyan_harness", "purple_harness", "blue_harness",
        "brown_harness", "green_harness", "red_harness", "black_harness",
        "bundle", "white_bundle", "black_bundle",
        "leaf_litter", "wildflowers", "firefly_bush", "bush",
        "cactus_flower", "short_dry_grass", "tall_dry_grass",
        "copper_golem_spawn_egg", "copper_chest", "copper_golem_statue",
    )
    add(
        "唱片",
        "music_disc_13", "music_disc_cat", "music_disc_blocks", "music_disc_chirp",
        "music_disc_far", "music_disc_mall", "music_disc_mellohi", "music_disc_stal",
        "music_disc_strad", "music_disc_ward", "music_disc_11", "music_disc_wait",
        "music_disc_otherside", "music_disc_5", "music_disc_pigstep",
        "music_disc_relic", "music_disc_creator", "music_disc_creator_music_box",
        "music_disc_precipice", "music_disc_tears", "disc_fragment_5",
    )
    add(
        "收藏与装备附件",
        "netherite_upgrade_smithing_template",
        "wolf_armor", "armadillo_scute", "armadillo_spawn_egg",
        "sniffer_egg", "torchflower", "torchflower_seeds", "pitcher_plant", "pitcher_pod",
        "goat_horn", "echo_shard", "recovery_compass", "spyglass",
        "brush", "decorated_pot", "decorated_pot_sherd",
        "ominous_bottle", "trial_key",
        "elytra", "dragon_egg", "nether_star", "heart_of_the_sea",
        "totem_of_undying", "enchanted_golden_apple",
        "trident", "saddle", "name_tag", "lead",
        "writable_book", "written_book", "map", "empty_map", "filled_map",
        "firework_rocket", "firework_star",
        "experience_bottle", "enchanted_book",
    )
    add(
        "常用生存漏项",
        "bundle", "ominous_bottle", "wind_charge", "breeze_rod",
        "wolf_armor", "armadillo_scute",
        "goat_horn", "sniffer_egg",
        "ominous_trial_key", "trial_key",
        "resin_clump", "resin_brick",
        "pale_moss_block", "creaking_heart",
        "dried_ghast",
        "copper_nugget",
        "iron_nugget", "gold_nugget",
        "netherite_scrap", "netherite_ingot",
        "ancient_debris",
        "lodestone", "respawn_anchor", "crying_obsidian",
        "end_crystal", "ender_chest",
        "shulker_shell", "shulker_box",
        "beacon", "conduit",
        "turtle_scute", "turtle_helmet",
        "phantom_membrane",
        "honey_bottle", "honeycomb", "honey_block", "beehive", "bee_nest",
        "suspicious_stew", "rabbit_stew",
        "mushroom_stew", "beetroot_soup",
        "cake", "pumpkin_pie",
        "fermented_spider_eye", "blaze_powder", "magma_cream",
        "glistering_melon_slice", "golden_carrot", "golden_apple",
        "ender_eye",
        "fire_charge", "fireball",
        "snowball", "egg", "ender_pearl",
        "ink_sac", "glow_ink_sac",
        "bone_meal", "bone",
        "wheat_seeds", "pumpkin_seeds", "melon_seeds", "beetroot_seeds",
        "cocoa_beans", "nether_wart",
        "kelp", "dried_kelp", "seagrass", "sea_pickle",
        "lily_pad", "vine", "glow_berries", "sweet_berries",
        "chorus_fruit", "popped_chorus_fruit", "chorus_flower", "chorus_plant",
        "sculk", "sculk_vein", "sculk_catalyst", "sculk_shrieker", "sculk_sensor",
        "calibrated_sculk_sensor",
        "froglight", "ochre_froglight", "pearlescent_froglight", "verdant_froglight",
        "pearlescent_froglight",
        "sponge", "wet_sponge",
        "tinted_glass",
        "obsidian", "crying_obsidian",
        "budding_amethyst", "amethyst_cluster",
        "small_amethyst_bud", "medium_amethyst_bud", "large_amethyst_bud",
        "pointed_dripstone",
        "cobweb", "string",
        "ice", "packed_ice", "blue_ice", "snow_block", "snow_layer",
        "dirt", "grass_block", "podzol", "mycelium", "dirt_with_roots", "rooted_dirt",
        "farmland", "dirt_path", "grass_path",
        "composter", "cauldron", "bell", "lantern", "soul_lantern",
        "campfire", "soul_campfire", "torch", "soul_torch",
        "crafting_table", "furnace", "blast_furnace", "smoker",
        "cartography_table", "fletching_table", "smithing_table", "loom",
        "grindstone", "stonecutter", "anvil", "chipped_anvil", "damaged_anvil",
        "enchanting_table", "bookshelf", "chiseled_bookshelf",
        "lectern", "jukebox", "note_block",
        "chest", "trapped_chest", "barrel", "ender_chest",
        "hopper", "dropper", "dispenser",
        "piston", "sticky_piston", "observer", "target",
        "redstone", "redstone_torch", "redstone_block", "redstone_lamp",
        "repeater", "comparator", "daylight_detector", "tripwire_hook",
        "lever", "tripwire",
        "tnt", "gunpowder",
        "bucket", "water_bucket", "lava_bucket", "milk_bucket", "powder_snow_bucket",
        "cod_bucket", "salmon_bucket", "tropical_fish_bucket", "pufferfish_bucket",
        "axolotl_bucket", "tadpole_bucket",
        "item.brewing_stand", "brewing_stand", "cauldron",
        "flower_pot", "item_frame", "glow_item_frame", "painting", "armor_stand",
        "oak_hanging_sign",
    )
    return cat


ALIASES = {
    "bricks": ["brick_block"],
    "brick_block": ["bricks"],
    "magma": ["magma_block"],
    "magma_block": ["magma"],
    "end_stone_bricks": ["end_bricks"],
    "end_bricks": ["end_stone_bricks"],
    "melon_block": ["melon"],
    "snow": ["snow_block"],
    "snow_block": ["snow"],
    "lily_pad": ["waterlily"],
    "sugar_cane": ["reeds"],
    "note_block": ["noteblock"],
    "grass_path": ["dirt_path"],
    "dirt_path": ["grass_path"],
    "rooted_dirt": ["dirt_with_roots"],
    "scute": ["turtle_scute"],
    "turtle_scute": ["scute"],
    "empty_map": ["map"],
    "map": ["empty_map"],
    "netherbrick": ["nether_brick"],
}


def present(have, name):
    if name in have:
        return True
    for a in ALIASES.get(name, []):
        if a in have:
            return True
    return False


def audit(data):
    rows, dups, _ = index_mc(data)
    have = set()
    for r in data["systemShopItems"]:
        pref, name = r[0]["NIN"].split(":", 1)
        if pref == "0" or True:
            pass
    rev = {str(v): k for k, v in data["nameSpaceMap"].items()}
    for r in data["systemShopItems"]:
        pref, name = r[0]["NIN"].split(":", 1)
        if rev.get(pref) == "minecraft":
            have.add(name)

    missing = []
    for group, names in catalog_missing().items():
        miss = sorted({n for n in names if not present(have, n)})
        if miss:
            missing.append((group, miss))

    # conversion arb
    extra_pairs = [
        ("iron_ingot", "iron_nugget", 9),
        ("gold_ingot", "gold_nugget", 9),
        ("copper_ingot", "copper_nugget", 9),
        ("netherite_ingot", "netherite_scrap", 4),  # 4 scrap + 4 gold, approx scrap side
        ("honeycomb_block", "honeycomb", 4),
        ("hay_block", "wheat", 9),
        ("bone_block", "bone_meal", 9),
        ("dried_kelp_block", "dried_kelp", 9),
        ("glowstone", "glowstone_dust", 4),
        ("clay", "clay_ball", 4),
        ("bricks", "brick", 4),
        ("snow", "snowball", 4),
        ("melon_block", "melon", 9),
        ("prismarine", "prismarine_shard", 4),
        ("sandstone", "sand", 4),
        ("red_sandstone", "red_sand", 4),
        ("quartz_block", "quartz", 4),
        ("wool", "string", 4),  # 4 string -> 1 wool
        ("packed_ice", "ice", 9),
        ("blue_ice", "packed_ice", 9),
        ("slime_block", "slime_ball", 9),
    ]
    arb = []
    for block, ing, n in AUDIT_COMPACT + extra_pairs:
        bname, br = first(rows, block, *ALIASES.get(block, []))
        iname, ir = first(rows, ing, *ALIASES.get(ing, []))
        if not br or not ir:
            continue
        bb, bs, ib, ise = buy_of(br), sellp(br), buy_of(ir), sellp(ir)
        uncraft = r2(n * ise - bb)
        craft = r2(bs - n * ib)
        if uncraft > 0.05 or craft > 0.05:
            arb.append({
                "kind": "compact",
                "out": bname,
                "out_buy": bb,
                "out_sell": bs,
                "ing": iname,
                "ing_buy": ib,
                "ing_sell": ise,
                "n": n,
                "uncraft_profit": uncraft,
                "craft_profit": craft,
            })

    # 2 slabs <-> 1 block
    slab_pairs = []
    for name in have:
        if name.endswith("_slab"):
            base = name[: -len("_slab")]
            for cand in (base, f"{base}s", f"{base}_planks", f"{base}_block", "bricks" if base == "brick" else base):
                if cand in rows:
                    slab_pairs.append((cand, name))
                    break
    slab_arb = []
    seen = set()
    for block, slab in slab_pairs:
        if (block, slab) in seen:
            continue
        seen.add((block, slab))
        br, sr = rows[block], rows[slab]
        # 1 block -> 2 slabs
        uncraft = r2(2 * sellp(sr) - buy_of(br))
        craft = r2(buy_of(br) and (sellp(br) - 2 * buy_of(sr)))
        if uncraft > 0.05 or craft > 0.05:
            slab_arb.append({
                "block": block,
                "block_buy": buy_of(br),
                "block_sell": sellp(br),
                "slab": slab,
                "slab_buy": buy_of(sr),
                "slab_sell": sellp(sr),
                "block_to_2slabs": uncraft,
                "2slabs_to_block": r2(sellp(br) - 2 * buy_of(sr)),
            })

    # stairs: 4 blocks -> 6 stairs, reverse ~4 stairs -> 3 blocks
    stair_arb = []
    for name in have:
        if not name.endswith("_stairs"):
            continue
        base = name[: -len("_stairs")]
        bname, br = first(rows, base, f"{base}_planks", f"{base}s")
        if not br:
            continue
        sr = rows[name]
        # buy 4 blocks, make 6 stairs, sell
        craft = r2(6 * sellp(sr) - 4 * buy_of(br))
        # buy 4 stairs (~3 blocks), sell 3 blocks
        revp = r2(3 * sellp(br) - 4 * buy_of(sr))
        if craft > 0.5 or revp > 0.5:
            stair_arb.append({
                "block": bname,
                "stairs": name,
                "block_buy": buy_of(br),
                "stair_buy": buy_of(sr),
                "four_block_to_six_stair": craft,
                "four_stair_to_three_block": revp,
            })

    # tools / armor vs mats
    recipes = [
        ("diamond_pickaxe", [("diamond", 3)], 1.08),
        ("diamond_axe", [("diamond", 3)], 1.08),
        ("diamond_sword", [("diamond", 2)], 1.12),
        ("diamond_hoe", [("diamond", 2)], 1.12),
        ("diamond_shovel", [("diamond", 1)], 1.25),
        ("diamond_helmet", [("diamond", 5)], 1.0),
        ("diamond_chestplate", [("diamond", 8)], 1.0),
        ("diamond_leggings", [("diamond", 7)], 1.0),
        ("diamond_boots", [("diamond", 4)], 1.0),
        ("iron_pickaxe", [("iron_ingot", 3)], 1.11),
        ("iron_chestplate", [("iron_ingot", 8)], 1.11),
        ("golden_chestplate", [("gold_ingot", 8)], 0.78),
        ("golden_pickaxe", [("gold_ingot", 3)], 0.7),
        ("netherite_ingot", [("netherite_scrap", 4), ("gold_ingot", 4)], 1.0),
        ("netherite_chestplate", [("netherite_ingot", 1), ("diamond_chestplate", 1)], 1.0),
        ("hopper", [("iron_ingot", 5), ("chest", 1)], 1.0),
        ("golden_apple", [("gold_ingot", 8), ("apple", 1)], 1.0),
        ("golden_carrot", [("gold_nugget", 8), ("carrot", 1)], 1.0),
        ("ender_eye", [("ender_pearl", 1), ("blaze_powder", 1)], 1.0),
        ("blaze_powder", [("blaze_rod", 1)], 0.5),  # 1 rod -> 2 powder
        ("end_crystal", [("glass", 7), ("ender_eye", 1), ("ghast_tear", 1)], 1.0),
        ("fire_charge", [("gunpowder", 1), ("blaze_powder", 1), ("coal", 1)], 1.0),
        ("bookshelf", [("book", 3), ("oak_planks", 6)], 1.0),
        ("enchanting_table", [("diamond", 2), ("obsidian", 4), ("book", 1)], 1.0),
        ("anvil", [("iron_block", 3), ("iron_ingot", 4)], 1.0),
        ("sticky_piston", [("piston", 1), ("slime_ball", 1)], 1.0),
        ("tnt", [("gunpowder", 5), ("sand", 4)], 1.0),
        ("beacon", [("nether_star", 1), ("obsidian", 3), ("glass", 5)], 1.0),
        ("elytra", [], 1.0),
    ]
    recipe_issues = []
    for out, ings, expect_ratio in recipes:
        if out not in rows:
            continue
        mat = 0.0
        ok = True
        parts = []
        for nm, q in ings:
            if nm not in rows:
                ok = False
                break
            mat += q * buy_of(rows[nm])
            parts.append(f"{q}x{nm}")
        if not ok or mat <= 0:
            continue
        ob = buy_of(rows[out])
        ratio = ob / mat
        # shop-arb: buy output, not relevant; buy mats craft sell output
        craft_sell = r2(sellp(rows[out]) - mat)
        # buy output cheaper than mats (undercut) — not shop loop unless uncraftable
        if craft_sell > 0.05 or ratio < 0.85 or ratio > 1.6:
            recipe_issues.append({
                "item": out,
                "buy": ob,
                "sell": sellp(rows[out]),
                "mat": r2(mat),
                "ratio": r2(ratio),
                "craft_sell_profit": craft_sell,
                "recipe": "+".join(parts),
            })

    sell_ge_buy = []
    for name, r in list(rows.items()):
        if not isinstance(name, str):
            continue
        if buy_of(r) > 0 and sellp(r) + 1e-9 >= buy_of(r):
            sell_ge_buy.append((name, buy_of(r), sellp(r)))

    # user-ish collectibles vs diamond/emerald anchors
    collect = []
    for name in sorted(have):
        if any(x in name for x in (
            "banner_pattern", "armor_trim", "pottery_sherd", "music_disc",
            "skull", "_head", "smithing_template",
        )):
            r = rows[name]
            collect.append((name, buy_of(r), sellp(r), r[6]))

    return {
        "have_mc": len(have),
        "missing": missing,
        "arb": arb,
        "slab_arb": sorted(slab_arb, key=lambda x: -max(x["block_to_2slabs"], x["2slabs_to_block"])),
        "stair_arb": sorted(stair_arb, key=lambda x: -max(x["four_block_to_six_stair"], x["four_stair_to_three_block"])),
        "recipe_issues": recipe_issues,
        "sell_ge_buy": sell_ge_buy,
        "collect": collect,
        "have": have,
    }


def main():
    data = load_cfg()
    fix_rep = fix_compact(data)
    share_len = write_share(data)

    # re-audit after write
    data = load_cfg()
    au = audit(data)

    out_fix = BASE / "03_对比报告" / "压缩块单价修复.csv"
    with open(out_fix, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["block", "ing", "old_buy", "new_buy", "note"])
        w.writerows(fix_rep)

    lines = []
    lines.append("商店审计（压缩块修复后）")
    lines.append("=" * 48)
    lines.append(f"原版条目: {au['have_mc']}")
    lines.append("")
    lines.append("【压缩块修复】")
    for block, ing, old, new, note in fix_rep:
        if old is None:
            lines.append(f"  skip {block}/{ing} {note}")
        else:
            flag = "  " if abs(old - new) < 0.02 else " *"
            lines.append(f"{flag}{block:24} {old:10.2f} -> {new:10.2f}  ({note})")
    lines.append("")
    lines.append("【仍存在的压缩/合成套利】")
    if not au["arb"]:
        lines.append("  无")
    for a in au["arb"]:
        bits = []
        if a["uncraft_profit"] > 0.05:
            bits.append(f"拆开卖赚{a['uncraft_profit']}")
        if a["craft_profit"] > 0.05:
            bits.append(f"合成卖赚{a['craft_profit']}")
        lines.append(
            f"  {a['out']:22} buy={a['out_buy']}  {a['n']}x{a['ing']} buy={a['ing_buy']} sell={a['ing_sell']}  {', '.join(bits)}"
        )
    lines.append("")
    lines.append("【台阶套利 top】")
    for a in au["slab_arb"][:25]:
        lines.append(
            f"  {a['block']:28} {a['slab']:28} 块→2台阶={a['block_to_2slabs']}  2台阶→块={a['2slabs_to_block']}"
        )
    lines.append("")
    lines.append("【楼梯套利 top】")
    for a in au["stair_arb"][:20]:
        lines.append(
            f"  {a['block']:24} {a['stairs']:28} 4块→6梯={a['four_block_to_six_stair']}  4梯→3块={a['four_stair_to_three_block']}"
        )
    lines.append("")
    lines.append("【配方比例异常】")
    for a in au["recipe_issues"]:
        lines.append(
            f"  {a['item']:24} buy={a['buy']} mat={a['mat']} ratio={a['ratio']} craft卖={a['craft_sell_profit']}  {a['recipe']}"
        )
    lines.append("")
    lines.append("【卖价>=买价】")
    for name, b, s in au["sell_ge_buy"]:
        lines.append(f"  {name} buy={b} sell={s}")
    lines.append("")
    lines.append("【疑似遗漏】")
    for group, miss in au["missing"]:
        lines.append(f"  {group}: {len(miss)}")
        for i in range(0, len(miss), 6):
            lines.append("    " + ", ".join(miss[i : i + 6]))
    lines.append("")
    lines.append("【收藏/纹饰/唱片现价】")
    for name, b, s, tag in au["collect"]:
        lines.append(f"  {name:48} buy={b:8.2f} sell={s:8.2f} {tag}")

    out_txt = BASE / "03_对比报告" / "修复后全量审计.txt"
    out_txt.write_text("\n".join(lines), encoding="utf-8")
    print(f"share_len={share_len} fix={len(fix_rep)} arb_left={len(au['arb'])} missing_groups={len(au['missing'])}")
    print(out_txt)


if __name__ == "__main__":
    main()
