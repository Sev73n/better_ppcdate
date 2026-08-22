# -*- coding: utf-8 -*-
"""08197 -> 08198: rebuild food draw pool, add 森罗美食/森罗酒馆 pools,
one-time free draw on all pools, new 森罗菜品/森罗酒类 shop categories,
price the 37 newly added rows. Preserve everything else (teleport, main page,
broadcast threshold, other pools' rewards)."""
import base64, json, math, uuid, zlib
from collections import Counter
from pathlib import Path

ROOT = Path(r"C:/Users/AI10/Desktop/ppcdata")
SRC = ROOT / "01_配置明文" / "08197_decoded.json"
OUT_JSON = ROOT / "01_配置明文" / "08198_decoded.json"
OUT_TXT = ROOT / "06_用户自行导入" / "08198.txt"
REPORT = ROOT / "03_对比报告" / "08198_落地报告.md"

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


def row_of(ns, name):
    for r in data["systemShopItems"]:
        if res(r) == f"{ns}:{name}":
            return r
    return None


def price(ns, name, buy, sell, tag=None, count=None):
    r = row_of(ns, name)
    if r is None:
        log.append(("MISS", f"{ns}:{name}", f"{buy}/{sell}"))
        return None
    r[1], r[2] = buy, sell
    if tag is not None:
        r[6] = tag
    if count is not None:
        r[0]["count"] = count
    return r


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


# ================================================================ 1. dedup
drop_dup_zero()

# ================================================================ 2. price new rows
# (ns, name, buy, sell, tag, count)
NEW_PRICES = [
    # farmer's delight (tag 农夫乐事, in 你饿了么 pool)
    ("farmer_delight_nullgr", "apple_cider", 25, 6, "农夫乐事", 16),
    ("farmer_delight_nullgr", "beef_patty", 12, 4, "农夫乐事", 16),
    ("farmer_delight_nullgr", "beef_stew", 25, 8, "农夫乐事", 16),
    ("farmer_delight_nullgr", "chicken_cuts", 10, 3, "农夫乐事", 16),
    ("farmer_delight_nullgr", "chicken_sandwich", 15, 5, "农夫乐事", 16),
    ("farmer_delight_nullgr", "chicken_soup", 20, 6, "农夫乐事", 16),
    ("farmer_delight_nullgr", "fried_rice", 20, 6, "农夫乐事", 16),
    ("farmer_delight_nullgr", "mutton_wrap", 15, 5, "农夫乐事", 16),
    ("farmer_delight_nullgr", "steak_and_potatoes", 30, 9, "农夫乐事", 16),
    # create builders tea (drink -> 森罗酒馆 pool, tag stays 机械动力)
    ("create", "builders_tea", 20, 5, "机械动力", 16),
    # cookery teas / tea egg (森罗菜品, in 森罗美食 pool)
    ("kaleidoscope_cookery", "butter_tea", 20, 5, "森罗菜品", 16),
    ("kaleidoscope_cookery", "mystery_tea", 25, 6, "森罗菜品", 16),
    ("kaleidoscope_cookery", "tea_egg", 12, 3, "森罗菜品", 16),
    # cookery tea bags / leaves (ingredients, stay 森罗物语（厨房）)
    ("kaleidoscope_cookery", "barley_tea_bag", 8, 2, "森罗物语（厨房）", 16),
    ("kaleidoscope_cookery", "biluochun_tea_bag", 15, 4, "森罗物语（厨房）", 16),
    ("kaleidoscope_cookery", "butter_tea_bag", 8, 2, "森罗物语（厨房）", 16),
    ("kaleidoscope_cookery", "oolong_tea_bag", 20, 5, "森罗物语（厨房）", 16),
    ("kaleidoscope_cookery", "sakura_fubuki_tea_bag", 12, 3, "森罗物语（厨房）", 16),
    ("kaleidoscope_cookery", "tieguanyin_tea_bag", 12, 3, "森罗物语（厨房）", 16),
    ("kaleidoscope_cookery", "fresh_tea_leaves", 3, 0.75, "森罗物语（厨房）", 16),
    # cookery double-prefix dishes (copy single-prefix prices; 森罗菜品, in pool)
    ("kaleidoscope_cookery", "kaleidoscope_cookery_bamboo_tube_rice", 38.75, 3.25, "森罗菜品", 16),
    ("kaleidoscope_cookery", "kaleidoscope_cookery_cold_roasted_meat", 30, 11.7, "森罗菜品", 16),
    ("kaleidoscope_cookery", "kaleidoscope_cookery_dongpo_pork", 38.25, 3.6, "森罗菜品", 16),
    ("kaleidoscope_cookery", "kaleidoscope_cookery_stuffed_tiger_skin_pepper", 40.31, 6.08, "森罗菜品", 16),
    ("kaleidoscope_cookery", "kaleidoscope_cookery_sweet_and_sour_ender_pearls", 724, 116.1, "森罗菜品", 16),
    # tavern beer (森罗酒类, in pool)
    ("kaleidoscope_tavern", "beer", 15, 4, "森罗酒类", 16),
    # tavern double-prefix drinks (copy single prices; 森罗酒类, in pool)
    ("kaleidoscope_tavern", "kaleidoscope_tavern_honey_wine", 51, 11.7, "森罗酒类", 16),
    ("kaleidoscope_tavern", "kaleidoscope_tavern_ice_wine", 43, 4.5, "森罗酒类", 16),
    ("kaleidoscope_tavern", "kaleidoscope_tavern_molotov", 62.25, 4.5, "森罗酒类", 16),
    ("kaleidoscope_tavern", "kaleidoscope_tavern_mystery_cocktail", 160, 100, "森罗酒类", 16),
    ("kaleidoscope_tavern", "kaleidoscope_tavern_plum_wine", 43, 6.3, "森罗酒类", 16),
    ("kaleidoscope_tavern", "kaleidoscope_tavern_rum", 42.2, 6.3, "森罗酒类", 16),
    ("kaleidoscope_tavern", "kaleidoscope_tavern_sakura_wine", 45, 6.3, "森罗酒类", 16),
    ("kaleidoscope_tavern", "kaleidoscope_tavern_sweet_berry_wine", 43, 6.3, "森罗酒类", 16),
    ("kaleidoscope_tavern", "kaleidoscope_tavern_wine", 43, 4.5, "森罗酒类", 16),
    # tavern furniture (stay 森罗物语（酒馆）)
    ("kaleidoscope_tavern", "kaleidoscope_tavern_holder", 35, 21.88, "森罗物语（酒馆）", 16),
    ("kaleidoscope_tavern", "bar_cabinet_clear", 35, 21.88, "森罗物语（酒馆）", 16),
]
for ns, name, b, s, tag, cnt in NEW_PRICES:
    r = price(ns, name, b, s, tag, cnt)
    if r is not None:
        log.append(("PRICE", f"{ns}:{name}", f"{b}/{s} tag={tag}"))

# restore the two deleted double-prefix dish rows (not present in 08197)
for ns, name, b, s in [
    ("kaleidoscope_cookery", "kaleidoscope_cookery_four_joy_meatball_soup", 63.6, 7.2),
    ("kaleidoscope_cookery", "kaleidoscope_cookery_stargazy_pie", 102.75, 13.05),
]:
    if row_of(ns, name) is None:
        r = template(f"{nsid[ns]}:{name}", {"count": 16})
        r[1], r[2], r[6] = b, s, "森罗菜品"
        data["systemShopItems"].append(r)
        log.append(("RESTORE", f"{ns}:{name}", f"{b}/{s}"))

# ================================================================ 3. tags
for t in ("森罗菜品", "森罗酒类"):
    if t not in data["customItemTags"]:
        data["customItemTags"].append(t)
data["customItemTypeMap"].setdefault("森罗菜品", {"texturePath": "textures/items/cake"})
data["customItemTypeMap"].setdefault("森罗酒类", {"texturePath": "textures/kaleidoscope_tavern/blocks/wine_rack_icon"})

# 森罗菜品 (cookery dishes/foods/teas - single AND double prefix)
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
kaleidoscope_cookery_end_style_sashimi kaleidoscope_cookery_four_joy_meatball_soup
kaleidoscope_cookery_stargazy_pie kaleidoscope_cookery_stuffed_tiger_skin_pepper
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
    elif nm == "create:builders_tea":
        pass  # tag stays 机械动力
log.append(("TAG", "森罗菜品/森罗酒类", "retagged dishes and drinks"))

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
        "freeDrawCount": 1, "freeDrawType": 4,   # one-time free draw (user's edit)
        "iconTexture": "textures/ui/ppeco_lucky_draw_box_variants_v2/ppeco_icon_luckeydraw_anim",
        "id": uuid.uuid4().hex, "limitCount": 10, "limitType": 1,
        "name": name, "requestItem": None, "rewards": rewards,
    }


def w_price(v):
    return max(1, min(60, round(20 / math.sqrt(v))))


def prize_value(r, mult=1):
    sell = r[2]
    cnt = r[0].get("count") or 1
    return sell / cnt * mult


def build_pool_food():
    """你饿了么: vanilla foods + farmer_delight foods, x6 each, cake x1 jackpot."""
    EXCLUDE = {"golden_apple", "enchanted_golden_apple", "cake", "pincers",
               "carrots", "potatoes", "melon_block"}
    rewards = [reward(15, "legendary", it("minecraft:cake", 1))]
    entries = []
    for r in data["systemShopItems"]:
        nm = res(r)
        if not (nm.startswith("minecraft:") or nm.startswith("farmer_delight_nullgr:")):
            continue
        name = nm.split(":", 1)[1]
        if name in EXCLUDE or name.endswith("_seeds"):
            continue
        if nm.startswith("minecraft:"):
            if r[6] != "食物":
                continue
            newname = f"minecraft:{name}"
        else:
            newname = f"farmer_delight_nullgr:{name}"
        v = prize_value(r, 6)
        q = "rare" if v >= 2 else "common"
        entries.append((newname, v, q))
    for newname, v, q in sorted(entries, key=lambda x: -x[1]):
        rewards.append(reward(w_price(v), q, it(newname, 6)))
    return pool("你饿了么", 20, rewards)


def build_pool_dishes():
    rewards = []
    for r in data["systemShopItems"]:
        nm = res(r)
        if not nm.startswith("kaleidoscope_cookery:"):
            continue
        if r[6] != "森罗菜品":
            continue
        v = prize_value(r, 1)
        q = "legendary" if v >= 2.5 else ("rare" if v >= 0.6 else "common")
        rewards.append(reward(w_price(v), q, it(nm, 1)))
    return pool("森罗美食", 30, rewards)


def build_pool_drinks():
    rewards = []
    for r in data["systemShopItems"]:
        nm = res(r)
        if not nm.startswith("kaleidoscope_tavern:") and nm != "create:builders_tea":
            continue
        if nm != "create:builders_tea" and r[6] != "森罗酒类":
            continue
        v = prize_value(r, 1)
        q = "legendary" if v >= 2 else ("rare" if v >= 0.7 else "common")
        rewards.append(reward(w_price(v), q, it(nm, 1)))
    return pool("森罗酒馆", 50, rewards)


old = {p["name"]: p for p in data["luckyDraws"]}
new_pools = [
    build_pool_food(),
    old["炼金学徒"], old["附魔书店"], old["武器池"], old["工具商店"],
    old["宠物盲盒"], old["花语盒"], old["唱片盒"], old["防具盲盒"],
    build_pool_dishes(), build_pool_drinks(),
]
for p in new_pools:
    if p.get("freeDrawType") != 4:
        p["freeDrawCount"] = 1
        p["freeDrawType"] = 4
        p["limitCount"] = 10
        p["limitType"] = 1
data["luckyDraws"] = new_pools
log.append(("DRAW", "luckyDraws", f"{len(new_pools)} pools, freeDrawType=4"))

# ================================================================ 5. save
OUT_JSON.write_text(json.dumps(wrap, ensure_ascii=False, indent=2), encoding="utf-8")
text = json.dumps(wrap, ensure_ascii=False, separators=(",", ":"))
raw = zlib.compress(text.encode("utf-8"), level=9)
OUT_TXT.write_text("ppcpdata2%" + base64.b64encode(raw).decode("ascii"), encoding="utf-8")

zero = [res(r) for r in data["systemShopItems"] if r[1] == 0.0 and r[2] == 0.0]
cnt = Counter(res(r).split(":", 1)[0] for r in data["systemShopItems"])
lines = ["# 08198 落地报告", "",
         f"- 基线：08197（2472 条）→ 输出：**08198.txt**（{len(data['systemShopItems'])} 条）",
         f"- 剩余 0/0 条目：{zero or '无'}",
         "", "## 抽奖池（全部 freeDrawType=4 一次性免费 1 次）", ""]
for p in data["luckyDraws"]:
    n_rew = len(p["rewards"])
    wsum = sum(r["weight"] for r in p["rewards"])
    lines.append(f"- {p['name']}（票 {p['buyPrice']}）：{n_rew} 个奖励，权重和 {wsum}")
lines += ["", "## 变更日志", ""]
for act, name, detail in log:
    lines.append(f"- **{act}** `{name}`：{detail}")
lines += ["", "## 待你在游戏里确认", "",
          "1. 双前缀条目（如 `kaleidoscope_cookery_dongpo_pork`）在你游戏商店里显示为物品还是空气？",
          "   如果正常，我恢复的两条（四喜丸子汤/仰望星空派双前缀）也保留；如果是空气，我改删。",
          "2. 你饿了么票价 80→20（奖品改成 ×6 后 80 太高了）；森罗美食 30、森罗酒馆 50 是我定的，可调。",
          "3. 金苹果/附魔金苹果没进你饿了么（价格差两个数量级，会压死蛋糕大奖）——要进说一声。",
          "4. 农夫乐事 8 个菜进了你饿了么、苹果酒和机械动力建筑师茶进了森罗酒馆（饮品池）——可按你口味挪。",
          "5. 新商品定价是我按锚点估的（见变更日志），游戏里觉得不合适就改。",
          ""]
REPORT.write_text("\n".join(lines), encoding="utf-8")
print(f"OK items={len(data['systemShopItems'])} pools={len(new_pools)} zero={len(zero)}")
for r in new_pools:
    print(f"  {r['name']:8} {r['buyPrice']:>5} rewards={len(r['rewards'])} wsum={sum(x['weight'] for x in r['rewards'])}")
