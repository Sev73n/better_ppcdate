# -*- coding: utf-8 -*-
"""Fill remaining vanilla: gold tools, skulls, banners, trims, sherds, eggs, potions."""
from __future__ import annotations

import base64
import csv
import json
import zlib
from collections import Counter
from pathlib import Path

BASE = Path(r"C:/Users/AI10/Desktop/ppcdata")
SHARE = BASE / "分享码.txt"
CFG = BASE / "01_配置明文" / "最终配置_rebuilt.json"
SELL = 0.625

MAX_DUR = {
    "golden_axe": 32,
    "golden_shovel": 32,
    "golden_hoe": 32,
    "golden_sword": 32,
    "golden_pickaxe": 32,
}

# Bedrock potion aux (common set; NetEase may differ — verify in-game)
POTION_EFFECTS = [
    # (aux, buy_base, label)
    (5, 35, "夜视短?"),
    (6, 40, "夜视长?"),
    (7, 35, "隐身短?"),
    (8, 40, "隐身长?"),
    (9, 35, "跳跃短"),
    (10, 40, "跳跃长"),
    (11, 45, "防火短"),
    (12, 50, "防火长"),
    (13, 40, "迅捷短"),
    (14, 55, "迅捷/隐身核"),
    (15, 45, "迟缓短"),
    (16, 50, "水肺短"),
    (17, 45, "治疗"),
    (18, 50, "伤害"),
    (19, 45, "毒短"),
    (21, 40, "治疗II档"),
    (22, 50, "伤害II档"),
    (23, 45, "再生短"),
    (24, 50, "再生长"),
    (25, 45, "抗火"),
    (26, 50, "力量短"),
    (27, 40, "夜视"),
    (28, 45, "迅捷"),
    (29, 50, "再生"),
    (30, 50, "水肺"),
    (31, 55, "力量"),
    (32, 45, "虚弱"),
    (33, 60, "缓降"),
    (34, 70, "龟仙"),
    (35, 65, "粘液?"),
    (36, 80, "黑暗?"),
    (37, 90, "织网?"),
    (38, 90, "渗浆?"),
    (39, 90, "寄生?"),
    (40, 100, "袭兆?"),
]

SPAWN_EGGS = {
    # T1 farm / passive
    "bat": 200,
    "cod": 200,
    "salmon": 200,
    "tropical_fish": 200,
    "pufferfish": 250,
    "squid": 200,
    "glow_squid": 300,
    "trader_llama": 400,
    "zombie_villager": 600,
    "zombie_horse": 800,
    "skeleton_horse": 800,
    "npc": 200,  # may fail on NetEase — skip if unwanted
}

# safer egg list without npc
SPAWN_EGGS.pop("npc", None)

TRIMS = {
    # common-ish structure
    "sentry": 400,
    "dune": 400,
    "coast": 400,
    "wild": 400,
    "tide": 500,
    "snout": 600,
    "rib": 600,
    "host": 500,
    "raiser": 500,
    "shaper": 500,
    "wayfinder": 500,
    # rarer
    "ward": 900,
    "eye": 900,
    "vex": 1000,
    "spire": 1200,
    "silence": 1500,
    "flow": 1200,
    "bolt": 1200,
}

SHERDS = [
    "angler",
    "archer",
    "arms_up",
    "blade",
    "brewer",
    "burn",
    "danger",
    "explorer",
    "friend",
    "heart",
    "heartbreak",
    "howl",
    "miner",
    "mourner",
    "plenty",
    "prize",
    "sheaf",
    "shelter",
    "skull",
    "snort",
    "flow",
    "guster",
    "scrape",
]

BANNERS = {
    "flower_banner_pattern": 80,
    "creeper_banner_pattern": 200,
    "skull_banner_pattern": 250,
    "mojang_banner_pattern": 800,
    "globe_banner_pattern": 300,
    "piglin_banner_pattern": 350,
    "flow_banner_pattern": 400,
    "guster_banner_pattern": 400,
    "field_masoned_banner_pattern": 120,
    "bordure_indented_banner_pattern": 120,
}


def r2(x):
    return round(float(x) + 1e-12, 2)


def sell_of(buy, zero=False):
    if zero:
        return 0.0
    s = r2(buy * SELL)
    if s >= buy and buy > 0:
        s = r2(buy - 0.01) if buy > 0.01 else 0.0
    return s


def load_share(p: Path):
    t = p.read_text(encoding="utf-8").strip()
    if t.startswith("ppcpdata%"):
        return json.loads(zlib.decompress(base64.b64decode(t.split("%", 1)[1])))
    return json.loads(t)


def main():
    data = load_share(SHARE)
    rev = {str(v): k for k, v in data["nameSpaceMap"].items()}
    fwd = {k: str(v) for k, v in data["nameSpaceMap"].items()}
    mc = fwd["minecraft"]

    # existing keys: name; multi-aux names use (name,dur)
    MULTI_AUX = {"potion", "splash_potion", "lingering_potion", "skull"}
    have = set()
    have_aux = set()
    for r in data["systemShopItems"]:
        pref, name = r[0]["NIN"].split(":", 1)
        if rev.get(pref) != "minecraft":
            continue
        dur = r[0].get("durability", 0)
        if name in MULTI_AUX:
            have_aux.add((name, dur))
        else:
            have.add(name)

    report = []
    added = 0

    def add(name, buy, count=1, tag="其他", dur=0, sell_zero=False):
        nonlocal added
        if name in MULTI_AUX:
            key = (name, dur)
            if key in have_aux:
                return False
            have_aux.add(key)
        else:
            if name in have:
                return False
            have.add(name)
        buy = r2(buy)
        item = {
            "NIN": f"{mc}:{name}",
            "durability": MAX_DUR.get(name, dur or 0),
            "modEnchantData": [],
        }
        if name in MULTI_AUX:
            item["durability"] = dur
        if count is not None:
            item["count"] = count
        f12 = min(count or 1, 64) if (count or 1) >= 16 else 1
        f13 = 0.0 if (count or 1) >= 16 else 0.2
        row = [
            item,
            buy,
            sell_of(buy, zero=sell_zero),
            "",
            0,
            0,
            tag,
            False,
            "金币",
            "金币",
            0,
            1.0,
            f12,
            f13,
            0.9,
            0.1,
        ]
        data["systemShopItems"].append(row)
        added += 1
        report.append((name, dur, buy, count, tag, "add"))
        return True

    # --- gold tools + odds ---
    add("golden_axe", 150, 1, "工具")
    add("golden_shovel", 60, 1, "工具")
    add("golden_hoe", 100, 1, "工具")
    add("spectral_arrow", 6, 64, "材料")
    add("dragon_egg", 13140, 1, "材料")
    add("melon_block", 8, 64, "食物")  # ~ melon_slice×4-ish convenience
    add("brick", 1.0, 64, "材料")  # clay brick item
    add("netherbrick", 1.5, 64, "材料")  # bedrock item alias
    add("map", 20, 16, "其他")
    add("empty_map", 20, 16, "其他")
    add("filled_map", 40, 1, "其他")
    add("written_book", 30, 1, "其他")

    # --- skulls (Bedrock often skull + aux; also try named heads) ---
    # Named IDs (newer) + legacy skull variants via durability aux if needed
    for name, buy in [
        ("skeleton_skull", 200),
        ("wither_skeleton_skull", 800),
        ("zombie_head", 300),
        ("creeper_head", 600),
        ("dragon_head", 4000),
        ("piglin_head", 500),
        ("player_head", 1000),
    ]:
        add(name, buy, 1, "其他")
    # legacy minecraft:skull + aux 0-5 (common Bedrock / NetEase)
    for aux, buy, _label in [
        (0, 200, "骷髅头颅"),
        (1, 800, "凋灵骷髅头颅"),
        (2, 300, "僵尸头"),
        (3, 1000, "玩家头"),
        (4, 600, "苦力怕头"),
        (5, 4000, "龙首"),
    ]:
        add("skull", buy, 1, "其他", dur=aux)

    # --- banner patterns ---
    for name, buy in BANNERS.items():
        add(name, buy, 1, "其他")

    # --- armor trims ---
    for t, buy in TRIMS.items():
        add(f"{t}_armor_trim_smithing_template", buy, 1, "材料")
    add("netherite_upgrade_smithing_template", 2000, 1, "材料")

    # --- pottery sherds ---
    for s in SHERDS:
        add(f"{s}_pottery_sherd", 100, 16, "材料")

    # --- missing spawn eggs (sell=0 policy) ---
    for mob, buy in SPAWN_EGGS.items():
        add(f"{mob}_spawn_egg", buy, 1, "刷怪蛋", sell_zero=True)

    # --- expand potions ---
    # water bottles
    add("potion", 8, 1, "药水", dur=0)
    add("splash_potion", 12, 1, "药水", dur=0)
    add("lingering_potion", 16, 1, "药水", dur=0)
    for aux, buy, label in POTION_EFFECTS:
        add("potion", buy, 1, "药水", dur=aux)
        add("splash_potion", r2(buy * 1.3), 1, "药水", dur=aux)
        if aux in (17, 18, 21, 22, 25, 28, 29, 31, 11, 12, 33):
            add("lingering_potion", r2(buy * 1.6), 1, "药水", dur=aux)

    # ensure tags include 药水
    tags = data.get("customItemTags") or []
    if "药水" not in tags:
        if "刷怪蛋" in tags:
            i = tags.index("刷怪蛋") + 1
            tags.insert(i, "药水")
        else:
            tags.append("药水")
        data["customItemTags"] = tags
    tm = data.setdefault("customItemTypeMap", {})
    tm.setdefault(
        "药水", {"texturePath": "textures/items/potion_bottle_heal"}
    )

    counts = Counter()
    for r in data["systemShopItems"]:
        counts[rev.get(r[0]["NIN"].split(":", 1)[0])] += 1
    total = len(data["systemShopItems"])
    mc_n = counts.get("minecraft", 0)
    cook = counts.get("kaleidoscope_cookery", 0)
    tav = counts.get("kaleidoscope_tavern", 0)
    doll = counts.get("kaleidoscope_doll", 0)
    ice = counts.get("bricefire", 0)
    extra = total - mc_n - cook - tav - doll - ice
    data.setdefault("ecoSystemData", {})["noticeMsg"] = (
        f"仅金币｜原版{mc_n}｜森罗厨{cook}+酒{tav}+偶{doll}｜冰火{ice}｜其他{extra}｜合计{total}｜"
        f"死亡扣30%｜刷怪蛋不可回收｜药水aux待核"
    )

    CFG.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    share = "ppcpdata%" + base64.b64encode(
        zlib.compress(
            json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode(), 9
        )
    ).decode()
    (BASE / "分享码.txt").write_text(share, encoding="utf-8")
    (BASE / "05_原始备份" / "最终分享串_副本.txt").write_text(share, encoding="utf-8")

    rep = BASE / "03_对比报告" / "原版收藏与蛋药水补齐.csv"
    with open(rep, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "durability", "buy", "count", "tag", "action"])
        w.writerows(report)

    (BASE / "02_定价锚点与说明" / "简介.txt").write_text(
        f"""分享码简介（当前版）

【货币】仅金币
【数量】原版{mc_n}｜森罗厨{cook}+酒{tav}+偶{doll}｜冰火{ice}｜其他{extra}｜合计{total}
【本轮】金工具零头｜头颅/旗帜图案｜盔甲纹饰｜陶片｜补蛋｜扩展药水aux
【注意】药水 durability=基岩aux，网易请创造核对；刷怪蛋不可回收
【公告】{data['ecoSystemData']['noticeMsg']}
""",
        encoding="utf-8",
    )

    print(f"added={added} mc={mc_n} total={total} share={len(share)}")
    for s in [
        "golden_axe",
        "spectral_arrow",
        "skeleton_skull",
        "skull",
        "sentry_armor_trim_smithing_template",
        "angler_pottery_sherd",
        "bat_spawn_egg",
        "dragon_egg",
        "creeper_banner_pattern",
    ]:
        hits = [
            r
            for r in data["systemShopItems"]
            if rev.get(r[0]["NIN"].split(":")[0]) == "minecraft"
            and r[0]["NIN"].split(":", 1)[1] == s
        ]
        if hits:
            r = hits[0]
            print(
                f"  {s:40} buy={r[1]} sell={r[2]} dur={r[0].get('durability')} c={r[0].get('count')}"
            )


if __name__ == "__main__":
    main()
