# -*- coding: utf-8 -*-
"""08195 独立验收测试（只读）：对照 03_对比报告/08194_完整调整计划.md 逐项核对。"""
import base64, json, zlib
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(r"C:/Users/AI10/Desktop/ppcdata")
P94 = ROOT / "01_配置明文" / "08194_decoded.json"
P95 = ROOT / "01_配置明文" / "08195_decoded.json"
T95 = ROOT / "06_用户自行导入" / "08195.txt"

BOOK_TAG = "§l原版|附魔书"
results = []  # (id, passed, name, details)


def check(cid, name, ok, *details):
    results.append((cid, ok, name, details))


def wrap(fname):
    return json.loads(Path(fname).read_text(encoding="utf-8"))


wrap94, wrap95 = wrap(P94), wrap(P95)
d94, d95 = wrap94["data"], wrap95["data"]
rev = {str(v): k for k, v in d95["nameSpaceMap"].items()}
sh94, sh95 = d94["systemShopItems"], d95["systemShopItems"]


def rname(r):
    nin = r[0].get("NIN", "")
    if ":" in nin:
        p, n = nin.split(":", 1)
    else:
        p, n = "", nin
    return f"{rev.get(p, '?' + p)}:{n}"


def ns_of(r):
    return rname(r).split(":", 1)[0]


def is_book_row(r):
    return r[0].get("NIN", "").split(":")[-1] == "enchanted_book" and r[0].get("userData") is not None


def enchant_of(r):
    ud = r[0].get("userData") or {}
    ench = ud.get("ench") or []
    if not ench:
        return None
    e0 = ench[0]
    return (e0["id"]["__value__"], e0["lvl"]["__value__"],
            (e0.get("modEnchant") or {}).get("__value__"))


def sig(r):
    it = {k: v for k, v in r[0].items() if k != "NIN"}
    return json.dumps(it, sort_keys=True, ensure_ascii=False)


# ============================================================== A. 编码完整性
# A1
txt = T95.read_text(encoding="utf-8").strip()
ok_prefix = txt.startswith("ppcpdata2%")
try:
    payload = txt[len("ppcpdata2%"):]
    raw = base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))
    wrap_txt = json.loads(zlib.decompress(raw).decode("utf-8"))
    dec_ok = True
except Exception as ex:
    wrap_txt, dec_ok = None, False
    dec_err = repr(ex)
check("A1", "08195.txt 解码成功", ok_prefix and dec_ok,
      f"prefix={ok_prefix} decode={dec_ok}" + ("" if dec_ok else f" err={dec_err}"))
top = set(wrap_txt.keys())
check("A1", "顶层含 data/formatVersion/sections", top >= {"data", "formatVersion", "sections"}, f"top={sorted(top)}")
check("A1", "formatVersion==2", wrap_txt.get("formatVersion") == 2, f"formatVersion={wrap_txt.get('formatVersion')}")
check("A1", "sections 与 08194 完全一致", wrap_txt.get("sections") == wrap94.get("sections"),
      "sections 相同" if wrap_txt.get("sections") == wrap94.get("sections") else "sections 不同")

# A2
check("A2", "08195.txt 解码结果 == 08195_decoded.json", wrap_txt == wrap95,
      "JSON 相等" if wrap_txt == wrap95 else "JSON 不等")

# A3
bad16 = [i for i, r in enumerate(sh95) if len(r) != 16]
check("A3", "systemShopItems 每行 16 元素", not bad16,
      f"{len(sh95)} 行, 非16元素行: {bad16[:10]}")
bad_rew = []
for pi, p in enumerate(d95["luckyDraws"]):
    for ri, rw in enumerate(p["rewards"]):
        if not all(k in rw for k in ("items", "quality", "weight")):
            bad_rew.append((p["name"], ri))
        for ii, it in enumerate(rw.get("items", [])):
            if not all(k in it for k in ("count", "newAuxValue", "newItemName")):
                bad_rew.append((p["name"], ri, ii, "item缺字段"))
check("A3", "luckyDraws 每池每奖励都有 items/quality/weight", not bad_rew,
      f"异常: {bad_rew[:10]}")

# ============================================================== B. 全量差异
# 按 (命名空间名:物品名, item字典签名) 做多重集对齐
c94 = Counter((rname(r), sig(r)) for r in sh94)
c95 = Counter((rname(r), sig(r)) for r in sh95)
del_keys = list((c94 - c95).elements())
add_keys = list((c95 - c94).elements())
both_keys = set(c94) & set(c95)

rows94 = defaultdict(list)
for r in sh94:
    rows94[(rname(r), sig(r))].append(r)
rows95 = defaultdict(list)
for r in sh95:
    rows95[(rname(r), sig(r))].append(r)

# --- 计划口径 ---
MACHINES = {
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
PLAN_PRICE = {}
for m, b in MACHINES.items():
    PLAN_PRICE[f"create:{m}"] = (float(b), round(b * 0.25, 2))
PLAN_PRICE["create:veridium"] = (2, 0.1)
PLAN_PRICE["create:ochrum"] = (2, 0.1)
JEWEL = {
    "breath_maid:npc_jie_1": (760, 152), "breath_maid:npc_jie_2": (200, 40),
    "breath_maid:npc_jie_3": (1480, 296), "breath_maid:npc_jie_4": (2440, 488),
    "breath_maid:npc_jie_5": (4040, 808), "breath_maid:npc_jie_6": (27012, 18008),
    "breath_maid:npc_xiang_1": (570, 114), "breath_maid:npc_xiang_2": (150, 30),
    "breath_maid:npc_xiang_3": (1110, 222), "breath_maid:npc_xiang_4": (1830, 366),
    "breath_maid:npc_xiang_5": (3030, 606), "breath_maid:npc_xiang_6": (20259, 13506),
}
PLAN_PRICE.update(JEWEL)
PLAN_PRICE["breath_maid:npc_55_food"] = (100, 1)
ARMOR = {
    "ihzao:leather_barmorht_1": (150, 31.25), "ihzao:leather_harmorht_1": (130, 18.75),
    "ihzao:leather_larmorht_1": (140, 25), "ihzao:chainmail_barmorht_1": (300, 125),
    "ihzao:iron_barmorht_1": (420, 200), "ihzao:golden_barmorht_1": (550, 281.25),
    "ihzao:diamond_barmorht_1": (1700, 1000), "ihzao:netherite_barmorht_1": (9100, 5625),
}
PLAN_PRICE.update(ARMOR)
PLAN_PRICE.update({
    "ihzao:chainmining": (2000, 0), "ihzao:httravbag": (400, 10), "ihzao:magnetht": (900, 0),
    "ysm_maid:explosion_protect_bauble": (2000, 100), "ysm_maid:smart_slab_empty": (150, 0),
    "farmer_delight_nullgr:dumplings": (40, 12), "farmer_delight_nullgr:pincers": (40, 25),
    "kaleidoscope_tavern:kaleidoscope_tavern_empty_bottle": (5, 3.13),
    "kaleidoscope_tavern:kaleidoscope_tavern_empty_glassware": (5, 3.13),
    "kaleidoscope_cookery:kaleidoscope_cookery_empty_cup": (10, 2),
})
PLAN_DEL = {"kaleidoscope_cookery:kaleidoscope_cookery_four_joy_meatball_soup",
            "kaleidoscope_cookery:kaleidoscope_cookery_stargazy_pie",
            "minecraft:chest"}  # chest：仅限无 NAV 的重复 0 价条
PLAN_ADD = {
    "create:asurine": (2, 0.1), "create:crimsite": (2, 0.1), "create:zinc_ore": (16, 10),
    "create:raw_zinc": (20, 12.5), "create:zinc_ingot": (24, 15), "create:zinc_block": (216, 135),
    "create:brass_ingot": (40, 15), "create:brass_block": (360, 135),
    "create:andesite_alloy": (10, 6.25),
}
MOD_TAG = {"ihzao": "旅行袋", "create": "机械动力", "ysm_maid": "车万女仆",
           "breath_maid": "娘化生物", "farmer_delight_nullgr": "农夫乐事",
           "farmers_tale_nullgr": "农夫传说", "ws": "透明玻璃"}
KC_TAG = {"kaleidoscope_tavern": "森罗物语（酒馆）", "kaleidoscope_cookery": "森罗物语（厨房）"}

# --- 附魔书 tier 表（任务口径）---
MAXLV = {0: 4, 1: 4, 2: 4, 3: 4, 4: 4, 5: 3, 6: 3, 7: 3, 8: 1, 9: 5, 10: 5, 11: 5,
         12: 2, 13: 2, 14: 3, 15: 5, 16: 1, 17: 3, 18: 3, 19: 5, 20: 2, 21: 1, 22: 1,
         23: 3, 24: 3, 26: 1, 30: 3, 31: 3, 32: 1, 33: 4, 34: 1, 35: 3, 36: 3, 37: 3,
         38: 3, 39: 5, 40: 4}
TIER = {12: 80, 13: 80, 21: 80, 23: 80, 24: 80,
        0: 180, 9: 180, 15: 180, 19: 180, 35: 180,
        14: 280, 17: 280, 18: 280,
        16: 450, 22: 450, 36: 450, 37: 450,
        26: 800, 38: 320, 39: 320, 40: 320}


def exp_book_price(eid, lvl, mod):
    if mod:  # brtool:sweep_blade
        tier, mx = 280, 3
    else:
        tier, mx = TIER.get(eid, 180), MAXLV.get(eid, 1)
    return round(tier * (lvl / mx) ** 2)


# --- 合并 count-only 的删除+新增对（同名列 item dict 仅差 count 键）---
merged_pairs = []
for k in list(del_keys):
    nm, sg_old = k
    if nm not in {kk[0] for kk in add_keys}:
        continue
    old_it = json.loads(sg_old)
    cand = [kk for kk in add_keys if kk[0] == nm]
    hits = []
    for kk in cand:
        new_it = json.loads(kk[1])
        o = {x: y for x, y in old_it.items() if x != "count"}
        n = {x: y for x, y in new_it.items() if x != "count"}
        if o == n:
            hits.append(kk)
    if len(hits) == 1:
        merged_pairs.append((k, hits[0]))
        del_keys.remove(k)
        add_keys.remove(hits[0])

# --- 变更分类 ---
price_changed, other_changed = [], []
for k in sorted(both_keys):
    for a, b in zip(rows94[k], rows95[k]):
        if (a[1], a[2]) != (b[1], b[2]):
            price_changed.append((k[0], a[1], a[2], b[1], b[2]))
        chg = []
        for idx in (3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15):
            if a[idx] != b[idx]:
                chg.append((idx, a[idx], b[idx]))
        if a[6] != b[6]:
            chg.append(("tag", a[6], b[6]))
        ac, bc = a[0].get("count"), b[0].get("count")
        if ac != bc:
            chg.append(("count", ac, bc))
        if chg:
            other_changed.append((k[0], a[1], a[2], chg))
for (ko, kn) in merged_pairs:
    a, b = rows94[ko][0], rows95[kn][0]
    nm = ko[0]
    if (a[1], a[2]) != (b[1], b[2]):
        price_changed.append((nm, a[1], a[2], b[1], b[2]))
    chg = []
    for idx in (3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15):
        if a[idx] != b[idx]:
            chg.append((idx, a[idx], b[idx]))
    if a[6] != b[6]:
        chg.append(("tag", a[6], b[6]))
    ac, bc = a[0].get("count"), b[0].get("count")
    if ac != bc:
        chg.append(("count", ac, bc))
    if chg:
        other_changed.append((nm, a[1], a[2], chg))

# 价格变更是否全部可解释
bad_price = []
for nm, ob, os, nb, ns in price_changed:
    if is_book_row_matching := None:
        pass
    is_book = nm.split(":")[-1] == "enchanted_book"
    if is_book:
        continue  # 书在 C13 单独核
    exp = PLAN_PRICE.get(nm)
    if exp is None or (nb, ns) != exp:
        bad_price.append((nm, f"{ob}/{os}->{nb}/{ns}", "期望 " + repr(exp)))
# 原版非书条目的价格必须不变
van_bad = [(nm, ob, os, nb, ns) for nm, ob, os, nb, ns in price_changed
           if nm.startswith("minecraft:") and not nm.endswith("enchanted_book")]
check("B4", "改价条目全部可由计划解释（改价/附魔书/新增矿物）", not bad_price,
      f"价格变更 {len(price_changed)} 条, 不可解释 {len(bad_price)} 条", bad_price[:20])
check("B4", "原版（minecraft）非附魔书条目买卖价与 08194 完全一致", not van_bad,
      f"原版改价条目数: {len(van_bad)}", van_bad[:20])

# 删除条目分类
bad_del, book_del_cnt, kc_del, chest_del = [], 0, [], []
for k in del_keys:
    nm, sg = k
    rows = rows94[k]
    for r in rows:
        if nm.endswith("enchanted_book"):
            book_del_cnt += 1
        elif nm in PLAN_DEL and nm != "minecraft:chest":
            kc_del.append((nm, r[1], r[2]))
        elif nm == "minecraft:chest" and r[1] == 0.0:
            chest_del.append((r[1], r[2], sg))
        else:
            bad_del.append((nm, r[1], r[2], sg[:120]))
check("B4", "删除条目全部可由计划解释（2 双前缀森罗行/重复箱子/空白书/低级书）", not bad_del,
      f"删除 {len(del_keys)} 条: 书 {book_del_cnt}, 双前缀 {len(kc_del)}, 箱子 {len(chest_del)}, 不可解释 {len(bad_del)}",
      bad_del[:20])
blank_book_del = [r for k in del_keys for r in rows94[k]
                  if k[0].endswith("enchanted_book") and r[0].get("userData") is None]
check("B4", "空白附魔书占位条已删除", len(blank_book_del) >= 1,
      f"空白书删除 {len(blank_book_del)} 条 (08194 价 {[(r[1], r[2]) for r in blank_book_del]})")
check("B4", "双前缀森罗坏 ID 已删除且无残留",
      {nm for nm, _, _ in kc_del} == (PLAN_DEL - {"minecraft:chest"})
      and not any(rname(r) in (PLAN_DEL - {"minecraft:chest"}) for r in sh95),
      f"删除的森罗行: {kc_del}")
check("B4", "重复 0 价箱子已删除", len(chest_del) == 1, f"chest_del={chest_del}")

# 新增条目分类
bad_add = []
for k in add_keys:
    nm, sg = k
    rows = rows95[k]
    for r in rows:
        if nm.endswith("enchanted_book"):
            continue
        exp = PLAN_ADD.get(nm)
        if exp is None or (r[1], r[2]) != exp:
            bad_add.append((nm, r[1], r[2], "期望 " + repr(exp)))
check("B4", "新增条目全部可由计划解释（9 条机械矿物/附魔书）", not bad_add,
      f"新增 {len(add_keys)} 条, 不可解释 {len(bad_add)} 条", bad_add[:20])

# 打标/其他字段变更
bad_tag, bad_field = [], []
for nm, ob, os, chg in other_changed:
    nsn = nm.split(":", 1)[0]
    tag_chg = [c for c in chg if c[0] == "tag"]
    field_chg = [c for c in chg if c[0] != "tag"]
    if tag_chg:
        _, ot, nt = tag_chg[0]
        if nsn in MOD_TAG:
            if nt != MOD_TAG[nsn]:
                bad_tag.append((nm, ot, nt, "应为 " + MOD_TAG[nsn]))
        elif nm.endswith("enchanted_book"):
            if nt != BOOK_TAG:
                bad_tag.append((nm, ot, nt))
        else:
            # 计划只允许 7 个模组标签与附魔书标签；森罗容器 方块→森罗物语 不在计划内
            bad_tag.append((nm, ot, nt))
    if field_chg:
        ok_cnt = (nm == "breath_maid:npc_55_food" and field_chg == [("count", None, 64)])
        if not ok_cnt:
            bad_field.append((nm, ob, os, field_chg))
check("B4", "打标变更全部符合计划（7 模组标签/附魔书/森罗容器）", not bad_tag,
      f"异常打标 {len(bad_tag)} 条", bad_tag[:20])
check("B4", "count 等其它字段变更仅限计划内（空气饲料/森罗容器）", not bad_field,
      f"异常字段变更 {len(bad_field)} 条", bad_field[:20])

# 新增 9 矿物 count==64 与 tag
min_bad = [(nm, r[1], r[2], r[0].get("count"), r[6]) for r in sh95 if rname(r) in PLAN_ADD
           if r[0].get("count") != 64 or r[6] != "机械动力"]
check("B4/C8", "新增 9 条机械矿物 count==64 且 tag==机械动力", not min_bad, min_bad)

# ============================================================== C. 关键数值
# C5
e = d95["ecoSystemData"]
cct = d95["customCoinTypes"]
check("C5", "defCoin==73", e["defCoin"] == 73, f"defCoin={e['defCoin']}")
check("C5", "preMinuteCoin==1.0", e["preMinuteCoin"] == 1.0, f"preMinuteCoin={e['preMinuteCoin']}")
jj = [c for c in cct if c.get("key") == "基金"]
check("C5", "基金 visibleInPack==false", bool(jj) and jj[0].get("visibleInPack") is False,
      f"基金={jj}")
check("C5", "deathLoseMoney==100", e["deathLoseMoney"] == 100, f"deathLoseMoney={e['deathLoseMoney']}")
eco_diff = [k for k in set(d94["ecoSystemData"]) | set(d95["ecoSystemData"])
            if d94["ecoSystemData"].get(k) != d95["ecoSystemData"].get(k)]
check("C5+", "ecoSystemData 仅 defCoin/preMinuteCoin/noticeMsg 变化",
      set(eco_diff) == {"preMinuteCoin", "noticeMsg", "defCoin"}, f"变化键={eco_diff}")

# C6
krm = d95["killEntityRewardMap"]
check("C6", "killEntityRewardMap 共 76 条", len(krm) == 76, f"len={len(krm)}")
spot = {"chicken": 1, "zombie": 10, "skeleton": 10, "creeper": 12, "spider": 10, "witch": 20,
        "blaze": 35, "warden": 80, "wither": 200, "ender_dragon": 200, "iron_golem": 0,
        "villager": 0, "cod": 0, "zombie_piglin": 5, "slime": 10}
bad_spot = [f"{m}={v[0]}≠{exp}" for m, exp in spot.items()
            for v in [krm.get(f"minecraft:{m}")] if v is None or v[0] != exp]
check("C6", "击杀表抽查 15 项全部符合", not bad_spot, bad_spot or "15/15 通过")
lost = [k for k in d94["killEntityRewardMap"] if k not in krm]
check("C6", "08194 原 4 条击杀全部保留", not lost, f"丢失: {lost}")
bad_type = [k for k, v in krm.items() if not (isinstance(v, list) and len(v) == 2 and v[1] == "金币")]
check("C6", "击杀表条目结构 [金币数,'金币']", not bad_type, f"异常: {bad_type[:5]}")

# C7 娘化生物
def find(name):
    return [r for r in sh95 if rname(r) == name]

jbad = []
for nm, (b, s) in JEWEL.items():
    rows = find(nm)
    if not rows or any((r[1], r[2]) != (float(b), float(s)) or r[6] != "娘化生物" for r in rows):
        jbad.append((nm, [(r[1], r[2], r[6]) for r in rows], (b, s)))
check("C7", "戒指/项链 12 条定价与标签符合计划", not jbad, jbad or "12/12 通过")
feed = find("breath_maid:npc_55_food")
check("C7", "npc_55_food==100/1 且 count==64", len(feed) == 1 and feed[0][1] == 100
      and feed[0][2] == 1 and feed[0][0].get("count") == 64 and feed[0][6] == "娘化生物",
      [(r[1], r[2], r[0].get("count"), r[6]) for r in feed])
cream = find("breath_maid:npc_item_1")
check("C7", "npc_item_1==200/10 且 tag 娘化生物", len(cream) == 1 and cream[0][1] == 200
      and cream[0][2] == 10 and cream[0][6] == "娘化生物",
      [(r[1], r[2], r[6]) for r in cream])
ratio_bad = []
for nm, (b, s) in JEWEL.items():
    if nm.endswith("_6"):
        exp = s * 1.5
        if abs(b - exp) > 0.01:
            ratio_bad.append((nm, b, s, "应为卖×1.5"))
    else:
        if b != s * 5:
            ratio_bad.append((nm, b, s, "应为卖×5"))
check("C7", "公式自检：买=配方×5（合金×1.5），卖=配方", not ratio_bad, ratio_bad or "12/12 通过")
anchors = {"minecraft:iron_ingot": 36, "minecraft:amethyst_shard": 8, "minecraft:gold_ingot": 72,
           "minecraft:emerald": 120, "minecraft:diamond": 200, "minecraft:slime_ball": 8,
           "minecraft:string": 3, "minecraft:netherite_ingot": 4500}
ab = []
for nm, exp in anchors.items():
    rows = find(nm)
    got = rows[0][1] if rows else None
    if got != exp:
        ab.append((nm, got, exp))
check("C7", "配方锚点价（铁锭36/紫晶8/金锭72/绿宝石120/钻石200/合金锭4500/粘液球8/线3）", not ab,
      ab or "锚点全部符合（合金锭=minecraft:netherite_ingot 4500）")
check("C7", "breath_maid 全部 14 条 tag==娘化生物",
      len([r for r in sh95 if rname(r).startswith("breath_maid:")]) == 14
      and all(r[6] == "娘化生物" for r in sh95 if rname(r).startswith("breath_maid:")))

# C8 机械动力
mach_bad = []
for m, b in MACHINES.items():
    nm = f"create:{m}"
    rows = find(nm)
    exp = (float(b), round(b * 0.25, 2))
    if not rows or any((r[1], r[2]) != exp or r[6] != "机械动力" for r in rows):
        mach_bad.append((nm, [(r[1], r[2], r[6]) for r in rows], exp))
check("C8", "机器 27 条按计划价（cogwheel 20 → mechanical_arm 350）卖价=round(买×0.25,2)", not mach_bad,
      mach_bad or "27/27 通过")
for nm in ("create:veridium", "create:ochrum"):
    rows = find(nm)
    ok = len(rows) == 1 and rows[0][1] == 2 and rows[0][2] == 0.1 and rows[0][6] == "机械动力"
    check("C8", f"{nm}==2/0.1 tag=机械动力", ok, [(r[1], r[2], r[6], r[0].get("count")) for r in rows])
create_rows = [r for r in sh95 if rname(r).startswith("create:")]
check("C8", "create 共 38 条且全部 tag==机械动力", len(create_rows) == 38
      and all(r[6] == "机械动力" for r in create_rows), f"create 行数={len(create_rows)}")
vb = find("create:veridium") + find("create:ochrum")
check("C8", "veridium/ochrum count==64（计划 ×64）", all(r[0].get("count") == 64 for r in vb),
      [(rname(r), r[0].get("count")) for r in vb])
cu = find("minecraft:copper_ingot")
zn = find("create:zinc_ingot")
br = find("create:brass_ingot")
ok_arb = bool(cu and zn and br) and cu[0][1] == 12 and zn[0][1] == 24 and br[0][2] == 15 \
    and 2 * br[0][2] < cu[0][1] + zn[0][1]
check("C8", "防套利：2×黄铜锭卖价(30) < 铜锭买价(12)+锌锭买价(24)=36",
      ok_arb, f"铜锭={cu[0][1] if cu else None} 锌锭={zn[0][1] if zn else None} "
              f"黄铜锭卖={br[0][2] if br else None}")

# C9 旅行袋
arm_bad = []
for nm, (b, s) in ARMOR.items():
    rows = find(nm)
    if not rows or any((r[1], r[2]) != (float(b), float(s)) or r[6] != "旅行袋" for r in rows):
        arm_bad.append((nm, [(r[1], r[2], r[6]) for r in rows], (b, s)))
check("C9", "盔甲插件 8 条定价+标签符合计划", not arm_bad, arm_bad or "8/8 通过")
ihz = {"ihzao:chainmining": (2000, 0), "ihzao:httravbag": (400, 10), "ihzao:magnetht": (900, 0)}
ihz_bad = []
for nm, (b, s) in ihz.items():
    rows = find(nm)
    if not rows or any((r[1], r[2]) != (float(b), float(s)) or r[6] != "旅行袋" for r in rows):
        ihz_bad.append((nm, [(r[1], r[2], r[6]) for r in rows]))
check("C9", "chainmining 2000/0、httravbag 400/10、magnetht 900/0", not ihz_bad, ihz_bad or "3/3 通过")
plht = [r for r in sh95 if rname(r).startswith("ihzao:") and "plht" in rname(r)]
plht_bad = [(rname(r), r[1], r[2], r[6]) for r in plht if (r[1], r[2]) != (500, 100) or r[6] != "旅行袋"]
check("C9", f"plht 系列({len(plht)} 条)全部维持 500/100", not plht_bad, plht_bad or f"{len(plht)} 条通过")
ihz_all = [r for r in sh95 if rname(r).startswith("ihzao:")]
check("C9", f"ihzao 全部 {len(ihz_all)} 条 tag==旅行袋", len(ihz_all) == 23
      and all(r[6] == "旅行袋" for r in ihz_all), f"ihzao 行数={len(ihz_all)}")

# C10 车万女仆
ysm_ok = True
for nm, (b, s) in {"ysm_maid:explosion_protect_bauble": (2000, 100),
                   "ysm_maid:smart_slab_empty": (150, 0)}.items():
    rows = find(nm)
    if not rows or any((r[1], r[2]) != (float(b), float(s)) or r[6] != "车万女仆" for r in rows):
        ysm_ok = False
        check("C10", f"{nm} 符合计划", False, [(r[1], r[2], r[6]) for r in rows])
check("C10", "explosion_protect_bauble 2000/100、smart_slab_empty 150/0", ysm_ok)
ysm_all = [r for r in sh95 if rname(r).startswith("ysm_maid:")]
check("C10", f"ysm_maid 全部 {len(ysm_all)} 条 tag==车万女仆", len(ysm_all) == 11
      and all(r[6] == "车万女仆" for r in ysm_all), f"ysm 行数={len(ysm_all)}")

# C11 农夫乐事
fd_ok = True
for nm, (b, s) in {"farmer_delight_nullgr:dumplings": (40, 12),
                   "farmer_delight_nullgr:pincers": (40, 25)}.items():
    rows = find(nm)
    if not rows or any((r[1], r[2]) != (float(b), float(s)) or r[6] != "农夫乐事" for r in rows):
        fd_ok = False
        check("C11", f"{nm} 符合计划", False, [(r[1], r[2], r[6]) for r in rows])
check("C11", "dumplings 40/12、pincers 40/25", fd_ok)
check("C11", "farmer_delight_nullgr 2 条 tag==农夫乐事、farmers_tale_nullgr 2 条 tag==农夫传说",
      all(r[6] == "农夫乐事" for r in sh95 if rname(r).startswith("farmer_delight_nullgr:"))
      and all(r[6] == "农夫传说" for r in sh95 if rname(r).startswith("farmers_tale_nullgr:")))

# C12 森罗 / 原版清理
kc_ok = True
for nm, (b, s) in {"kaleidoscope_tavern:kaleidoscope_tavern_empty_bottle": (5, 3.13),
                   "kaleidoscope_tavern:kaleidoscope_tavern_empty_glassware": (5, 3.13),
                   "kaleidoscope_cookery:kaleidoscope_cookery_empty_cup": (10, 2)}.items():
    rows = find(nm)
    if not rows or any((r[1], r[2]) != (float(b), float(s)) for r in rows):
        kc_ok = False
        check("C12", f"{nm} 定价符合计划", False, [(r[1], r[2]) for r in rows])
check("C12", "空瓶 5/3.13、空酒杯 5/3.13、空杯 10/2", kc_ok)
chests = [r for r in sh95 if rname(r) == "minecraft:chest"]
check("C12", "minecraft:chest 只剩 1 条且 8/5", len(chests) == 1 and chests[0][1] == 8 and chests[0][2] == 5,
      [(r[1], r[2]) for r in chests])
blanks = [r for r in sh95 if rname(r).endswith("enchanted_book") and r[0].get("userData") is None]
check("C12", "无 userData 的空白 enchanted_book 行不存在", not blanks,
      [(r[1], r[2]) for r in blanks])
dp = [r for r in sh95 if rname(r) in PLAN_DEL and rname(r) != "minecraft:chest"]
check("C12", "双前缀森罗行不存在", not dp, dp)

# C13 附魔书
books = [r for r in sh95 if is_book_row(r)]
nbooks = len(books)
btag = all(r[6] == BOOK_TAG for r in books)
bsell = all(r[2] == 6.25 for r in books)
brange = all(20 <= r[1] <= 800 for r in books)
check("C13", f"附魔书共 {nbooks} 本（计划 69）、全部 tag==§l原版|附魔书、卖价 6.25、买价 20–800",
      nbooks == 69 and btag and bsell and brange,
      f"n={nbooks} tag_ok={btag} sell_ok={bsell} range_ok={brange}")
groups = defaultdict(set)
for r in books:
    eid, lvl, mod = enchant_of(r)
    groups[(eid, mod)].add(lvl)
lvl_bad = []
for (eid, mod), lvls in groups.items():
    mx = 3 if mod else MAXLV.get(eid, 1)
    want = {mx} if mx < 2 else {mx, mx - 1}
    if lvls != want:
        lvl_bad.append((eid, mod, sorted(lvls), sorted(want)))
check("C13", "每种附魔（id+modEnchant）只保留 {满级, 满级-1} 两级", not lvl_bad, lvl_bad or f"{len(groups)} 组通过")
price_bad = []
for r in books:
    eid, lvl, mod = enchant_of(r)
    exp = exp_book_price(eid, lvl, mod)
    if abs(r[1] - exp) > 0.01:
        price_bad.append((eid, lvl, mod, r[1], exp))
check("C13", "买价符合 tier×(lvl/max)² 四舍五入（任务 tier 表）", not price_bad, price_bad or "69/69 通过")
mend = [r for r in books if enchant_of(r)[0] == 26 and enchant_of(r)[1] == 1]
check("C13", "修补(26,1)=800 存在", len(mend) == 1 and mend[0][1] == 800,
      [(r[1], r[2]) for r in mend])
# 实际 tier 与任务表差异明细（由满级书价格反推 tier）
tier_actual = {}
for r in books:
    eid, lvl, mod = enchant_of(r)
    mx = 3 if mod else MAXLV.get(eid, 1)
    if lvl == mx:
        tier_actual[(eid, mod)] = round(r[1] / ((lvl / mx) ** 2))
tier_diff = {k: (tier_actual[k], (280 if k[1] else TIER.get(k[0], 180)))
             for k in tier_actual
             if tier_actual[k] != (280 if k[1] else TIER.get(k[0], 180))}

# C14
zz = [(rname(r), r[1], r[2]) for r in sh95 if r[1] == 0 and r[2] == 0]
check("C14", "全店无买价和卖价同时为 0 的条目", not zz, zz or f"{len(zz)} 条")
sell_gt = [(rname(r), r[1], r[2]) for r in sh95 if r[2] > r[1]]
sell_gt_bad = [(nm, b, s) for nm, b, s in sell_gt if not nm.endswith("_spawn_egg")]
check("C14", "除刷怪蛋外无卖价高于买价的条目", not sell_gt_bad,
      f"卖>买共 {len(sell_gt)} 条（刷怪蛋 {len(sell_gt) - len(sell_gt_bad)} 条）, 异常: {sell_gt_bad[:20]}")

# C15 noticeMsg
notice = e["noticeMsg"]
total = len(sh95)
cnt = Counter(rname(r).split(":", 1)[0] for r in sh95)
check("C15", f"noticeMsg 含合计 {total}（实际总数）", str(total) in notice, notice[:160] + "…")
keys_ok = all(s in notice for s in ("开局73", "在线+1/分", "基金隐藏", "死亡固定扣100"))
check("C15", "noticeMsg 含关键数字（73/1分/基金隐藏/扣100）", keys_ok, notice)
n_books = sum(1 for r in sh95 if is_book_row(r))
expect_frag = {
    "minecraft": cnt.get("minecraft", 0), "附魔书": n_books,
    "kaleidoscope_cookery": cnt.get("kaleidoscope_cookery", 0),
    "kaleidoscope_tavern": cnt.get("kaleidoscope_tavern", 0),
    "kaleidoscope_doll": cnt.get("kaleidoscope_doll", 0),
    "bricefire": cnt.get("bricefire", 0), "ihzao": cnt.get("ihzao", 0),
    "ysm_maid": cnt.get("ysm_maid", 0), "create": cnt.get("create", 0),
    "breath_maid": cnt.get("breath_maid", 0), "ws": cnt.get("ws", 0),
}
frag_bad = []
for nsnm, n in expect_frag.items():
    frag_bad.append((nsnm, n, f"{n}" in notice))
check("C15", "noticeMsg 各命名空间计数与真实数字一致", all(x[2] for x in frag_bad),
      [x for x in frag_bad if not x[2]])

# ============================================================== D. 抽奖
pools = d95["luckyDraws"]
PLAN_POOLS = {"你饿了么": 80, "炼金学徒": 100, "附魔书店": 250, "武器池": 200, "工具商店": 300,
              "宠物盲盒": 150, "花语盒": 40, "唱片盒": 350, "防具盲盒": 600}
check("D16", "luckyDraws 共 9 池", len(pools) == 9, f"len={len(pools)}")
nm_bad = [(p["name"], p["buyPrice"], PLAN_POOLS.get(p["name"])) for p in pools
          if PLAN_POOLS.get(p["name"]) != p["buyPrice"]]
check("D16", "池名与票价与计划一致", sorted(p["name"] for p in pools) == sorted(PLAN_POOLS) and not nm_bad,
      nm_bad or [p["name"] for p in pools])
w_bad = [(p["name"], sum(rw["weight"] for rw in p["rewards"])) for p in pools
         if sum(rw["weight"] for rw in p["rewards"]) != 100]
check("D16", "每池权重和 == 100", not w_bad, w_bad or "9/9 通过")
q_bad = [(p["name"], rw["quality"]) for p in pools for rw in p["rewards"]
         if rw["quality"] not in ("common", "rare", "legendary")]
check("D16", "quality 只出现 common/rare/legendary", not q_bad, q_bad or "全部符合")

# D17 武器/工具/防具
def book_item(eid, lvl):
    return {"count": 1, "newAuxValue": 0, "newItemName": "minecraft:enchanted_book",
            "userData": {"ench": [{"id": {"__type__": 2, "__value__": eid},
                                   "lvl": {"__type__": 2, "__value__": lvl}}]}}


def potion6():
    return {"count": 1, "newAuxValue": 6, "newItemName": "minecraft:potion"}


def plain(name, q, w):
    return {"count": 1, "newAuxValue": 0, "newItemName": name}


EXPECT_POOLS = {
    "武器池": [
        (3, "legendary", [plain("minecraft:diamond_sword", "l", 0), book_item(9, 5)]),
        (3, "legendary", [plain("minecraft:diamond_sword", "l", 0), book_item(14, 3)]),
        (3, "legendary", [plain("minecraft:diamond_sword", "l", 0), book_item(13, 2)]),
        (3, "legendary", [plain("minecraft:diamond_sword", "l", 0), book_item(26, 1)]),
        (1, "legendary", [plain("minecraft:netherite_sword", "l", 0), book_item(26, 1)]),
        (47, "rare", [plain("minecraft:diamond_sword", "l", 0)]),
        (40, "common", [potion6()]),
    ],
    "工具商店": [
        (3, "legendary", [plain("minecraft:diamond_pickaxe", "l", 0), book_item(15, 5)]),
        (3, "legendary", [plain("minecraft:diamond_pickaxe", "l", 0), book_item(18, 3)]),
        (3, "legendary", [plain("minecraft:diamond_pickaxe", "l", 0), book_item(16, 1)]),
        (3, "legendary", [plain("minecraft:diamond_pickaxe", "l", 0), book_item(26, 1)]),
        (1, "legendary", [plain("minecraft:netherite_pickaxe", "l", 0), book_item(26, 1)]),
        (47, "rare", [plain("minecraft:diamond_pickaxe", "l", 0)]),
        (40, "common", [potion6()]),
    ],
    "防具盲盒": [
        (3, "legendary", [plain("minecraft:diamond_chestplate", "l", 0), book_item(0, 4)]),
        (3, "legendary", [plain("minecraft:diamond_chestplate", "l", 0), book_item(17, 3)]),
        (3, "legendary", [plain("minecraft:diamond_chestplate", "l", 0), book_item(5, 3)]),
        (3, "legendary", [plain("minecraft:diamond_chestplate", "l", 0), book_item(26, 1)]),
        (1, "legendary", [plain("minecraft:netherite_chestplate", "l", 0), book_item(26, 1)]),
        (47, "rare", [plain("minecraft:diamond_leggings", "l", 0)]),
        (40, "common", [potion6()]),
    ],
}
d17_bad = []
for pname, exp_rw in EXPECT_POOLS.items():
    p = next((x for x in pools if x["name"] == pname), None)
    if p is None:
        d17_bad.append((pname, "池不存在"))
        continue
    got = [(rw["weight"], rw["quality"], rw["items"]) for rw in p["rewards"]]
    for (w, q, items), (ew, eq, eitems) in zip(got, exp_rw):
        if w != ew or q != eq or items != eitems:
            d17_bad.append((pname, "差异", (w, q, items), (ew, eq, eitems)))
    if len(got) != len(exp_rw):
        d17_bad.append((pname, f"奖励数 {len(got)}≠{len(exp_rw)}"))
check("D17", "武器池/工具商店/防具盲盒奖励结构与计划完全一致（4×3%头奖+1%合金+47%+40%药水）",
      not d17_bad, d17_bad[:6] or "3 池全部一致")
# 附魔书奖励 userData 与商店附魔书同构
shop_book_ud = None
for r in books:
    if enchant_of(r) == (9, 5, None):
        shop_book_ud = r[0]["userData"]
struct_bad = []
for p in pools:
    for rw in p["rewards"]:
        for it in rw["items"]:
            if it.get("userData") is not None:
                ud = it["userData"]
                keys_ok = set(ud.keys()) == {"ench"} and len(ud["ench"]) == 1
                if keys_ok:
                    e0 = ud["ench"][0]
                    keys_ok = set(e0.keys()) == {"id", "lvl"} and \
                        e0["id"].get("__type__") == 2 and e0["lvl"].get("__type__") == 2
                if not keys_ok:
                    struct_bad.append((p["name"], ud))
                elif shop_book_ud is not None and json.dumps(ud, sort_keys=True) != json.dumps(shop_book_ud, sort_keys=True) and \
                        set(ud["ench"][0].keys()) != set(shop_book_ud["ench"][0].keys()):
                    struct_bad.append((p["name"], "键结构异于商店书", ud))
check("D17", "抽奖附魔书 userData 结构与商店附魔书同构", not struct_bad, struct_bad[:5] or "同构")

# D18
p = next(x for x in pools if x["name"] == "炼金学徒")
aux = sorted({(it["newAuxValue"]) for rw in p["rewards"] for it in rw["items"]})
check("D18", "炼金学徒药水 aux == {16,21,7,0}", aux == [0, 7, 16, 21], f"aux={aux}")
p = next(x for x in pools if x["name"] == "你饿了么")
food_items = [(it["newItemName"], it["count"]) for rw in p["rewards"] for it in rw["items"]]
check("D18", "你饿了么奖励与计划一致", food_items == [("minecraft:golden_carrot", 128), ("minecraft:cake", 2),
      ("minecraft:golden_carrot", 64), ("minecraft:bread", 64), ("minecraft:cooked_beef", 64)],
      food_items)
p = next(x for x in pools if x["name"] == "附魔书店")
book_rw = [(rw["weight"], rw["quality"],
            [(it["newItemName"], it.get("userData", {}).get("ench", [{}])[0].get("id", {}).get("__value__"),
              it.get("userData", {}).get("ench", [{}])[0].get("lvl", {}).get("__value__")) for it in rw["items"]])
           for rw in p["rewards"]]
check("D18", "附魔书店奖励与计划一致（10%修补/60%耐久III/30%书×16）", book_rw == [
      (10, "legendary", [("minecraft:enchanted_book", 26, 1)]),
      (60, "rare", [("minecraft:enchanted_book", 17, 3)]),
      (30, "common", [("minecraft:book", None, None)])], book_rw)
HOSTILE = {"blaze", "creeper", "drowned", "elder_guardian", "endermite", "evoker", "ghast",
           "guardian", "hoglin", "husk", "magma_cube", "phantom", "piglin", "piglin_brute",
           "pillager", "ravager", "shulker", "silverfish", "skeleton", "slime", "spider",
           "stray", "vex", "vindicator", "warden", "witch", "wither", "wither_skeleton",
           "zoglin", "zombie", "zombie_villager", "zombified_piglin", "breeze", "bogged"}
p = next(x for x in pools if x["name"] == "宠物盲盒")
egg_bad = []
for rw in p["rewards"]:
    for it in rw["items"]:
        mob = it["newItemName"].split(":")[-1].replace("_spawn_egg", "")
        if mob in HOSTILE:
            egg_bad.append(it["newItemName"])
check("D18", "宠物盲盒全是被动/中立宠物蛋（无敌对）", not egg_bad,
      egg_bad or "18 种蛋均被动/中立")
p = next(x for x in pools if x["name"] == "花语盒")
fl = [(rw["weight"], rw["quality"], [(it["newItemName"], it["count"]) for it in rw["items"]])
      for rw in p["rewards"]]
check("D18", "花语盒与计划一致且含 breath_maid:npc_item_1", fl == [
      (10, "legendary", [("breath_maid:npc_item_1", 1)]),
      (40, "rare", [("minecraft:wither_rose", 16)]),
      (50, "common", [("minecraft:poppy", 32), ("minecraft:dandelion", 32)])], fl)
p = next(x for x in pools if x["name"] == "唱片盒")
jb = [(rw["weight"], rw["quality"], [it["newItemName"] for it in rw["items"]]) for rw in p["rewards"]]
jb_ok = all("minecraft:jukebox" in [i["newItemName"] for i in rw["items"]] for rw in p["rewards"]) \
    and jb == [(10, "legendary", ["minecraft:music_disc_pigstep", "minecraft:jukebox"]),
               (20, "rare", ["minecraft:music_disc_relic", "minecraft:jukebox"]),
               (20, "rare", ["minecraft:music_disc_5", "minecraft:jukebox"]),
               (10, "common", ["minecraft:music_disc_13", "minecraft:jukebox"]),
               (10, "common", ["minecraft:music_disc_cat", "minecraft:jukebox"]),
               (10, "common", ["minecraft:music_disc_far", "minecraft:jukebox"]),
               (10, "common", ["minecraft:music_disc_mall", "minecraft:jukebox"]),
               (10, "common", ["minecraft:music_disc_stal", "minecraft:jukebox"])]
check("D18", "唱片盒每个奖励都含 jukebox 且与计划一致", jb_ok, jb)
create_in_pools = [(p["name"], it["newItemName"]) for p in pools for rw in p["rewards"]
                   for it in rw["items"] if it["newItemName"].startswith("create:")]
check("D18", "任何池无 create/齿轮类奖品", not create_in_pools, create_in_pools or "无")

# D19
d19_bad = []
ids = []
for p in pools:
    if p.get("freeDrawCount") != 1:
        d19_bad.append((p["name"], "freeDrawCount", p.get("freeDrawCount")))
    if p.get("limitCount") != 10:
        d19_bad.append((p["name"], "limitCount", p.get("limitCount")))
    if p.get("requestItem") is not None:
        d19_bad.append((p["name"], "requestItem", p.get("requestItem")))
    if not p.get("id"):
        d19_bad.append((p["name"], "id 为空"))
    ids.append(p.get("id"))
if len(set(ids)) != len(ids):
    d19_bad.append(("id 重复", ids))
check("D19", "每池 freeDrawCount=1、limitCount=10、requestItem=null、id 非空不重复", not d19_bad, d19_bad or "9/9 通过")
check("D19", "freeDrawType=1 / limitType=1（每日）", all(p.get("freeDrawType") == 1 and p.get("limitType") == 1 for p in pools))

# ============================================================== 汇总
print("=" * 100)
print("验收汇总表")
print("=" * 100)
ids_order = ["A1", "A2", "A3", "B4", "C5", "C6", "C7", "C8", "C9", "C10", "C11", "C12",
             "C13", "C14", "C15", "D16", "D17", "D18", "D19"]
agg = defaultdict(lambda: [True, []])
for cid, ok, name, details in results:
    key = cid.split("/")[0].split("+")[0]
    agg[key][0] = agg[key][0] and ok
    agg[key][1].append((cid, name, ok, details))
for key in ids_order:
    ok, items = agg[key]
    print(f"{key:5s} {'PASS' if ok else 'FAIL'}  ({len(items)} 子项)")
print()
print("=" * 100)
print("FAIL 明细与证据")
print("=" * 100)
nfail = 0
for key in ids_order:
    ok, items = agg[key]
    for cid, name, isok, details in items:
        if not isok:
            nfail += 1
            print(f"\n[{cid}] {name}")
            for d in details:
                print("    " + repr(d))
print(f"\n共 {nfail} 个子项 FAIL")
print("\n关键证据补充：")
print("- 商店条目 08194/08195:", len(sh94), "->", len(sh95), "| 附魔书:", len(books))
print("- 价格变更条目:", len(price_changed), "| 删除:", len(del_keys), "| 新增:", len(add_keys),
      "| 合并count对:", len(merged_pairs))
print("- 原版非书改价条目:", len(van_bad), "| 卖>买条目(全部为刷怪蛋):", len(sell_gt))
print("- noticeMsg:", notice)
print("\n附：满级价反推 tier 与任务表不一致的附魔 (id,mod)->(实际,任务表):",
      tier_diff if tier_diff else "无")
print("\nnamespace 实际计数:", dict(sorted(cnt.items())))
