# -*- coding: utf-8 -*-
"""原版合成/熔炼配方表：产物 -> [(材料[(名,数量)], 产出数)]。

用于"玩家最低获取成本"计算（配方法成本口径修复，见 fix_truecost_09218.py）。
材料名均为完整命名空间（minecraft:xxx）；熔炼以 1 煤/8 件折算燃料成本。
"""
from collections import defaultdict

COAL_PER_SMELT = 0.125  # 1 煤熔炼 8 件


def build_vanilla_recipes():
    V = defaultdict(list)

    def add(res, mats, out=1):
        V["minecraft:" + res].append((mats, out))

    MC = "minecraft:"
    wood = ["oak", "spruce", "birch", "jungle", "acacia", "dark_oak",
            "mangrove", "cherry", "crimson", "warped"]
    for w in wood:
        log = MC + (w + "_log" if w not in ("crimson", "warped") else w + "_stem")
        add(w + "_planks", [(log, 1)], 4)
        add(w + "_slab", [(MC + w + "_planks", 3)], 6)
        add(w + "_fence", [(MC + w + "_planks", 4), (MC + "stick", 2)], 3)
        add(w + "_trapdoor", [(MC + w + "_planks", 6)], 2)
        add(w + "_pressure_plate", [(MC + w + "_planks", 2)], 1)
        add(w + "_sign", [(MC + w + "_planks", 6), (MC + "stick", 1)], 3)
    add("bamboo_planks", [(MC + "bamboo_block", 1)], 2)
    add("bamboo_slab", [(MC + "bamboo_planks", 3)], 6)
    add("bamboo_trapdoor", [(MC + "bamboo_planks", 6)], 2)
    add("bamboo_raft", [(MC + "bamboo_planks", 5)], 1)
    add("stick", [(MC + "oak_planks", 2)], 4)
    add("chest", [(MC + "oak_planks", 8)], 1)
    add("hopper", [(MC + "iron_ingot", 5), (MC + "chest", 1)], 1)
    add("lever", [(MC + "stick", 1), (MC + "cobblestone", 1)], 1)
    add("bowl", [(MC + "oak_planks", 3)], 4)
    add("bucket", [(MC + "iron_ingot", 3)], 1)
    add("paper", [(MC + "sugar_cane", 3)], 3)
    add("sugar", [(MC + "sugar_cane", 1)], 1)
    add("ladder", [(MC + "stick", 7)], 3)
    add("barrel", [(MC + "oak_planks", 6), (MC + "oak_slab", 2)], 1)
    add("composter", [(MC + "oak_slab", 7)], 1)
    add("campfire", [(MC + "stick", 3), (MC + "coal", 1), (MC + "oak_log", 3)], 1)
    add("soul_campfire", [(MC + "stick", 3), (MC + "soul_sand", 1), (MC + "oak_log", 3)], 1)
    add("lantern", [(MC + "iron_nugget", 8), (MC + "torch", 1)], 1)
    add("soul_lantern", [(MC + "iron_nugget", 8), (MC + "soul_torch", 1)], 1)
    add("torch", [(MC + "coal", 1), (MC + "stick", 1)], 4)
    add("soul_torch", [(MC + "coal", 1), (MC + "stick", 1), (MC + "soul_sand", 1)], 4)
    add("end_rod", [(MC + "blaze_rod", 1), (MC + "popped_chorus_fruit", 1)], 4)
    add("ender_eye", [(MC + "ender_pearl", 1), (MC + "blaze_powder", 1)], 1)
    add("blaze_powder", [(MC + "blaze_rod", 1)], 2)
    add("glistering_melon_slice", [(MC + "gold_nugget", 8), (MC + "melon_slice", 1)], 1)
    add("golden_carrot", [(MC + "gold_nugget", 8), (MC + "carrot", 1)], 1)
    add("golden_apple", [(MC + "gold_ingot", 8), (MC + "apple", 1)], 1)
    add("pumpkin_pie", [(MC + "pumpkin", 1), (MC + "sugar", 1), (MC + "egg", 1)], 1)
    add("painting", [(MC + "stick", 8), (MC + "white_wool", 1)], 1)
    add("item_frame", [(MC + "stick", 8), (MC + "leather", 1)], 1)
    add("flower_pot", [(MC + "brick", 3)], 1)
    add("grindstone", [(MC + "stick", 2), (MC + "stone_slab", 1), (MC + "oak_planks", 2)], 1)
    add("stone_button", [(MC + "stone", 1)], 1)
    add("heavy_weighted_pressure_plate", [(MC + "iron_ingot", 2)], 1)
    add("chain", [(MC + "iron_ingot", 1), (MC + "iron_nugget", 2)], 1)
    add("iron_hoe", [(MC + "iron_ingot", 2), (MC + "stick", 2)], 1)
    for raw, ck in [("beef", "cooked_beef"), ("chicken", "cooked_chicken"),
                    ("porkchop", "cooked_porkchop"), ("mutton", "cooked_mutton"),
                    ("rabbit", "cooked_rabbit"), ("cod", "cooked_cod"),
                    ("salmon", "cooked_salmon")]:
        add(ck, [(MC + raw, 1), (MC + "coal", COAL_PER_SMELT)], 1)
    for ore, out in [("iron_ore", "iron_ingot"), ("deepslate_iron_ore", "iron_ingot"),
                     ("raw_iron", "iron_ingot"),
                     ("gold_ore", "gold_ingot"), ("deepslate_gold_ore", "gold_ingot"),
                     ("nether_gold_ore", "gold_ingot"),
                     ("copper_ore", "copper_ingot"), ("deepslate_copper_ore", "copper_ingot"),
                     ("coal_ore", "coal"), ("deepslate_coal_ore", "coal"),
                     ("redstone_ore", "redstone"), ("deepslate_redstone_ore", "redstone"),
                     ("lapis_ore", "lapis_lazuli"), ("deepslate_lapis_ore", "lapis_lazuli"),
                     ("diamond_ore", "diamond"), ("deepslate_diamond_ore", "diamond"),
                     ("emerald_ore", "emerald"), ("deepslate_emerald_ore", "emerald"),
                     ("nether_quartz_ore", "quartz"),
                     ("cobblestone", "stone"), ("cobbled_deepslate", "deepslate"),
                     ("sand", "glass"), ("clay_ball", "brick")]:
        V[MC + out].append(([(MC + ore, 1), (MC + "coal", COAL_PER_SMELT)], 1))
    add("iron_ingot", [(MC + "iron_nugget", 9)], 1)
    add("gold_ingot", [(MC + "gold_nugget", 9)], 1)
    add("iron_nugget", [(MC + "iron_ingot", 1)], 9)
    add("gold_nugget", [(MC + "gold_ingot", 1)], 9)
    add("iron_ingot", [(MC + "iron_block", 1)], 9)
    add("gold_ingot", [(MC + "gold_block", 1)], 9)
    add("diamond", [(MC + "diamond_block", 1)], 9)
    add("quartz", [(MC + "quartz_block", 1)], 4)
    add("quartz_block", [(MC + "quartz", 4)], 1)
    add("quartz_bricks", [(MC + "quartz_block", 4)], 4)
    add("quartz_pillar", [(MC + "quartz_block", 2)], 2)
    add("chiseled_quartz_block", [(MC + "quartz_slab", 2)], 1)
    add("sandstone", [(MC + "sand", 4)], 1)
    add("red_sandstone", [(MC + "red_sand", 4)], 1)
    add("packed_ice", [(MC + "ice", 9)], 1)
    add("blue_ice", [(MC + "packed_ice", 9)], 1)
    add("amethyst_block", [(MC + "amethyst_shard", 4)], 1)
    add("white_wool", [(MC + "string", 4)], 1)
    for c in ["red", "blue", "brown", "cyan", "gray", "green", "light_blue",
              "light_gray", "lime", "magenta", "orange", "pink", "purple",
              "yellow", "black"]:
        add(c + "_wool", [(MC + "white_wool", 1), (MC + c + "_dye", 1)], 1)
    add("smooth_stone", [(MC + "stone", 1), (MC + "coal", COAL_PER_SMELT)], 1)
    add("smooth_quartz", [(MC + "quartz_block", 1), (MC + "coal", COAL_PER_SMELT)], 1)
    add("smooth_basalt", [(MC + "basalt", 1), (MC + "coal", COAL_PER_SMELT)], 1)
    add("glass_bottle", [(MC + "glass", 3)], 3)
    add("coal", [(MC + "coal_block", 1)], 9)
    # 原版熔炼：腐肉 -> 皮革（Java/Bedrock 均有）
    V[MC + "leather"].append(([(MC + "rotten_flesh", 1), (MC + "coal", COAL_PER_SMELT)], 1))
    return V


# 森罗磨石（millstone）对原版材料的转化路径（模组机器，无额外消耗）。
# 这些是玩家真实可用的廉价获取路径，必须计入最低获取成本，否则卖价封顶失真。
KALEIDO_CONVERSIONS = [
    ("minecraft:gilded_blackstone", "minecraft:gold_nugget", 3),
    ("minecraft:nether_gold_ore", "minecraft:gold_nugget", 5),
    ("minecraft:diamond_ore", "minecraft:diamond", 2),
    ("minecraft:deepslate_diamond_ore", "minecraft:diamond", 2),
    ("minecraft:emerald_ore", "minecraft:emerald", 2),
    ("minecraft:deepslate_emerald_ore", "minecraft:emerald", 2),
    ("minecraft:coal_ore", "minecraft:coal", 3),
    ("minecraft:deepslate_coal_ore", "minecraft:coal", 3),
    ("minecraft:lapis_ore", "minecraft:lapis_lazuli", 7),
    ("minecraft:deepslate_lapis_ore", "minecraft:lapis_lazuli", 7),
    ("minecraft:redstone_ore", "minecraft:redstone", 7),
    ("minecraft:deepslate_redstone_ore", "minecraft:redstone", 7),
    ("minecraft:nether_quartz_ore", "minecraft:quartz", 3),
    ("minecraft:quartz_block", "minecraft:quartz", 3),
    ("minecraft:iron_ore", "minecraft:raw_iron", 3),
    ("minecraft:deepslate_iron_ore", "minecraft:raw_iron", 3),
    ("minecraft:gold_ore", "minecraft:raw_gold", 3),
    ("minecraft:deepslate_gold_ore", "minecraft:raw_gold", 3),
    ("minecraft:copper_ore", "minecraft:raw_copper", 5),
    ("minecraft:deepslate_copper_ore", "minecraft:raw_copper", 5),
    ("minecraft:bone", "minecraft:bone_meal", 5),
    ("minecraft:flint", "minecraft:gunpowder", 1),
    ("minecraft:amethyst_block", "minecraft:amethyst_shard", 3),
    ("minecraft:white_wool", "minecraft:string", 3),
    ("minecraft:cobblestone", "minecraft:smooth_stone", 1),
    ("minecraft:stone", "minecraft:cobblestone", 1),
]


def add_kaleido_conversions(V):
    """把森罗磨石转化路径并入配方表。"""
    for src, out, cnt in KALEIDO_CONVERSIONS:
        V[out].append(([(src, 1)], cnt))
    # raw_* 熔炼（并入后与磨石路径联动）
    for raw, ing in [("minecraft:raw_iron", "minecraft:iron_ingot"),
                     ("minecraft:raw_gold", "minecraft:gold_ingot"),
                     ("minecraft:raw_copper", "minecraft:copper_ingot")]:
        V[ing].append(([(raw, 1), ("minecraft:coal", COAL_PER_SMELT)], 1))
    # 磨石可磨的染色羊毛同白羊毛（成员过多，模式生成）
    for c in ["orange", "magenta", "light_blue", "yellow", "lime", "pink",
              "gray", "light_gray", "cyan", "purple", "blue", "brown",
              "green", "red", "black"]:
        V["minecraft:string"].append(([(f"minecraft:{c}_wool", 1)], 3))
    return V


def true_costs(shop_buy, iters=60):
    """固定点：玩家最低获取单价 = min(商店买价, 自制成本)。"""
    V = build_vanilla_recipes()
    add_kaleido_conversions(V)
    cost = dict(shop_buy)
    for _ in range(iters):
        changed = False
        for res, vlist in V.items():
            best = None
            for mats, out in vlist:
                tot, ok = 0.0, True
                for m, q in mats:
                    mc = cost.get(m)
                    if mc is None:
                        ok = False
                        break
                    tot += mc * q
                if ok:
                    c = tot / out
                    if best is None or c < best:
                        best = c
            if best is None:
                continue
            cur = cost.get(res)
            if cur is None or best < cur - 1e-9:
                cost[res] = best
                changed = True
        if not changed:
            break
    return cost
