# -*- coding: utf-8 -*-
"""Add vault / trial_spawner / mob_spawner and remaining obtainable vanilla leftovers."""
from __future__ import annotations

import base64
import csv
import json
import zlib
from collections import Counter
from pathlib import Path

BASE = Path(r"C:/Users/AI10/Desktop/ppcdata")
CFG = BASE / "01_配置明文" / "最终配置_rebuilt.json"
SHARE = BASE / "分享码.txt"
SELL = 0.625


def r2(x):
    return round(float(x) + 1e-12, 2)


def sell_of(buy, zero=False):
    if zero:
        return 0.0
    s = r2(buy * SELL)
    if s >= buy and buy > 0:
        s = r2(buy - 0.01) if buy > 0.01 else 0.0
    return s


def main():
    data = json.loads(CFG.read_text(encoding="utf-8"))
    rev = {str(v): k for k, v in data["nameSpaceMap"].items()}
    fwd = {k: str(v) for k, v in data["nameSpaceMap"].items()}
    mc = fwd["minecraft"]
    have = {}
    for r in data["systemShopItems"]:
        pref, name = r[0]["NIN"].split(":", 1)
        if rev.get(pref) == "minecraft":
            have[name] = r

    report = []
    added = 0

    def add(name, buy, count=1, tag="方块", sell_zero=False, reason="add"):
        nonlocal added
        if name in have:
            return False
        buy = r2(buy)
        item = {"NIN": f"{mc}:{name}", "durability": 0, "modEnchantData": []}
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
        have[name] = row
        added += 1
        report.append((name, reason, buy, row[2], tag, count))
        return True

    # ----- trial chambers / spawners (user confirmed in NetEase) -----
    add("vault", 800.0, 1, "其他", reason="试炼宝库")
    add("trial_spawner", 600.0, 1, "其他", reason="试炼刷怪笼")
    add("mob_spawner", 2500.0, 1, "其他", reason="刷怪笼")

    # ----- block-id aliases already sold under another name -----
    add("brewing_stand", 100.0, 1, "其他", reason="alias of item.brewing_stand")
    add("iron_chain", 8.0, 64, "材料", reason="alias of chain")
    add("golden_rail", 40.0, 64, "其他", reason="alias of powered_rail")
    add("silver_glazed_terracotta", 3.5, 64, "方块", reason="alias of light_gray glazed")
    add("reeds", 2.0, 64, "材料", reason="alias of sugar_cane")
    add("tallgrass", 0.6, 16, "方块", reason="alias of tall_grass")
    add("small_dripleaf", 4.0, 16, "方块", reason="alias of small_dripleaf_block")
    add("evocation_illager_spawn_egg", 8000.0, 1, "刷怪蛋", sell_zero=True, reason="alias of evoker")
    add("vindication_illager_spawn_egg", 4000.0, 1, "刷怪蛋", sell_zero=True, reason="alias of vindicator")

    # ----- leftover placeable vanilla -----
    add("farmland", 0.3, 64, "方块")
    add("azalea_leaves", 1.0, 64, "方块")
    add("azalea_leaves_flowered", 1.2, 64, "方块")
    add("bamboo_sapling", 1.0, 64, "方块")
    add("cave_vines", 3.0, 64, "方块")
    add("cave_vines_head_with_berries", 4.0, 16, "方块")
    add("sweet_berry_bush", 2.0, 16, "方块")
    add("carrots", 3.0, 64, "食物", reason="bedrock crop block")
    add("potatoes", 3.0, 64, "食物", reason="bedrock crop block")
    add("cocoa", 3.0, 64, "方块", reason="bedrock cocoa block")
    add("snow_layer", 0.3, 64, "方块")
    add("powder_snow", 2.0, 64, "方块")
    add("polished_blackstone_pressure_plate", 2.0, 16, "其他")
    add("smooth_stone_slab", 0.19, 64, "方块")
    add("normal_stone_stairs", 0.3, 64, "方块")
    add("cut_red_sandstone_slab", 0.94, 64, "方块")
    add("smooth_red_sandstone_slab", 0.99, 64, "方块")
    add("smooth_red_sandstone_stairs", 2.7, 64, "方块")
    add("smooth_sandstone_stairs", 2.25, 64, "方块")
    add("petrified_oak_slab", 0.33, 64, "方块")
    for c in ("tube", "brain", "bubble", "fire", "horn"):
        add(f"{c}_coral_wall_fan", 4.0, 16, "方块")
        add(f"dead_{c}_coral_wall_fan", 1.5, 16, "方块")
    for n in (
        "infested_stone",
        "infested_cobblestone",
        "infested_stone_bricks",
        "infested_mossy_stone_bricks",
        "infested_cracked_stone_bricks",
        "infested_chiseled_stone_bricks",
        "infested_deepslate",
    ):
        add(n, 8.0, 64, "方块")

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
    notice = (
        f"仅金币｜原版{mc_n}｜森罗厨{cook}+酒{tav}+偶{doll}｜冰火{ice}｜其他{extra}｜合计{total}｜"
        f"死亡扣30%｜刷怪蛋不可回收｜药水aux待核｜铜器时代已补"
    )
    data.setdefault("ecoSystemData", {})["noticeMsg"] = notice

    CFG.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    share = "ppcpdata%" + base64.b64encode(
        zlib.compress(
            json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode(), 9
        )
    ).decode()
    SHARE.write_text(share, encoding="utf-8")
    (BASE / "05_原始备份" / "最终分享串_副本.txt").write_text(share, encoding="utf-8")

    (BASE / "02_定价锚点与说明" / "简介.txt").write_text(
        f"""分享码简介（当前版）

【货币】仅金币
【数量】原版{mc_n}｜森罗厨{cook}+酒{tav}+偶{doll}｜冰火{ice}｜其他{extra}｜合计{total}
【本轮】试炼宝库/试炼笼/刷怪笼｜杜鹃叶与石台阶缺口｜基岩别名
【注意】建筑楼梯/唱片/陶片维持便利价；刷怪蛋不可回收
【公告】{notice}
""",
        encoding="utf-8",
    )

    csv_path = BASE / "03_对比报告" / "试炼宝库与遗漏补齐.csv"
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "reason", "buy", "sell", "tag", "count"])
        w.writerows(report)

    must = ["vault", "trial_spawner", "mob_spawner", "azalea_leaves", "smooth_stone_slab"]
    lines = [f"added={added} mc={mc_n} total={total} share={len(share)}"]
    ok = True
    for n in must:
        hit = n in have
        if not hit:
            ok = False
        lines.append(f"  [{'OK' if hit else 'FAIL'}] {n} buy={have[n][1] if hit else '-'}")
    txt = BASE / "03_对比报告" / "试炼宝库与遗漏补齐.txt"
    txt.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    if not ok:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
