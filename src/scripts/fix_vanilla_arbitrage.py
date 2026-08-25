# -*- coding: utf-8 -*-
"""Fix vanilla compact-block arbitrage, buckets, sell>=buy, enchanted apple."""
from __future__ import annotations

import base64
import csv
import json
import zlib
from collections import Counter
from pathlib import Path

BASE = Path(r"C:/Users/AI10/Desktop/ppcdata")
CFG = BASE / "01_配置明文" / "最终配置_rebuilt.json"
SELL = 0.625

COMPACT = [
    ("minecraft:coal_block", "minecraft:coal", 9, 1.1),
    ("minecraft:iron_block", "minecraft:iron_ingot", 9, 1.1),
    ("minecraft:gold_block", "minecraft:gold_ingot", 9, 1.1),
    ("minecraft:diamond_block", "minecraft:diamond", 9, 1.1),
    ("minecraft:emerald_block", "minecraft:emerald", 9, 1.1),
    ("minecraft:lapis_block", "minecraft:lapis_lazuli", 9, 1.1),
    ("minecraft:redstone_block", "minecraft:redstone", 9, 1.1),
    ("minecraft:copper_block", "minecraft:copper_ingot", 9, 1.1),
    ("minecraft:raw_iron_block", "minecraft:raw_iron", 9, 1.1),
    ("minecraft:raw_gold_block", "minecraft:raw_gold", 9, 1.1),
    ("minecraft:raw_copper_block", "minecraft:raw_copper", 9, 1.1),
    ("minecraft:netherite_block", "minecraft:netherite_ingot", 9, 1.1),
    ("minecraft:slime_block", "minecraft:slime_ball", 9, 1.1),
    ("minecraft:quartz_block", "minecraft:quartz", 4, 1.1),
    ("minecraft:amethyst_block", "minecraft:amethyst_shard", 4, 1.1),
    ("minecraft:honey_block", "minecraft:honey_bottle", 4, 1.1),
]

BUCKETS = {
    "minecraft:water_bucket": 45.0,
    "minecraft:lava_bucket": 80.0,
    "minecraft:milk_bucket": 50.0,
    "minecraft:powder_snow_bucket": 55.0,
    "minecraft:cod_bucket": 60.0,
    "minecraft:salmon_bucket": 60.0,
    "minecraft:tropical_fish_bucket": 70.0,
    "minecraft:pufferfish_bucket": 90.0,
    "minecraft:tadpole_bucket": 65.0,
    "minecraft:axolotl_bucket": 300.0,
}


def r2(x):
    return round(float(x) + 1e-12, 2)


def sell_of(buy):
    s = r2(buy * SELL)
    if s >= buy and buy > 0:
        s = r2(buy - 0.01) if buy > 0.01 else 0.0
    return s


def main():
    data = json.loads(CFG.read_text(encoding="utf-8"))
    rev = {str(v): k for k, v in data["nameSpaceMap"].items()}
    rows = {}
    for r in data["systemShopItems"]:
        pref, name = r[0]["NIN"].split(":", 1)
        rows[f"{rev.get(pref, pref)}:{name}"] = r

    def unit(abs_id):
        r = rows.get(abs_id)
        if not r:
            return None
        # count 是默认交易堆，买/卖价是单件价，不能除以 count
        return float(r[1])

    def set_price(abs_id, buy, count=None):
        r = rows.get(abs_id)
        if not r:
            return
        r[1] = r2(buy)
        r[2] = sell_of(buy)
        if count is not None:
            r[0]["count"] = count

    report = []
    for block, ing, n, mult in COMPACT:
        u = unit(ing)
        if u is None or block not in rows:
            continue
        old = rows[block][1]
        set_price(block, n * u * mult, count=1)
        report.append((block, old, rows[block][1], f"unit={r2(u)} x{n} x{mult}"))

    set_price("minecraft:bucket", 40.0, count=1)
    for bid, buy in BUCKETS.items():
        if bid in rows:
            old = rows[bid][1]
            set_price(bid, buy, count=1)
            report.append((bid, old, buy, "bucket count=1"))

    if "minecraft:bed" in rows:
        set_price("minecraft:bed", 8.0, count=1)
        report.append(("minecraft:bed", 1.0, 8.0, "align beds"))
    for brew in ("minecraft:item.brewing_stand", "minecraft:brewing_stand"):
        if brew in rows:
            old = rows[brew][1]
            set_price(brew, 100.0, count=1)
            report.append((brew, old, 100.0, "brewing stand"))
    if "minecraft:enchanted_golden_apple" in rows:
        old = rows["minecraft:enchanted_golden_apple"][1]
        set_price("minecraft:enchanted_golden_apple", 6000.0, count=1)
        report.append(("minecraft:enchanted_golden_apple", old, 6000.0, "rarity"))

    if "minecraft:red_flower" in rows and float(rows["minecraft:red_flower"][2]) == 0:
        rows["minecraft:red_flower"][2] = sell_of(rows["minecraft:red_flower"][1])

    for abs_id, r in rows.items():
        if abs_id.startswith("bricefire:") and "map" in abs_id.split(":", 1)[1]:
            buy = float(r[1])
            if buy > 0 and abs(float(r[2]) / buy - 0.3125) < 0.02:
                r[2] = sell_of(buy)

    counts = Counter()
    for r in data["systemShopItems"]:
        counts[rev.get(r[0]["NIN"].split(":", 1)[0])] += 1
    mc = counts.get("minecraft", 0)
    cook = counts.get("kaleidoscope_cookery", 0)
    tav = counts.get("kaleidoscope_tavern", 0)
    doll = counts.get("kaleidoscope_doll", 0)
    ice = counts.get("bricefire", 0)
    total = len(data["systemShopItems"])
    data["ecoSystemData"]["noticeMsg"] = (
        f"仅金币｜原版{mc}｜森罗厨{cook}+酒{tav}+偶{doll}｜冰火{ice}｜合计{total}｜"
        f"死亡扣30%｜森罗按配方材料×人工C｜刷怪蛋不可回收"
    )

    CFG.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    share = "ppcpdata%" + base64.b64encode(
        zlib.compress(
            json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode(), 9
        )
    ).decode()
    (BASE / "分享码.txt").write_text(share, encoding="utf-8")
    (BASE / "05_原始备份" / "最终分享串_副本.txt").write_text(share, encoding="utf-8")
    with open(BASE / "03_对比报告" / "原版套利与桶族修复.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "old_buy", "new_buy", "note"])
        w.writerows(report)
    print(f"fixes={len(report)} share={len(share)}")


if __name__ == "__main__":
    main()
