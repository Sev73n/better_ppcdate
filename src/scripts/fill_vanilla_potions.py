# -*- coding: utf-8 -*-
"""Base = user's adjusted share. Fix brew/cup, add potion category + vanilla gaps."""
import json
import base64
import zlib
from collections import Counter
from pathlib import Path

BASE = Path(r"C:/Users/AI10/Desktop/ppcdata")
SRC = Path(r"C:/Users/AI10/AppData/Local/Temp/ppcp_decode/user_cfg_adj.json")
CFG = BASE / "01_配置明文" / "最终配置_rebuilt.json"
SELL = 0.625

data = json.loads(SRC.read_text(encoding="utf-8"))
ns = data["nameSpaceMap"]


def r2(x):
    return round(float(x) + 1e-12, 2)


def sell_of(buy):
    s = r2(buy * SELL)
    if s >= buy and buy > 0:
        s = r2(buy - 0.01) if buy > 0.01 else 0.0
    return s


def make(ns_id, name, count, buy, tag, dur=0):
    buy = r2(buy)
    item = {"NIN": f"{ns_id}:{name}", "durability": dur, "modEnchantData": []}
    if count is not None:
        item["count"] = count
    return [
        item,
        buy,
        sell_of(buy),
        "",
        0,
        0,
        tag,
        False,
        "金币",
        "金币",
        0,
        1.0,
        min(count or 1, 64) if (count or 1) >= 16 else 1,
        0.0 if (count or 1) >= 16 else 0.2,
        0.9,
        0.1,
    ]


rev = {str(v): k for k, v in ns.items()}
abs_to_idx = {}
kept = []
removed = []
for r in data["systemShopItems"]:
    nin = r[0]["NIN"]
    pref, name = nin.split(":", 1)
    abs_id = f"{rev.get(pref, pref)}:{name}"
    if abs_id == "minecraft:brewing_stand":
        removed.append(abs_id)
        continue
    if abs_id in abs_to_idx:
        removed.append(f"dup:{abs_id}")
        continue
    if len(r) > 8:
        r[8] = "金币"
    if len(r) > 9:
        r[9] = "金币"
    if abs_id == "kaleidoscope_cookery:empty_cup":
        r[1], r[2] = 10.0, 2.0
        if r[0].get("count") is None:
            r[0]["count"] = 16
    if abs_id == "minecraft:item.brewing_stand":
        r[1], r[2] = 100.0, sell_of(100)
        r[6] = "方块"
        if r[0].get("count") is None:
            r[0]["count"] = 1
    if not r[6]:
        if name.endswith("_spawn_egg"):
            r[6] = "刷怪蛋"
        elif name == "bed":
            r[6] = "方块"
        else:
            r[6] = "其他"
    abs_to_idx[abs_id] = len(kept)
    kept.append(r)
data["systemShopItems"] = kept

have = set(abs_to_idx)
mc_ns = ns["minecraft"]
added = []


def add(name, count, buy, tag, dur=0):
    abs_id = f"minecraft:{name}"
    if dur == 0 and abs_id in have:
        return False
    if dur != 0:
        for r in data["systemShopItems"]:
            if r[0].get("NIN") == f"{mc_ns}:{name}" and r[0].get("durability", 0) == dur:
                return False
    elif abs_id in have:
        return False
    data["systemShopItems"].append(make(mc_ns, name, count, buy, tag, dur))
    have.add(abs_id)
    added.append(name if dur == 0 else f"{name}#{dur}")
    return True


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
for c in COLORS:
    add(f"{c}_bed", 1, 8.0, "方块")

COMMON = [
    ("dandelion", 16, 1.0, "方块"),
    ("poppy", 16, 1.0, "方块"),
    ("blue_orchid", 16, 1.5, "方块"),
    ("allium", 16, 1.5, "方块"),
    ("azure_bluet", 16, 1.0, "方块"),
    ("oxeye_daisy", 16, 1.0, "方块"),
    ("cornflower", 16, 1.5, "方块"),
    ("lily_of_the_valley", 16, 2.0, "方块"),
    ("sunflower", 16, 2.0, "方块"),
    ("lilac", 16, 2.0, "方块"),
    ("rose_bush", 16, 2.0, "方块"),
    ("peony", 16, 2.0, "方块"),
    ("wither_rose", 16, 25.0, "方块"),
    ("torchflower", 16, 8.0, "方块"),
    ("pitcher_plant", 16, 8.0, "方块"),
    ("pink_petals", 16, 2.0, "方块"),
    ("spore_blossom", 16, 12.0, "方块"),
    ("sculk_vein", 64, 8.0, "方块"),
    ("sculk_shrieker", 1, 80.0, "方块"),
    ("flower_pot", 16, 5.0, "方块"),
    ("item.flower_pot", 16, 5.0, "方块"),
    ("painting", 16, 10.0, "其他"),
    ("armor_stand", 16, 20.0, "其他"),
    ("firework_rocket", 64, 8.0, "其他"),
    ("firework_star", 64, 5.0, "材料"),
    ("fire_charge", 64, 6.0, "材料"),
    ("goat_horn", 1, 150.0, "其他"),
    ("recovery_compass", 1, 200.0, "其他"),
    ("echo_shard", 16, 80.0, "材料"),
    ("disc_fragment_5", 16, 40.0, "材料"),
    ("end_crystal", 1, 800.0, "材料"),
    ("totem_of_undying", 1, 2000.0, "材料"),
    ("nether_star", 1, 5000.0, "材料"),
    ("heart_of_the_sea", 1, 400.0, "材料"),
    ("nautilus_shell", 16, 40.0, "材料"),
    ("trident", 1, 800.0, "工具"),
    ("trial_key", 1, 200.0, "材料"),
    ("ominous_trial_key", 1, 400.0, "材料"),
    ("breeze_rod", 16, 40.0, "材料"),
    ("wind_charge", 64, 15.0, "材料"),
    ("mace", 1, 8000.0, "工具"),
    ("glass_pane", 64, 2.0, "方块"),
    ("terracotta", 64, 1.5, "方块"),
    ("clay", 64, 2.0, "方块"),
    ("bookshelf", 64, 20.0, "方块"),
    ("powder_snow_bucket", 1, 20.0, "其他"),
    ("tadpole_bucket", 1, 80.0, "其他"),
    ("tube_coral_block", 64, 6.0, "方块"),
    ("brain_coral_block", 64, 6.0, "方块"),
    ("bubble_coral_block", 64, 6.0, "方块"),
    ("fire_coral_block", 64, 6.0, "方块"),
    ("horn_coral_block", 64, 6.0, "方块"),
]
for c in COLORS:
    COMMON.append((f"{c}_wool", 64, 4.0, "方块"))

DISCS = [
    ("music_disc_13", 80),
    ("music_disc_cat", 80),
    ("music_disc_blocks", 80),
    ("music_disc_chirp", 80),
    ("music_disc_far", 80),
    ("music_disc_mall", 80),
    ("music_disc_mellohi", 80),
    ("music_disc_stal", 80),
    ("music_disc_strad", 80),
    ("music_disc_ward", 80),
    ("music_disc_11", 80),
    ("music_disc_wait", 80),
    ("music_disc_otherside", 120),
    ("music_disc_5", 150),
    ("music_disc_pigstep", 200),
    ("music_disc_relic", 150),
    ("music_disc_creator", 120),
    ("music_disc_creator_music_box", 120),
    ("music_disc_precipice", 120),
]
for name, buy in DISCS:
    COMMON.append((name, 1, buy, "其他"))

for name, count, buy, tag in COMMON:
    add(name, count, buy, tag)

# Potions: durability = Bedrock aux (VERIFY in-game on NetEase)
POTION_TAG = "药水"
potion_added = []
for name, dur, buy in [
    ("potion", 0, 8.0),
    ("splash_potion", 0, 12.0),
    ("lingering_potion", 0, 16.0),
]:
    if add(name, 1, buy, POTION_TAG, dur):
        potion_added.append(f"{name}:{dur}")

EFFECTS = [
    (21, 40, "治疗"),
    (22, 50, "伤害"),
    (28, 45, "迅捷"),
    (29, 50, "再生"),
    (31, 55, "力量"),
    (25, 45, "抗火"),
    (27, 40, "夜视"),
    (30, 50, "水肺"),
    (14, 55, "隐身?待核"),
]
for dur, buy, label in EFFECTS:
    for base, mult in [("potion", 1.0), ("splash_potion", 1.3), ("lingering_potion", 1.6)]:
        if base == "lingering_potion" and dur not in (21, 31, 25, 28):
            continue
        price = r2(buy * mult)
        if add(base, 1, price, POTION_TAG, dur):
            potion_added.append(f"{base}:{dur}:{label}")

TAG_ORDER = [
    "材料",
    "方块",
    "食物",
    "工具",
    "装备",
    "刷怪蛋",
    "药水",
    "其他",
    "森罗物语（厨房）",
    "森罗物语（酒馆）",
    "森罗物语（玩偶）",
    "冰火传说",
]
TYPE_MAP = {
    "全部": {"texturePath": "textures/ui/magnifyingGlass"},
    "材料": {"texturePath": "textures/ui/ppeco_tag/tag_5"},
    "方块": {"texturePath": "textures/ui/ppeco_tag/tag_20"},
    "食物": {"texturePath": "textures/items/cake"},
    "工具": {"texturePath": "textures/items/diamond_pickaxe"},
    "装备": {"texturePath": "textures/ui/ppeco_tag/tag_2"},
    "刷怪蛋": {"texturePath": "textures/items/egg"},
    "药水": {"texturePath": "textures/items/potion_bottle_heal"},
    "其他": {"texturePath": "textures/ui/permissions_custom_dots"},
    "森罗物语（厨房）": {
        "texturePath": "textures/kaleidoscope_cookery/items/crop/rice_panicle"
    },
    "森罗物语（酒馆）": {
        "texturePath": "textures/ktavern/item/brew/drink/sakura_wine"
    },
    "森罗物语（玩偶）": {
        "texturePath": "textures/kaleidoscope_doll/blocks/doll_machine_icon"
    },
    "冰火传说": {"texturePath": "textures/items/bone"},
}
# keep 基金 icon entry if present in old type map from user
for k, v in data.get("customItemTypeMap", {}).items():
    if k not in TYPE_MAP and "基金" not in k:
        TYPE_MAP[k] = v

data["customItemTags"] = TAG_ORDER
data["customItemTypeMap"] = TYPE_MAP

counts = Counter()
tags = Counter()
for r in data["systemShopItems"]:
    pref = r[0]["NIN"].split(":", 1)[0]
    counts[rev.get(pref, pref)] += 1
    tags[r[6]] += 1

mc = counts.get("minecraft", 0)
cook = counts.get("kaleidoscope_cookery", 0)
tav = counts.get("kaleidoscope_tavern", 0)
doll = counts.get("kaleidoscope_doll", 0)
ice = counts.get("bricefire", 0)
total = len(data["systemShopItems"])
notice = (
    f"仅金币｜原版{mc}｜森罗厨{cook}+酒{tav}+偶{doll}｜冰火{ice}｜合计{total}｜死亡扣30%｜含药水分类"
)
data["ecoSystemData"]["noticeMsg"] = notice

CFG.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
share = "ppcpdata%" + base64.b64encode(
    zlib.compress(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode(), 9
    )
).decode()
(BASE / "分享码.txt").write_text(share, encoding="utf-8")
(BASE / "05_原始备份" / "最终分享串_副本.txt").write_text(share, encoding="utf-8")

(BASE / "03_对比报告" / "本次补齐说明.txt").write_text(
    f"""本次基于你调整版的补齐说明
========================

【酿造台】
保留 minecraft:item.brewing_stand（你手动验证可用）
删除 minecraft:brewing_stand
价格：买100 / 卖62.5

【空杯】
维持买10/卖2。
旧价30原因：脚本把 empty_cup 误判成厨具设备档(与茶壶/蒸笼同价)，
不是故意比茶贵。茶≈18；空杯应是便宜容器。

【药水分类】
标签「药水」。用 durability=基岩 aux 区分效果。
网易版本 aux 可能不同，请创造核对治疗/力量等是否正确。

【补齐】彩色床、花、羊毛、唱片、烟花、珊瑚、幽匿等（已有则跳过）
vanilla新增约 {len(added)}（含药水行）
药水行: {len(potion_added)}
删除: {removed}

数量: 原版{mc} 森罗{cook+tav+doll} 冰火{ice} 合计{total}
""",
    encoding="utf-8",
)

print("removed", removed)
print("added", len(added))
print("potions", len(potion_added))
print("tags", dict(tags))
print("ns", dict(counts), "total", total)
print("notice", notice)
print("share_len", len(share))
