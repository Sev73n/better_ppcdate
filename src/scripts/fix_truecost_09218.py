# -*- coding: utf-8 -*-
"""刷钱漏洞修复（20260902_18，内部标签 08218）：真实成本模型重锚。

根因：配方法成本口径是"商店买价"，原版中间件（漏斗/灯笼/梯子/金苹果等）商店价
高于自制成本，虚高成本 ×1.2 写进卖价 → 卖价 > 玩家真实成本 → 刷钱。

修复（用户拍板 2026-09-02）：
  1. 画作 14 条：收购价降到真实材料成本（买价 300 保留为收藏价）
  2. 森罗配方法成本改为"玩家最低获取成本"= min(商店买价, 自制成本)，
     原版合成/熔炼表并入固定点迭代；漏洞条目重锚（保 20% 加工税）
  3. 原版可合成物硬约束：卖价 ≤ 真实合成成本（直接压卖价）
  4. 校验不变量：全店 卖价 ≤ 真实成本 × 1.2 + 容差（画作除外）

基线：20260828_17 → 输出 20260902_18
用法：cd 到仓库根，python src/scripts/fix_truecost_09218.py
"""
import json
import sys
import zlib
import base64
from pathlib import Path
from collections import defaultdict

ROOT = Path("C:/Users/AI10/Desktop/ppcdata")
sys.path.insert(0, str(ROOT / "src"))
from ppcp_lib import namespace_maps, validate_items, zero_items  # noqa: E402
from vanilla_recipes import build_vanilla_recipes, true_costs  # noqa: E402

SRC_JSON = ROOT / "data" / "decoded" / (sys.argv[1] if len(sys.argv) > 1 else "20260828_17.json")
OUT_JSON = ROOT / "data" / "decoded" / (sys.argv[2] if len(sys.argv) > 2 else "20260902_18.json")
OUT_TXT = ROOT / "releases" / (OUT_JSON.stem + ".txt")
COOK = Path("C:/Users/AI10/AppData/Local/Temp/KaleidoscopeCookery/src/generated/resources/data/kaleidoscope_cookery/recipes")
TAV = Path("C:/Users/AI10/AppData/Local/Temp/KaleidoscopeTavern/src/generated/resources/data/kaleidoscope_tavern/recipes")
TAV_TAGS = Path("C:/Users/AI10/AppData/Local/Temp/KaleidoscopeTavern/src/generated/resources/data/kaleidoscope_tavern/tags/items")

PROC_TAX = 1.2          # 加工税：卖价 = 成本 × 1.2
SELL_RATE = 0.625       # 卖价率
COST_FLOOR = 0.005      # 低于此成本视为无法核算，保留现价
COAL_PER_SMELT = 0.125  # 1 煤熔炼 8 件

# 与 reanchor_kaleido.py 一致：不按食物重定价的机器件（工具件要重算以堵印钞）
KEEP_ITEMS = {
    "kaleidoscope_cookery_pot", "kaleidoscope_cookery_stove", "kaleidoscope_cookery_millstone",
    "kaleidoscope_cookery_teapot", "kaleidoscope_cookery_stockpot", "kaleidoscope_cookery_chopping_board",
    "kaleidoscope_cookery_trash_can", "kaleidoscope_cookery_steamer",
}
KEEP_SUFFIX = ("_painting",)


def main():
    wrap = json.loads(SRC_JSON.read_text(encoding="utf-8"))
    data = wrap["data"]
    items = data["systemShopItems"]
    rev, nsid = namespace_maps(data)
    ck_id, tv_id = nsid["kaleidoscope_cookery"], nsid["kaleidoscope_tavern"]
    MC = "minecraft:"
    CK, TV = "kaleidoscope_cookery:", "kaleidoscope_tavern:"

    # ---------- 商店单价 ----------
    shop = {}
    for row in items:
        p, n = row[0]["NIN"].split(":", 1)
        full = f"{rev.get(p, '?' + p)}:{n}"
        cnt = row[0].get("count") or 1
        if full not in shop or row[1] / cnt < shop[full]:
            shop[full] = row[1] / cnt

    # ---------- 原版真实成本固定点（含磨石转化与腐肉皮革，共享模块） ----------
    V = build_vanilla_recipes()
    cost = true_costs(shop)

    # ---------- 标签（与 reanchor 同口径，但用真实成本） ----------
    def cheapest(prefs):
        best = None
        for x in prefs:
            key = x if ":" in x else MC + x
            p = cost.get(key)
            if p is not None and p > 0 and (best is None or p < best):
                best = p
        return best

    TAG = {}
    for tag, prefs in {
        "forge:raw_beef": ["beef"], "forge:raw_pork": ["porkchop"],
        "forge:raw_chicken": ["chicken"], "forge:raw_mutton": ["mutton"],
        "forge:raw_fishes": ["cod", "salmon"],
        "forge:raw_meats": ["beef", "porkchop", "chicken", "mutton", "rabbit"],
        "forge:eggs": ["egg"], "forge:mushrooms": ["brown_mushroom", "red_mushroom"],
        "forge:vegetables": ["carrot", "potato"],
        "forge:seeds": ["wheat_seeds", CK + "lettuce_seed", CK + "tomato_seed", CK + "chili_seed"],
        "forge:crops/chilipepper": [CK + "green_chili", CK + "red_chili"],
        "forge:crops/lettuce": [CK + "lettuce"], "forge:crops/tomato": [CK + "tomato"],
        "forge:grain/rice": [CK + "rice"], "forge:cooked_rice": [CK + "cooked_rice"],
        "forge:dough": [CK + "raw_dough"], "forge:flour": [CK + "flour"],
        "forge:gems/diamond": ["diamond"], "forge:ingots/iron": ["iron_ingot"],
        "forge:ingots/gold": ["gold_ingot"], "forge:ingots/copper": ["copper_ingot"],
        "forge:nuggets/iron": ["iron_nugget"], "forge:nuggets/gold": ["gold_nugget"],
        "forge:string": ["string"], "forge:cobblestone": ["cobblestone"],
        "forge:stone": ["stone"], "forge:gravel": ["gravel"],
        "forge:sand/red": ["red_sand"], "forge:sand/colorless": ["sand"],
        "forge:rods/wooden": ["stick"], "forge:leather": ["leather"],
        "forge:glass_panes": ["glass_pane"], "forge:fences/wooden": ["oak_fence"],
        "forge:dyes/white": ["bone_meal"], "forge:dyes/red": ["red_dye"],
        "forge:dyes/blue": ["blue_dye"], "forge:dyes/yellow": ["yellow_dye"],
        "forge:dyes/lime": ["lime_dye"], "forge:dyes/purple": ["purple_dye"],
        "forge:dyes/light_blue": ["light_blue_dye"],
        "minecraft:flowers": ["poppy", "dandelion"],
        "minecraft:small_flowers": ["poppy", "dandelion"],
        "minecraft:planks": ["oak_planks"], "minecraft:wooden_slabs": ["oak_slab"],
        "minecraft:wooden_pressure_plates": ["oak_pressure_plate"],
        "minecraft:trapdoors": ["oak_trapdoor"], "minecraft:signs": ["oak_sign"],
        "minecraft:fences": ["oak_fence"],
        CK + "caterpillars": [CK + "caterpillar"],
        CK + "straw_bale": [CK + "straw_block"], CK + "straw_hat": [CK + "straw_hat"],
    }.items():
        TAG[tag] = cheapest(prefs)
    for f in TAV_TAGS.glob("cocktail_ingredient_*.json"):
        try:
            vals = json.loads(f.read_text(encoding="utf-8")).get("values", [])
        except Exception:
            continue
        mc = [cost.get(v) for v in vals]
        mc = [v for v in mc if v is not None and v > 0]
        if mc:
            TAG[TV + f.stem] = min(mc)

    # ---------- 森罗配方解析（与 reanchor 一致） ----------
    def ing_ref(ing):
        if "item" in ing:
            it = ing["item"]
            return None if it.endswith("_bucket") else ("item", it)
        if "tag" in ing:
            return ("tag", ing["tag"])
        return None

    variants = defaultdict(list)
    for base in (COOK, TAV):
        for f in base.rglob("*.json"):
            try:
                rec = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            r = rec.get("result")
            if not isinstance(r, dict) or "item" not in r:
                continue
            res = r["item"]
            rescount = r.get("count", 1) or 1
            matrefs = []

            def walk_ing(v):
                if isinstance(v, dict):
                    if "item" in v or "tag" in v:
                        ref = ing_ref(v)
                        if ref:
                            matrefs.append(ref)
                        return True
                    for x in v.values():
                        if walk_ing(x):
                            return True
                elif isinstance(v, list):
                    for x in v:
                        walk_ing(x)
                return False

            for ing in rec.get("ingredients", []):
                walk_ing(ing)
            if rec.get("pattern") and rec.get("key"):
                used = defaultdict(int)
                for row in rec["pattern"]:
                    for ch in row:
                        if ch != " ":
                            used[ch] += 1
                for ch, c in used.items():
                    k = rec["key"].get(ch)
                    if k:
                        ref = ing_ref(k)
                        if ref:
                            for _ in range(c):
                                matrefs.append(ref)
            if rec.get("ingredient"):
                walk_ing(rec["ingredient"])
                mult = rec.get("ingredient_count")
                if mult:
                    matrefs = matrefs * mult
            for fld in ("addition", "base", "template"):
                if rec.get(fld):
                    walk_ing(rec[fld])
            fluid = rec.get("fluid")
            rtype = rec.get("type", "").split(":")[-1]
            if not matrefs and not fluid:
                continue
            variants[res].append((matrefs, fluid, rtype, rescount))

    grape = cost.get(TV + "grape") or 0.0156
    FLUID = {
        "minecraft:water": 0.0, "minecraft:lava": 0.0,
        TV + "grape_juice": grape * 2,
        TV + "gold_grape_juice": grape * 2,
        TV + "ice_grape_juice": grape * 2,
        TV + "green_grape_juice": grape * 2,
        TV + "sweet_berries_juice": (cost.get(MC + "sweet_berries") or 0.05) * 2,
        TV + "glow_berries_juice": (cost.get(MC + "glow_berries") or 0.1) * 2,
    }
    BOWL = cost.get(MC + "bowl") or 0.01
    BOTTLE = 0.0005  # 先占位，配方固定点收敛后用 empty_bottle 真实成本回填

    # ---------- 森罗成本固定点（材料用真实成本，min(商店价, 自制)） ----------
    def variant_cost(matrefs, fluid, rtype, rescount):
        tot = 0.0
        for kind, key in matrefs:
            if kind == "item":
                # 材料获取成本 = min(商店价, 自制成本)：cost_cache 已按此收敛
                c = cost_cache.get(key)
                if c is None:
                    c = cost.get(key, 0.0)
                tot += c
            else:
                v = TAG.get(key)
                tot += v if v is not None else 0.0
        if fluid:
            tot += FLUID.get(fluid, 0.0)
        if rtype in ("barrel", "shaker", "pressing_tub", "teapot"):
            tot += BOTTLE
        if rtype in ("pot", "stockpot", "flex_pot", "flex_stockpot", "rice_bowl", "steamer"):
            tot += BOWL
        return tot / rescount

    # 外层迭代：empty_bottle 等载体自身也是配方产物，其真实成本需收敛后
    # 回填到 BOTTLE，再重算依赖它的条目（否则酒/茶成本被商店空瓶价虚抬）。
    # 每轮从商店价/原版真实成本重新初始化 cost_cache，再单调下降到收敛，
    # 保证依赖载体的条目能随 BOTTLE 回填而正确更新。
    cost_cache = {}
    for _outer in range(6):
        cost_cache = {res: (cost[res] if res in cost else shop.get(res))
                      for res in variants}
        for _ in range(60):
            changed = False
            for res, vlist in variants.items():
                make = min(variant_cost(m, f, t, c) for m, f, t, c in vlist)
                if make > 0:
                    old = cost_cache.get(res)
                    # 单调下降：真实获取成本 = min(商店价, 自制成本)
                    if old is None or make < old - 1e-9:
                        cost_cache[res] = make
                        changed = True
            if not changed:
                break
        eb = cost_cache.get(TV + "empty_bottle")
        new_bottle = min(eb, shop.get(TV + "empty_bottle", eb)) if eb else BOTTLE
        if abs(new_bottle - BOTTLE) < 1e-9:
            break
        BOTTLE = new_bottle

    # ---------- 应用 ----------
    n_paint, n_reanchor, n_vanilla = 0, 0, 0
    vanilla_fix_log, paint_log = [], []
    for row in items:
        p, n = row[0]["NIN"].split(":", 1)
        full = f"{rev.get(p, '?' + p)}:{n}"
        cnt = row[0].get("count") or 1

        # 3) 原版可合成物：卖价 ≤ 真实成本
        if p not in (ck_id, tv_id):
            if full in V and row[2] > 0:
                tc = cost.get(full)
                if tc is not None and row[2] / cnt > tc + 1e-9:
                    new_sell = round(tc * cnt, 2)
                    vanilla_fix_log.append((full, round(row[2] / cnt, 4), round(tc, 4)))
                    row[2] = new_sell
                    if row[2] >= row[1]:
                        row[2] = round(row[1] - 0.01, 2) if row[1] > 0.01 else 0.0
                    n_vanilla += 1
            continue

        ns = "kaleidoscope_cookery" if p == ck_id else "kaleidoscope_tavern"
        kfull = f"{ns}:{n}"

        # 1) 画作：收购价 = 真实材料成本
        if n.endswith("_painting"):
            c = cost_cache.get(kfull)
            if c is not None and c > 0:
                new_sell = round(c * cnt, 2)
                if new_sell < float(row[2]):
                    paint_log.append((kfull, round(row[2] / cnt, 3), round(c, 3)))
                    row[2] = new_sell
                    n_paint += 1
            continue

        if n in KEEP_ITEMS or n.startswith("kaleidoscope_cookery_"):
            continue

        # 2) 森罗条目：真实成本重锚（卖价 = 成本×1.2）
        c = cost_cache.get(kfull)
        if c is None or c < COST_FLOOR:
            continue
        sell = round(c * PROC_TAX, 2)
        cur_sell = float(row[2]) / cnt
        # 仅当新卖价低于现卖价时调整（只堵漏洞，不压低本来就健康的价）
        if sell >= cur_sell - 1e-9:
            continue
        buy = round(sell / SELL_RATE, 2)
        row[1] = round(buy * cnt, 2)
        row[2] = round(sell * cnt, 2)
        if row[2] >= row[1]:
            row[2] = round(row[1] - 0.01, 2) if row[1] > 0.01 else 0.0
        n_reanchor += 1

    print(f"画作降价 {n_paint} 条；森罗重锚 {n_reanchor} 条；原版卖价封顶 {n_vanilla} 条")
    print("--- 画作 ---")
    for k, old, new in paint_log:
        print(f"  {k}: 卖 {old} -> {new}")
    print("--- 原版封顶 ---")
    for k, old, new in vanilla_fix_log:
        print(f"  {k}: 卖 {old} -> {new}")

    # ---------- 校验 ----------
    bad = validate_items(items)
    zz = zero_items(items, rev)
    # 不变量：森罗非画作 卖价 ≤ 真实成本×1.2 + 容差
    viol = []
    for row in items:
        p, n = row[0]["NIN"].split(":", 1)
        if p not in (ck_id, tv_id) or n.endswith("_painting"):
            continue
        cnt = row[0].get("count") or 1
        kfull = ("kaleidoscope_cookery:" if p == ck_id else "kaleidoscope_tavern:") + n
        c = cost_cache.get(kfull)
        if c is None or row[2] <= 0:
            continue
        if row[2] / cnt > c * PROC_TAX + 0.011:
            viol.append((kfull, round(c, 4), round(row[2] / cnt, 3)))
    print(f"套利违规 {len(bad)}；0/0 {len(zz)}；不变量违规 {len(viol)}")
    for v in viol[:20]:
        print("  违规:", v)

    OUT_JSON.write_text(json.dumps(wrap, ensure_ascii=False, indent=2), encoding="utf-8")
    text = json.dumps(wrap, ensure_ascii=False, separators=(",", ":"))
    raw = zlib.compress(text.encode("utf-8"), level=9)
    OUT_TXT.write_text("ppcpdata2%" + base64.b64encode(raw).decode("ascii"), encoding="utf-8")
    print(f"已写出 {OUT_TXT.name} 与 {OUT_JSON.name}（{len(items)} 条）")


if __name__ == "__main__":
    main()
