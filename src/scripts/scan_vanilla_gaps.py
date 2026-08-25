# -*- coding: utf-8 -*-
"""Scan current share for missing common vanilla items."""
import base64
import json
import zlib
from pathlib import Path

SHARE = Path(r"C:/Users/AI10/Desktop/ppcdata/分享码.txt")
OUT = Path(r"C:/Users/AI10/Desktop/ppcdata/03_对比报告/原版缺口扫描.txt")

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
WOODS = [
    "oak",
    "spruce",
    "birch",
    "jungle",
    "acacia",
    "dark_oak",
    "mangrove",
    "cherry",
    "pale_oak",
    "bamboo",
    "crimson",
    "warped",
]


def load(p: Path):
    t = p.read_text(encoding="utf-8").strip()
    if t.startswith("ppcpdata%"):
        return json.loads(zlib.decompress(base64.b64decode(t.split("%", 1)[1])))
    return json.loads(t)


def add(catalog, cat, *names):
    catalog.setdefault(cat, set()).update(names)


def build_catalog():
    catalog = {}
    for c in COLORS:
        add(
            catalog,
            "彩色方块(毛毯玻砼陶床烛潜影)",
            f"{c}_wool",
            f"{c}_carpet",
            f"{c}_concrete",
            f"{c}_concrete_powder",
            f"{c}_terracotta",
            f"{c}_glazed_terracotta",
            f"{c}_stained_glass",
            f"{c}_stained_glass_pane",
            f"{c}_bed",
            f"{c}_candle",
            f"{c}_shulker_box",
            f"{c}_banner",
        )
    add(
        catalog,
        "彩色方块(毛毯玻砼陶床烛潜影)",
        "terracotta",
        "glass",
        "glass_pane",
        "tinted_glass",
    )

    for w in WOODS:
        add(
            catalog,
            "木材家族",
            f"{w}_planks",
            f"{w}_stairs",
            f"{w}_slab",
            f"{w}_fence",
            f"{w}_fence_gate",
            f"{w}_door",
            f"{w}_trapdoor",
            f"{w}_button",
            f"{w}_pressure_plate",
            f"{w}_sign",
            f"{w}_hanging_sign",
        )
        if w not in ("crimson", "warped", "bamboo"):
            add(
                catalog,
                "木材家族",
                f"{w}_log",
                f"{w}_wood",
                f"stripped_{w}_log",
                f"stripped_{w}_wood",
                f"{w}_leaves",
                f"{w}_sapling",
            )
        if w in ("crimson", "warped"):
            add(
                catalog,
                "木材家族",
                f"{w}_stem",
                f"stripped_{w}_stem",
                f"{w}_hyphae",
                f"stripped_{w}_hyphae",
                f"{w}_nylium",
                f"{w}_fungus",
                f"{w}_roots",
            )
    add(
        catalog,
        "木材家族",
        "nether_wart_block",
        "warped_wart_block",
        "bamboo_block",
        "bamboo_mosaic",
        "bamboo_mosaic_stairs",
        "bamboo_mosaic_slab",
    )

    for w in [
        "oak",
        "spruce",
        "birch",
        "jungle",
        "acacia",
        "dark_oak",
        "mangrove",
        "cherry",
        "pale_oak",
    ]:
        add(catalog, "船与铁轨", f"{w}_boat", f"{w}_chest_boat")
    add(
        catalog,
        "船与铁轨",
        "rail",
        "powered_rail",
        "detector_rail",
        "activator_rail",
        "minecart",
        "chest_minecart",
        "hopper_minecart",
        "tnt_minecart",
        "furnace_minecart",
        "saddle",
    )

    add(
        catalog,
        "石材深板岩砂岩",
        "stone",
        "cobblestone",
        "mossy_cobblestone",
        "stone_bricks",
        "mossy_stone_bricks",
        "cracked_stone_bricks",
        "chiseled_stone_bricks",
        "smooth_stone",
        "stone_stairs",
        "cobblestone_stairs",
        "cobblestone_slab",
        "cobblestone_wall",
        "mossy_cobblestone_stairs",
        "mossy_cobblestone_slab",
        "mossy_cobblestone_wall",
        "stone_brick_stairs",
        "stone_brick_slab",
        "stone_brick_wall",
        "mossy_stone_brick_stairs",
        "mossy_stone_brick_slab",
        "mossy_stone_brick_wall",
        "andesite",
        "polished_andesite",
        "andesite_stairs",
        "andesite_slab",
        "andesite_wall",
        "polished_andesite_stairs",
        "polished_andesite_slab",
        "diorite",
        "polished_diorite",
        "diorite_stairs",
        "diorite_slab",
        "diorite_wall",
        "polished_diorite_stairs",
        "polished_diorite_slab",
        "granite",
        "polished_granite",
        "granite_stairs",
        "granite_slab",
        "granite_wall",
        "polished_granite_stairs",
        "polished_granite_slab",
        "deepslate",
        "cobbled_deepslate",
        "polished_deepslate",
        "deepslate_bricks",
        "deepslate_tiles",
        "chiseled_deepslate",
        "cracked_deepslate_bricks",
        "cracked_deepslate_tiles",
        "cobbled_deepslate_stairs",
        "cobbled_deepslate_slab",
        "cobbled_deepslate_wall",
        "polished_deepslate_stairs",
        "polished_deepslate_slab",
        "polished_deepslate_wall",
        "deepslate_brick_stairs",
        "deepslate_brick_slab",
        "deepslate_brick_wall",
        "deepslate_tile_stairs",
        "deepslate_tile_slab",
        "deepslate_tile_wall",
        "tuff",
        "polished_tuff",
        "tuff_bricks",
        "chiseled_tuff",
        "chiseled_tuff_bricks",
        "calcite",
        "dripstone_block",
        "sandstone",
        "smooth_sandstone",
        "cut_sandstone",
        "chiseled_sandstone",
        "sandstone_stairs",
        "sandstone_slab",
        "sandstone_wall",
        "red_sandstone",
        "smooth_red_sandstone",
        "cut_red_sandstone",
        "chiseled_red_sandstone",
        "red_sandstone_stairs",
        "red_sandstone_slab",
        "red_sandstone_wall",
        "prismarine",
        "prismarine_bricks",
        "dark_prismarine",
        "prismarine_stairs",
        "prismarine_slab",
        "prismarine_wall",
        "brick_block",
        "bricks",
        "brick_stairs",
        "brick_slab",
        "brick_wall",
        "mud_bricks",
        "mud_brick_stairs",
        "mud_brick_slab",
        "mud_brick_wall",
        "packed_mud",
        "mud",
    )

    add(
        catalog,
        "下界末地",
        "netherrack",
        "nether_brick",
        "red_nether_brick",
        "nether_brick_fence",
        "nether_brick_stairs",
        "nether_brick_slab",
        "nether_brick_wall",
        "red_nether_brick_stairs",
        "red_nether_brick_slab",
        "red_nether_brick_wall",
        "chiseled_nether_bricks",
        "cracked_nether_bricks",
        "basalt",
        "polished_basalt",
        "smooth_basalt",
        "blackstone",
        "gilded_blackstone",
        "polished_blackstone",
        "polished_blackstone_bricks",
        "chiseled_polished_blackstone",
        "cracked_polished_blackstone_bricks",
        "blackstone_stairs",
        "blackstone_slab",
        "blackstone_wall",
        "polished_blackstone_stairs",
        "polished_blackstone_slab",
        "polished_blackstone_wall",
        "polished_blackstone_brick_stairs",
        "polished_blackstone_brick_slab",
        "polished_blackstone_brick_wall",
        "soul_sand",
        "soul_soil",
        "magma",
        "magma_block",
        "glowstone",
        "shroomlight",
        "crying_obsidian",
        "respawn_anchor",
        "nether_gold_ore",
        "nether_quartz_ore",
        "ancient_debris",
        "end_stone",
        "end_stone_bricks",
        "end_bricks",
        "end_stone_brick_stairs",
        "end_brick_stairs",
        "end_stone_brick_slab",
        "end_stone_brick_wall",
        "end_rod",
        "purpur_block",
        "purpur_pillar",
        "purpur_stairs",
        "purpur_slab",
        "chorus_flower",
        "end_crystal",
        "ochre_froglight",
        "pearlescent_froglight",
        "verdant_froglight",
    )

    add(
        catalog,
        "铜家族",
        "copper_block",
        "cut_copper",
        "exposed_copper",
        "weathered_copper",
        "oxidized_copper",
        "exposed_cut_copper",
        "weathered_cut_copper",
        "oxidized_cut_copper",
        "waxed_copper",
        "waxed_cut_copper",
        "waxed_exposed_copper",
        "waxed_weathered_copper",
        "waxed_oxidized_copper",
        "cut_copper_stairs",
        "cut_copper_slab",
        "copper_bulb",
        "copper_door",
        "copper_trapdoor",
        "copper_grate",
        "chiseled_copper",
        "raw_copper_block",
    )

    add(
        catalog,
        "红石功能方块",
        "redstone_block",
        "redstone_torch",
        "redstone_lamp",
        "repeater",
        "comparator",
        "observer",
        "hopper",
        "dropper",
        "dispenser",
        "piston",
        "sticky_piston",
        "slime_block",
        "honey_block",
        "target",
        "lever",
        "tripwire_hook",
        "daylight_detector",
        "note_block",
        "lectern",
        "jukebox",
        "smithing_table",
        "fletching_table",
        "cartography_table",
        "loom",
        "composter",
        "barrel",
        "smoker",
        "blast_furnace",
        "furnace",
        "crafting_table",
        "enchanting_table",
        "anvil",
        "grindstone",
        "stonecutter",
        "cauldron",
        "bell",
        "beacon",
        "conduit",
        "lodestone",
        "scaffolding",
        "ladder",
        "iron_bars",
        "chain",
        "lantern",
        "soul_lantern",
        "torch",
        "soul_torch",
        "campfire",
        "soul_campfire",
        "bookshelf",
        "chiseled_bookshelf",
        "decorated_pot",
        "flower_pot",
        "painting",
        "item_frame",
        "glow_item_frame",
        "armor_stand",
        "chest",
        "trapped_chest",
        "ender_chest",
        "shulker_box",
        "lightning_rod",
        "crafter",
        "heavy_core",
        "mace",
    )

    add(
        catalog,
        "自然植物花冰雪",
        "grass_block",
        "dirt",
        "coarse_dirt",
        "rooted_dirt",
        "podzol",
        "mycelium",
        "dirt_path",
        "sand",
        "red_sand",
        "gravel",
        "clay",
        "ice",
        "packed_ice",
        "blue_ice",
        "snow",
        "cactus",
        "sugar_cane",
        "bamboo",
        "kelp",
        "dried_kelp_block",
        "sea_pickle",
        "lily_pad",
        "vine",
        "glow_lichen",
        "moss_block",
        "moss_carpet",
        "azalea",
        "flowering_azalea",
        "sponge",
        "wet_sponge",
        "cobweb",
        "obsidian",
        "amethyst_block",
        "amethyst_cluster",
        "budding_amethyst",
        "sculk",
        "sculk_vein",
        "sculk_catalyst",
        "sculk_shrieker",
        "sculk_sensor",
        "dandelion",
        "poppy",
        "blue_orchid",
        "allium",
        "azure_bluet",
        "oxeye_daisy",
        "cornflower",
        "lily_of_the_valley",
        "wither_rose",
        "sunflower",
        "lilac",
        "rose_bush",
        "peony",
        "brown_mushroom",
        "red_mushroom",
        "dead_bush",
        "fern",
        "large_fern",
        "short_grass",
        "tall_grass",
    )

    for c in ["tube", "brain", "bubble", "fire", "horn"]:
        add(
            catalog,
            "珊瑚",
            f"{c}_coral",
            f"{c}_coral_block",
            f"{c}_coral_fan",
            f"dead_{c}_coral",
            f"dead_{c}_coral_block",
            f"dead_{c}_coral_fan",
        )

    add(
        catalog,
        "石英铜矿杂块",
        "quartz_block",
        "smooth_quartz",
        "chiseled_quartz_block",
        "quartz_bricks",
        "quartz_pillar",
        "quartz_stairs",
        "quartz_slab",
        "smooth_quartz_stairs",
        "smooth_quartz_slab",
        "hay_block",
        "bone_block",
        "dried_kelp_block",
        "honeycomb_block",
        "magma_block",
    )
    return catalog


def main():
    data = load(SHARE)
    rev = {str(v): k for k, v in data["nameSpaceMap"].items()}
    have = set()
    for r in data["systemShopItems"]:
        pref, name = r[0]["NIN"].split(":", 1)
        if rev.get(pref) == "minecraft":
            have.add(name)

    catalog = build_catalog()
    lines = []
    lines.append(f"当前商店原版条目: {len(have)}")
    lines.append(f"end_rod 已有: {'end_rod' in have}")
    lines.append(f"end_bricks 已有: {'end_bricks' in have} | end_stone_bricks: {'end_stone_bricks' in have}")
    lines.append("")
    total_miss = 0
    for cat, names in sorted(catalog.items(), key=lambda x: -len([n for n in x[1] if n not in have])):
        miss = sorted(n for n in names if n not in have)
        ok = len(names) - len(miss)
        total_miss += len(miss)
        lines.append(f"【{cat}】缺 {len(miss)} / 清单{len(names)}（已有{ok}）")
        for i in range(0, len(miss), 6):
            lines.append("  " + ", ".join(miss[i : i + 6]))
        lines.append("")
    lines.append(f"清单内合计仍缺: {total_miss}")
    lines.append("")
    lines.append("说明: 清单=常见生存/建筑向，不是全量创造模式图鉴；")
    lines.append("网易基岩部分用旧名(end_bricks/magma/brick_block)，有任一别名即算覆盖。")

    # alias pairs: if either present, don't count both as missing for summary highlight
    aliases = [
        ("end_bricks", "end_stone_bricks"),
        ("end_brick_stairs", "end_stone_brick_stairs"),
        ("magma", "magma_block"),
        ("bricks", "brick_block"),
        ("note_block", "noteblock"),
        ("lily_pad", "waterlily"),
        ("sugar_cane", "reeds"),
        ("cobblestone_wall", "cobblestone_wall"),
    ]
    lines.append("")
    lines.append("别名互认检查:")
    for a, b in aliases:
        lines.append(f"  {a}={a in have} | {b}={b in have}")

    text = "\n".join(lines)
    OUT.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
