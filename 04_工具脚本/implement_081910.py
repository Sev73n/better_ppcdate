# -*- coding: utf-8 -*-
"""08199 -> 081910:
1) Fix potions: drop all wrong (durability-encoded) rows, shelf = 12 top-tier splash potions (NAV encoding, verified via user markers: 9/10/11 = leaping I/long/II).
2) Rebuild 你饿了么 (common x12 / rare x1 / golden apples legendary) and 炼金学徒 (positive combat/utility splash potions, probability by quality).
3) Re-apply 08198 work lost in the user's export: price the 37 new items, 森罗菜品/森罗酒类 categories, 森罗美食/森罗酒馆 pools, npc_yao price, builders_tea price.
4) freeDrawType=4 on all pools; fix jump potion aux 6 -> 9 in weapon/tool/armor pools.
Preserve everything else (teleport, main page, broadcast epic, etc.).
"""
import base64, json, math, uuid, zlib
from collections import Counter
from pathlib import Path

ROOT = Path(r"C:/Users/AI10/Desktop/ppcdata")
SRC = ROOT / "01_配置明文" / "08199_decoded.json"
OUT_JSON = ROOT / "01_配置明文" / "081910_decoded.json"
OUT_TXT = ROOT / "06_用户自行导入" / "081910.txt"
REPORT = ROOT / "03_对比报告" / "081910_落地报告.md"

wrap = json.loads(SRC.read_text(encoding="utf-8"))
data = wrap["data"]
rev = {str(v): k for k, v in data["nameSpaceMap"].items()}
nsid = {k: str(v) for k, v in data["nameSpaceMap"].items()}
MC = nsid["minecraft"]
log = []


def res(r):
    nin = r[0].get("NIN", "")
    p, n = nin.split(":", 1) if ":" in nin else ("", nin)
    return f"{rev.get(p, '?' + p)}:{n}"


def price(ns, name, buy, sell, tag=None, count=None):
    hits = [r for r in data["systemShopItems"] if res(r) == f"{ns}:{name}"]
    if not hits:
        log.append(("MISS", f"{ns}:{name}", f"{buy}/{sell}"))
        return None
    for r in hits:
        r[1], r[2] = buy, sell
        if tag is not None:
            r[6] = tag
        if count is not None:
            r[0]["count"] = count
    return hits[0]


def drop_dup_zero():
    from collections import defaultdict
    by_name = defaultdict(list)
    for r in data["systemShopItems"]:
        by_name[res(r)].append(r)
    bad = [id(r) for rows in by_name.values() if len(rows) > 1
           for r in rows if r[1] == 0.0 and r[2] == 0.0]
    if bad:
        data["systemShopItems"] = [r for r in data["systemShopItems"] if id(r) not in bad]
        log.append(("DEDUP", "0/0 duplicate rows", f"{len(bad)} removed"))


def template(nin, extra=None):
    item = {"NIN": nin}
    if extra:
        item.update(extra)
    return [item, 0.0, 0.0, "", 0, 0, "", False, "金币", "金币", 0, 1.0, 64, 0.0, 0.9, 0.1]


# ================================================================ 1. potion overhaul
drop_dup_zero()
POTION_NAMES = ("potion", "splash_potion", "lingering_potion")
n_before = len(data["systemShopItems"])
data["systemShopItems"] = [
    r for r in data["systemShopItems"]
    if not (res(r).split(":", 1)[0] == "minecraft"
            and res(r).split(":", 1)[1] in POTION_NAMES)
]
n_dropped = n_before - len(data["systemShopItems"])
log.append(("POTION", "dropped wrong rows", f"{n_dropped} removed (durability/NAV-marker rows)"))

# top-tier splash shelf (Bedrock PotionType NAV ids)
SPLASH_SHELF = [
    (6, 80, 8),    # 夜视(延长)
    (8, 90, 9),    # 隐身(延长)
    (11, 100, 10),  # 跳跃II  (user marker 100/10)
    (13, 80, 8),   # 抗火(延长)
    (16, 90, 9),   # 迅捷II
    (20, 80, 8),   # 水肺(延长)
    (22, 100, 10),  # 治疗II
    (30, 100, 10),  # 再生II
    (33, 100, 10),  # 力量II
    (39, 120, 12),  # 龟甲大师II
    (41, 80, 8),   # 缓落(延长)
    (42, 100, 10),  # 风冲
]
for nav, b, s in SPLASH_SHELF:
    r = template(f"{MC}:splash_potion", {"NAV": nav})
    r[1], r[2], r[6] = float(b), float(s), "药水"
    data["systemShopItems"].append(r)
log.append(("POTION", "top splash shelf", f"{len(SPLASH_SHELF)} rows added (NAV encoding)"))

# ================================================================ 2. re-apply 08198 item pricing (lost in user export)
NEW_PRICES = [
    ("farmer_delight_nullgr", "apple_cider", 25, 6, "农夫乐事", 16),
    ("farmer_delight_nullgr", "beef_patty", 12, 4, "农夫乐事", 16),
    ("farmer_delight_nullgr", "beef_stew", 25, 8, "农夫乐事", 16),
    ("farmer_delight_nullgr", "chicken_cuts", 10, 3, "农夫乐事", 16),
    ("farmer_delight_nullgr", "chicken_sandwich", 15, 5, "农夫乐事", 16),
    ("farmer_delight_nullgr", "chicken_soup", 20, 6, "农夫乐事", 16),
    ("farmer_delight_nullgr", "fried_rice", 20, 6, "农夫乐事", 16),
    ("farmer_delight_nullgr", "mutton_wrap", 15, 5, "农夫乐事", 16),
    ("farmer_delight_nullgr", "steak_and_potatoes", 30, 9, "农夫乐事", 16),
    ("create", "builders_tea", 20, 5, "机械动力", 16),
    ("kaleidoscope_cookery", "butter_tea", 20, 5, "森罗菜品", 16),
    ("kaleidoscope_cookery", "mystery_tea", 25, 6, "森罗菜品", 16),
    ("kaleidoscope_cookery", "tea_egg", 12, 3, "森罗菜品", 16),
    ("kaleidoscope_cookery", "barley_tea_bag", 8, 2, "森罗物语（厨房）", 16),
    ("kaleidoscope_cookery", "biluochun_tea_bag", 15, 4, "森罗物语（厨房）", 16),
    ("kaleidoscope_cookery", "butter_tea_bag", 8, 2, "森罗物语（厨房）", 16),
    ("kaleidoscope_cookery", "oolong_tea_bag", 20, 5, "森罗物语（厨房）", 16),
    ("kaleidoscope_cookery", "sakura_fubuki_tea_bag", 12, 3, "森罗物语（厨房）", 16),
    ("kaleidoscope_cookery", "tieguanyin_tea_bag", 12, 3, "森罗物语（厨房）", 16),
    ("kaleidoscope_cookery", "fresh_tea_leaves", 3, 0.75, "森罗物语（厨房）", 16),
    ("kaleidoscope_cookery", "kaleidoscope_cookery_bamboo_tube_rice", 38.75, 3.25, "森罗菜品", 16),
    ("kaleidoscope_cookery", "kaleidoscope_cookery_cold_roasted_meat", 30, 11.7, "森罗菜品", 16),
    ("kaleidoscope_cookery", "kaleidoscope_cookery_dongpo_pork", 38.25, 3.6, "森罗菜品", 16),
    ("kaleidoscope_cookery", "kaleidoscope_cookery_stuffed_tiger_skin_pepper", 40.31, 6.08, "森罗菜品", 16),
    ("kaleidoscope_cookery", "kaleidoscope_cookery_sweet_and_sour_ender_pearls", 724, 116.1, "森罗菜品", 16),
    ("kaleidoscope_tavern", "beer", 15, 4, "森罗酒类", 16),
    ("kaleidoscope_tavern", "kaleidoscope_tavern_honey_wine", 51, 11.7, "森罗酒类", 16),
    ("kaleidoscope_tavern", "kaleidoscope_tavern_ice_wine", 43, 4.5, "森罗酒类", 16),
    ("kaleidoscope_tavern", "kaleidoscope_tavern_molotov", 62.25, 4.5, "森罗酒类", 16),
    ("kaleidoscope_tavern", "kaleidoscope_tavern_mystery_cocktail", 160, 100, "森罗酒类", 16),
    ("kaleidoscope_tavern", "kaleidoscope_tavern_plum_wine", 43, 6.3, "森罗酒类", 16),
    ("kaleidoscope_tavern", "kaleidoscope_tavern_rum", 42.2, 6.3, "森罗酒类", 16),
    ("kaleidoscope_tavern", "kaleidoscope_tavern_sakura_wine", 45, 6.3, "森罗酒类", 16),
    ("kaleidoscope_tavern", "kaleidoscope_tavern_sweet_berry_wine", 43, 6.3, "森罗酒类", 16),
    ("kaleidoscope_tavern", "kaleidoscope_tavern_wine", 43, 4.5, "森罗酒类", 16),
    ("kaleidoscope_tavern", "kaleidoscope_tavern_holder", 35, 21.88, "森罗物语（酒馆）", 16),
    ("kaleidoscope_tavern", "bar_cabinet_clear", 35, 21.88, "森罗物语（酒馆）", 16),
    ("breath_maid", "npc_yao", 100, 10, "娘化生物", None),
]
for ns, name, b, s, tag, cnt in NEW_PRICES:
    price(ns, name, b, s, tag, cnt)

# ================================================================ 3. tags (re-add 森罗菜品/森罗酒类)
for t in ("森罗菜品", "森罗酒类"):
    if t not in data["customItemTags"]:
        data["customItemTags"].append(t)
data["customItemTypeMap"].setdefault("森罗菜品", {"texturePath": "textures/items/cake"})
data["customItemTypeMap"].setdefault("森罗酒类", {"texturePath": "textures/kaleidoscope_tavern/blocks/wine_rack_icon"})

DISHES = """apple_platter bamboo_tube_rice baozi baozi_plate barley_tea beef_meatball_soup
beef_noodle berry_platter biluochun blaze_lamb_chop borscht braised_beef
braised_beef_rice_bowl braised_beef_with_potatoes braised_fish braised_pork_ribs
brown_mushroom_pot_soup buddha_jumps_over_the_wall butter_tea candied_potato
chicken_and_mushroom_stew chorus_fried_egg chorus_fruit_platter cold_roasted_meat
cold_style_sashimi cooked_cow_offal cooked_cut_small_meats cooked_lamb_chops
cooked_meatball cooked_pork_belly cooked_rice crimson_fungus_pot_soup crystal_lamb_chop
dark_cuisine desert_style_sashimi dongpo_pork donkey_burger dough_drop_soup dumpling
egg_fried_rice end_style_sashimi fearsome_thick_soup fish_flavored_shredded_pork
fish_flavored_shredded_pork_rice_bowl flower_tea fondant_pie fondant_spider_eye
four_joy_meatball_soup fried_caterpillar fried_egg fried_spring_roll frost_lamb_chop
fruit_platter golden_salad hot_dry_noodles hui_noodle laba_congee lamb_and_radish_soup
mantou meat_pie mystery_tea nether_style_sashimi numbing_spicy_chicken oil_splashed_fish
oolong pan_seared_knight_steak pork_bone_soup pufferfish_soup qingtuan qingtuan_plate
red_mushroom_pot_soup sakura_fubuki samsa sashimi scramble_egg_with_tomatoes
scramble_egg_with_tomatoes_rice_bowl seafood_miso_soup shengjian_mantou
shengjian_mantou_plate slime_ball_meal spicy_blood_stew spicy_chicken spicy_rabbit_head
stargazy_pie sticky_candy sticky_candy_plate sticky_rice_cake sticky_rice_cake_plate
stir_fried_beef_offal stir_fried_beef_offal_rice_bowl stir_fried_pork_with_peppers
stir_fried_pork_with_peppers_rice_bowl stuffed_tiger_skin_pepper suspicious_stir_fry
sweet_and_sour_ender_pearls sweet_and_sour_pork sweet_and_sour_pork_rice_bowl tea_egg
tieguanyin tomato_beef_brisket_soup tomato_platter tundra_style_sashimi udon_noodle
warped_fungus_pot_soup watermelon_platter wild_mushroom_rabbit_soup yakitori zongzi
zongzi_plate kaleidoscope_cookery_bamboo_tube_rice kaleidoscope_cookery_cold_cut_ham_slices
kaleidoscope_cookery_cold_roasted_meat kaleidoscope_cookery_dongpo_pork
kaleidoscope_cookery_end_style_sashimi kaleidoscope_cookery_stuffed_tiger_skin_pepper
kaleidoscope_cookery_sweet_and_sour_ender_pearls""".split()

DRINKS = """allium_garden beer bloody_mary brandy brass_heart carignan champagne depth_charge
emerald glow_berries_juice glowflower_brew gold_grape_juice godfather grape_juice
grasshopper green_grape_juice honey_wine ice_grape_juice ice_wine luminous_bride
madame_shexiang melon miners_star mojito molotov mother_snow mystery_cocktail
nether_special plum_wine polaris_sweet_white red_queen riesling_dry_white rum
sakura_wine sauvignon_blanc_dry_white screwdriver sculk_special sherry signature_cocktail
sunset_glow sweet_berries_juice sweet_berry_wine vodka watermelon_juice whiskey white_lady
wine builders_tea kaleidoscope_tavern_honey_wine kaleidoscope_tavern_ice_wine
kaleidoscope_tavern_molotov kaleidoscope_tavern_mystery_cocktail
kaleidoscope_tavern_plum_wine kaleidoscope_tavern_rum kaleidoscope_tavern_sakura_wine
kaleidoscope_tavern_sweet_berry_wine kaleidoscope_tavern_wine""".split()

for r in data["systemShopItems"]:
    nm = res(r)
    if nm.startswith("kaleidoscope_cookery:") and nm.split(":", 1)[1] in DISHES:
        r[6] = "森罗菜品"
    elif nm.startswith("kaleidoscope_tavern:") and nm.split(":", 1)[1] in DRINKS:
        r[6] = "森罗酒类"

# ================================================================ 4. pools
def it(name, count=1, aux=0, userdata=None):
    d = {"count": count, "newAuxValue": aux, "newItemName": name}
    if userdata is not None:
        d["userData"] = userdata
    return d


def reward(weight, quality, *items):
    return {"items": list(items), "quality": quality, "weight": weight}


def pool(name, price, rewards):
    return {
        "buyPrice": float(price), "coinType": "金币",
        "freeDrawCount": 1, "freeDrawType": 4,
        "iconTexture": "textures/ui/ppeco_lucky_draw_box_variants_v2/ppeco_icon_luckeydraw_anim",
        "id": uuid.uuid4().hex, "limitCount": 10, "limitType": 1,
        "name": name, "requestItem": None, "rewards": rewards,
    }


def build_food():
    """你饿了么: common staples x12, rare crafted x1, golden apples legendary."""
    LEGENDARY = [("minecraft:enchanted_golden_apple", 1), ("minecraft:golden_apple", 4),
                 ("minecraft:golden_carrot", 6)]
    RARE = [("minecraft:cake", 6), ("minecraft:milk_bucket", 3), ("minecraft:suspicious_stew", 3),
            ("minecraft:honey_bottle", 4), ("minecraft:cookie", 3), ("minecraft:pumpkin_pie", 3),
            ("minecraft:rabbit_stew", 3), ("minecraft:mushroom_stew", 2), ("minecraft:beetroot_soup", 2)]
    EXCLUDE = {"golden_apple", "enchanted_golden_apple", "golden_carrot", "cake", "milk_bucket",
               "suspicious_stew", "honey_bottle", "cookie", "pumpkin_pie", "rabbit_stew",
               "mushroom_stew", "beetroot_soup", "pincers", "carrots", "potatoes", "melon_block",
               "spider_eye", "rotten_flesh", "pufferfish", "tropical_fish", "poisonous_potato"}
    rewards = [reward(w, "legendary", it(nm, 1)) for nm, w in LEGENDARY]
    rewards += [reward(w, "rare", it(nm, 1)) for nm, w in RARE]
    commons = []
    for r in data["systemShopItems"]:
        nm = res(r)
        if not (nm.startswith("minecraft:") or nm.startswith("farmer_delight_nullgr:")):
            continue
        name = nm.split(":", 1)[1]
        if name in EXCLUDE or name.endswith("_seeds"):
            continue
        if nm.startswith("minecraft:") and r[6] != "食物":
            continue
        commons.append(nm)
    for nm in sorted(commons):
        rewards.append(reward(3, "common", it(nm, 12)))
    return pool("你饿了么", 80, rewards)


def build_alchemy():
    """炼金学徒: positive combat/utility splash potions; weight by quality."""
    tiers = [
        ("legendary", [("力量II", 33, 3), ("治疗II", 22, 3), ("再生II", 30, 3)]),
        ("rare", [("迅捷II", 16, 5), ("跳跃II", 11, 5), ("抗火(长)", 13, 4), ("水肺(长)", 20, 4),
                  ("缓落(长)", 41, 4), ("夜视(长)", 6, 3), ("隐身(长)", 8, 3),
                  ("龟甲大师II", 39, 2), ("风冲", 42, 1)]),
        ("common", [("夜视I", 5, 7), ("跳跃I", 9, 7), ("迅捷I", 14, 7), ("抗火I", 12, 7),
                    ("水肺I", 19, 6), ("隐身I", 7, 6), ("缓落I", 40, 6), ("治疗I", 21, 5),
                    ("再生I", 28, 5), ("力量I", 31, 4)]),
    ]
    rewards = []
    for q, entries in tiers:
        for label, nav, w in entries:
            rewards.append(reward(w, q, it("minecraft:splash_potion", 1, nav)))
    return pool("炼金学徒", 100, rewards)


def prize_value(r, mult=1):
    sell = r[2]
    cnt = r[0].get("count") or 1
    return sell / cnt * mult


def w_price(v):
    v = max(v, 1e-6)
    return max(1, min(60, round(20 / math.sqrt(v))))


def build_dishes():
    rewards = []
    for r in data["systemShopItems"]:
        nm = res(r)
        if nm.startswith("kaleidoscope_cookery:") and r[6] == "森罗菜品":
            v = prize_value(r, 1)
            q = "legendary" if v >= 2.5 else ("rare" if v >= 0.6 else "common")
            rewards.append(reward(w_price(v), q, it(nm, 1)))
    return pool("森罗美食", 30, rewards)


def build_drinks():
    rewards = []
    for r in data["systemShopItems"]:
        nm = res(r)
        if (nm.startswith("kaleidoscope_tavern:") and r[6] == "森罗酒类") or nm == "create:builders_tea":
            v = prize_value(r, 1)
            q = "legendary" if v >= 2 else ("rare" if v >= 0.7 else "common")
            rewards.append(reward(w_price(v), q, it(nm, 1)))
    return pool("森罗酒馆", 50, rewards)


old = {p["name"]: p for p in data["luckyDraws"]}
# fix jump potion aux in weapon/tool/armor pools (6 = long night vision, wrong)
for pname in ("武器池", "工具商店", "防具盲盒"):
    if pname in old:
        for r in old[pname]["rewards"]:
            for i in r["items"]:
                if i["newItemName"] == "minecraft:potion" and i["newAuxValue"] == 6:
                    i["newAuxValue"] = 9  # 跳跃I

new_pools = [
    build_food(), build_alchemy(),
    old["附魔书店"], old["武器池"], old["工具商店"],
    old["宠物盲盒"], old["花语盒"], old["唱片盒"], old["防具盲盒"],
    build_dishes(), build_drinks(),
]
for p in new_pools:
    p["freeDrawCount"] = 1
    p["freeDrawType"] = 4
    p["limitCount"] = 10
    p["limitType"] = 1
data["luckyDraws"] = new_pools
log.append(("DRAW", "pools rebuilt", f"{len(new_pools)} pools, freeType=4, 饿了么/炼金学徒重做"))

# ================================================================ 5. save + report
OUT_JSON.write_text(json.dumps(wrap, ensure_ascii=False, indent=2), encoding="utf-8")
text = json.dumps(wrap, ensure_ascii=False, separators=(",", ":"))
raw = zlib.compress(text.encode("utf-8"), level=9)
OUT_TXT.write_text("ppcpdata2%" + base64.b64encode(raw).decode("ascii"), encoding="utf-8")

zero = [res(r) for r in data["systemShopItems"] if r[1] == 0.0 and r[2] == 0.0]
pot = [r for r in data["systemShopItems"]
       if res(r).split(":", 1)[0] == "minecraft" and res(r).split(":", 1)[1] in POTION_NAMES]
lines = ["# 081910 落地报告", "",
         f"- 基线：08199（2539 条）→ 输出：**081910.txt**（{len(data['systemShopItems'])} 条）",
         f"- 药水行：删除错误编码 {n_dropped} 条，上架顶级喷溅 {len(pot)} 条（NAV 编码）",
         f"- 剩余 0/0 条目：{zero or '无'}",
         "", "## 抽奖池", ""]
for p in data["luckyDraws"]:
    lines.append(f"- {p['name']}（票 {p['buyPrice']}）：{len(p['rewards'])} 个奖励，权重和 {sum(r['weight'] for r in p['rewards'])}")
lines += ["", "## 变更日志", ""]
for act, name, detail in log:
    lines.append(f"- **{act}** `{name}`：{detail}")
lines += ["", "## 待确认", "",
          "1. 药水货架 = 12 种顶级喷溅药水（NAV 编码），普通/滞留/低级已全部下架——游戏里核对显示。",
          "2. 你饿了么：普通×12 / 稀有×1 / 大奖=金苹果+金胡萝卜+附魔金苹果，票 80 保留。",
          "3. 炼金学徒：21 种正向喷溅药水，II 级 9%、实用延长 31%、I 级常用 60%。",
          "4. 森罗美食/森罗酒馆两池在 08199 里没了（你的存档没带上 08198），我按原方案补回；不想要就删。",
          "5. npc_yao 是什么？先按 100/10 挂娘化生物。",
          "6. 你删掉的两条双前缀菜（四喜丸子汤/仰望星空派）我没有恢复。",
          ""]
REPORT.write_text("\n".join(lines), encoding="utf-8")
print(f"OK items={len(data['systemShopItems'])} dropped_potions={n_dropped} zero={len(zero)}")
for p in new_pools:
    print(f"  {p['name']:8} {p['buyPrice']:>5} rew={len(p['rewards'])} wsum={sum(r['weight'] for r in p['rewards'])}")
