# -*- coding: utf-8 -*-
"""08202 -> 08203: full re-anchor of the price system.

Rules (all confirmed with user):
- 0.01 floor, 2dp rounding; 开局73/在线+1/金币锚不动；经济从零重启。
- Chainable commodities: /30 (rarity ratios preserved since old prices embed them).
- Non-chainable stay: mob drops, meat/dairy/eggs/honey, netherite, books, rare drops,
  spawn eggs, discs, bricefire, maid service items, paintings, chainmail.
- Craft tax: 1.5x simple, 1.8x multi-step (blocks in recipe), 3x cooking, 5x jewelry.
- Kill rewards re-anchored (20 zombies = 1 iron sword 3.6 -> zombie 0.18).
- Pool tickets re-derived; structures unchanged.
- chainmining 500/0. 森罗旧茶统一 1/0.36；茶包 1.5/1；新式茶 0.5~1.5。
"""
import base64, json, zlib
from collections import Counter
from pathlib import Path

from kaleido_prices import KALEIDO_PRICES

ROOT = Path(r"C:/Users/AI10/Desktop/ppcdata")
SRC = ROOT / "01_配置明文" / "08202_decoded.json"
OUT_JSON = ROOT / "01_配置明文" / "08205_decoded.json"
OUT_TXT = ROOT / "06_用户自行导入" / "08205.txt"
REPORT = ROOT / "03_对比报告" / "08205_落地报告.md"

wrap = json.loads(SRC.read_text(encoding="utf-8"))
data = wrap["data"]
rev = {str(v): k for k, v in data["nameSpaceMap"].items()}
nsid = {k: str(v) for k, v in data["nameSpaceMap"].items()}
log = []


def res(r):
    nin = r[0].get("NIN", "")
    p, n = nin.split(":", 1) if ":" in nin else ("", nin)
    return f"{rev.get(p, '?' + p)}:{n}"


def r2(x):
    return max(0.01, round(x, 2))


# ================================================================ KEEP list (explicit names, minecraft ns)
KEEP_MC = set("""
enchanted_book netherite_ingot netherite_scrap netherite_block netherite_sword
netherite_pickaxe netherite_axe netherite_shovel netherite_hoe netherite_helmet
netherite_chestplate netherite_leggings netherite_boots
netherite_upgrade_smithing_template ancient_debris bone bone_meal rotten_flesh
gunpowder string spider_eye slime_ball leather rabbit_hide feather egg milk_bucket
honey_bottle honeycomb beef porkchop chicken mutton rabbit cod salmon tropical_fish
pufferfish cooked_beef cooked_porkchop cooked_chicken cooked_mutton cooked_rabbit
cooked_cod cooked_salmon blaze_rod blaze_powder ghast_tear magma_cream ender_pearl
phantom_membrane nautilus_shell heart_of_the_sea nether_star beacon elytra
totem_of_undying trident shulker_shell shulker_box ender_chest dragon_breath
prismarine_shard prismarine_crystals echo_shard goat_horn skull wither_rose saddle
name_tag lead chainmail_helmet chainmail_chestplate chainmail_leggings chainmail_boots
recovery_compass ominous_bottle trial_key breeze_rod heavy_core painting pufferfish_bucket
tropical_fish_bucket cod_bucket salmon_bucket axolotl_bucket tadpole_bucket turtle_egg
sniffer_egg frogspawn
""".split())

# 种植物生长约束锚：连锁只省采收不省生长 → 快熟 ÷3 / 慢熟 ÷2（不是 ÷30）
CROP_DIV3 = set("""
wheat carrot potato beetroot melon pumpkin melon_slice sweet_berries glow_berries
kelp bamboo sugar_cane sugar nether_wart wheat_seeds melon_seeds pumpkin_seeds
beetroot_seeds torchflower_seeds pitcher_pod rice rice_panicle wild_rice tomato
lettuce green_chili red_chili chili_seed tomato_seed lettuce_seed wild_rice_seed
fresh_tea_leaves oil grape green_grape gold_grape ice_grape wild_grape grape_crop
green_grape_crop gold_grape_crop ice_grape_crop grapevine wild_grapevine wild_grapevine_plant
gold_grapevine_trellis grapevine_trellis ice_grapevine_trellis vine honey_grape
""".split())
CROP_DIV2 = set("""cocoa_beans""".split())

# ================================================================ RECIPE pricing
# (name, materials, tax) -> buy = r2(materials*tax), sell = r2(materials)
ING = {"iron": 1.2, "gold": 2.4, "diamond": 6.7, "cobble": 0.01, "plank": 0.02,
       "stick": 0.01, "string": 3.0, "leather": 0.09, "slime": 5.0, "redstone": 0.53,
       "quartz": 0.33, "wheat": 0.1, "egg": 2.0, "sugar": 0.13, "paper": 0.07,
       "book": 0.33, "chest": 0.33, "apple": 0.13, "carrot": 0.1, "potato": 0.1,
       "beef": 4.0, "porkchop": 4.0, "chicken": 3.5, "mutton": 4.0, "rice": 0.13,
       "gunpowder": 6.0, "sand": 0.03, "obsidian": 0.1, "flint": 2.0, "glass": 0.07,
       "kelp": 0.02, "copper": 0.4, "zinc": 0.8, "andesite": 0.01, "cake": 7.7,
       "bone": 2.0, "gold_nugget": 0.27, "bucket": 5.4, "bow": 13.5, "furnace": 0.12}

RECIPES = {
    # tools / weapons (simple 1.5x)
    "iron_sword": (2 * ING["iron"] + ING["stick"], 1.5),
    "iron_pickaxe": (3 * ING["iron"] + 2 * ING["stick"], 1.5),
    "iron_axe": (3 * ING["iron"] + 2 * ING["stick"], 1.5),
    "iron_shovel": (1 * ING["iron"] + 2 * ING["stick"], 1.5),
    "iron_hoe": (2 * ING["iron"] + 2 * ING["stick"], 1.5),
    "golden_sword": (2 * ING["gold"] + ING["stick"], 1.5),
    "golden_pickaxe": (3 * ING["gold"] + 2 * ING["stick"], 1.5),
    "golden_axe": (3 * ING["gold"] + 2 * ING["stick"], 1.5),
    "golden_shovel": (1 * ING["gold"] + 2 * ING["stick"], 1.5),
    "golden_hoe": (2 * ING["gold"] + 2 * ING["stick"], 1.5),
    "diamond_sword": (2 * ING["diamond"] + ING["stick"], 1.5),
    "diamond_pickaxe": (3 * ING["diamond"] + 2 * ING["stick"], 1.5),
    "diamond_axe": (3 * ING["diamond"] + 2 * ING["stick"], 1.5),
    "diamond_shovel": (1 * ING["diamond"] + 2 * ING["stick"], 1.5),
    "diamond_hoe": (2 * ING["diamond"] + 2 * ING["stick"], 1.5),
    "bow": (3 * ING["string"] + 3 * ING["stick"], 1.5),
    "crossbow": (2.5 * ING["string"] + 4 * ING["stick"] + ING["iron"] + 0.5 * ING["iron"], 1.5),
    "fishing_rod": (3 * ING["stick"] + 2 * ING["string"], 1.5),
    "shears": (2 * ING["iron"], 1.5),
    "flint_and_steel": (ING["flint"] + ING["iron"], 1.5),
    "bucket": (3 * ING["iron"], 1.5),
    "shield": (6 * ING["plank"] + ING["iron"], 1.5),
    # armor (1.5x)
    "iron_helmet": (5 * ING["iron"], 1.5), "iron_chestplate": (8 * ING["iron"], 1.5),
    "iron_leggings": (7 * ING["iron"], 1.5), "iron_boots": (4 * ING["iron"], 1.5),
    "golden_helmet": (5 * ING["gold"], 1.5), "golden_chestplate": (8 * ING["gold"], 1.5),
    "golden_leggings": (7 * ING["gold"], 1.5), "golden_boots": (4 * ING["gold"], 1.5),
    "diamond_helmet": (5 * ING["diamond"], 1.5), "diamond_chestplate": (8 * ING["diamond"], 1.5),
    "diamond_leggings": (7 * ING["diamond"], 1.5), "diamond_boots": (4 * ING["diamond"], 1.5),
    "leather_helmet": (5 * ING["leather"], 1.5), "leather_chestplate": (8 * ING["leather"], 1.5),
    "leather_leggings": (7 * ING["leather"], 1.5), "leather_boots": (4 * ING["leather"], 1.5),
    # blocks / machines (1.5x simple, 1.8x multi-step)
    "iron_block": (9 * ING["iron"], 1.5), "gold_block": (9 * ING["gold"], 1.5),
    "diamond_block": (9 * ING["diamond"], 1.5), "emerald_block": (9 * 4.0, 1.5),
    "copper_block": (9 * ING["copper"], 1.5),
    "anvil": (31 * ING["iron"], 1.8),
    "hopper": (5 * ING["iron"] + ING["chest"], 1.8),
    "piston": (3 * ING["plank"] + 4 * ING["cobble"] + ING["iron"] + ING["redstone"], 1.8),
    "sticky_piston": (3 * ING["plank"] + 4 * ING["cobble"] + ING["iron"] + ING["redstone"] + ING["slime"], 1.8),
    "observer": (6 * ING["cobble"] + 2 * ING["redstone"] + ING["quartz"], 1.8),
    "dispenser": (7 * ING["cobble"] + ING["bow"], 1.8),
    "dropper": (7 * ING["cobble"] + ING["redstone"], 1.8),
    "furnace": (8 * ING["cobble"], 1.5),
    "blast_furnace": (5 * ING["iron"] + ING["furnace"] + 3 * ING["cobble"], 1.8),
    "smoker": (ING["furnace"] + 4 * 0.07, 1.8),
    "enchanting_table": (ING["book"] + 2 * ING["diamond"] + 4 * ING["obsidian"], 1.8),
    "jukebox": (8 * ING["plank"] + ING["diamond"], 1.5),
    "bookshelf": (6 * ING["plank"] + 3 * ING["book"], 1.5),
    "lectern": (4 * ING["plank"] + 1.7, 1.5),
    "tnt": (4 * ING["sand"] + 5 * ING["gunpowder"], 1.5),
    "redstone_block": (9 * ING["redstone"], 1.5),
    "redstone_lamp": (4 * ING["redstone"] + ING["glass"], 1.5),
    "minecart": (5 * ING["iron"], 1.5),
    "chest_minecart": (ING["chest"] + 5 * ING["iron"], 1.5),
    "furnace_minecart": (ING["furnace"] + 5 * ING["iron"], 1.5),
    "rail": (0.375 * ING["iron"] + 0.0625 * ING["stick"], 1.5),
    "powered_rail": (0.375 * ING["gold"] + 0.0625 * ING["stick"] + 0.0625 * ING["redstone"], 1.5),
    "detector_rail": (0.375 * ING["iron"] + 0.0625 * ING["plank"] + 0.0625 * ING["redstone"], 1.5),
    "activator_rail": (0.375 * ING["iron"] + 0.125 * ING["stick"] + 0.0625 * ING["redstone"], 1.5),
    "bundle": (6 * 3.0 + 2 * ING["string"], 1.5),
    # foods (3x cooking; stacked foods priced per-64 group, single items per-piece)
    "bread": (3.0, 3.0),                      # 64x(3 wheat x3)
    "cake": (0.099, 3.0),                     # single: 3 wheat+2 sugar+egg, milk returns
    "cookie": (3.49, 3.0),                    # 64x(2 wheat+cocoa)
    "pumpkin_pie": (4.0, 3.0),                # 64x(pumpkin+egg+sugar)
    "golden_carrot": (137.4, 1.5),            # 64x(8 nuggets+carrot)
    "golden_apple": (19.2, 1.5),              # single: 8 gold+apple
    "enchanted_golden_apple": (172.8, 1.8),   # single: 72 gold
    "rabbit_stew": (6.3, 3.0),                # 64x(rabbit+carrot+potato+mushroom+bowl)
    "mushroom_stew": (0.26, 3.0),             # 64x(2 mushrooms+bowl)
    "beetroot_soup": (6.0, 3.0),              # 64x(6 beetroot+bowl)
}

# ================================================================ explicit mod price map
EXPLICIT = {
    # create (v3 table)
    "create:cogwheel": (0.7, 0.4), "create:large_cogwheel": (1.3, 0.8),
    "create:belt_connector": (0.5, 0.3), "create:fluid_pipe": (0.7, 0.4),
    "create:chute": (0.8, 0.5), "create:smart_chute": (1.7, 1.0),
    "create:depot": (1.3, 0.8), "create:weighted_ejector": (1.5, 0.9),
    "create:fluid_valve": (1.0, 0.6), "create:fluid_tank": (2.7, 1.7),
    "create:hose_pulley": (2.3, 1.5), "create:portable_fluid_interface": (3.0, 1.9),
    "create:smart_fluid_pipe": (2.0, 1.3),
    "create:mechanical_arm": (12.0, 7.4), "create:precision_mechanism": (4.0, 2.5),
    "create:electron_tube": (2.0, 1.3), "create:brass_hand": (1.0, 0.6),
    "create:andesite_casing": (0.8, 0.5), "create:copper_casing": (1.3, 0.8),
    "create:brass_casing": (2.3, 1.5), "create:sturdy_sheet": (1.7, 1.0),
    "create:super_glue": (1.0, 0.6), "create:rose_quartz": (0.5, 0.3),
    "create:polished_rose_quartz": (0.7, 0.4),
    "create:andesite_alloy": (0.33, 0.21),
    "create:zinc_ingot": (0.8, 0.5), "create:zinc_block": (7.2, 4.5),
    "create:brass_ingot": (0.9, 0.6), "create:brass_block": (8.1, 5.4),
    "create:zinc_nugget": (0.1, 0.06), "create:brass_nugget": (0.17, 0.1),
    "create:builders_tea": (0.7, 0.2),
    "create:veridium": (0.07, 0.01), "create:ochrum": (0.07, 0.01),
    "create:asurine": (0.07, 0.01), "create:crimsite": (0.07, 0.01),
    "create:zinc_ore": (0.53, 0.33), "create:raw_zinc": (0.67, 0.42),
    # breath_maid jewelry (5x, slime ball 5 stays)
    "breath_maid:npc_jie_1": (64, 12.8), "breath_maid:npc_jie_2": (45.4, 9.08),
    "breath_maid:npc_jie_3": (88, 17.6), "breath_maid:npc_jie_4": (120, 24),
    "breath_maid:npc_jie_5": (174, 34.8),
    "breath_maid:npc_xiang_1": (50, 9.98), "breath_maid:npc_xiang_2": (35.3, 7.06),
    "breath_maid:npc_xiang_3": (68, 13.6), "breath_maid:npc_xiang_4": (92, 18.4),
    "breath_maid:npc_xiang_5": (131, 26.3),
    "breath_maid:npc_item_1": (8, 0.6),  # 多彩膏
    "breath_maid:npc_55_food": (3.3, 0.3), "breath_maid:npc_yao": (3.3, 0.3),
    # netherite jewelry unchanged (netherite + slime both non-chainable)
    "breath_maid:npc_jie_6": (27012, 18008), "breath_maid:npc_xiang_6": (20259, 13506),
    # netherite kitchen knife unchanged
    "kaleidoscope_cookery:netherite_kitchen_knife": (2000, 1250),
    # ihzao
    "ihzao:chainmining": (500, 0), "ihzao:httravbag": (90, 60), "ihzao:magnetht": (57, 0),
    "ihzao:ancient_debris_plht": (17, 3), "ihzao:raw_iron_plht": (17, 3),
    "ihzao:raw_gold_plht": (17, 3), "ihzao:raw_copper_plht": (17, 3),
    "ihzao:fish_plht": (17, 3), "ihzao:beef_plht": (17, 3), "ihzao:salmon_plht": (17, 3),
    "ihzao:porkchop_plht": (17, 3), "ihzao:muttonraw_plht": (17, 3),
    "ihzao:rabbit_plht": (17, 3), "ihzao:chicken_plht": (17, 3),
    "ihzao:l_fallobjearehighl": (17, 3),
    "ihzao:leather_barmorht_1": (1.7, 0.75), "ihzao:leather_harmorht_1": (1.4, 0.63),
    "ihzao:leather_larmorht_1": (1.55, 0.69), "ihzao:iron_barmorht_1": (21.6, 9.6),
    "ihzao:golden_barmorht_1": (43.2, 19.2), "ihzao:diamond_barmorht_1": (120.6, 53.6),
    # ws glass
    "ws:clear_glass": (0.07, 0.04),
    # 森罗 tea final
    "kaleidoscope_cookery:butter_tea": (1.5, 0.5), "kaleidoscope_cookery:mystery_tea": (1, 0.35),
    "kaleidoscope_cookery:tea_egg": (1, 0.35),
    "kaleidoscope_cookery:barley_tea": (1, 0.36), "kaleidoscope_cookery:biluochun": (1, 0.36),
    "kaleidoscope_cookery:oolong": (1, 0.36), "kaleidoscope_cookery:tieguanyin": (1, 0.36),
    "kaleidoscope_cookery:sakura_fubuki": (1, 0.36), "kaleidoscope_cookery:flower_tea": (1, 0.36),
    "kaleidoscope_cookery:barley_tea_bag": (1.5, 1), "kaleidoscope_cookery:biluochun_tea_bag": (1.5, 1),
    "kaleidoscope_cookery:butter_tea_bag": (1.5, 1), "kaleidoscope_cookery:oolong_tea_bag": (1.5, 1),
    "kaleidoscope_cookery:sakura_fubuki_tea_bag": (1.5, 1), "kaleidoscope_cookery:tieguanyin_tea_bag": (1.5, 1),
    # farmer's delight (3x on meat-heavy materials; meat stays)
    "farmer_delight_nullgr:beef_stew": (12.6, 4.2), "farmer_delight_nullgr:beef_patty": (12.3, 4.1),
    "farmer_delight_nullgr:chicken_cuts": (10.5, 3.5),
    "farmer_delight_nullgr:chicken_sandwich": (13.2, 4.4),
    "farmer_delight_nullgr:chicken_soup": (10.8, 3.6),
    "farmer_delight_nullgr:fried_rice": (6.7, 2.2), "farmer_delight_nullgr:mutton_wrap": (12, 4),
    "farmer_delight_nullgr:steak_and_potatoes": (12.3, 4.1),
    "farmer_delight_nullgr:apple_cider": (1.5, 0.5),
    "farmer_delight_nullgr:dumplings": (12.3, 4.1), "farmer_delight_nullgr:pincers": (3.6, 2.4),
}

# ================================================================ apply
changed = Counter()
for r in data["systemShopItems"]:
    nm = res(r)
    ns = nm.split(":", 1)[0]
    name = nm.split(":", 1)[1] if ":" in nm else nm
    old = (r[1], r[2])
    new = None
    if ns == "minecraft" and (name in KEEP_MC or name.endswith("_spawn_egg")
                              or name.startswith("music_disc") or "skull" in name
                              or name.endswith("_head") or name == "painting"):
        new = old  # keep
    elif ns in ("bricefire", "ysm_maid"):  # whole mods keep (maid service items)
        new = old
    elif ns == "kaleidoscope_tavern" and (name.endswith("_painting") or name == "painting"):
        new = old  # paintings keep (300/10 collection items)
    elif nm in EXPLICIT:
        new = EXPLICIT[nm]
    elif name in CROP_DIV2:
        new = (r2(r[1] / 2.0), r2(r[2] / 2.0))
    elif name in CROP_DIV3:
        new = (r2(r[1] / 3.0), r2(r[2] / 3.0))
    elif nm in KALEIDO_PRICES:
        new = KALEIDO_PRICES[nm]  # recipe-derived dish/drink prices
    elif ns == "minecraft" and name in RECIPES:
        mat, tax = RECIPES[name]
        new = (r2(mat * tax), r2(mat))
    elif ns == "minecraft" and name.startswith("skull"):
        new = old
    elif ns == "kaleidoscope_tavern" and (name.endswith("_painting") or name == "painting"):
        new = old  # paintings keep
    elif ns == "ihzao" and ("barmorht" in name or "harmorht" in name or "larmorht" in name):
        new = old if name.startswith(("chainmail", "netherite")) else None  # handled in EXPLICIT
    else:
        new = (r2(r[1] / 30.0), r2(r[2] / 30.0))
    if new is None:
        new = old
    if new != old:
        r[1], r[2] = new
        changed[nm] = old
log.append(("REANCHOR", "shop items", f"{len(changed)} repriced"))

# ================================================================ kill rewards
kill = {
    0.18: ["zombie", "skeleton", "cave_spider", "husk", "stray", "drowned", "bogged",
           "silverfish", "endermite", "piglin", "zombie_villager", "slime"],
    0.15: ["spider"],
    0.27: ["creeper", "magma_cube", "pillager"],
    0.36: ["witch", "enderman", "phantom", "guardian", "vex"],
    0.45: ["wither_skeleton"],
    0.63: ["blaze", "ghast", "evoker", "vindicator", "shulker", "piglin_brute",
           "hoglin", "zoglin", "breeze"],
    1.5: ["ravager", "elder_guardian"],
    3.0: ["warden"],
    8.0: ["wither"],
    12.0: ["ender_dragon"],
    0.1: ["polar_bear", "zombie_piglin"],
    0.0: ["chicken", "cow", "pig", "sheep", "rabbit", "cat", "ocelot", "wolf", "fox",
          "parrot", "turtle", "dolphin", "panda", "frog", "axolotl", "armadillo",
          "bee", "bat", "squid", "glow_squid", "mooshroom", "horse", "donkey", "mule",
          "llama", "camel", "goat", "sniffer", "strider", "iron_golem", "snow_golem",
          "villager", "wandering_trader", "allay", "cod", "salmon", "tropical_fish",
          "pufferfish"],
}
krm = {}
for coins, mobs in kill.items():
    for m in mobs:
        krm[f"minecraft:{m}"] = [float(coins), "金币"]
data["killEntityRewardMap"] = krm
log.append(("KILL", "killEntityRewardMap", f"{len(krm)} entries, zombie=0.18"))

# ================================================================ pool tickets
# 武器/工具/防具三池票价按"下界合金大奖回收价"重核（合金不降价，1% 大奖回收期望需 <= 票价）
TICKETS = {"你饿了么": 15, "炼金学徒": 10, "附魔书店": 250, "武器池": 40, "工具商店": 45,
           "防具盲盒": 90, "花语盒": 4, "森罗美食": 3, "森罗酒馆": 3, "齿轮杂货铺": 6,
           "唱片盒": 350, "宠物盲盒": 150, "钓鱼佬的日常": 80}
for p in data["luckyDraws"]:
    if p["name"] in TICKETS:
        p["buyPrice"] = float(TICKETS[p["name"]])
log.append(("TICKETS", "luckyDraws", str(TICKETS)))

# ================================================================ rebuild 森罗 pool weights from new prices
import math


def w_price(v):
    return max(1, min(60, round(20 / math.sqrt(max(v, 1e-6)))))


def rebuild_pool(pname, ns, quality_fn, extra=()):
    rewards = []
    for r in data["systemShopItems"]:
        nm = res(r)
        if nm.startswith(f"{ns}:") and r[6] in ("森罗菜品", "森罗酒类") or nm in extra:
            v = r[2] / (r[0].get("count") or 1)
            q = quality_fn(v)
            rewards.append({"items": [{"count": 1, "newAuxValue": 0, "newItemName": nm}],
                            "quality": q, "weight": w_price(v)})
    for p in data["luckyDraws"]:
        if p["name"] == pname:
            p["rewards"] = rewards
            return


rebuild_pool("森罗美食", "kaleidoscope_cookery",
             lambda v: "legendary" if v >= 2.5 else ("rare" if v >= 0.6 else "common"))
rebuild_pool("森罗酒馆", "kaleidoscope_tavern",
             lambda v: "legendary" if v >= 2 else ("rare" if v >= 0.7 else "common"),
             extra=("create:builders_tea",))
log.append(("POOLS", "森罗美食/森罗酒馆", "weights rebuilt from new dish prices"))

# ================================================================ save + report
OUT_JSON.write_text(json.dumps(wrap, ensure_ascii=False, indent=2), encoding="utf-8")
text = json.dumps(wrap, ensure_ascii=False, separators=(",", ":"))
raw = zlib.compress(text.encode("utf-8"), level=9)
OUT_TXT.write_text("ppcpdata2%" + base64.b64encode(raw).decode("ascii"), encoding="utf-8")

zero = [res(r) for r in data["systemShopItems"] if r[1] == 0.0 and r[2] == 0.0]
lines = ["# 08205 落地报告（新价格体系：生长约束作物锚 + 配方重算）", "",
         f"- 基线：08202（2362 条）→ 输出：**08205.txt**（{len(data['systemShopItems'])} 条）",
         f"- 重锚条目数：{len(changed)}；剩余 0/0：{zero or '无'}",
         f"- 击杀表：{len(krm)} 条（僵尸 0.18=20只换铁剑3.6；苦力怕 0.27；被动 0；凋灵 8/龙 12）",
         "", "## 重锚规则", "",
         "- 可连锁采集品：÷30（0.01 地板、两位小数；稀有度比例保留）",
         "- 不降：怪物掉落/肉蛋奶蜂蜜/下界合金/附魔书/稀有掉落/刷怪蛋/唱片/冰火/女仆服务类/名画/锁链甲",
         "- 合成税：简单配方 1.5×、多次合成 1.8×、料理 3×、饰品 5×",
         "- 茶：茶包 1.5/1、旧式茶统一 1/0.36、新式茶 0.5–1.5",
         "- 连锁挖矿 500/0；抽奖票价按新奖品价值重定", "",
         "## 抽奖票价", ""]
for p in data["luckyDraws"]:
    lines.append(f"- {p['name']}: {p['buyPrice']}")
lines += ["", "## 抽查（新价）", ""]
for nm in ["minecraft:iron_ingot", "minecraft:diamond", "minecraft:iron_sword",
           "minecraft:diamond_chestplate", "minecraft:anvil", "minecraft:bread",
           "minecraft:cake", "minecraft:golden_apple", "minecraft:enchanted_golden_apple",
           "minecraft:oak_log", "minecraft:wheat", "minecraft:cobblestone",
           "create:mechanical_arm", "breath_maid:npc_jie_1", "breath_maid:npc_jie_6",
           "ihzao:chainmining", "ihzao:httravbag", "farmer_delight_nullgr:beef_stew",
           "kaleidoscope_cookery:butter_tea", "kaleidoscope_cookery:oolong"]:
    hit = [r for r in data["systemShopItems"] if res(r) == nm]
    if hit:
        lines.append(f"- {nm}: {hit[0][1]}/{hit[0][2]}")
    else:
        lines.append(f"- {nm}: NOT FOUND")
REPORT.write_text("\n".join(lines), encoding="utf-8")
print(f"OK items={len(data['systemShopItems'])} repriced={len(changed)} zero={len(zero)}")
print("tickets:", {p['name']: p['buyPrice'] for p in data['luckyDraws']})
