# -*- coding: utf-8 -*-
"""08202 -> 08209：÷30 → ÷10 全局重锚 + 分级人工价值（制作卖出微利）。

规则（用户已确认）：
- 尺度：可连锁采集品 ÷30 → ÷10（直接从原始价 ÷10），作物 ÷3/÷2 保持、不降保持。
- 人工价值：配方物品卖价 = 材料 × (1+人工率)，人工率分级 简单10%/多次15%/料理20%/饰品25%。
- 覆盖：vanilla 配方 + 森罗料理 + 饰品(EXPLICIT) 全部。
- 击杀奖励、抽奖票价 ×3；死亡 100→3；公告重写。
- 防套利：卖价强制 < 买价（0.01 地板除外）。

用法（04_工具脚本/ 下）：python implement_08209.py
"""
import ast
import base64
import json
import zlib
from collections import Counter
from pathlib import Path

from kaleido_prices import KALEIDO_PRICES
from ppcp_lib import namespace_maps, resolve_nin

ROOT = Path(r"C:/Users/AI10/Desktop/ppcdata")
SRC = ROOT / "01_配置明文" / "08202_decoded.json"
IMPL = ROOT / "04_工具脚本" / "implement_08203.py"
OUT_JSON = ROOT / "01_配置明文" / "08209_decoded.json"
OUT_TXT = ROOT / "06_用户自行导入" / "08209.txt"
REPORT = ROOT / "03_对比报告" / "08209_落地报告.md"

LABOR = {1.5: 0.10, 1.8: 0.15, 3: 0.20, 5: 0.25}
MOD_LABOR = {"breath_maid": 0.25, "create": 0.15, "ihzao": 0.15,
             "ws": 0.15, "kaleidoscope_cookery": 0.20, "farmer_delight_nullgr": 0.20}
KEEP_EXPLICIT = {"breath_maid:npc_jie_6", "breath_maid:npc_xiang_6",
                 "kaleidoscope_cookery:netherite_kitchen_knife", "ihzao:chainmining"}

ING_ITEM = {
    "iron": "iron_ingot", "gold": "gold_ingot", "diamond": "diamond",
    "cobble": "cobblestone", "plank": "oak_planks", "stick": "stick",
    "string": "string", "leather": "leather", "slime": "slime_ball",
    "redstone": "redstone", "quartz": "quartz", "wheat": "wheat",
    "egg": "egg", "sugar": "sugar", "paper": "paper", "book": "book",
    "chest": "chest", "apple": "apple", "carrot": "carrot", "potato": "potato",
    "beef": "beef", "porkchop": "porkchop", "chicken": "chicken", "mutton": "mutton",
    "rice": "rice", "gunpowder": "gunpowder", "sand": "sand", "obsidian": "obsidian",
    "flint": "flint", "glass": "glass", "kelp": "kelp", "copper": "copper_ingot",
    "zinc": "zinc_ingot", "andesite": "andesite", "cake": "cake", "bone": "bone",
    "gold_nugget": "gold_nugget", "bucket": "bucket", "bow": "bow", "furnace": "furnace",
}


def r2f(x):
    return max(0.01, round(float(x) + 1e-12, 2))


def extract_assigns(src: str):
    tree = ast.parse(src)
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id in ("ING", "RECIPES", "EXPLICIT", "kill", "TICKETS"):
                    out[t.id] = node.value
    return out


def main():
    wrap = json.loads(SRC.read_text(encoding="utf-8"))
    data = wrap["data"]
    rev, _ = namespace_maps(data)
    items = data["systemShopItems"]
    eco = data["ecoSystemData"]

    assigns = extract_assigns(IMPL.read_text(encoding="utf-8"))
    ING = ast.literal_eval(assigns["ING"])
    EXPLICIT = ast.literal_eval(assigns["EXPLICIT"])
    recipe_names = {k.value for k in assigns["RECIPES"].keys}
    rec_code = compile(ast.Expression(assigns["RECIPES"]), "<recipes>", "eval")

    KEEP_MC = set("""enchanted_book netherite_ingot netherite_scrap netherite_block netherite_sword
netherite_pickaxe netherite_axe netherite_shovel netherite_hoe netherite_helmet
netherite_chestplate netherite_leggings netherite_boots netherite_upgrade_smithing_template
ancient_debris bone bone_meal rotten_flesh gunpowder string spider_eye slime_ball leather
rabbit_hide feather egg milk_bucket honey_bottle honeycomb beef porkchop chicken mutton rabbit
cod salmon tropical_fish pufferfish cooked_beef cooked_porkchop cooked_chicken cooked_mutton
cooked_rabbit cooked_cod cooked_salmon blaze_rod blaze_powder ghast_tear magma_cream ender_pearl
phantom_membrane nautilus_shell heart_of_the_sea nether_star beacon elytra totem_of_undying
trident shulker_shell shulker_box ender_chest dragon_breath prismarine_shard prismarine_crystals
echo_shard goat_horn skull wither_rose saddle name_tag lead chainmail_helmet chainmail_chestplate
chainmail_leggings chainmail_boots recovery_compass ominous_bottle trial_key breeze_rod heavy_core
painting pufferfish_bucket tropical_fish_bucket cod_bucket salmon_bucket axolotl_bucket
tadpole_bucket turtle_egg sniffer_egg frogspawn""".split())

    CROP_DIV3 = set("""wheat carrot potato beetroot melon pumpkin melon_slice sweet_berries
glow_berries kelp bamboo sugar_cane sugar nether_wart wheat_seeds melon_seeds pumpkin_seeds
beetroot_seeds torchflower_seeds pitcher_pod rice rice_panicle wild_rice tomato lettuce
green_chili red_chili chili_seed tomato_seed lettuce_seed wild_rice_seed fresh_tea_leaves oil
grape green_grape gold_grape ice_grape wild_grape grape_crop green_grape_crop gold_grape_crop
ice_grape_crop grapevine wild_grapevine wild_grapevine_plant gold_grapevine_trellis
grapevine_trellis ice_grapevine_trellis vine honey_grape""".split())
    CROP_DIV2 = set("""cocoa_beans""".split())

    def is_keep(ns, name):
        if ns == "minecraft":
            return (name in KEEP_MC or name.endswith("_spawn_egg")
                    or name.startswith("music_disc") or "skull" in name
                    or name.endswith("_head") or name == "painting"
                    or name.startswith("skull"))
        if ns in ("bricefire", "ysm_maid"):
            return True
        if ns == "kaleidoscope_tavern" and (name.endswith("_painting") or name == "painting"):
            return True
        return False

    # ================================================================ 第一遍：重锚（÷10 直除）
    changed = Counter()
    for r in items:
        nin = r[0].get("NIN", "")
        p, n = nin.split(":", 1) if ":" in nin else ("", nin)
        ns = rev.get(p, "?" + p)
        nm = f"{ns}:{n}"
        name = n
        old = (r[1], r[2])
        new = None
        if is_keep(ns, name):
            new = old
        elif nm in EXPLICIT:
            new = EXPLICIT[nm] if nm in KEEP_EXPLICIT else (r2f(EXPLICIT[nm][0] * 3), r2f(EXPLICIT[nm][1] * 3))
        elif name in CROP_DIV2:
            new = (r2f(r[1] / 2.0), r2f(r[2] / 2.0))
        elif name in CROP_DIV3:
            new = (r2f(r[1] / 3.0), r2f(r[2] / 3.0))
        elif nm in KALEIDO_PRICES:
            new = (r2f(KALEIDO_PRICES[nm][0] * 3), r2f(KALEIDO_PRICES[nm][1] * 3))
        elif ns == "minecraft" and name in recipe_names:
            new = old  # 配方项第二遍重算
        elif ns == "ihzao" and ("barmorht" in name or "harmorht" in name or "larmorht" in name):
            new = old if name.startswith(("chainmail", "netherite")) else None
        else:
            new = (r2f(r[1] / 10.0), r2f(r[2] / 10.0))  # ÷10 直除
        if new is None:
            new = old
        if new != old:
            r[1], r[2] = new
            changed[nm] = old

    # ================================================================ 第二遍：vanilla 配方重算（单价 + 人工价值）
    shop = {}
    for r in items:
        shop[resolve_nin(r[0].get("NIN", ""), rev)] = (r[1], r[2], r[0].get("count") or 1)

    per_buy = {nm: buy / cnt for nm, (buy, _, cnt) in shop.items()}
    for _ in range(20):
        ING_now = {k: per_buy.get(f"minecraft:{ING_ITEM[k]}", ING[k]) for k in ING}
        REC_now = eval(rec_code, {"ING": ING_now})
        moved = False
        for name, (mat, tax) in REC_now.items():
            full = f"minecraft:{name}"
            if full not in shop:
                continue
            new_per = r2f(mat * tax) / shop[full][2]
            if abs(new_per - per_buy.get(full, 0.0)) > 1e-9:
                per_buy[full] = new_per
                moved = True
        if not moved:
            break

    ING_final = {k: per_buy.get(f"minecraft:{ING_ITEM[k]}", ING[k]) for k in ING}
    REC_final = eval(rec_code, {"ING": ING_final})

    p = lambda item: per_buy.get(f"minecraft:{item}", 0.0)
    bookshelf = 6 * p("oak_planks") + 3 * p("book")
    manual = {
        "lectern": (4 * p("oak_planks") + bookshelf, 1.5),
        "smoker": (p("furnace") + 4 * p("oak_log"), 1.8),
        "bundle": (6 * p("rabbit_hide") + 2 * p("string"), 1.5),
    }

    for r in items:
        nm = resolve_nin(r[0].get("NIN", ""), rev)
        if not nm.startswith("minecraft:"):
            continue
        name = nm.split(":", 1)[1]
        if name in manual:
            mat, tax = manual[name]
        elif name in REC_final:
            mat, tax = REC_final[name]
        else:
            continue
        r[1] = r2f(mat * tax)
        r[2] = r2f(mat * (1 + LABOR.get(tax, 0.15)))

    # ================================================================ 第三遍：KALEIDO + EXPLICIT 人工价值（卖价加人工率）
    for r in items:
        nin = r[0].get("NIN", "")
        p, n = nin.split(":", 1) if ":" in nin else ("", nin)
        ns = rev.get(p, "?" + p)
        nm = f"{ns}:{n}"
        if nm in KALEIDO_PRICES:
            r[2] = r2f(r[2] * 1.20)
        elif nm in EXPLICIT and ns in MOD_LABOR and nm not in KEEP_EXPLICIT:
            r[2] = r2f(r[2] * (1 + MOD_LABOR[ns]))

    # ================================================================ 防套利：卖价强制 < 买价
    for r in items:
        if r[1] > 0.01 and r[2] >= r[1]:
            r[2] = round(r[1] - 0.01, 2)
        elif r[1] == 0.01 and r[2] > 0.01:
            r[2] = 0.01

    # ================================================================ 击杀表 ×3（用 08203 重锚值）
    kill = ast.literal_eval(assigns["kill"])
    krm = {}
    for coins, mobs in kill.items():
        for m in mobs:
            krm[f"minecraft:{m}"] = [round(float(coins) * 3.0, 2), "金币"]
    data["killEntityRewardMap"] = krm

    # ================================================================ 抽奖票价 ×3（用 08203 重锚值）
    tickets = ast.literal_eval(assigns["TICKETS"])
    for pr in data["luckyDraws"]:
        if pr["name"] in tickets:
            pr["buyPrice"] = round(float(tickets[pr["name"]]) * 3.0, 2)

    # ================================================================ 死亡 + 公告
    eco["deathLoseMoney"] = 3.0
    ns_count = Counter()
    for r in items:
        ns_count[resolve_nin(r[0].get("NIN", ""), rev).split(":", 1)[0]] += 1
    ench = sum(1 for r in items if "附魔书" in (r[6] or ""))
    farm = ns_count.get("farmer_delight_nullgr", 0) + ns_count.get("farmers_tale_nullgr", 0)
    eco["noticeMsg"] = (
        f"仅金币｜原版{ns_count.get('minecraft', 0)}(附魔书{ench})"
        f"｜森罗厨{ns_count.get('kaleidoscope_cookery', 0)}+酒{ns_count.get('kaleidoscope_tavern', 0)}"
        f"+偶{ns_count.get('kaleidoscope_doll', 0)}｜冰火{ns_count.get('bricefire', 0)}"
        f"｜旅行袋{ns_count.get('ihzao', 0)}｜车万女仆{ns_count.get('ysm_maid', 0)}"
        f"｜机械{ns_count.get('create', 0)}｜娘化{ns_count.get('breath_maid', 0)}"
        f"｜农夫{farm}｜透明玻璃{ns_count.get('ws', 0)}｜合计{len(items)}"
        f"｜开局73｜在线+1/分｜基金隐藏｜死亡固定扣3｜附魔书仅满级/次顶级"
    )

    # ================================================================ 保存
    OUT_JSON.write_text(json.dumps(wrap, ensure_ascii=False, indent=2), encoding="utf-8")
    text = json.dumps(wrap, ensure_ascii=False, separators=(",", ":"))
    raw = zlib.compress(text.encode("utf-8"), level=9)
    OUT_TXT.write_text("ppcpdata2%" + base64.b64encode(raw).decode("ascii"), encoding="utf-8")

    # ================================================================ 校验
    bad = []
    for r in items:
        nm = resolve_nin(r[0].get("NIN", ""), rev)
        if r[1] > 0 and r[2] >= r[1] and not (r[1] == r[2] == 0.01):
            bad.append((nm, r[1], r[2]))
    zero = [resolve_nin(r[0].get("NIN", ""), rev) for r in items if r[1] == 0.0 and r[2] == 0.0]

    # ================================================================ 报告
    lines = [
        "# 08209 落地报告（÷10 重锚 + 分级人工价值）", "",
        f"- 基线：08202 → 输出 **08209.txt**（{len(items)} 条）",
        "- 尺度：可连锁采集品 ÷30→÷10；作物 ÷3/÷2 保持；不降保持",
        "- 人工价值：卖价=材料×(1+人工率)，简单10%/多次15%/料理20%/饰品25%",
        "- 击杀表、抽奖票价 ×3；死亡 100→3；公告重写；卖价强制<买价",
        f"- 套利（卖≥买）违规：{len(bad)} 条；0/0：{len(zero)} 条", "",
        "## 抽查（新价 ÷10 + 人工价值）", "",
    ]
    for nm in ["minecraft:iron_ingot", "minecraft:diamond", "minecraft:iron_sword",
               "minecraft:diamond_chestplate", "minecraft:anvil", "minecraft:bread",
               "minecraft:cake", "minecraft:golden_apple", "minecraft:oak_log",
               "minecraft:wheat", "minecraft:cobblestone", "create:mechanical_arm",
               "breath_maid:npc_jie_1", "breath_maid:npc_jie_6", "ihzao:chainmining",
               "farmer_delight_nullgr:beef_stew", "kaleidoscope_cookery:butter_tea",
               "kaleidoscope_cookery:brown_mushroom_pot_soup"]:
        hit = [r for r in items if resolve_nin(r[0].get("NIN", ""), rev) == nm]
        lines.append(f"- {nm}: {hit[0][1]}/{hit[0][2]}" if hit else f"- {nm}: NOT FOUND")
    if bad:
        lines += ["", "## 套利违规明细", ""]
        lines += [f"- {nm}: {b}/{s}" for nm, b, s in bad[:30]]
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"OK items={len(items)} changed={len(changed)} bad={len(bad)} zero={len(zero)}")
    for line in lines[lines.index("## 抽查（新价 ÷10 + 人工价值）") + 1:]:
        if line.startswith("- "):
            print(line)


if __name__ == "__main__":
    main()
