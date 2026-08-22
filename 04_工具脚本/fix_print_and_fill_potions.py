# -*- coding: utf-8 -*-
"""Close remaining print-money loops + fill potion/arrow/horn/bottle/lit_pumpkin.

Does NOT add new external mods.
"""
from __future__ import annotations

import base64
import csv
import json
import sys
import zlib
from collections import Counter
from pathlib import Path

BASE = Path(r"C:/Users/AI10/Desktop/ppcdata")
CFG = BASE / "01_配置明文" / "最终配置_rebuilt.json"
SHARE = BASE / "分享码.txt"
SELL = 0.625
PREMIUM = 1.1

sys.path.insert(0, str(BASE / "04_工具脚本"))
from reprice_kaleidoscope_B_recipes import (  # noqa: E402
    REC_COOK,
    REC_TAV,
    TAG_FALLBACK,
    expand_tag_members,
    load_tags,
    parse_recipe,
    should_keep,
    short_id,
)

NEW_POTIONS = [
    (1, 10, "平凡"),
    (2, 10, "平凡长"),
    (3, 10, "浓稠"),
    (4, 12, "粗制"),
    (20, 55, "水肺长"),
    (41, 70, "缓降长"),
    (42, 55, "缓慢IV"),
    (43, 90, "风弹"),
    (44, 90, "盘丝"),
    (45, 90, "渗浆"),
    (46, 90, "寄生"),
]


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
    report = []

    rows = {}
    have_aux = set()
    for r in data["systemShopItems"]:
        pref, name = r[0]["NIN"].split(":", 1)
        ns = rev.get(pref, pref)
        abs_id = f"{ns}:{name}"
        dur = r[0].get("durability", 0)
        rows[abs_id] = r
        rows.setdefault(name, r)
        have_aux.add((name, dur))

    def buy_of(abs_id):
        r = rows.get(abs_id)
        return float(r[1]) if r else None

    def set_buy(abs_id, buy, reason):
        r = rows.get(abs_id)
        if not r:
            return
        old_b, old_s = float(r[1]), float(r[2])
        buy = r2(buy)
        r[1] = buy
        r[2] = sell_of(buy)
        report.append((abs_id, "reprice", old_b, buy, old_s, r[2], reason))

    def set_sell(abs_id, new_sell, reason):
        r = rows.get(abs_id)
        if not r:
            return
        old_s = float(r[2])
        new_sell = r2(new_sell)
        if new_sell < 0:
            new_sell = 0.0
        if abs(old_s - new_sell) < 0.005:
            return
        r[2] = new_sell
        report.append((abs_id, "cap-sell", float(r[1]), float(r[1]), old_s, new_sell, reason))

    def add(name, buy, count=1, tag="其他", dur=0, sell_zero=False, reason="add"):
        key = (name, dur)
        if key in have_aux:
            return False
        have_aux.add(key)
        buy = r2(buy)
        item = {"NIN": f"{mc}:{name}", "durability": dur, "modEnchantData": []}
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
        rows[f"minecraft:{name}"] = row
        report.append((f"minecraft:{name}#{dur}", reason, "", buy, "", row[2], f"tag={tag}"))
        return True

    # ----- vanilla print loops -----
    slice_p = buy_of("minecraft:melon_slice") or 2.0
    set_buy("minecraft:melon_block", r2(9 * slice_p * PREMIUM), "9x melon_slice x1.1")
    snowball = buy_of("minecraft:snowball") or 1.0
    set_buy("minecraft:snow", r2(4 * snowball * PREMIUM), "4x snowball x1.1")
    clay_ball = buy_of("minecraft:clay_ball") or 2.0
    set_buy("minecraft:clay", r2(4 * clay_ball * PREMIUM), "4x clay_ball x1.1")
    kelp = buy_of("minecraft:dried_kelp") or 1.0
    set_buy("minecraft:dried_kelp_block", r2(9 * kelp * PREMIUM), "9x dried_kelp x1.1")

    # fill lava: sell(lava) must be < buy(empty)
    bucket = buy_of("minecraft:bucket") or 40.0
    set_buy("minecraft:lava_bucket", r2(bucket / SELL * 0.9), "sell(lava)<buy(empty)")

    # craft-sell: sell < shop mat buy
    ender_mats = 8 * (buy_of("minecraft:obsidian") or 40) + (buy_of("minecraft:ender_eye") or 80)
    set_buy("minecraft:ender_chest", r2(ender_mats / SELL * 0.95), "sell<8 obsidian+eye")
    rod_mats = 3 * (buy_of("minecraft:stick") or 0.2) + 2 * (buy_of("minecraft:string") or 3)
    set_buy("minecraft:fishing_rod", r2(rod_mats / SELL * 0.95), "sell<3 stick+2 string")

    # ice-and-fire eggs
    for abs_id, r in list(rows.items()):
        if not isinstance(abs_id, str) or not abs_id.startswith("bricefire:"):
            continue
        if abs_id.endswith("_spawn_egg") and float(r[2]) > 0:
            set_sell(abs_id, 0.0, "spawn egg sell=0")

    # cooked meat sell < raw buy
    for abs_id, r in list(rows.items()):
        if not isinstance(abs_id, str) or not abs_id.startswith("bricefire:"):
            continue
        name = abs_id.split(":", 1)[1]
        if name.startswith("cooked_"):
            raw = "bricefire:" + name[len("cooked_") :]
            rb = buy_of(raw)
            if rb is not None and float(r[2]) >= rb:
                set_sell(abs_id, r2(rb * 0.9), f"cooked sell<raw {raw}")

    # ----- kitchen/tavern: cap sell below shop-mat cost -----
    shop_buy = {}
    for abs_id, r in rows.items():
        if not isinstance(abs_id, str) or ":" not in abs_id:
            continue
        shop_buy[abs_id] = float(r[1])

    tags = load_tags()
    recipes = []
    for folder in (REC_COOK, REC_TAV):
        if not folder.exists():
            continue
        for p in folder.rglob("*.json"):
            rec = parse_recipe(p)
            if rec:
                recipes.append(rec)

    def resolve_ing(kind, ref, crafted):
        if kind == "item":
            if ref in crafted:
                return crafted[ref]
            return shop_buy.get(ref)
        if kind == "tag":
            members = expand_tag_members(tags, ref)
            prices = []
            for m in members:
                if m in crafted:
                    prices.append(crafted[m])
                elif m in shop_buy:
                    prices.append(shop_buy[m])
            if prices:
                return min(prices)
            fb = TAG_FALLBACK.get(ref)
            if fb:
                if fb in crafted:
                    return crafted[fb]
                return shop_buy.get(fb)
        return None

    crafted = {}
    fluid_mb = {}
    for _ in range(24):
        changed = 0
        for rec in recipes:
            if rec["type"] == "kaleidoscope_tavern:pressing_tub" and rec.get("fluid_out"):
                costs = []
                ok = True
                for kind, ref, cnt in rec["ings"]:
                    m = resolve_ing(kind, ref, crafted)
                    if m is None:
                        ok = False
                        break
                    costs.append(m * cnt)
                if not ok:
                    continue
                amt = max(rec["fluid_amount"], 1)
                per_mb = sum(costs) / amt
                if fluid_mb.get(rec["fluid_out"]) != per_mb:
                    fluid_mb[rec["fluid_out"]] = per_mb
                    changed += 1
                fname = short_id(rec["fluid_out"])
                bottle = shop_buy.get("kaleidoscope_tavern:empty_bottle") or shop_buy.get(
                    "minecraft:glass_bottle", 5.0
                )
                juice_id = f"kaleidoscope_tavern:{fname}"
                juice_cost = per_mb * 250 + bottle
                if crafted.get(juice_id) != juice_cost:
                    crafted[juice_id] = juice_cost
                    changed += 1
                continue
            out = rec.get("out")
            if not out:
                continue
            total = 0.0
            ok = True
            for kind, ref, cnt in rec["ings"]:
                m = resolve_ing(kind, ref, crafted)
                if m is None:
                    ok = False
                    break
                total += m * cnt
            if not ok:
                continue
            carrier = rec.get("carrier")
            if carrier and carrier in shop_buy:
                total += shop_buy[carrier]
            fl = rec.get("fluid_in")
            if fl and fl in fluid_mb:
                total += fluid_mb[fl] * 250
            if rec["type"] == "kaleidoscope_cookery:rice_bowl":
                cr = "kaleidoscope_cookery:cooked_rice"
                total += crafted.get(cr, shop_buy.get(cr, 0) or 0)
            per = total / max(rec["out_count"], 1)
            old = crafted.get(out)
            if old is None or per < old - 1e-12:
                crafted[out] = per
                changed += 1
        if changed == 0:
            break

    for abs_id, r in list(rows.items()):
        if not isinstance(abs_id, str):
            continue
        mod, name = abs_id.split(":", 1) if ":" in abs_id else ("", abs_id)
        if mod not in ("kaleidoscope_cookery", "kaleidoscope_tavern"):
            continue
        if should_keep(name) and name not in (
            "raw_noodles",
            "raw_dough",
            "stuffed_dough_food",
            "raw_zongzi",
            "raw_bamboo_tube_rice",
            "raw_meatball",
        ):
            continue
        mat = crafted.get(abs_id)
        if mat is None:
            continue
        cur_sell = float(r[2])
        if cur_sell < mat - 1e-9:
            continue
        cap = r2(mat * 0.9)
        if cap >= mat:
            cap = r2(mat - 0.01) if mat > 0.01 else 0.0
        set_sell(abs_id, cap, f"sell<mat {r2(mat)}")

    # ----- potions / arrows / horns / bottles / pumpkin -----
    drink_buy = {}
    for r in data["systemShopItems"]:
        pref, name = r[0]["NIN"].split(":", 1)
        if rev.get(pref) != "minecraft" or name != "potion":
            continue
        drink_buy[r[0].get("durability", 0)] = float(r[1])

    for aux, buy, _label in NEW_POTIONS:
        add("potion", buy, 1, "药水", dur=aux, reason="potion-aux")
        add("splash_potion", r2(buy * 1.3), 1, "药水", dur=aux, reason="splash-aux")
        drink_buy.setdefault(aux, buy)

    # lingering for every drink aux we know
    for aux, buy in sorted(drink_buy.items()):
        add("lingering_potion", r2(buy * 1.6), 1, "药水", dur=aux, reason="lingering-aux")

    arrow0 = buy_of("minecraft:arrow") or 2.0
    for aux, buy in sorted(drink_buy.items()):
        if aux == 0:
            continue
        add("arrow", r2(max(8.0, arrow0 + buy * 0.35)), 64, "材料", dur=aux, reason="tipped-arrow")

    for aux in range(1, 5):
        add("ominous_bottle", r2(150 + 70 * aux), 16, "材料", dur=aux, reason="ominous-level")
    for aux in range(1, 8):
        add("goat_horn", 120.0, 1, "材料", dur=aux, reason="goat-horn")
    add("lit_pumpkin", 8.0, 16, "方块", reason="bedrock jack-o-lantern")

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
【本轮】关西瓜/雪/粘土/熔岩桶/末影箱/钓竿/厨房回收｜补药水药箭不祥瓶羊角南瓜灯
【注意】模组新扩展未加；刷怪蛋不可回收；药水aux请创造核对
【公告】{notice}
""",
        encoding="utf-8",
    )

    csv_path = BASE / "03_对比报告" / "印钱修复与药水扩充.csv"
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "action", "old_buy", "new_buy", "old_sell", "new_sell", "reason"])
        w.writerows(report)

    # verify
    def b(i):
        return float(rows[i][1])

    def s(i):
        return float(rows[i][2])

    checks = []
    checks.append(("melon uncraft", 9 * s("minecraft:melon_slice") - b("minecraft:melon_block")))
    checks.append(("snow uncraft", 4 * s("minecraft:snowball") - b("minecraft:snow")))
    checks.append(("clay uncraft", 4 * s("minecraft:clay_ball") - b("minecraft:clay")))
    checks.append(("lava fill", s("minecraft:lava_bucket") - b("minecraft:bucket")))
    checks.append(("ender_chest craft-sell", s("minecraft:ender_chest") - ender_mats))
    checks.append(("fishing_rod craft-sell", s("minecraft:fishing_rod") - rod_mats))
    if "kaleidoscope_cookery:fried_egg" in rows:
        checks.append(("fried_egg vs egg", s("kaleidoscope_cookery:fried_egg") - b("minecraft:egg")))
    if "kaleidoscope_cookery:cooked_rice" in rows:
        checks.append(("cooked_rice vs rice", s("kaleidoscope_cookery:cooked_rice") - b("kaleidoscope_cookery:rice")))
    if "kaleidoscope_cookery:oolong" in rows:
        checks.append(("oolong vs 12 breath", s("kaleidoscope_cookery:oolong") - 12 * (buy_of("minecraft:dragon_breath") or 80)))
    for egg in ("bricefire:kpshop_npc_spawn_egg", "bricefire:dwarf_spawn_egg"):
        if egg in rows:
            checks.append((egg, s(egg)))
    ok = True
    lines = [
        f"changes={len(report)} mc={mc_n} total={total} share={len(share)} crafted={len(crafted)}"
    ]
    for label, val in checks:
        passed = val < -1e-9 or (abs(val) < 1e-9 and "egg" in label)
        if "egg" in label and val == 0:
            passed = True
        if not passed:
            ok = False
        lines.append(f"  [{'OK' if passed else 'FAIL'}] {label}: {r2(val)}")
    for name, aux in [("potion", 43), ("arrow", 43), ("ominous_bottle", 4), ("goat_horn", 7), ("lit_pumpkin", 0)]:
        hit = (name, aux) in have_aux
        if not hit:
            ok = False
        lines.append(f"  [{'OK' if hit else 'FAIL'}] has {name}#{aux}")
    txt = BASE / "03_对比报告" / "印钱修复与药水扩充.txt"
    txt.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    if not ok:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
