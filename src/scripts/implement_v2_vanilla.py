# -*- coding: utf-8 -*-
"""v2 锚点体系落地：只重算原版（minecraft）条目 + 全局常量（在线/开局/死亡）。

基线：20260824_09 → 输出 20260827_10
规则来源：docs/价格锚点方案_v2.md + 价格锚点方案_v2_补充草案.md（含 2026-08-27 拍板的 7 项）
- 买价锚：圆石 0.01/块｜钻石 10｜金 5｜绿宝石 1（只卖不回收）｜鞘翅 13140（保持）
- 回收分级：量产地板块 0.01/堆 固定｜连锁矿石/材料 5%｜不可连锁/合成/生肉/药水/附魔书 0.625｜绿宝石/刷怪蛋 0
- 工具/装备：max(材料×1.5, 阶梯地板)；金工具用地板值（金锭 5 但金工具垃圾）
- 建筑块：材料基底 × 形式系数（台阶0.55/楼梯1.5/墙1.2/栅栏1.2/栅栏门1.5/门2.5/活板门2.0/压力板0.5/按钮0.3）
- 刷怪蛋六档：200/600/1500/4000/8000/13140；mob_spawner=4000/sell0
- 耐久修复：crossbow 465、mace 500、wolf_armor 64、铜器时代族 190/锁链档
- 删坏行：item.brewing_stand、item.flower_pot；删重复蛋：vindication_illager/evocation_illager
- 补缺失：chorus_plant、thing_banner_pattern
用法：cd 到仓库根，python src/scripts/implement_v2_vanilla.py
"""
import json
import sys
import zlib
import base64
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))
from ppcp_lib import namespace_maps  # noqa: E402
SRC_JSON = ROOT / "data" / "decoded" / "20260824_09.json"
OUT_JSON = ROOT / "data" / "decoded" / "20260827_10.json"
OUT_TXT = ROOT / "releases" / "20260827_10.txt"
REPORT = ROOT / "reports" / "落地报告" / "08210.md"


def r2(x, floor=0.01):
    """四舍五入两位小数，最低 0.01。"""
    v = round(float(x) + 1e-12, 2)
    return max(floor, v)


# ================================================================ 定价表
# 类：bulk=量产地板回收(0.01/堆)｜ore=连锁矿石5%｜k625=0.625 回收｜zero=0 回收
BULK, ORE, K625, ZERO = "bulk", "ore", "k625", "zero"

# ---- 单块买价锚（含回收类）----
ANCHOR = {
    # 地板/量产地板块
    "cobblestone": (0.01, BULK), "stone": (0.01, BULK), "granite": (0.01, BULK),
    "diorite": (0.01, BULK), "andesite": (0.01, BULK), "dirt": (0.01, BULK),
    "coarse_dirt": (0.01, BULK), "rooted_dirt": (0.01, BULK), "grass_block": (0.01, BULK),
    "mycelium": (0.01, BULK), "podzol": (0.01, BULK), "dirt_path": (0.01, BULK),
    "farmland": (0.01, BULK), "sand": (0.01, BULK), "red_sand": (0.01, BULK),
    "gravel": (0.01, BULK), "netherrack": (0.01, BULK), "snow": (0.01, BULK),
    "snow_layer": (0.01, BULK), "mud": (0.01, BULK), "mossy_cobblestone": (0.02, BULK),
    "smooth_stone": (0.02, K625), "clay": (0.02, BULK), "clay_ball": (0.02, ORE),
    "soul_sand": (0.02, BULK), "soul_soil": (0.02, BULK), "basalt": (0.02, BULK),
    "polished_basalt": (0.03, K625), "smooth_basalt": (0.03, K625), "blackstone": (0.02, BULK),
    "cobbled_deepslate": (0.02, BULK), "deepslate": (0.03, BULK), "tuff": (0.02, BULK),
    "calcite": (0.03, BULK), "dripstone_block": (0.02, BULK), "pointed_dripstone": (0.02, BULK),
    "end_stone": (0.05, BULK), "packed_mud": (0.02, K625), "packed_ice": (0.05, BULK),
    "ice": (0.02, BULK), "blue_ice": (0.30, K625), "magma_block": (0.03, BULK),
    "obsidian": (0.50, BULK), "crying_obsidian": (10.0, K625), "glowstone": (0.60, K625),
    "sea_lantern": (0.60, K625), "shroomlight": (0.60, BULK), "amethyst_block": (1.20, K625),
    "budding_amethyst": (2.00, BULK), "nether_wart_block": (0.10, BULK), "warped_wart_block": (0.10, BULK),
    "crimson_nylium": (0.02, BULK), "warped_nylium": (0.02, BULK), "sponge": (0.50, K625),
    "wet_sponge": (0.45, K625), "hay_block": (0.09, K625), "slime_block": (1.80, K625),
    "honey_block": (2.60, K625), "honeycomb_block": (1.30, K625), "bone_block": (0.45, K625),
    "dried_kelp_block": (0.15, K625), "sculk": (0.02, BULK), "sculk_vein": (0.01, BULK),
    "suspicious_sand": (0.05, K625), "suspicious_gravel": (0.05, K625),
    "froglight": (0.60, K625), "ochre_froglight": (0.60, K625), "verdant_froglight": (0.60, K625),
    "pearlescent_froglight": (0.60, K625),
    # 矿石/矿物（ore 类 5% 回收）
    "coal": (0.50, ORE), "charcoal": (0.50, ORE), "coal_ore": (0.50, ORE),
    "deepslate_coal_ore": (0.50, ORE),
    "copper_ingot": (0.80, ORE), "copper_ore": (0.64, ORE), "deepslate_copper_ore": (0.64, ORE),
    "raw_copper": (0.68, ORE), "copper_nugget": (0.09, ORE),
    "iron_ingot": (1.00, ORE), "iron_ore": (0.80, ORE), "deepslate_iron_ore": (0.80, ORE),
    "raw_iron": (0.85, ORE), "iron_nugget": (0.11, ORE),
    "gold_ingot": (5.00, ORE), "gold_ore": (4.00, ORE), "deepslate_gold_ore": (4.00, ORE),
    "nether_gold_ore": (4.00, ORE), "raw_gold": (4.25, ORE), "gold_nugget": (0.56, ORE),
    "redstone": (2.00, ORE), "redstone_ore": (8.00, ORE), "deepslate_redstone_ore": (8.00, ORE),
    "lapis_lazuli": (2.50, ORE), "lapis_ore": (15.00, ORE), "deepslate_lapis_ore": (15.00, ORE),
    "diamond": (10.00, ORE), "diamond_ore": (10.00, ORE), "deepslate_diamond_ore": (10.00, ORE),
    "emerald": (1.00, ZERO), "emerald_ore": (1.00, ORE), "deepslate_emerald_ore": (1.00, ORE),
    "quartz": (0.15, ORE), "nether_quartz_ore": (0.15, ORE), "amethyst_shard": (0.25, ORE),
    "glowstone_dust": (0.15, ORE), "prismarine_shard": (0.10, ORE), "prismarine_crystals": (0.12, ORE),
    "flint": (0.05, ORE), "snowball": (0.01, ORE), "stick": (0.031, ORE),
    "nautilus_shell": (1.00, ORE), "heart_of_the_sea": (10.00, K625),
    "breeze_rod": (1.00, ORE), "wind_charge": (0.50, ORE), "heavy_core": (100.00, K625),
    "trial_key": (5.00, K625), "ominous_trial_key": (10.00, K625), "ominous_bottle": (2.00, K625),
    "echo_shard": (5.00, ORE), "disc_fragment_5": (10.00, K625), "goat_horn": (10.00, K625),
    "dragon_breath": (5.00, K625), "experience_bottle": (10.00, K625),
    # 木材/作物（连锁采集，ore 类 5%）
    "oak_log": (0.02, ORE), "spruce_log": (0.02, ORE), "birch_log": (0.02, ORE),
    "jungle_log": (0.02, ORE), "acacia_log": (0.02, ORE), "dark_oak_log": (0.02, ORE),
    "mangrove_log": (0.02, ORE), "cherry_log": (0.02, ORE), "bamboo_block": (0.02, ORE),
    "crimson_stem": (0.02, ORE), "warped_stem": (0.02, ORE),
    "wheat": (0.05, K625), "wheat_seeds": (0.02, K625), "carrot": (0.04, K625),
    "potato": (0.04, K625), "beetroot": (0.07, K625), "beetroot_seeds": (0.03, K625),
    "melon": (0.25, K625), "melon_slice": (0.03, K625), "melon_seeds": (0.02, K625),
    "pumpkin": (0.17, K625), "pumpkin_seeds": (0.02, K625), "sugar_cane": (0.03, ORE),
    "sugar": (0.02, K625), "bamboo": (0.01, ORE), "kelp": (0.02, ORE),
    "nether_wart": (0.045, ORE), "cocoa_beans": (0.05, ORE), "chorus_fruit": (0.05, ORE),
    "popped_chorus_fruit": (0.06, ORE), "chorus_flower": (0.05, K625), "chorus_plant": (0.05, BULK),
    "sweet_berries": (0.05, K625), "glow_berries": (0.10, K625), "apple": (0.25, K625),
    "torchflower": (0.03, K625), "torchflower_seeds": (0.02, K625), "pitcher_plant": (0.03, K625),
    "pitcher_pod": (0.02, K625), "pink_petals": (0.02, K625), "cactus": (0.02, ORE),
    "vine": (0.02, ORE), "lily_pad": (0.02, ORE), "sea_pickle": (0.05, ORE),
    "seagrass": (0.02, ORE), "fern": (0.02, ORE), "large_fern": (0.02, ORE),
    "tall_grass": (0.02, ORE), "short_grass": (0.01, ORE), "dead_bush": (0.02, ORE),
    "moss_block": (0.02, BULK), "moss_carpet": (0.02, K625), "glow_lichen": (0.02, ORE),
    "hanging_roots": (0.02, ORE), "spore_blossom": (0.10, K625),
    "big_dripleaf": (0.03, K625), "small_dripleaf": (0.03, K625),
    "mangrove_propagule": (0.05, K625), "mangrove_roots": (0.02, BULK),
    "muddy_mangrove_roots": (0.02, BULK), "azalea": (0.03, K625), "flowering_azalea": (0.03, K625),
    "crimson_fungus": (0.03, ORE), "warped_fungus": (0.03, ORE), "crimson_roots": (0.02, ORE),
    "warped_roots": (0.02, ORE), "weeping_vines": (0.02, ORE), "twisting_vines": (0.02, ORE),
    "nether_sprouts": (0.02, ORE), "brown_mushroom": (0.03, ORE), "red_mushroom": (0.03, ORE),
    "turtle_egg": (0.25, K625), "sniffer_egg": (0.50, K625), "frogspawn": (0.30, K625),
    # 掉落/材料
    "bone": (0.05, ORE), "bone_meal": (0.06, ORE), "gunpowder": (0.10, ORE),
    "string": (0.05, ORE), "spider_eye": (0.08, ORE), "fermented_spider_eye": (0.10, ORE),
    "rotten_flesh": (0.03, ORE), "ender_pearl": (4.00, ORE), "ender_eye": (6.00, K625),
    "blaze_rod": (2.00, ORE), "blaze_powder": (1.00, ORE), "ghast_tear": (5.00, ORE),
    "slime_ball": (0.20, ORE), "magma_cream": (0.50, ORE), "leather": (0.167, ORE),
    "feather": (0.03, ORE), "rabbit_hide": (0.11, ORE), "rabbit_foot": (0.50, ORE),
    "turtle_scute": (0.25, ORE), "armadillo_scute": (0.25, ORE), "phantom_membrane": (2.00, ORE),
    "shulker_shell": (8.00, ORE), "nether_star": (500.00, K625), "totem_of_undying": (100.00, K625),
    "ink_sac": (0.05, ORE), "glow_ink_sac": (0.10, ORE), "paper": (0.042, ORE),
    "book": (0.40, K625), "glass_bottle": (0.11, ORE), "egg": (0.02, K625),
    "fire_charge": (1.80, K625), "firework_rocket": (0.15, K625), "firework_star": (0.12, K625),
    "saddle": (6.00, K625), "name_tag": (20.00, K625), "lead": (0.20, K625),
    "water_bucket": (3.30, K625), "lava_bucket": (3.50, K625), "milk_bucket": (3.30, K625),
    "powder_snow_bucket": (3.35, K625), "bucket": (3.30, K625),
    "cod_bucket": (3.60, K625), "salmon_bucket": (3.60, K625), "pufferfish_bucket": (3.60, K625),
    "tropical_fish_bucket": (3.70, K625), "axolotl_bucket": (4.00, K625), "tadpole_bucket": (3.80, K625),
    "honey_bottle": (0.60, K625), "honeycomb": (0.30, ORE), "bee_nest": (0.50, K625),
    "beehive": (0.55, K625), "ladder": (0.07, K625), "scaffolding": (0.03, K625),
    "torch": (0.13, K625), "soul_torch": (0.15, K625), "lantern": (5.00, K625),
    "soul_lantern": (5.20, K625), "campfire": (0.70, K625), "soul_campfire": (0.75, K625),
    "chain": (1.30, K625), "end_rod": (2.20, K625), "iron_bars": (0.55, K625),
    # 食物
    "bread": (0.17, K625), "cake": (1.00, K625), "cookie": (0.17, K625),
    "pumpkin_pie": (0.25, K625), "golden_carrot": (4.50, K625), "glistering_melon_slice": (4.60, K625),
    "golden_apple": (42.00, K625), "enchanted_golden_apple": (400.00, K625),
    "mushroom_stew": (0.27, K625), "beetroot_soup": (1.35, K625), "rabbit_stew": (1.35, K625),
    "suspicious_stew": (0.50, K625), "baked_potato": (0.10, K625), "dried_kelp": (0.03, K625),
    "poisonous_potato": (0.02, ORE),
    "beef": (0.143, K625), "porkchop": (0.143, K625), "chicken": (0.143, K625),
    "mutton": (0.143, K625), "rabbit": (0.10, K625), "cod": (0.167, K625),
    "salmon": (0.167, K625), "tropical_fish": (0.10, K625), "pufferfish": (0.10, K625),
    "cooked_beef": (0.36, K625), "cooked_porkchop": (0.36, K625), "cooked_chicken": (0.36, K625),
    "cooked_mutton": (0.36, K625), "cooked_rabbit": (0.25, K625), "cooked_cod": (0.42, K625),
    "cooked_salmon": (0.42, K625),
    # 工具/武器（金工具用地板值，其余 = 材料×1.5）
    "wooden_sword": (0.30, K625), "wooden_pickaxe": (0.30, K625), "wooden_axe": (0.30, K625),
    "wooden_shovel": (0.30, K625), "wooden_hoe": (0.30, K625),
    "stone_sword": (0.50, K625), "stone_pickaxe": (0.50, K625), "stone_axe": (0.50, K625),
    "stone_shovel": (0.50, K625), "stone_hoe": (0.50, K625),
    "iron_sword": (3.00, K625), "iron_pickaxe": (4.50, K625), "iron_axe": (4.50, K625),
    "iron_shovel": (1.50, K625), "iron_hoe": (3.00, K625),
    "golden_sword": (5.00, K625), "golden_pickaxe": (7.50, K625), "golden_axe": (7.50, K625),
    "golden_shovel": (2.50, K625), "golden_hoe": (5.00, K625),
    "diamond_sword": (30.00, K625), "diamond_pickaxe": (45.00, K625), "diamond_axe": (45.00, K625),
    "diamond_shovel": (15.00, K625), "diamond_hoe": (30.00, K625),
    "copper_sword": (2.40, K625), "copper_pickaxe": (3.60, K625), "copper_axe": (3.60, K625),
    "copper_shovel": (1.20, K625), "copper_hoe": (2.40, K625),
    "bow": (0.30, K625), "crossbow": (2.00, K625), "fishing_rod": (0.25, K625),
    "shears": (2.20, K625), "flint_and_steel": (1.20, K625), "shield": (1.30, K625),
    "brush": (1.00, K625), "spyglass": (2.00, K625), "carrot_on_a_stick": (0.35, K625),
    "warped_fungus_on_a_stick": (0.35, K625), "trident": (150.00, K625), "mace": (110.00, K625),
    "arrow": (0.02, K625), "compass": (6.60, K625), "clock": (24.00, K625),
    "recovery_compass": (47.00, K625), "lodestone_compass": (4507.00, K625),
    "map": (7.20, K625), "empty_map": (0.40, K625),
    # 装备
    "leather_helmet": (1.00, K625), "leather_chestplate": (1.50, K625),
    "leather_leggings": (1.20, K625), "leather_boots": (0.80, K625),
    "chainmail_helmet": (15.00, K625), "chainmail_chestplate": (24.00, K625),
    "chainmail_leggings": (21.00, K625), "chainmail_boots": (12.00, K625),
    "iron_helmet": (7.50, K625), "iron_chestplate": (12.00, K625),
    "iron_leggings": (10.50, K625), "iron_boots": (6.00, K625),
    "golden_helmet": (37.50, K625), "golden_chestplate": (60.00, K625),
    "golden_leggings": (52.50, K625), "golden_boots": (30.00, K625),
    "diamond_helmet": (75.00, K625), "diamond_chestplate": (120.00, K625),
    "diamond_leggings": (105.00, K625), "diamond_boots": (60.00, K625),
    "copper_helmet": (6.00, K625), "copper_chestplate": (9.60, K625),
    "copper_leggings": (8.40, K625), "copper_boots": (4.80, K625),
    "turtle_helmet": (1.50, K625), "wolf_armor": (1.80, K625),
    "leather_horse_armor": (6.00, K625), "iron_horse_armor": (20.00, K625),
    "golden_horse_armor": (30.00, K625), "diamond_horse_armor": (80.00, K625),
    "copper_horse_armor": (14.00, K625),
    # 稀有/战利品
    "skeleton_skull": (50.00, K625), "wither_skeleton_skull": (300.00, K625),
    "dragon_head": (500.00, K625), "piglin_head": (80.00, K625),
    "zombie_head": (50.00, K625), "creeper_head": (50.00, K625), "player_head": (50.00, K625),
    "beacon": (550.00, K625), "conduit": (20.00, K625), "end_crystal": (11.50, K625),
    "respawn_anchor": (60.00, K625), "lodestone": (4500.00, K625),
    "mob_spawner": (4000.00, ZERO), "dragon_egg": (5000.00, K625),
    "elytra": (13140.00, K625),
    # 红石/机械
    "redstone_torch": (2.20, K625), "repeater": (7.00, K625), "comparator": (7.40, K625),
    "observer": (4.60, K625), "piston": (3.40, K625), "sticky_piston": (3.60, K625),
    "dispenser": (2.60, K625), "dropper": (2.30, K625), "hopper": (7.20, K625),
    "redstone_lamp": (9.00, K625), "redstone_block": (19.80, K625),
    "lever": (0.05, K625), "tripwire_hook": (0.60, K625), "target": (8.30, K625),
    "daylight_detector": (0.70, K625), "note_block": (2.10, K625), "jukebox": (10.10, K625),
    "tnt": (0.65, K625), "rail": (6.60, K625), "powered_rail": (34.00, K625),
    "activator_rail": (9.00, K625), "detector_rail": (8.80, K625),
    "minecart": (5.50, K625), "chest_minecart": (5.70, K625), "furnace_minecart": (5.80, K625),
    "hopper_minecart": (13.00, K625), "tnt_minecart": (6.20, K625),
    "sculk_sensor": (5.00, K625), "calibrated_sculk_sensor": (6.00, K625),
    "sculk_shrieker": (5.00, K625), "sculk_catalyst": (5.00, K625),
    "crafter": (11.50, K625), "copper_bulb": (6.50, K625), "lightning_rod": (2.60, K625),
    # 工作台/容器/装饰
    "crafting_table": (0.05, K625), "furnace": (0.10, K625), "blast_furnace": (5.70, K625),
    "smoker": (5.70, K625), "chest": (0.20, K625), "trapped_chest": (0.25, K625),
    "barrel": (0.15, K625), "bookshelf": (1.50, K625), "lectern": (1.60, K625),
    "enchanting_table": (24.00, K625), "anvil": (33.00, K625), "chipped_anvil": (25.00, K625),
    "damaged_anvil": (12.00, K625), "grindstone": (0.15, K625), "loom": (0.15, K625),
    "stonecutter": (1.10, K625), "smithing_table": (2.20, K625), "fletching_table": (0.15, K625),
    "cartography_table": (0.15, K625), "composter": (0.10, K625), "cauldron": (7.70, K625),
    "brewing_stand": (2.20, K625), "flower_pot": (0.10, K625), "decorated_pot": (0.50, K625),
    "bell": (36.00, K625), "item_frame": (0.50, K625), "glow_item_frame": (0.55, K625),
    "painting": (0.35, K625), "armor_stand": (0.30, K625), "jukebox": (10.10, K625),
    "ender_chest": (17.20, K625), "end_portal_frame": (50.00, K625),
    # 染料
    "white_dye": (0.05, K625), "black_dye": (0.05, K625), "red_dye": (0.05, K625),
    "green_dye": (0.05, K625), "brown_dye": (0.05, K625), "blue_dye": (0.10, K625),
    "purple_dye": (0.05, K625), "cyan_dye": (0.05, K625), "light_gray_dye": (0.05, K625),
    "gray_dye": (0.05, K625), "pink_dye": (0.05, K625), "lime_dye": (0.05, K625),
    "yellow_dye": (0.05, K625), "light_blue_dye": (0.05, K625), "magenta_dye": (0.05, K625),
    "orange_dye": (0.05, K625),
    # 花朵（k625，价格低）
    "dandelion": (0.02, K625), "poppy": (0.02, K625), "blue_orchid": (0.02, K625),
    "allium": (0.02, K625), "azure_bluet": (0.02, K625), "red_tulip": (0.02, K625),
    "orange_tulip": (0.02, K625), "white_tulip": (0.02, K625), "pink_tulip": (0.02, K625),
    "oxeye_daisy": (0.02, K625), "cornflower": (0.02, K625), "lily_of_the_valley": (0.02, K625),
    "wither_rose": (0.50, K625), "sunflower": (0.03, K625), "lilac": (0.03, K625),
    "rose_bush": (0.03, K625), "peony": (0.03, K625),
    # 音乐唱片（分档）
    "music_disc_13": (20.0, K625), "music_disc_cat": (20.0, K625),
    "music_disc_blocks": (20.0, K625), "music_disc_chirp": (20.0, K625),
    "music_disc_far": (20.0, K625), "music_disc_mall": (20.0, K625),
    "music_disc_mellohi": (20.0, K625), "music_disc_stal": (20.0, K625),
    "music_disc_strad": (20.0, K625), "music_disc_ward": (20.0, K625),
    "music_disc_11": (20.0, K625), "music_disc_wait": (20.0, K625),
    "music_disc_otherside": (60.0, K625), "music_disc_creator": (60.0, K625),
    "music_disc_creator_music_box": (60.0, K625), "music_disc_precipice": (60.0, K625),
    "music_disc_lava_chicken": (60.0, K625), "music_disc_tears": (60.0, K625),
    "music_disc_pigstep": (120.0, K625), "music_disc_relic": (120.0, K625),
    "music_disc_5": (120.0, K625),
    # 陶片/旗帜图案/锻造模板
    "thing_banner_pattern": (5.0, K625),
}

# 锻造模板（20~100 档）
for _t, _p in {"sentry": 20, "dune": 20, "coast": 20, "wild": 20, "tide": 25, "snout": 30,
               "rib": 30, "host": 25, "raiser": 25, "shaper": 25, "wayfinder": 25,
               "ward": 45, "eye": 45, "vex": 50, "spire": 60, "silence": 75, "flow": 60,
               "bolt": 50, "netherite_upgrade": 100}.items():
    ANCHOR[_t + "_armor_trim_smithing_template"] = (float(_p), K625)
ANCHOR["netherite_upgrade_smithing_template"] = (100.0, K625)
# 陶片
for _s in ["angler", "archer", "arms_up", "blade", "brewer", "burn", "danger", "explorer",
           "flow", "friend", "guster", "heart", "heartbreak", "howl", "miner", "mourner",
           "plenty", "prize", "scrape", "sheaf", "shelter", "skull", "snort"]:
    ANCHOR[_s + "_pottery_sherd"] = (5.0, K625)
# 旗帜图案
for _b in ["skull", "creeper", "flower", "thing", "globe", "piglin", "mojang", "guster", "flow"]:
    ANCHOR[_b + "_banner_pattern"] = (5.0, K625)
# 床/旗帜/蜡烛/潜影盒/羊毛地毯/染色陶瓦/混凝土（16 色，统一价）
for _c in ["", "white_", "orange_", "magenta_", "light_blue_", "yellow_", "lime_", "pink_",
           "gray_", "light_gray_", "cyan_", "purple_", "blue_", "brown_", "green_", "red_", "black_"]:
    ANCHOR[_c + "bed"] = (0.25, K625)
    ANCHOR[_c + "banner"] = (0.45, K625)
    ANCHOR[_c + "candle"] = (0.40 if not _c else 0.45, K625)
    ANCHOR[_c + "shulker_box"] = (17.0 if not _c else 17.2, K625)
    ANCHOR["undyed_shulker_box"] = (17.0, K625)
    ANCHOR[_c + "wool"] = (0.06, K625)
    ANCHOR[_c + "carpet"] = (0.04, K625)
    ANCHOR[_c + "terracotta"] = (0.10, K625) if not _c else (0.15, K625)
    ANCHOR[_c + "glazed_terracotta"] = (0.25, K625)
    ANCHOR[_c + "concrete"] = (0.08, K625)
    ANCHOR[_c + "concrete_powder"] = (0.06, K625)
    ANCHOR[_c + "glass"] = (0.05, K625)
    ANCHOR[_c + "glass_pane"] = (0.02, K625)
    ANCHOR[_c + "stained_glass"] = (0.10, K625)
    ANCHOR[_c + "stained_glass_pane"] = (0.05, K625)
ANCHOR["tinted_glass"] = (0.10, K625)
ANCHOR["shulker_box"] = (17.0, K625)

# ---- 矿物块 / 合成块（count=1，k625）----
for _n, _b in {
    "coal_block": 4.95, "iron_block": 9.90, "gold_block": 49.50, "copper_block": 7.92,
    "redstone_block": 19.80, "lapis_block": 24.75, "diamond_block": 99.00,
    "quartz_block": 0.70, "raw_iron_block": 8.40,
    "raw_gold_block": 42.10, "raw_copper_block": 6.70, "smooth_quartz": 0.75,
    "quartz_bricks": 0.75, "quartz_pillar": 0.70, "chiseled_quartz_block": 0.70,
    "amethyst_block": 1.20, "snow_block": 0.01, "waxed_copper": 7.92,
}.items():
    ANCHOR[_n] = (_b, K625)
ANCHOR["emerald_block"] = (9.90, ZERO)  # 绿宝石块只卖不回收（封 9 绿换块套利）
# 按钮/压力板（移除形式系数后显式定价）
for _w in ["oak", "spruce", "birch", "jungle", "acacia", "dark_oak", "mangrove",
           "cherry", "bamboo", "crimson", "warped", "pale_oak"]:
    ANCHOR[_w + "_button"] = (0.02, K625)
    ANCHOR[_w + "_pressure_plate"] = (0.02, K625)
ANCHOR["stone_button"] = (0.05, K625)
ANCHOR["stone_pressure_plate"] = (0.05, K625)
ANCHOR["polished_blackstone_button"] = (0.02, K625)
ANCHOR["polished_blackstone_pressure_plate"] = (0.06, K625)
ANCHOR["wooden_button"] = (0.02, K625)      # Bedrock 橡木按钮别名
ANCHOR["stone_block_slab3"] = (0.02, K625)  # Bedrock 双层石台阶

# ---- 建筑块基底（单块买价，k625 合成物；BULK 原料）----
BLOCK_BASE = {
    "cobblestone": (0.01, BULK), "mossy_cobblestone": (0.02, BULK),
    "stone": (0.01, BULK), "smooth_stone": (0.02, K625),
    "stone_bricks": (0.03, K625), "mossy_stone_bricks": (0.04, K625),
    "cracked_stone_bricks": (0.03, K625), "chiseled_stone_bricks": (0.035, K625),
    "granite": (0.01, BULK), "polished_granite": (0.02, K625),
    "diorite": (0.01, BULK), "polished_diorite": (0.02, K625),
    "andesite": (0.01, BULK), "polished_andesite": (0.02, K625),
    "deepslate": (0.03, BULK), "cobbled_deepslate": (0.02, BULK),
    "polished_deepslate": (0.04, K625), "deepslate_bricks": (0.045, K625),
    "deepslate_tiles": (0.045, K625), "chiseled_deepslate": (0.05, K625),
    "cracked_deepslate_bricks": (0.045, K625), "cracked_deepslate_tiles": (0.045, K625),
    "tuff": (0.02, BULK), "polished_tuff": (0.03, K625), "tuff_bricks": (0.04, K625),
    "chiseled_tuff": (0.04, K625), "chiseled_tuff_bricks": (0.04, K625),
    "bricks": (0.045, K625), "mud_bricks": (0.025, K625),
    "sandstone": (0.02, K625), "smooth_sandstone": (0.03, K625),
    "cut_sandstone": (0.025, K625), "chiseled_sandstone": (0.025, K625),
    "red_sandstone": (0.02, K625), "smooth_red_sandstone": (0.03, K625),
    "cut_red_sandstone": (0.025, K625), "chiseled_red_sandstone": (0.025, K625),
    "prismarine": (0.45, K625), "prismarine_bricks": (0.50, K625),
    "dark_prismarine": (0.55, K625),
    "nether_brick": (0.05, K625), "red_nether_brick": (0.06, K625),
    "chiseled_nether_bricks": (0.06, K625), "cracked_nether_bricks": (0.05, K625),
    "end_stone_bricks": (0.06, K625), "purpur_block": (0.08, K625),
    "purpur_pillar": (0.08, K625),
    "quartz_block": (0.70, K625), "smooth_quartz": (0.75, K625),
    "quartz_bricks": (0.75, K625), "quartz_pillar": (0.70, K625),
    "chiseled_quartz_block": (0.70, K625),
    "blackstone": (0.02, BULK), "polished_blackstone": (0.03, K625),
    "polished_blackstone_bricks": (0.04, K625), "chiseled_polished_blackstone": (0.04, K625),
    "gilded_blackstone": (0.05, BULK), "cracked_polished_blackstone_bricks": (0.04, K625),
    # 铜切制系（氧化/涂蜡同价，防套利）
    "cut_copper": (3.84, K625), "chiseled_copper": (3.84, K625),
    "copper_grate": (3.84, K625), "copper_door": (2.00, K625),
    "copper_trapdoor": (3.50, K625), "copper_bulb": (6.50, K625),
    "lightning_rod": (2.60, K625),
    # 珊瑚系
    "tube_coral_block": (0.15, K625), "brain_coral_block": (0.15, K625),
    "bubble_coral_block": (0.15, K625), "fire_coral_block": (0.15, K625),
    "horn_coral_block": (0.15, K625),
    "dead_tube_coral_block": (0.02, BULK), "dead_brain_coral_block": (0.02, BULK),
    "dead_bubble_coral_block": (0.02, BULK), "dead_fire_coral_block": (0.02, BULK),
    "dead_horn_coral_block": (0.02, BULK),
    "tube_coral": (0.10, K625), "brain_coral": (0.10, K625), "bubble_coral": (0.10, K625),
    "fire_coral": (0.10, K625), "horn_coral": (0.10, K625),
    "tube_coral_fan": (0.05, K625), "brain_coral_fan": (0.05, K625),
    "bubble_coral_fan": (0.05, K625), "fire_coral_fan": (0.05, K625),
    "horn_coral_fan": (0.05, K625),
    # 原木/木板 11 族
    "oak_log": (0.02, ORE), "spruce_log": (0.02, ORE), "birch_log": (0.02, ORE),
    "jungle_log": (0.02, ORE), "acacia_log": (0.02, ORE), "dark_oak_log": (0.02, ORE),
    "mangrove_log": (0.02, ORE), "cherry_log": (0.02, ORE), "bamboo_block": (0.02, ORE),
    "crimson_stem": (0.02, ORE), "warped_stem": (0.02, ORE),
    "oak_planks": (0.01, ORE), "spruce_planks": (0.01, ORE), "birch_planks": (0.01, ORE),
    "jungle_planks": (0.01, ORE), "acacia_planks": (0.01, ORE), "dark_oak_planks": (0.01, ORE),
    "mangrove_planks": (0.01, ORE), "cherry_planks": (0.01, ORE), "bamboo_planks": (0.01, ORE),
    "crimson_planks": (0.01, ORE), "warped_planks": (0.01, ORE),
    "bamboo_mosaic": (0.015, ORE),
}
# 去皮原木/木块/菌核 +0.005~0.01
for _w in ["oak", "spruce", "birch", "jungle", "acacia", "dark_oak", "mangrove", "cherry"]:
    BLOCK_BASE["stripped_" + _w + "_log"] = (0.025, ORE)
    BLOCK_BASE[_w + "_wood"] = (0.03, ORE)
    BLOCK_BASE["stripped_" + _w + "_wood"] = (0.035, ORE)
BLOCK_BASE["stripped_bamboo_block"] = (0.025, ORE)
BLOCK_BASE["stripped_crimson_stem"] = (0.025, ORE)
BLOCK_BASE["stripped_warped_stem"] = (0.025, ORE)
BLOCK_BASE["crimson_hyphae"] = (0.03, ORE)
BLOCK_BASE["warped_hyphae"] = (0.03, ORE)
BLOCK_BASE["stripped_crimson_hyphae"] = (0.035, ORE)
BLOCK_BASE["stripped_warped_hyphae"] = (0.035, ORE)
BLOCK_BASE["mushroom_stem"] = (0.02, BULK)
BLOCK_BASE["brown_mushroom_block"] = (0.05, K625)
BLOCK_BASE["red_mushroom_block"] = (0.05, K625)
# 氧化/涂蜡铜前缀同价
for _p in ["exposed_", "weathered_", "oxidized_", "waxed_", "waxed_exposed_",
           "waxed_weathered_", "waxed_oxidized_"]:
    for _base, _pr in [("cut_copper", 3.84), ("chiseled_copper", 3.84), ("copper_grate", 3.84),
                       ("copper_door", 2.0), ("copper_trapdoor", 3.5), ("copper_bulb", 6.5),
                       ("lightning_rod", 2.6), ("copper_block", 7.92)]:
        BLOCK_BASE[_p + _base] = (_pr, K625)

# ---- 形式系数基底补全（单数/复数、木族裸名、船/告示牌/树叶/树苗）----
for _w, _b in {"oak": 0.01, "spruce": 0.01, "birch": 0.01, "jungle": 0.01, "acacia": 0.01,
               "dark_oak": 0.01, "mangrove": 0.01, "cherry": 0.01, "bamboo": 0.01,
               "crimson": 0.01, "warped": 0.01, "pale_oak": 0.01}.items():
    BLOCK_BASE[_w] = (_b, ORE)  # 使 oak_stairs / oak_door 等形式派生自木板价
    ANCHOR[_w + "_boat"] = (0.15, K625)
    ANCHOR[_w + "_chest_boat"] = (0.35, K625)
    ANCHOR[_w + "_sign"] = (0.03, K625)
    ANCHOR[_w + "_hanging_sign"] = (0.05, K625)
    ANCHOR[_w + "_leaves"] = (0.02, ORE)
    ANCHOR[_w + "_sapling"] = (0.05, K625)
ANCHOR["bamboo_raft"] = (0.15, K625)
ANCHOR["bamboo_chest_raft"] = (0.35, K625)
ANCHOR["bamboo_sign"] = (0.03, K625)
ANCHOR["bamboo_hanging_sign"] = (0.05, K625)
ANCHOR["azalea_leaves"] = (0.02, ORE)
ANCHOR["flowering_azalea_leaves"] = (0.02, ORE)
# 1.21.4 苍白橡木（pale_oak 形式走上方木族循环，此处补 log/wood/planks 基底）
for _n, _pr in [("pale_oak_log", 0.02), ("stripped_pale_oak_log", 0.025),
                ("pale_oak_wood", 0.03), ("stripped_pale_oak_wood", 0.035),
                ("pale_oak_planks", 0.01), ("pale_oak_leaves", 0.02),
                ("pale_oak_sapling", 0.05), ("pale_oak_boat", 0.15),
                ("pale_oak_chest_boat", 0.35), ("pale_oak_sign", 0.03),
                ("pale_oak_hanging_sign", 0.05)]:
    BLOCK_BASE[_n] = (_pr, ORE if "log" in _n or "planks" in _n or "leaves" in _n else K625)
# 1.21.4/1.21.5 新内容
ANCHOR["creaking_heart"] = (5.00, K625)
ANCHOR["resin_clump"] = (0.05, ORE)
ANCHOR["resin_block"] = (0.50, K625)
ANCHOR["resin_brick"] = (0.06, ORE)
ANCHOR["resin_bricks"] = (0.07, K625)
ANCHOR["chiseled_resin_bricks"] = (0.07, K625)
BLOCK_BASE["resin_bricks"] = (0.07, K625)
BLOCK_BASE["chiseled_resin_bricks"] = (0.07, K625)
ANCHOR["open_eyeblossom"] = (0.02, K625)
ANCHOR["closed_eyeblossom"] = (0.02, K625)
ANCHOR["wildflowers"] = (0.02, K625)
ANCHOR["cactus_flower"] = (0.02, K625)
ANCHOR["firefly_bush"] = (0.02, K625)
ANCHOR["bush"] = (0.02, K625)
ANCHOR["leaf_litter"] = (0.01, BULK)
ANCHOR["short_dry_grass"] = (0.01, ORE)
ANCHOR["tall_dry_grass"] = (0.02, ORE)
ANCHOR["pale_moss_block"] = (0.02, BULK)
ANCHOR["pale_moss_carpet"] = (0.02, K625)
ANCHOR["pale_hanging_moss"] = (0.02, ORE)
ANCHOR["dried_ghast"] = (2.00, ORE)
ANCHOR["small_dripleaf_block"] = (0.03, K625)
ANCHOR["writable_book"] = (0.50, K625)
ANCHOR["chiseled_bookshelf"] = (0.12, K625)
for _w in ["oak", "spruce", "birch", "jungle", "acacia", "dark_oak", "mangrove",
           "cherry", "bamboo", "crimson", "warped"]:
    ANCHOR[_w + "_shelf"] = (0.12, K625)
ANCHOR["bundle"] = (0.80, K625)
for _c in ["black", "blue", "brown", "cyan", "gray", "green", "light_blue", "light_gray",
           "lime", "magenta", "orange", "pink", "purple", "red", "white", "yellow"]:
    ANCHOR[_c + "_bundle"] = (0.80, K625)
# 铜块 Bedrock 裸名（exposed_copper 等）
for _p in ["exposed_", "weathered_", "oxidized_", "waxed_", "waxed_exposed_",
           "waxed_weathered_", "waxed_oxidized_"]:
    ANCHOR[_p + "copper"] = (7.92, K625)
# 铜器时代装饰件 + 氧化变体（同价，防刷差价）
for _p in ["", "exposed_", "weathered_", "oxidized_", "waxed_", "waxed_exposed_",
           "waxed_weathered_", "waxed_oxidized_"]:
    ANCHOR[_p + "copper_bars"] = (0.45, K625)
    ANCHOR[_p + "copper_chain"] = (0.50, K625)
    ANCHOR[_p + "copper_chest"] = (7.00, K625)
    ANCHOR[_p + "copper_lantern"] = (4.60, K625)
    ANCHOR[_p + "copper_golem_statue"] = (30.00, K625)
ANCHOR["copper_torch"] = (0.13, K625)
# 紫水晶芽簇
ANCHOR["small_amethyst_bud"] = (0.25, K625)
ANCHOR["medium_amethyst_bud"] = (0.50, K625)
ANCHOR["large_amethyst_bud"] = (0.75, K625)
ANCHOR["amethyst_cluster"] = (1.00, K625)
# 珊瑚（活/死、扇/墙扇）
for _c in ["tube", "brain", "bubble", "fire", "horn"]:
    ANCHOR[_c + "_coral_wall_fan"] = (0.05, K625)
    ANCHOR["dead_" + _c + "_coral"] = (0.02, K625)
    ANCHOR["dead_" + _c + "_coral_fan"] = (0.02, K625)
    ANCHOR["dead_" + _c + "_coral_wall_fan"] = (0.02, K625)
# 蛊虫石族（按对应普通方块价）
for _n, _pr in [("infested_stone", 0.01), ("infested_cobblestone", 0.01),
                ("infested_stone_bricks", 0.03), ("infested_mossy_stone_bricks", 0.04),
                ("infested_cracked_stone_bricks", 0.03), ("infested_chiseled_stone_bricks", 0.035),
                ("infested_deepslate", 0.03)]:
    ANCHOR[_n] = (_pr, BULK)
# 杂项
ANCHOR["cobweb"] = (0.05, K625)
ANCHOR["bowl"] = (0.01, K625)
ANCHOR["powder_snow"] = (0.01, BULK)
ANCHOR["sweet_berry_bush"] = (0.02, ORE)
ANCHOR["azalea_leaves_flowered"] = (0.02, ORE)
ANCHOR["cave_vines"] = (0.02, ORE)
ANCHOR["cave_vines_head_with_berries"] = (0.02, ORE)
ANCHOR["reinforced_deepslate"] = (0.20, K625)
ANCHOR["petrified_oak_slab"] = (0.01, K625)
ANCHOR["quartz_ore"] = (0.15, ORE)          # 下界石英矿（Bedrock 名）
ANCHOR["silver_glazed_terracotta"] = (0.25, K625)
ANCHOR["potatoes"] = (0.04, K625)           # 土豆（Bedrock 名）
ANCHOR["spectral_arrow"] = (0.05, K625)
ANCHOR["written_book"] = (0.50, K625)
ANCHOR["filled_map"] = (7.20, K625)
ANCHOR["bordure_indented_banner_pattern"] = (5.0, K625)
ANCHOR["field_masoned_banner_pattern"] = (5.0, K625)
ANCHOR["pale_oak_shelf"] = (0.12, K625)
BLOCK_BASE["resin_brick"] = (0.07, K625)    # 使 resin_brick_stairs/slab/wall 可派生
# 单数楼梯名基底（stairs 名用单数 brick）
for _n, _pr, _cls in [("stone_brick", 0.03, K625), ("mossy_stone_brick", 0.04, K625),
                      ("deepslate_brick", 0.045, K625), ("deepslate_tile", 0.045, K625),
                      ("tuff_brick", 0.04, K625), ("nether_brick", 0.05, K625),
                      ("red_nether_brick", 0.06, K625), ("end_stone_brick", 0.06, K625),
                      ("prismarine_brick", 0.50, K625), ("mud_brick", 0.025, K625),
                      ("purpur", 0.08, K625), ("quartz", 0.70, K625),
                      ("polished_blackstone_brick", 0.04, K625)]:
    BLOCK_BASE[_n] = (_pr, _cls)
# 砖族（Bedrock 命名）
ANCHOR["brick"] = (0.01, ORE)           # 红砖（物品）
ANCHOR["brick_block"] = (0.045, K625)   # 红砖块（Bedrock 名）
ANCHOR["bricks"] = (0.045, K625)        # 红砖块（Java 名）
ANCHOR["brick_stairs"] = (0.07, K625)
ANCHOR["brick_slab"] = (0.03, K625)
ANCHOR["brick_wall"] = (0.05, K625)
ANCHOR["netherbrick"] = (0.02, ORE)     # 下界砖（物品，Bedrock 名）
# 铁门类
ANCHOR["iron_door"] = (2.40, K625)
ANCHOR["iron_trapdoor"] = (4.40, K625)
# Bedrock 别名（常见）
ANCHOR["golden_rail"] = (34.0, K625)     # = 动力铁轨
ANCHOR["noteblock"] = (2.10, K625)
ANCHOR["frame"] = (0.50, K625)
ANCHOR["glow_frame"] = (0.55, K625)
ANCHOR["reeds"] = (0.03, ORE)            # = 甘蔗
ANCHOR["carrots"] = (0.04, K625)         # = 胡萝卜
ANCHOR["cocoa"] = (0.05, ORE)            # = 可可豆
ANCHOR["waterlily"] = (0.02, ORE)        # = 睡莲
ANCHOR["stonecutter_block"] = (1.10, K625)
ANCHOR["web"] = (0.05, K625)             # = 蜘蛛网
ANCHOR["magma"] = (0.03, BULK)           # = 岩浆块
ANCHOR["slime"] = (1.80, K625)           # = 粘液块
ANCHOR["melon_block"] = (0.25, K625)     # = 西瓜
ANCHOR["lit_pumpkin"] = (0.35, K625)     # = 南瓜灯
ANCHOR["carved_pumpkin"] = (0.18, K625)
ANCHOR["jack_o_lantern"] = (0.35, K625)
ANCHOR["dirt_with_roots"] = (0.01, BULK) # = 缠根泥土
ANCHOR["frog_spawn"] = (0.30, K625)      # = 青蛙卵
ANCHOR["grass_path"] = (0.01, BULK)      # = 土径
ANCHOR["deadbush"] = (0.02, ORE)
ANCHOR["tallgrass"] = (0.02, ORE)
ANCHOR["red_flower"] = (0.02, K625)
ANCHOR["yellow_flower"] = (0.02, K625)
ANCHOR["normal_stone_slab"] = (0.01, K625)
ANCHOR["normal_stone_stairs"] = (0.02, K625)
ANCHOR["stone_block_slab3"] = (0.02, K625)
ANCHOR["stone_block_slab4"] = (0.02, K625)
ANCHOR["end_bricks"] = (0.06, K625)
ANCHOR["end_brick_stairs"] = (0.09, K625)
ANCHOR["iron_chain"] = (1.30, K625)
ANCHOR["standing_banner"] = (0.45, K625)
ANCHOR["wooden_button"] = (0.02, K625)
ANCHOR["wooden_door"] = (0.03, K625)
ANCHOR["wooden_pressure_plate"] = (0.01, K625)
ANCHOR["trapdoor"] = (0.02, K625)        # = 橡木活板门（Bedrock 名）
ANCHOR["heavy_weighted_pressure_plate"] = (2.10, K625)
ANCHOR["light_weighted_pressure_plate"] = (1.10, K625)
ANCHOR["golden_carrot"] = (4.50, K625)
ANCHOR["glistering_melon_slice"] = (4.60, K625)

FORM = {
    "_stairs": 1.5, "_slab": 0.55, "_wall": 1.2, "_fence": 1.2, "_fence_gate": 1.5,
    "_door": 2.5, "_trapdoor": 2.0,
}

# ---- 刷怪蛋六档 ----
EGG_TIER = {}
for _m in """chicken cow pig sheep rabbit cod salmon tropical_fish pufferfish squid glow_squid
bat cat ocelot fox wolf parrot donkey mule horse llama trader_llama goat bee camel armadillo
sniffer mooshroom""".split():
    EGG_TIER[_m + "_spawn_egg"] = 200
for _m in """allay axolotl dolphin frog tadpole turtle panda polar_bear snow_golem iron_golem
copper_golem villager wandering_trader zombie_villager skeleton_horse zombie_horse""".split():
    EGG_TIER[_m + "_spawn_egg"] = 600
for _m in """zombie skeleton spider cave_spider creeper witch drowned husk stray slime
silverfish endermite phantom bogged breeze creaking""".split():
    EGG_TIER[_m + "_spawn_egg"] = 1500
for _m in """blaze elder_guardian ghast guardian hoglin magma_cube piglin piglin_brute
pillager shulker strider vex vindicator zoglin zombie_pigman happy_ghast""".split():
    EGG_TIER[_m + "_spawn_egg"] = 4000
for _m in """enderman evoker ravager warden wither_skeleton""".split():
    EGG_TIER[_m + "_spawn_egg"] = 8000
EGG_TIER["wither_spawn_egg"] = 13140
EGG_TIER["ender_dragon_spawn_egg"] = 13140
EGG_TIER["copper_golem_spawn_egg"] = 600
EGG_TIER["dried_ghast_spawn_egg"] = 4000
EGG_TIER["mob_spawner"] = 4000

# ---- 修复清单 ----
DUR_FIX = {"crossbow": 465, "mace": 500, "wolf_armor": 64}
DUR_FIX.update({_t: 190 for _t in
    ["copper_sword", "copper_pickaxe", "copper_axe", "copper_shovel", "copper_hoe"]})
DUR_FIX.update({"copper_helmet": 165, "copper_chestplate": 240, "copper_leggings": 225,
                "copper_boots": 195})
REMOVE_NIN = {"item.brewing_stand", "item.flower_pot",
              "vindication_illager_spawn_egg", "evocation_illager_spawn_egg",
              "skull"}
ADD_NIN = {
    # name: (buy, sell, count, tag)
    "chorus_plant": (0.05 * 64, 0.01, 64, "方块"),
    "thing_banner_pattern": (5.0, 3.13, 1, "其他"),
}

KEEP_PRICE = {"netherite_scrap", "netherite_ingot", "netherite_block", "ancient_debris"}


def make_row(nin_id, name, buy, sell, count, tag, durability=0):
    return [{"NIN": f"{nin_id}:{name}", "count": count, "durability": durability,
             "modEnchantData": []},
            buy, sell, "", 0, 0, tag, False, "金币", "金币", 0, 1.0,
            min(count, 64) if count >= 16 else 1, 0.0 if count >= 16 else 0.2, 0.9, 0.1]


def main():
    wrap = json.loads(SRC_JSON.read_text(encoding="utf-8"))
    data = wrap["data"]
    items = data["systemShopItems"]
    rev, _ = namespace_maps(data)
    mc = next(str(v) for k, v in data["nameSpaceMap"].items() if k == "minecraft")

    def name_of(r):
        return r[0]["NIN"].split(":", 1)[1]

    # ---------- 1) 删坏行/重复行 ----------
    before = len(items)
    items[:] = [r for r in items
                if not (r[0]["NIN"].startswith(mc + ":") and name_of(r) in REMOVE_NIN)]
    removed = before - len(items)

    # ---------- 2) 补缺失 ----------
    added = 0
    for name, (buy, sell, count, tag) in ADD_NIN.items():
        if not any(r[0]["NIN"].startswith(mc + ":") and name_of(r) == name for r in items):
            items.append(make_row(mc, name, buy, sell, count, tag))
            added += 1

    # ---------- 3) 重算原版行 ----------
    changed = Counter()
    kept = []
    potion_fixed = 0
    for r in items:
        if not r[0]["NIN"].startswith(mc + ":"):
            continue
        name = name_of(r)
        old = (r[1], r[2])
        cnt = r[0].get("count") or 1

        if name in KEEP_PRICE or name.startswith("netherite_") and "_spawn_egg" not in name:
            continue
        if "enchanted_book" in name:
            kept.append((name, old, "附魔书待附魔ID表"))
            continue
        if name in ("potion", "splash_potion", "lingering_potion", "water_bottle"):
            # NAV 可区分效果但无公开映射表：按规范 §5 兜底"均价 2.0"，卖价 0.625
            r[1], r[2] = 2.0, 1.25
            potion_fixed += 1
            if (r[1], r[2]) != old:
                changed[name] = old
            continue
        if name.endswith("_spawn_egg") or name == "mob_spawner":
            buy = EGG_TIER.get(name)
            if buy is None:
                buy = r[1]
                kept.append((name, old, "未知蛋档"))
            r[1], r[2] = buy, 0.0
        elif name in ANCHOR:
            buy, cls = ANCHOR[name]
            r[1] = r2(buy * cnt)
            r[2] = sell_of(r[1], cls, cnt)
        elif name in BLOCK_BASE:
            buy, cls = BLOCK_BASE[name]
            r[1] = r2(buy * cnt)
            r[2] = sell_of(r[1], cls, cnt)
        else:
            # 形式系数：<基底>_stairs/slab/...
            for suf, mul in FORM.items():
                if name.endswith(suf):
                    base = name[: -len(suf)]
                    if base in BLOCK_BASE:
                        b0, cls = BLOCK_BASE[base]
                        r[1] = r2(b0 * mul * cnt)
                        r[2] = sell_of(r[1], cls, cnt)
                        break
            else:
                kept.append((name, old, "未覆盖"))
                continue
        if (r[1], r[2]) != old:
            changed[name] = old

    # ---------- 4) 耐久修复 ----------
    dur_fixed = 0
    for r in items:
        if not r[0]["NIN"].startswith(mc + ":"):
            continue
        name = name_of(r)
        if name in DUR_FIX:
            if r[0].get("durability") != DUR_FIX[name]:
                r[0]["durability"] = DUR_FIX[name]
                dur_fixed += 1

    # ---------- 5) 全局常量 + 公告 ----------
    eco = data["ecoSystemData"]
    eco["preMinuteCoin"] = 0.1
    eco["defCoin"] = 7
    eco["deathLoseMoney"] = 10.0
    ns_count = Counter()
    for r in items:
        ns_count[r[0]["NIN"].split(":", 1)[0]] += 1
    from collections import defaultdict
    ns_names = defaultdict(int)
    for r in items:
        ns_names[rev.get(r[0]["NIN"].split(":", 1)[0], "?")] += 1
    ench = sum(1 for r in items if "附魔书" in (r[6] or ""))
    eco["noticeMsg"] = (
        f"仅金币｜原版{ns_names.get('minecraft', 0)}(附魔书{ench})"
        f"｜森罗厨{ns_names.get('kaleidoscope_cookery', 0)}+酒{ns_names.get('kaleidoscope_tavern', 0)}"
        f"+偶{ns_names.get('kaleidoscope_doll', 0)}｜冰火{ns_names.get('bricefire', 0)}"
        f"｜旅行袋{ns_names.get('ihzao', 0)}｜车万女仆{ns_names.get('ysm_maid', 0)}"
        f"｜机械{ns_names.get('create', 0)}｜娘化{ns_names.get('breath_maid', 0)}"
        f"｜农夫{ns_names.get('farmer_delight_nullgr', 0) + ns_names.get('farmers_tale_nullgr', 0)}"
        f"｜透明玻璃{ns_names.get('ws', 0)}｜合计{len(items)}"
        f"｜开局7｜在线+0.1/分｜基金隐藏｜死亡固定扣10｜附魔书仅满级/次顶级"
    )

    # ---------- 6) 校验 ----------
    bad = []
    for r in items:
        nm = r[0]["NIN"]
        if r[1] > 0 and r[2] >= r[1]:
            bad.append((nm, r[1], r[2]))
    zero = [r[0]["NIN"] for r in items if r[1] == 0.0 and r[2] == 0.0]
    ore_bad_sell = [(r[0]["NIN"], r[1], r[2]) for r in items
                    if r[2] > 0 and r[1] > 0 and round(r[1], 2) == round(r[2], 2)]

    # ---------- 7) 保存 ----------
    OUT_JSON.write_text(json.dumps(wrap, ensure_ascii=False, indent=2), encoding="utf-8")
    text = json.dumps(wrap, ensure_ascii=False, separators=(",", ":"))
    raw = zlib.compress(text.encode("utf-8"), level=9)
    OUT_TXT.write_text("ppcpdata2%" + base64.b64encode(raw).decode("ascii"), encoding="utf-8")

    # ---------- 8) 报告 ----------
    lines = [
        "# 08210 落地报告（v2 锚点体系 · 原版重算）", "",
        f"- 基线：20260824_09 → 输出 **20260827_10.txt**（{len(items)} 条）",
        "- 规则：docs/价格锚点方案_v2.md + _补充草案.md（含 7 项拍板）",
        f"- 重算原版条目：{sum(1 for r in items if r[0]['NIN'].startswith(mc + ':'))} 条；改动 {len(changed)} 条",
        f"- 删除坏行/重复行 {removed} 条；补缺失 {added} 条；耐久修复 {dur_fixed} 处；药水卖价修复 {potion_fixed} 条",
        f"- 套利（卖≥买）违规：{len(bad)} 条；0/0：{len(zero)} 条", "",
        "## 抽查（新价 buy/sell）", "",
    ]
    for nm in ["minecraft:cobblestone", "minecraft:diamond", "minecraft:gold_ingot",
               "minecraft:iron_ingot", "minecraft:redstone", "minecraft:emerald",
               "minecraft:diamond_pickaxe", "minecraft:diamond_chestplate",
               "minecraft:iron_pickaxe", "minecraft:chainmail_chestplate",
               "minecraft:bread", "minecraft:cake", "minecraft:golden_apple",
               "minecraft:tnt", "minecraft:powered_rail", "minecraft:elytra",
               "minecraft:netherite_ingot", "minecraft:chicken_spawn_egg",
               "minecraft:wither_spawn_egg"]:
        hit = [r for r in items if r[0]["NIN"] == f"{mc}:{nm.split(':', 1)[1]}"]
        lines.append(f"- {nm}: {hit[0][1]}/{hit[0][2]}" if hit else f"- {nm}: NOT FOUND")
    if bad:
        lines += ["", "## 套利违规明细", ""]
        lines += [f"- {nm}: {b}/{s}" for nm, b, s in bad[:30]]
    if kept:
        lines += ["", f"## 未覆盖条目（保留现价，共 {len(kept)}）", ""]
        for name, old, why in kept[:300]:
            lines.append(f"- {name}: {old[0]}/{old[1]}（{why}）")
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"OK total={len(items)} changed={len(changed)} removed={removed} added={added} "
          f"dur_fixed={dur_fixed} potion={potion_fixed} bad={len(bad)} zero={len(zero)} kept={len(kept)}")
    for line in lines[lines.index("## 抽查（新价 buy/sell）") + 1:]:
        if line.startswith("- "):
            print(line)


def sell_of(buy, cls, cnt):
    if cls == ZERO:
        return 0.0
    if cls == BULK:
        return 0.01
    if cls == ORE:
        s = r2(buy * 0.05, floor=0.01)
    else:
        s = r2(buy * 0.625, floor=0.0)
    if buy > 0 and s >= buy:
        s = max(0.0, r2(buy - 0.01, floor=0.0))
    return s


if __name__ == "__main__":
    main()
