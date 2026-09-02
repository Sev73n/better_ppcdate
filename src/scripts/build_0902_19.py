# -*- coding: utf-8 -*-
"""构建 20260902_19（内部标签 08219）：合并用户导入配置 + 精修。

基线：data/decoded/用户导入0902.json（用户从游戏导回，含 18 条 0/0 + 17 条卖价调整 + 新插件字段）

改动（用户拍板 2026-09-02）：
  1. 删除坏 ID `minecraft:item.brewing_stand`（带 item. 前缀，购买失效）
  2. ihzao 马铠 16 件按档位定价（标签对齐现有「旅行袋」；h≈0.8b、l≈0.9b、c≈0.9b）
  3. ysm_maid:eternal_love 按工具档 150 定价（标签「车万女仆」）
  4. 原版（minecraft）分类细化：食物/桶装/矿石/矿物块/建材/装饰/红石/工具/武器/
     装备/材料/植物/药水/交通工具/稀有/其他 + 保留附魔书/刷怪蛋
  5. noticeMsg 精简为「商店总量 + 支持模组」
用法：cd 到仓库根，python src/scripts/build_0902_19.py
"""
import json
import sys
import zlib
import base64
from pathlib import Path

ROOT = Path("C:/Users/AI10/Desktop/ppcdata")
sys.path.insert(0, str(ROOT / "src"))
from ppcp_lib import namespace_maps, validate_items, zero_items, r2  # noqa: E402

SRC_JSON = ROOT / "data/decoded/用户导入0902.json"
OUT_JSON = ROOT / "data/decoded/20260902_19.json"
OUT_TXT = ROOT / "releases/20260902_19.txt"

SELL_RATE = 0.625

# ihzao 马铠档位：b=本体（已有），h=头，l=腿，c=胸
HORSE_ARMOR = {
    "leather":   {"b": 10,  "h": 8,   "l": 9,   "c": 9},
    "chainmail": {"b": 25,  "h": 20,  "l": 22,  "c": 23},
    "iron":      {"b": 30,  "h": 24,  "l": 27,  "c": 28},
    "golden":    {"b": 30,  "h": 24,  "l": 27,  "c": 28},
    "diamond":   {"b": 80,  "h": 64,  "l": 72,  "c": 76},
    "netherite": {"b": 200, "h": 160, "l": 180, "c": 190},
}


# ============ 原版分类 ============
def classify_mc(name: str) -> str:
    # 顺序判定，先命中先得
    if name.endswith("_spawn_egg"):
        return "刷怪蛋"
    if name == "enchanted_book":
        return "§l原版|附魔书"

    # 桶装
    if name == "bucket" or name.endswith("_bucket"):
        return "桶装"

    # 矿石
    if name.endswith("_ore") or name in ("ancient_debris",):
        return "矿石"

    # 矿物块（金属/宝石/石英/紫晶/生矿块）
    if name in MINERAL_BLOCKS:
        return "矿物块"

    # 红石元件
    if name in REDSTONE or name.endswith(("_button", "_pressure_plate", "_lightning_rod")):
        return "红石"

    # 武器
    if name in WEAPON:
        return "武器"

    # 装备
    if name in ARMOR:
        return "装备"

    # 工具
    if name in TOOL:
        return "工具"

    # 食物
    if name in FOOD:
        return "食物"

    # 植物
    if name in PLANT:
        return "植物"

    # 药水
    if name in POTION:
        return "药水"

    # 交通工具
    if name in VEHICLE:
        return "交通工具"

    # 稀有/收藏
    if name in RARE:
        return "稀有"

    # 装饰
    if name in DECOR:
        return "装饰"

    # 材料
    if name in MATERIAL:
        return "材料"

    # 建材（大量后缀规则兜底）
    if name in BUILDING or is_building(name):
        return "建材"

    return "其他"


MINERAL_BLOCKS = {
    "coal_block", "iron_block", "gold_block", "diamond_block", "emerald_block",
    "redstone_block", "lapis_block", "copper_block", "netherite_block",
    "quartz_block", "quartz_pillar", "quartz_bricks", "chiseled_quartz_block",
    "smooth_quartz", "amethyst_block", "amethyst_cluster", "budding_amethyst",
    "small_amethyst_bud", "medium_amethyst_bud", "large_amethyst_bud",
    "glowstone", "magma",
    "raw_iron_block", "raw_gold_block", "raw_copper_block",
    "waxed_copper_block", "exposed_copper", "weathered_copper", "oxidized_copper",
    "waxed_copper", "waxed_exposed_copper", "waxed_weathered_copper",
    "waxed_oxidized_copper", "cut_copper", "exposed_cut_copper",
    "weathered_cut_copper", "oxidized_cut_copper", "waxed_cut_copper",
    "waxed_exposed_cut_copper", "waxed_weathered_cut_copper",
    "waxed_oxidized_cut_copper", "chiseled_copper", "exposed_chiseled_copper",
    "weathered_chiseled_copper", "oxidized_chiseled_copper",
    "waxed_chiseled_copper", "waxed_exposed_chiseled_copper",
    "waxed_weathered_chiseled_copper", "waxed_oxidized_chiseled_copper",
}

REDSTONE = {
    "redstone", "redstone_torch", "redstone_lamp", "repeater", "comparator",
    "observer", "piston", "sticky_piston", "dropper", "dispenser", "hopper",
    "lever", "note_block", "noteblock", "daylight_detector", "target",
    "tripwire_hook", "lightning_rod", "sculk_sensor",
    "calibrated_sculk_sensor", "crafter", "tnt", "rail", "powered_rail",
    "detector_rail", "activator_rail", "golden_rail", "redstone_torch",
    "sculk_catalyst", "sculk_shrieker",
}

WEAPON = {
    "wooden_sword", "stone_sword", "iron_sword", "golden_sword",
    "diamond_sword", "netherite_sword", "copper_sword",
    "bow", "crossbow", "trident", "mace", "arrow", "spectral_arrow",
    "tipped_arrow", "fire_charge", "wind_charge",
}

ARMOR = {
    # 全套盔甲
    "leather_helmet", "leather_chestplate", "leather_leggings", "leather_boots",
    "chainmail_helmet", "chainmail_chestplate", "chainmail_leggings", "chainmail_boots",
    "iron_helmet", "iron_chestplate", "iron_leggings", "iron_boots",
    "golden_helmet", "golden_chestplate", "golden_leggings", "golden_boots",
    "diamond_helmet", "diamond_chestplate", "diamond_leggings", "diamond_boots",
    "netherite_helmet", "netherite_chestplate", "netherite_leggings", "netherite_boots",
    "copper_helmet", "copper_chestplate", "copper_leggings", "copper_boots",
    "turtle_helmet", "wolf_armor", "elytra", "shield",
    # 马铠
    "leather_horse_armor", "iron_horse_armor", "golden_horse_armor",
    "diamond_horse_armor", "copper_horse_armor",
}

TOOL = {
    # 镐斧铲锄
    "wooden_pickaxe", "stone_pickaxe", "iron_pickaxe", "golden_pickaxe",
    "diamond_pickaxe", "netherite_pickaxe", "copper_pickaxe",
    "wooden_axe", "stone_axe", "iron_axe", "golden_axe", "diamond_axe",
    "netherite_axe", "copper_axe",
    "wooden_shovel", "stone_shovel", "iron_shovel", "golden_shovel",
    "diamond_shovel", "netherite_shovel", "copper_shovel",
    "wooden_hoe", "stone_hoe", "iron_hoe", "golden_hoe", "diamond_hoe",
    "netherite_hoe", "copper_hoe",
"shears", "fishing_rod", "flint_and_steel", "brush", "spyglass",
    "compass", "recovery_compass", "clock", "lead", "name_tag",
    "carrot_on_a_stick", "warped_fungus_on_a_stick", "saddle",
    "lodestone_compass", "bundle", "white_bundle", "orange_bundle",
    "magenta_bundle", "light_blue_bundle", "yellow_bundle", "lime_bundle",
    "pink_bundle", "gray_bundle", "light_gray_bundle", "cyan_bundle",
    "purple_bundle", "blue_bundle", "brown_bundle", "green_bundle",
    "red_bundle", "black_bundle", "map", "empty_map", "filled_map",
    "book", "writable_book", "written_book", "paper",
}

FOOD = {
    # 肉（生/熟）
    "beef", "porkchop", "chicken", "mutton", "rabbit",
    "cod", "salmon", "tropical_fish", "pufferfish",
    "cooked_beef", "cooked_porkchop", "cooked_chicken", "cooked_mutton",
    "cooked_rabbit", "cooked_cod", "cooked_salmon",
    # 果蔬
    "apple", "golden_apple", "enchanted_golden_apple", "melon_slice",
    "sweet_berries", "glow_berries", "chorus_fruit",
    "carrot", "potato", "beetroot", "baked_potato", "poisonous_potato",
    "golden_carrot",
    # 烘焙/汤羹
    "bread", "cake", "cookie", "pumpkin_pie",
    "mushroom_stew", "beetroot_soup", "rabbit_stew", "suspicious_stew",
    "dried_kelp", "honey_bottle",
    # 合成食材
    "sugar", "egg",
}

PLANT = {
    # 种子
    "wheat_seeds", "melon_seeds", "pumpkin_seeds", "beetroot_seeds",
    "torchflower_seeds", "pitcher_pod",
    # 作物/块
    "wheat", "pumpkin", "melon", "carrots", "potatoes", "beetroots",
    "sugar_cane", "reeds", "cactus", "bamboo", "kelp", "sea_pickle",
    "cocoa_beans", "nether_wart",
    "melon_block", "carved_pumpkin", "jack_o_lantern", "lit_pumpkin",
    "brown_mushroom_block", "red_mushroom_block", "mushroom_stem",
    "hay_block", "dried_kelp_block",
    # 蘑菇/菌
    "brown_mushroom", "red_mushroom", "crimson_fungus", "warped_fungus",
    "crimson_roots", "warped_roots", "nether_sprouts", "twisting_vines",
    "weeping_vines", "hanging_roots", "glow_lichen", "cave_vines",
    "cave_vines_head_with_berries", "vine",
    # 树苗/叶/草/花
    "oak_sapling", "spruce_sapling", "birch_sapling", "jungle_sapling",
    "acacia_sapling", "dark_oak_sapling", "mangrove_propagule",
    "cherry_sapling", "bamboo_sapling", "azalea", "flowering_azalea",
    "azalea_leaves", "azalea_leaves_flowered",
    "oak_leaves", "spruce_leaves", "birch_leaves", "jungle_leaves",
    "acacia_leaves", "dark_oak_leaves", "mangrove_leaves", "cherry_leaves",
    "short_grass", "tall_grass", "fern", "large_fern", "dead_bush",
    "dandelion", "poppy", "blue_orchid", "allium", "azure_bluet",
    "red_tulip", "orange_tulip", "white_tulip", "pink_tulip",
    "oxeye_daisy", "cornflower", "lily_of_the_valley", "wither_rose",
    "sunflower", "lilac", "rose_bush", "peony", "pitcher_plant",
    "torchflower", "cactus_flower", "pink_petals", "wildflowers",
    "open_eyeblossom", "closed_eyeblossom",
    "lily_pad", "waterlily", "seagrass", "spore_blossom", "big_dripleaf",
    "small_dripleaf", "small_dripleaf_block", "firefly_bush", "bush", "leaf_litter",
    "short_dry_grass", "tall_dry_grass", "short_grass", "tall_grass", "tallgrass",
    "cocoa", "deadbush", "red_flower", "frog_spawn",
    "mangrove_sapling", "pale_oak_sapling", "pale_oak_leaves",
    "nether_wart_block", "warped_wart_block",
    # 方块性植物
    "moss_block", "moss_carpet", "pale_moss_block", "pale_moss_carpet",
    "pale_hanging_moss", "beehive", "bee_nest", "composter",
    "chorus_plant", "chorus_flower",
    "crimson_nylium", "warped_nylium", "mycelium", "podzol",
    "farmland", "dirt_path", "grass_path", "sweet_berry_bush",
    "frogspawn", "sniffer_egg", "turtle_egg", "mangrove_roots",
    "muddy_mangrove_roots",
}

POTION = {
    "potion", "splash_potion", "lingering_potion", "experience_bottle",
    "glass_bottle", "dragon_breath", "ominous_bottle", "fermented_spider_eye",
    "glistering_melon_slice", "nether_wart", "blaze_powder", "glowstone_dust",
    "redstone", "gunpowder", "spider_eye",
}

VEHICLE = {
    "oak_boat", "spruce_boat", "birch_boat", "jungle_boat", "acacia_boat",
    "dark_oak_boat", "mangrove_boat", "cherry_boat", "pale_oak_boat",
    "bamboo_raft",
    "oak_chest_boat", "spruce_chest_boat", "birch_chest_boat",
    "jungle_chest_boat", "acacia_chest_boat", "dark_oak_chest_boat",
    "mangrove_chest_boat", "cherry_chest_boat", "pale_oak_chest_boat",
    "bamboo_chest_raft",
    "minecart", "chest_minecart", "furnace_minecart", "hopper_minecart",
    "tnt_minecart",
}

RARE = {
    "nether_star", "dragon_egg", "totem_of_undying", "heart_of_the_sea",
    "nautilus_shell", "beacon", "conduit", "end_crystal", "respawn_anchor",
    "dragon_head", "wither_skeleton_skull", "skeleton_skull", "zombie_head",
    "creeper_head", "piglin_head", "player_head", "echo_shard", "heavy_core",
    "breeze_rod", "scute", "turtle_scute", "armadillo_scute",
    "goat_horn", "disc_fragment_5", "trial_key", "ominous_trial_key",
    "music_disc_13", "music_disc_cat", "music_disc_blocks", "music_disc_chirp",
    "music_disc_far", "music_disc_mall", "music_disc_mellohi",
    "music_disc_stal", "music_disc_strad", "music_disc_ward", "music_disc_11",
    "music_disc_wait", "music_disc_otherside", "music_disc_5",
    "music_disc_pigstep", "music_disc_relic", "music_disc_creator",
    "music_disc_creator_music_box", "music_disc_precipice",
    "music_disc_tears", "music_disc_lava_chicken",
    "mob_spawner", "trial_spawner", "vault", "creaking_heart", "dried_ghast",
}

DECOR = {
    "painting", "item_frame", "glow_item_frame", "frame",
    "flower_pot", "lantern", "soul_lantern", "campfire", "soul_campfire",
    "end_rod", "chain", "iron_chain", "bell", "armor_stand", "jukebox",
    "decorated_pot", "torch", "soul_torch", "lantern", "sea_lantern",
    "shroomlight", "ochre_froglight", "pearlescent_froglight",
    "verdant_froglight", "candle", "standing_banner", "flower_banner_pattern",
    "creeper_banner_pattern", "skull_banner_pattern", "mojang_banner_pattern",
    "globe_banner_pattern", "piglin_banner_pattern", "flow_banner_pattern",
    "guster_banner_pattern", "field_masoned_banner_pattern",
    "bordure_indented_banner_pattern", "thing_banner_pattern",
    "firework_rocket", "firework_star",
    "lectern", "bookshelf", "chiseled_bookshelf",
    "anvil", "chipped_anvil", "damaged_anvil", "enchanting_table",
    "brewing_stand", "cauldron", "smithing_table", "fletching_table",
    "cartography_table", "loom", "stonecutter", "stonecutter_block",
    "crafting_table", "furnace", "blast_furnace", "smoker", "grindstone",
    "ladder", "scaffolding", "iron_bars", "iron_door", "iron_trapdoor",
    "wooden_door", "barrel", "chest", "trapped_chest", "ender_chest",
    "shulker_box", "undyed_shulker_box", "white_shulker_box",
    "orange_shulker_box", "magenta_shulker_box", "light_blue_shulker_box",
    "yellow_shulker_box", "lime_shulker_box", "pink_shulker_box",
    "gray_shulker_box", "light_gray_shulker_box", "cyan_shulker_box",
    "purple_shulker_box", "blue_shulker_box", "brown_shulker_box",
    "green_shulker_box", "red_shulker_box", "black_shulker_box",
    "white_bed", "orange_bed", "magenta_bed", "light_blue_bed", "yellow_bed",
    "lime_bed", "pink_bed", "gray_bed", "light_gray_bed", "cyan_bed",
    "purple_bed", "blue_bed", "brown_bed", "green_bed", "red_bed", "black_bed",
    "bed", "glow_frame",
    "lodestone", "lightning_rod", "white_harness", "orange_harness",
    "magenta_harness", "light_blue_harness", "yellow_harness", "lime_harness",
    "pink_harness", "gray_harness", "light_gray_harness", "cyan_harness",
    "purple_harness", "blue_harness", "brown_harness", "green_harness",
    "red_harness", "black_harness",
}

MATERIAL = {
    # 锭/粒/宝石/粉
    "iron_ingot", "gold_ingot", "copper_ingot", "netherite_ingot",
    "iron_nugget", "gold_nugget", "copper_nugget", "netherite_scrap",
    "diamond", "emerald", "lapis_lazuli", "quartz", "amethyst_shard",
    "prismarine_shard", "prismarine_crystals", "coal", "charcoal",
    "raw_iron", "raw_gold", "raw_copper", "clay_ball", "brick", "netherbrick",
    "resin_clump", "resin_brick",
    # 掉落物
    "bone", "string", "feather", "leather", "rabbit_foot", "rabbit_hide",
    "slime_ball", "magma_cream", "blaze_rod", "ender_pearl", "ender_eye",
    "ghast_tear", "phantom_membrane", "shulker_shell", "spider_eye",
    "rotten_flesh", "gunpowder", "flint", "snowball", "glow_ink_sac",
    "ink_sac", "honeycomb", "bone_meal", "egg",
    # 染料
    "white_dye", "orange_dye", "magenta_dye", "light_blue_dye", "yellow_dye",
    "lime_dye", "pink_dye", "gray_dye", "light_gray_dye", "cyan_dye",
    "purple_dye", "blue_dye", "brown_dye", "green_dye", "red_dye", "black_dye",
    # 模板/陶片
    "netherite_upgrade_smithing_template",
    "sentry_armor_trim_smithing_template", "dune_armor_trim_smithing_template",
    "coast_armor_trim_smithing_template", "wild_armor_trim_smithing_template",
    "tide_armor_trim_smithing_template", "snout_armor_trim_smithing_template",
    "rib_armor_trim_smithing_template", "host_armor_trim_smithing_template",
    "raiser_armor_trim_smithing_template", "shaper_armor_trim_smithing_template",
    "wayfinder_armor_trim_smithing_template", "ward_armor_trim_smithing_template",
    "eye_armor_trim_smithing_template", "vex_armor_trim_smithing_template",
    "spire_armor_trim_smithing_template", "silence_armor_trim_smithing_template",
    "flow_armor_trim_smithing_template", "bolt_armor_trim_smithing_template",
    "angler_pottery_sherd", "archer_pottery_sherd", "arms_up_pottery_sherd",
    "blade_pottery_sherd", "brewer_pottery_sherd", "burn_pottery_sherd",
    "danger_pottery_sherd", "explorer_pottery_sherd", "friend_pottery_sherd",
    "heart_pottery_sherd", "heartbreak_pottery_sherd", "howl_pottery_sherd",
    "miner_pottery_sherd", "mourner_pottery_sherd", "plenty_pottery_sherd",
    "prize_pottery_sherd", "sheaf_pottery_sherd", "shelter_pottery_sherd",
    "skull_pottery_sherd", "snort_pottery_sherd", "flow_pottery_sherd",
    "guster_pottery_sherd", "scrape_pottery_sherd",
    # 基础材料/杂
    "stick", "obsidian", "crying_obsidian", "dirt", "coarse_dirt", "sand",
    "red_sand", "gravel", "soul_sand", "soul_soil", "clay", "snow",
    "snowball", "ice", "packed_ice", "blue_ice", "snow_layer", "powder_snow",
    "magma_block", "basalt", "smooth_basalt", "blackstone", "gilded_blackstone",
    "netherrack", "nether_gold_ore", "nether_quartz_ore", "cobblestone",
    "stone", "deepslate", "cobbled_deepslate", "tuff", "calcite",
    "dripstone_block", "pointed_dripstone", "end_stone", "purpur_block",
    "sculk", "sculk_vein", "suspicious_sand", "suspicious_gravel",
    "reinforced_deepslate", "sponge", "wet_sponge", "web", "cobweb",
    "blue_egg", "brown_egg", "bowl", "glass_bottle", "slime", "popped_chorus_fruit",
}

BUILDING = {
    "glass", "glass_pane", "white_stained_glass", "orange_stained_glass",
    "magenta_stained_glass", "light_blue_stained_glass", "yellow_stained_glass",
    "lime_stained_glass", "pink_stained_glass", "gray_stained_glass",
    "light_gray_stained_glass", "cyan_stained_glass", "purple_stained_glass",
    "blue_stained_glass", "brown_stained_glass", "green_stained_glass",
    "red_stained_glass", "black_stained_glass",
    "white_stained_glass_pane", "orange_stained_glass_pane",
    "magenta_stained_glass_pane", "light_blue_stained_glass_pane",
    "yellow_stained_glass_pane", "lime_stained_glass_pane",
    "pink_stained_glass_pane", "gray_stained_glass_pane",
    "light_gray_stained_glass_pane", "cyan_stained_glass_pane",
    "purple_stained_glass_pane", "blue_stained_glass_pane",
    "brown_stained_glass_pane", "green_stained_glass_pane",
    "red_stained_glass_pane", "black_stained_glass_pane", "stained_glass",
    "stained_glass_pane", "tinted_glass",
    "white_concrete", "orange_concrete", "magenta_concrete",
    "light_blue_concrete", "yellow_concrete", "lime_concrete", "pink_concrete",
    "gray_concrete", "light_gray_concrete", "cyan_concrete", "purple_concrete",
    "blue_concrete", "brown_concrete", "green_concrete", "red_concrete",
    "black_concrete", "white_concrete_powder", "orange_concrete_powder",
    "magenta_concrete_powder", "light_blue_concrete_powder",
    "yellow_concrete_powder", "lime_concrete_powder", "pink_concrete_powder",
    "gray_concrete_powder", "light_gray_concrete_powder", "cyan_concrete_powder",
    "purple_concrete_powder", "blue_concrete_powder", "brown_concrete_powder",
    "green_concrete_powder", "red_concrete_powder", "black_concrete_powder",
    "terracotta", "white_terracotta", "orange_terracotta", "magenta_terracotta",
    "light_blue_terracotta", "yellow_terracotta", "lime_terracotta",
    "pink_terracotta", "gray_terracotta", "light_gray_terracotta",
    "cyan_terracotta", "purple_terracotta", "blue_terracotta",
    "brown_terracotta", "green_terracotta", "red_terracotta",
    "black_terracotta", "white_glazed_terracotta", "orange_glazed_terracotta",
    "magenta_glazed_terracotta", "light_blue_glazed_terracotta",
    "yellow_glazed_terracotta", "lime_glazed_terracotta",
    "pink_glazed_terracotta", "gray_glazed_terracotta",
    "light_gray_glazed_terracotta", "cyan_glazed_terracotta",
    "purple_glazed_terracotta", "blue_glazed_terracotta",
    "brown_glazed_terracotta", "green_glazed_terracotta",
    "red_glazed_terracotta", "black_glazed_terracotta",
    "silver_glazed_terracotta",
    "white_wool", "orange_wool", "magenta_wool", "light_blue_wool",
    "yellow_wool", "lime_wool", "pink_wool", "gray_wool", "light_gray_wool",
    "cyan_wool", "purple_wool", "blue_wool", "brown_wool", "green_wool",
    "red_wool", "black_wool", "white_carpet", "orange_carpet",
    "magenta_carpet", "light_blue_carpet", "yellow_carpet", "lime_carpet",
    "pink_carpet", "gray_carpet", "light_gray_carpet", "cyan_carpet",
    "purple_carpet", "blue_carpet", "brown_carpet", "green_carpet",
    "red_carpet", "black_carpet", "carpet",
    "sandstone", "red_sandstone", "smooth_sandstone", "smooth_red_sandstone",
    "cut_sandstone", "cut_red_sandstone", "chiseled_sandstone",
    "chiseled_red_sandstone", "stone_bricks", "cracked_stone_bricks",
    "mossy_stone_bricks", "chiseled_stone_bricks", "bricks", "mud_bricks",
    "packed_mud", "mud", "deepslate_bricks", "cracked_deepslate_bricks",
    "deepslate_tiles", "cracked_deepslate_tiles", "polished_deepslate",
    "chiseled_deepslate", "polished_blackstone", "polished_blackstone_bricks",
    "cracked_polished_blackstone_bricks", "chiseled_polished_blackstone",
    "nether_brick", "red_nether_brick", "nether_bricks", "red_nether_bricks",
    "chiseled_nether_bricks", "cracked_nether_bricks",
    "prismarine", "prismarine_bricks", "dark_prismarine",
    "purpur_pillar", "end_stone_bricks", "end_bricks", "end_portal_frame",
    "polished_andesite", "polished_diorite", "polished_granite",
    "polished_tuff", "chiseled_tuff", "tuff_bricks", "chiseled_tuff_bricks",
    "resin_block", "resin_bricks", "chiseled_resin_bricks",
    "mossy_cobblestone", "grass_block", "dirt_with_roots", "rooted_dirt",
    "mangrove_propagule", "smooth_stone", "infested_stone", "stone_block_slab3",
}


def is_building(name: str) -> bool:
    """建材后缀兜底规则。"""
    suffixes = (
        "_planks", "_log", "_wood", "_stem", "_hyphae", "_slab", "_stairs",
        "_wall", "_fence", "_fence_gate", "_gate", "_door", "_trapdoor",
        "_sign", "_hanging_sign", "_pressure_plate", "_button", "_coral",
        "_coral_block", "_coral_fan", "_coral_wall_fan", "_banner",
        "_candle", "_bulb", "_grate", "_chain", "_bars", "_torch",
        "_shelf", "_mosaic", "_pillar", "_bricks", "_tiles", "_block",
    )
    if any(name.endswith(s) for s in suffixes):
        return True
    # 各类石头/砖/沙岩变体
    return any(k in name for k in (
        "andesite", "diorite", "granite", "sandstone", "stone_brick",
        "cobblestone", "deepslate", "blackstone", "basalt", "prismarine",
        "purpur", "nether_brick", "quartz", "tuff", "copper_", "brick",
    )) and name not in ("brick", "netherbrick", "quartz", "copper_ingot",
                        "copper_nugget", "raw_copper")


# ============ 主流程 ============
def main():
    wrap = json.loads(SRC_JSON.read_text(encoding="utf-8"))
    data = wrap["data"]
    items = data["systemShopItems"]
    rev, nsid = namespace_maps(data)
    mc_id, ck_id = nsid["minecraft"], nsid["kaleidoscope_cookery"]
    ih_id, ysm_id = nsid["ihzao"], nsid["ysm_maid"]

    # 1) 删除坏 ID
    before = len(items)
    items[:] = [r for r in items if r[0]["NIN"] != f"{mc_id}:item.brewing_stand"]
    print(f"删除坏 ID brewing_stand: {before} -> {len(items)}")

    # 2) 马铠 16 件定价 + 3) eternal_love
    n_armor, n_maid = 0, 0
    for r in items:
        p, n = r[0]["NIN"].split(":", 1)
        if p == ih_id and n.endswith("armorht_1"):
            pre = n[: -len("armorht_1")]      # 如 iron_c / netherite_h
            part = pre[-1]                    # b / c / h / l
            mat = pre[:-2]                    # 材料档名
            tier = HORSE_ARMOR.get(mat)
            if tier and part in ("h", "l", "c"):
                buy = tier[part]
                r[1] = r2(buy)
                r[2] = r2(buy * SELL_RATE)
                r[6] = "旅行袋"
                n_armor += 1
        elif p == ysm_id and n == "eternal_love":
            r[1] = r2(150)
            r[2] = r2(150 * SELL_RATE)
            r[6] = "车万女仆"
            n_maid += 1
    print(f"马铠定价 {n_armor} 件；eternal_love 定价 {n_maid} 件")

    # 4) 原版分类细化
    n_reclass = 0
    from collections import Counter
    cat = Counter()
    for r in items:
        p, n = r[0]["NIN"].split(":", 1)
        if p != mc_id:
            cat[r[6] or "(空)"] += 1
            continue
        new_tag = classify_mc(n)
        if r[6] != new_tag:
            r[6] = new_tag
            n_reclass += 1
        cat[new_tag] += 1
    print(f"原版重分类 {n_reclass} 条")
    print("  新分类分布:")
    for k, v in sorted(cat.items(), key=lambda x: -x[1]):
        print(f"    {k!r}: {v}")

    # 4b) 全店价格收敛到两位小数（用户 0.4×买价 产生 0.512 类三位小数）
    n_r = 0
    for r in items:
        for idx in (1, 2):
            v = r2(r[idx])
            if v != r[idx]:
                r[idx] = v
                n_r += 1
    print(f"价格两位小数收敛 {n_r} 处")

    # 4c) 抽查分类成员（调试）
    for t in ("武器", "食物", "其他", "桶装"):
        members = [r[0]["NIN"].split(":", 1)[1] for r in items
                   if r[0]["NIN"].startswith(mc_id + ":") and r[6] == t]
        print(f"  [{t}]{len(members)}: {' '.join(sorted(members))}")

    # 5) noticeMsg 精简
    total = len(items)
    data["ecoSystemData"]["noticeMsg"] = (
        f"商店共 {total} 条商品｜支持：原版 + 森罗物语(烹饪/酒馆/玩偶/茶)、"
        "机械动力、冰火传说、车万女仆、YSM女仆、农夫乐事、农夫传说、WS透明玻璃"
    )
    print("noticeMsg 已精简")

    # 6) 校验
    bad = validate_items(items)
    zz = zero_items(items, rev)
    print(f"套利违规 {len(bad)}；0/0 {len(zz)}；总条目 {len(items)}")
    for b in bad[:10]:
        print("  违规:", b)

    OUT_JSON.write_text(json.dumps(wrap, ensure_ascii=False, indent=2), encoding="utf-8")
    text = json.dumps(wrap, ensure_ascii=False, separators=(",", ":"))
    raw = zlib.compress(text.encode("utf-8"), level=9)
    OUT_TXT.write_text("ppcpdata2%" + base64.b64encode(raw).decode("ascii"), encoding="utf-8")
    print(f"已写出 {OUT_TXT.name} 与 {OUT_JSON.name}")


if __name__ == "__main__":
    main()
