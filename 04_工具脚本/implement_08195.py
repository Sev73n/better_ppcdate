# -*- coding: utf-8 -*-
"""Implement the confirmed 08194 adjustment plan -> produce 08195 share code.

Applies: economy switches, kill rewards, categories, mod pricing, enchant book
overhaul (keep top/second tier, method-B prices, sell 6.25), 9 lucky draw pools,
Create mineral additions, notice message rewrite.
"""
import base64, json, zlib, uuid
from collections import Counter
from pathlib import Path

ROOT = Path(r"C:/Users/AI10/Desktop/ppcdata")
SRC = ROOT / "01_配置明文" / "08194_decoded.json"
OUT_JSON = ROOT / "01_配置明文" / "08195_decoded.json"
OUT_TXT = ROOT / "06_用户自行导入" / "08195.txt"
REPORT = ROOT / "03_对比报告" / "08195_落地报告.md"

wrap = json.loads(SRC.read_text(encoding="utf-8"))
data = wrap["data"]
rev = {str(v): k for k, v in data["nameSpaceMap"].items()}
nsid = {k: str(v) for k, v in data["nameSpaceMap"].items()}
MC = nsid["minecraft"]

log = []  # (action, name, detail)


def resolved(r):
    nin = r[0].get("NIN", "")
    p, n = nin.split(":", 1) if ":" in nin else ("", nin)
    return f"{rev.get(p, '?' + p)}:{n}"


def find_all(name):
    out = []
    for i, r in enumerate(data["systemShopItems"]):
        if resolved(r) == name:
            out.append((i, r))
    return out


def set_price(name, buy, sell, tag=None, count=None):
    hits = find_all(name)
    if not hits:
        log.append(("MISS", name, f"{buy}/{sell}"))
        return
    for i, r in hits:
        r[1], r[2] = buy, sell
        if tag is not None:
            r[6] = tag
        if count is not None:
            r[0]["count"] = count
        log.append(("PRICE", name, f"{buy}/{sell} tag={tag!r}"))


def row_template(nin, item_extra=None):
    item = {"NIN": nin}
    if item_extra:
        item.update(item_extra)
    return [item, 0.0, 0.0, "", 0, 0, "", False, "金币", "金币", 0, 1.0, 64, 0.0, 0.9, 0.1]


def add_item(ns, name, buy, sell, tag, count=None):
    r = row_template(f"{nsid[ns]}:{name}", {"count": count} if count else None)
    r[1], r[2], r[6] = buy, sell, tag
    data["systemShopItems"].append(r)
    log.append(("ADD", f"{ns}:{name}", f"{buy}/{sell} tag={tag!r}"))


def del_rows(predicate, why):
    data["systemShopItems"] = [r for r in data["systemShopItems"] if not predicate(r)]
    log.append(("DELETE", why, ""))


# ---------------------------------------------------------------- 1. economy
e = data["ecoSystemData"]
e["defCoin"] = 73
e["preMinuteCoin"] = 1.0
for ct in data["customCoinTypes"]:
    if ct.get("key") == "基金":
        ct["visibleInPack"] = False
log.append(("ECON", "defCoin/preMinute/基金", "73 / 1.0 / visibleInPack=false"))

# ---------------------------------------------------------------- 2. kill rewards
kill = {
    1: ["chicken", "cow", "pig", "sheep", "rabbit", "cat", "ocelot", "wolf", "fox",
        "parrot", "turtle", "dolphin", "panda", "frog", "axolotl", "armadillo",
        "bee", "bat", "squid", "glow_squid", "mooshroom"],
    2: ["horse", "donkey", "mule", "llama", "camel", "goat", "sniffer", "strider"],
    5: ["polar_bear", "zombie_piglin"],
    10: ["zombie", "skeleton", "spider", "cave_spider", "husk", "stray", "drowned",
         "bogged", "silverfish", "endermite", "piglin", "zombie_villager", "slime"],
    12: ["creeper", "magma_cube", "pillager"],
    20: ["witch", "enderman", "phantom", "wither_skeleton", "guardian", "vex"],
    35: ["blaze", "ghast", "evoker", "vindicator", "shulker", "piglin_brute",
         "hoglin", "zoglin", "breeze"],
    80: ["warden", "ravager", "elder_guardian"],
    200: ["wither", "ender_dragon"],
    0: ["iron_golem", "snow_golem", "villager", "wandering_trader", "allay",
        "cod", "salmon", "tropical_fish", "pufferfish"],
}
krm = {}
for coins, mobs in kill.items():
    for m in mobs:
        krm[f"minecraft:{m}"] = [float(coins), "金币"]
data["killEntityRewardMap"] = krm
log.append(("KILL", "killEntityRewardMap", f"{len(krm)} entries"))

# ---------------------------------------------------------------- 3. tags
new_tags = ["旅行袋", "机械动力", "车万女仆", "娘化生物", "农夫乐事", "农夫传说", "透明玻璃",
            "§l原版|附魔书"]
for t in new_tags:
    if t not in data["customItemTags"]:
        data["customItemTags"].append(t)
tag_tex = {
    "旅行袋": "textures/ui/ppeco_tag/tag_2",
    "机械动力": "textures/ui/ppeco_tag/tag_20",
    "车万女仆": "textures/ui/ppeco_tag/tag_5",
    "娘化生物": "textures/ui/ppeco_tag/tag_30",
    "农夫乐事": "textures/items/cake",
    "农夫传说": "textures/items/egg",
    "透明玻璃": "textures/ui/ppeco_tag/tag_20",
}
for t, tex in tag_tex.items():
    data["customItemTypeMap"].setdefault(t, {"texturePath": tex})

mod_tag = {
    "ihzao": "旅行袋", "create": "机械动力", "ysm_maid": "车万女仆",
    "breath_maid": "娘化生物", "farmer_delight_nullgr": "农夫乐事",
    "farmers_tale_nullgr": "农夫传说", "ws": "透明玻璃",
}
BOOK_TAG = "§l原版|附魔书"
for r in data["systemShopItems"]:
    nin = r[0].get("NIN", "")
    p = nin.split(":", 1)[0] if ":" in nin else ""
    ns = rev.get(p, None)
    if ns in mod_tag:
        r[6] = mod_tag[ns]
    elif ns == "minecraft" and nin.split(":", 1)[1] == "enchanted_book":
        r[6] = BOOK_TAG
log.append(("TAG", "customItemTags", f"+{len(new_tags)} tags, mod items retagged"))

# ---------------------------------------------------------------- 4. jewelry / cream / feed
jewel = {
    "breath_maid:npc_jie_1": (760, 152), "breath_maid:npc_jie_2": (200, 40),
    "breath_maid:npc_jie_3": (1480, 296), "breath_maid:npc_jie_4": (2440, 488),
    "breath_maid:npc_jie_5": (4040, 808), "breath_maid:npc_jie_6": (27012, 18008),
    "breath_maid:npc_xiang_1": (570, 114), "breath_maid:npc_xiang_2": (150, 30),
    "breath_maid:npc_xiang_3": (1110, 222), "breath_maid:npc_xiang_4": (1830, 366),
    "breath_maid:npc_xiang_5": (3030, 606), "breath_maid:npc_xiang_6": (20259, 13506),
}
for name, (b, s) in jewel.items():
    set_price(name, b, s, tag="娘化生物")
set_price("breath_maid:npc_55_food", 100, 1, tag="娘化生物", count=64)
# 多彩膏 keep 200/10, tag
set_price("breath_maid:npc_item_1", 200, 10, tag="娘化生物")

# ---------------------------------------------------------------- 5. create machines
machines = {
    "cogwheel": 20, "andesite_encased_cogwheel": 30, "mechanical_piston_head": 30,
    "sticky_mechanical_piston_head": 35, "large_cogwheel": 40,
    "andesite_encased_large_cogwheel": 50, "gearbox": 50, "furnace_minecart": 50,
    "gearbox_vertical": 60, "mechanical_bearing": 60, "gearshift": 70,
    "brass_encased_cogwheel": 80, "mechanical_piston": 90,
    "brass_encased_large_cogwheel": 100, "mechanical_drill": 100, "mechanical_saw": 100,
    "sticky_mechanical_piston": 110, "mechanical_crafter": 120, "mechanical_plough": 120,
    "mechanical_harvester": 150, "mechanical_mixer": 150, "mechanical_pump": 150,
    "speedometer": 150, "mechanical_press": 200, "empty_blaze_burner": 200,
    "rotation_speed_controller": 300, "mechanical_arm": 350,
}
for name, buy in machines.items():
    set_price(f"create:{name}", float(buy), round(buy * 0.25, 2), tag="机械动力")
# minerals: existing reprice + new
set_price("create:veridium", 2, 0.1, tag="机械动力")
set_price("create:ochrum", 2, 0.1, tag="机械动力")
minerals = [("asurine", 2, 0.1), ("crimsite", 2, 0.1), ("zinc_ore", 16, 10),
            ("raw_zinc", 20, 12.5), ("zinc_ingot", 24, 15), ("zinc_block", 216, 135),
            ("brass_ingot", 40, 15), ("brass_block", 360, 135),
            ("andesite_alloy", 10, 6.25)]
for name, b, s in minerals:
    add_item("create", name, b, s, "机械动力", count=64)

# ---------------------------------------------------------------- 6. maid / ihzao / farmer
set_price("ysm_maid:explosion_protect_bauble", 2000, 100, tag="车万女仆")
set_price("ysm_maid:smart_slab_empty", 150, 0, tag="车万女仆")
set_price("ihzao:chainmining", 2000, 0, tag="旅行袋")
set_price("ihzao:httravbag", 400, 10, tag="旅行袋")
set_price("ihzao:magnetht", 900, 0, tag="旅行袋")
armor_pl = {
    "ihzao:leather_barmorht_1": (150, 31.25), "ihzao:leather_harmorht_1": (130, 18.75),
    "ihzao:leather_larmorht_1": (140, 25), "ihzao:chainmail_barmorht_1": (300, 125),
    "ihzao:iron_barmorht_1": (420, 200), "ihzao:golden_barmorht_1": (550, 281.25),
    "ihzao:diamond_barmorht_1": (1700, 1000), "ihzao:netherite_barmorht_1": (9100, 5625),
}
for name, (b, s) in armor_pl.items():
    set_price(name, b, s, tag="旅行袋")
set_price("farmer_delight_nullgr:dumplings", 40, 12, tag="农夫乐事")
set_price("farmer_delight_nullgr:pincers", 40, 25, tag="农夫乐事")

# ---------------------------------------------------------------- 7. kaleidoscope dupes
kc = nsid["kaleidoscope_cookery"]; kt = nsid["kaleidoscope_tavern"]
set_price("kaleidoscope_tavern:kaleidoscope_tavern_empty_bottle", 5, 3.13,
          tag="森罗物语（酒馆）", count=64)
set_price("kaleidoscope_cookery:kaleidoscope_cookery_empty_cup", 10, 2,
          tag="森罗物语（厨房）", count=16)
set_price("kaleidoscope_tavern:kaleidoscope_tavern_empty_glassware", 5, 3.13,
          tag="森罗物语（酒馆）", count=64)
del_rows(lambda r: r[0].get("NIN") in (f"{kc}:kaleidoscope_cookery_four_joy_meatball_soup",
                                       f"{kc}:kaleidoscope_cookery_stargazy_pie"),
         "double-prefix kaleidoscope rows")
del_rows(lambda r: r[0].get("NIN") == f"{MC}:chest" and r[1] == 0.0 and "NAV" not in r[0],
         "duplicate unpriced minecraft:chest")
del_rows(lambda r: r[0].get("NIN") == f"{MC}:enchanted_book"
         and r[0].get("userData") is None,
         "blank enchanted_book placeholder (300)")

# ---------------------------------------------------------------- 8. enchant books
# id -> (name, tier_price, max_level)
ENCH = {
    0: ("protection", 180, 4), 1: ("fire_protection", 180, 4),
    2: ("feather_falling", 180, 4), 3: ("blast_protection", 180, 4),
    4: ("projectile_protection", 180, 4), 5: ("thorns", 180, 3),
    6: ("respiration", 180, 3), 7: ("depth_strider", 180, 3),
    8: ("aqua_affinity", 180, 1), 9: ("sharpness", 180, 5),
    10: ("smite", 180, 5), 11: ("bane_of_arthropods", 180, 5),
    12: ("knockback", 80, 2), 13: ("fire_aspect", 80, 2),
    14: ("looting", 280, 3), 15: ("efficiency", 180, 5),
    16: ("silk_touch", 450, 1), 17: ("unbreaking", 280, 3),
    18: ("fortune", 280, 3), 19: ("power", 180, 5),
    20: ("punch", 80, 2), 21: ("flame", 80, 1),
    22: ("infinity", 450, 1), 23: ("luck_of_the_sea", 80, 3),
    24: ("lure", 80, 3), 26: ("mending", 800, 1),
    30: ("riptide", 180, 3), 31: ("loyalty", 180, 3),
    32: ("channeling", 180, 1), 33: ("piercing", 180, 4),
    34: ("multishot", 180, 1), 35: ("quick_charge", 180, 3),
    36: ("soul_speed", 450, 3), 37: ("swift_sneak", 450, 3),
    38: ("wind_burst", 320, 3), 39: ("density", 320, 5),
    40: ("breach", 320, 4),
}
BOOK_SELL = 6.25
keep_levels = {}   # (id, lvl)
for eid, (nm, tier, mx) in ENCH.items():
    keep_levels[(eid, mx)] = True
    if mx >= 2:
        keep_levels[(eid, mx - 1)] = True
# mod enchant sweep_blade (id 255, max 3, tier 280)
keep_levels[(255, 3)] = True
keep_levels[(255, 2)] = True


def book_price(eid, lvl):
    if eid == 255:
        tier, mx = 280, 3
    else:
        _, tier, mx = ENCH[eid]
    return round(tier * (lvl / mx) ** 2)


def book_enchant(item):
    ud = item.get("userData") or {}
    ench = ud.get("ench") or []
    if not ench:
        return None
    e0 = ench[0]
    eid = e0["id"]["__value__"]
    lvl = e0["lvl"]["__value__"]
    return eid, lvl


def is_book(r):
    nin = r[0].get("NIN", "")
    return nin.split(":", 1)[-1] == "enchanted_book" and (r[0].get("userData") is not None)


# delete low-level books, price kept ones
data["systemShopItems"] = [r for r in data["systemShopItems"]
                           if not (is_book(r) and book_enchant(r[0]) not in keep_levels)]
kept = Counter(); priced = Counter()
for r in data["systemShopItems"]:
    if is_book(r):
        eid, lvl = book_enchant(r[0])
        r[1] = float(book_price(eid, lvl))
        r[2] = BOOK_SELL
        r[6] = BOOK_TAG
        kept[eid] += 1
        priced[f"{eid}:{lvl}"] = book_price(eid, lvl)
log.append(("BOOKS", "kept+priced", f"{sum(kept.values())} books kept, {len(kept)} enchants"))

# add missing books (top/second tier not in stock)
def book_userdata(eid, lvl, mod=None):
    ench = {"id": {"__type__": 2, "__value__": eid}, "lvl": {"__type__": 2, "__value__": lvl}}
    if mod:
        ench["modEnchant"] = {"__type__": 8, "__value__": mod}
    return {"ench": [ench]}

stock = {(eid, lvl) for r in data["systemShopItems"]
         if is_book(r) for eid, lvl in [book_enchant(r[0])]}
insert_at = None
for i, r in enumerate(data["systemShopItems"]):
    if is_book(r):
        insert_at = i
if insert_at is None:
    insert_at = len(data["systemShopItems"]) - 1
added_books = []
for (eid, lvl) in sorted(keep_levels):
    if (eid, lvl) in stock:
        continue
    if eid == 255:
        ud = book_userdata(255, lvl, "brtool:sweep_blade")
    else:
        ud = book_userdata(eid, lvl)
    r = row_template(f"{MC}:enchanted_book", {"userData": ud})
    r[1] = float(book_price(eid, lvl)); r[2] = BOOK_SELL; r[6] = BOOK_TAG
    data["systemShopItems"].insert(insert_at + 1, r)
    added_books.append((eid, lvl, book_price(eid, lvl)))
log.append(("BOOKS", "added missing", str(added_books)))

# ---------------------------------------------------------------- 9. lucky draws
def reward(weight, quality, *items):
    return {"items": list(items), "quality": quality, "weight": weight}


def it(name, count=1, aux=0, userdata=None):
    d = {"count": count, "newAuxValue": aux, "newItemName": name}
    if userdata is not None:
        d["userData"] = userdata
    return d


B = lambda eid, lvl, mod=None: it("minecraft:enchanted_book", 1, 0, book_userdata(eid, lvl, mod))
POOL_ICON = "textures/ui/ppeco_lucky_draw_box_variants_v2/ppeco_icon_luckeydraw_anim"


def pool(name, price, rewards):
    return {
        "buyPrice": float(price), "coinType": "金币", "freeDrawCount": 1, "freeDrawType": 1,
        "iconTexture": POOL_ICON, "id": uuid.uuid4().hex, "limitCount": 10, "limitType": 1,
        "name": name, "requestItem": None, "rewards": rewards,
    }


pools = [
    pool("你饿了么", 80, [
        reward(10, "legendary", it("minecraft:golden_carrot", 128), it("minecraft:cake", 2)),
        reward(60, "rare", it("minecraft:golden_carrot", 64)),
        reward(30, "common", it("minecraft:bread", 64), it("minecraft:cooked_beef", 64)),
    ]),
    pool("炼金学徒", 100, [
        reward(10, "legendary", it("minecraft:potion", 3, 16), it("minecraft:potion", 3, 21)),
        reward(60, "rare", it("minecraft:potion", 3, 7)),
        reward(30, "common", it("minecraft:potion", 3, 0)),
    ]),
    pool("附魔书店", 250, [
        reward(10, "legendary", B(26, 1)),
        reward(60, "rare", B(17, 3)),
        reward(30, "common", it("minecraft:book", 16)),
    ]),
    pool("武器池", 200, [
        reward(3, "legendary", it("minecraft:diamond_sword"), B(9, 5)),
        reward(3, "legendary", it("minecraft:diamond_sword"), B(14, 3)),
        reward(3, "legendary", it("minecraft:diamond_sword"), B(13, 2)),
        reward(3, "legendary", it("minecraft:diamond_sword"), B(26, 1)),
        reward(1, "legendary", it("minecraft:netherite_sword"), B(26, 1)),
        reward(47, "rare", it("minecraft:diamond_sword")),
        reward(40, "common", it("minecraft:potion", 1, 6)),
    ]),
    pool("工具商店", 300, [
        reward(3, "legendary", it("minecraft:diamond_pickaxe"), B(15, 5)),
        reward(3, "legendary", it("minecraft:diamond_pickaxe"), B(18, 3)),
        reward(3, "legendary", it("minecraft:diamond_pickaxe"), B(16, 1)),
        reward(3, "legendary", it("minecraft:diamond_pickaxe"), B(26, 1)),
        reward(1, "legendary", it("minecraft:netherite_pickaxe"), B(26, 1)),
        reward(47, "rare", it("minecraft:diamond_pickaxe")),
        reward(40, "common", it("minecraft:potion", 1, 6)),
    ]),
    pool("宠物盲盒", 150, [
        reward(2, "legendary", it("minecraft:allay_spawn_egg")),
        reward(2, "legendary", it("minecraft:sniffer_spawn_egg")),
        reward(2, "legendary", it("minecraft:panda_spawn_egg")),
        reward(2, "legendary", it("minecraft:axolotl_spawn_egg")),
        reward(2, "legendary", it("minecraft:frog_spawn_egg")),
        reward(5, "rare", it("minecraft:cat_spawn_egg")),
        reward(5, "rare", it("minecraft:wolf_spawn_egg")),
        reward(5, "rare", it("minecraft:fox_spawn_egg")),
        reward(5, "rare", it("minecraft:parrot_spawn_egg")),
        reward(5, "rare", it("minecraft:turtle_spawn_egg")),
        reward(5, "rare", it("minecraft:goat_spawn_egg")),
        reward(5, "rare", it("minecraft:bee_spawn_egg")),
        reward(5, "rare", it("minecraft:armadillo_spawn_egg")),
        reward(10, "common", it("minecraft:chicken_spawn_egg")),
        reward(10, "common", it("minecraft:cow_spawn_egg")),
        reward(10, "common", it("minecraft:pig_spawn_egg")),
        reward(10, "common", it("minecraft:sheep_spawn_egg")),
        reward(10, "common", it("minecraft:rabbit_spawn_egg")),
    ]),
    pool("花语盒", 40, [
        reward(10, "legendary", it("breath_maid:npc_item_1")),
        reward(40, "rare", it("minecraft:wither_rose", 16)),
        reward(50, "common", it("minecraft:poppy", 32), it("minecraft:dandelion", 32)),
    ]),
    pool("唱片盒", 350, [
        reward(10, "legendary", it("minecraft:music_disc_pigstep"), it("minecraft:jukebox")),
        reward(20, "rare", it("minecraft:music_disc_relic"), it("minecraft:jukebox")),
        reward(20, "rare", it("minecraft:music_disc_5"), it("minecraft:jukebox")),
        reward(10, "common", it("minecraft:music_disc_13"), it("minecraft:jukebox")),
        reward(10, "common", it("minecraft:music_disc_cat"), it("minecraft:jukebox")),
        reward(10, "common", it("minecraft:music_disc_far"), it("minecraft:jukebox")),
        reward(10, "common", it("minecraft:music_disc_mall"), it("minecraft:jukebox")),
        reward(10, "common", it("minecraft:music_disc_stal"), it("minecraft:jukebox")),
    ]),
    pool("防具盲盒", 600, [
        reward(3, "legendary", it("minecraft:diamond_chestplate"), B(0, 4)),
        reward(3, "legendary", it("minecraft:diamond_chestplate"), B(17, 3)),
        reward(3, "legendary", it("minecraft:diamond_chestplate"), B(5, 3)),
        reward(3, "legendary", it("minecraft:diamond_chestplate"), B(26, 1)),
        reward(1, "legendary", it("minecraft:netherite_chestplate"), B(26, 1)),
        reward(47, "rare", it("minecraft:diamond_leggings")),
        reward(40, "common", it("minecraft:potion", 1, 6)),
    ]),
]
data["luckyDraws"] = pools
log.append(("DRAW", "luckyDraws", f"{len(pools)} pools"))

# ---------------------------------------------------------------- 10. notice + recount
cnt = Counter()
for r in data["systemShopItems"]:
    nin = r[0].get("NIN", "")
    p = nin.split(":", 1)[0] if ":" in nin else ""
    cnt[rev.get(p, "?" + p)] += 1
nbooks = sum(1 for r in data["systemShopItems"] if is_book(r))
total = sum(cnt.values())
e["noticeMsg"] = (
    f"仅金币｜原版{cnt['minecraft']}(附魔书{nbooks})｜森罗厨{cnt['kaleidoscope_cookery']}"
    f"+酒{cnt['kaleidoscope_tavern']}+偶{cnt['kaleidoscope_doll']}｜冰火{cnt['bricefire']}"
    f"｜旅行袋{cnt['ihzao']}｜车万女仆{cnt['ysm_maid']}｜机械{cnt['create']}"
    f"｜娘化{cnt['breath_maid']}｜农夫{cnt['farmer_delight_nullgr'] + cnt['farmers_tale_nullgr']}"
    f"｜透明玻璃{cnt['ws']}｜合计{total}｜开局73｜在线+1/分｜基金隐藏｜死亡固定扣100"
    f"｜附魔书仅满级/次顶级"
)
log.append(("NOTICE", "noticeMsg", e["noticeMsg"]))

# ---------------------------------------------------------------- save + encode
OUT_JSON.write_text(json.dumps(wrap, ensure_ascii=False, indent=2), encoding="utf-8")
text = json.dumps(wrap, ensure_ascii=False, separators=(",", ":"))
raw = zlib.compress(text.encode("utf-8"), level=9)
OUT_TXT.write_text("ppcpdata2%" + base64.b64encode(raw).decode("ascii"), encoding="utf-8")

# report
lines = ["# 08195 落地报告", "",
         f"- 输入：`01_配置明文/08194_decoded.json`（{len(data['systemShopItems'])} → 见下）",
         f"- 输出：`06_用户自行导入/08195.txt`、`01_配置明文/08195_decoded.json`",
         f"- 商品总数：{total}（原 2441），附魔书 {nbooks} 本",
         "", "## 变更日志", ""]
for act, name, detail in log:
    lines.append(f"- **{act}** `{name}`：{detail}")
lines += ["", "## 命名空间统计", ""]
for k, v in cnt.most_common():
    lines.append(f"- {k}: {v}")
lines += ["", "## 需要在游戏里验证的事项", "",
          "1. 抽奖奖励的 `userData`（附魔书/带附魔组合包）——插件若不支持，开出的是空白附魔书，",
          "   需要改方案（换经验瓶或纯钻石工具组合）。",
          "2. 药水 aux：跳跃=6、抗火=7、力量=16、治疗=21、水瓶=0（均为商店已有行的同值）。",
          "3. 击杀表 `minecraft:zombie_piglin` 的实体 ID（旧版可能叫 zombie_pigman）。",
          "4. 新增机械动力矿物 ID（asurine/crimsite/锌系列/安山合金）以游戏内为准。",
          "5. 多彩膏抽奖奖励 `breath_maid:npc_item_1` 的 newItemName 写法。",
          ""]
REPORT.write_text("\n".join(lines), encoding="utf-8")
print(f"OK items={total} books={nbooks} -> {OUT_TXT.name}")
for act, name, detail in log:
    if act in ("MISS",):
        print("MISS:", name)
