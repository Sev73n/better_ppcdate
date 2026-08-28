# -*- coding: utf-8 -*-
"""森罗大重锚实施：cookery/tavern 按真实材料成本重算，落实"卖价略>成本(加工税)"。

基线：20260828_14 → 输出 20260828_15
定价模型（用户拍板：卖价略>成本×1.1~1.3 留激励，本实现取 1.2）：
  cost = 固定点迭代的最低变体材料成本（中间件=自制与商店价取低；标签取最低价成员；
         流体按单份计价；酒/汤计入空瓶/碗载体；批量配方摊到单件）
  sell = cost × 1.2（加工税：做菜卖回有 20% 温和利润，激励玩家做菜）
  buy  = sell / 0.625（维持全局卖价率 0.625）
排除：烹饪机器/工具件（pot/stove/millstone/teapot/stockpot/stove/steamer/chopping_board/
     trash_can/sickle/kitchen_shovel/各厨房刀）不按食物定价，保留现价；画作保留收藏价；
     计算成本 <0.005 的近零条目（鸡尾酒等，基料未上架无法核算）保留现价。
对 A 组的修正：完整标签映射、流体计价、空瓶/碗载体、批量配方除以产出、多配方取最低成本、
     中间件固定点迭代——消除 A 组成本低估导致的印钞。
用法：cd 到仓库根，python src/scripts/reanchor_kaleido.py
"""
import json
import sys
import zlib
import base64
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))
from ppcp_lib import namespace_maps, validate_items, zero_items  # noqa: E402

SRC_JSON = ROOT / "data" / "decoded" / "20260828_14.json"
OUT_JSON = ROOT / "data" / "decoded" / "20260828_15.json"
OUT_TXT = ROOT / "releases" / "20260828_15.txt"
COOK = Path(r"C:/Users/AI10/AppData/Local/Temp/KaleidoscopeCookery/src/generated/resources/data/kaleidoscope_cookery/recipes")
TAV = Path(r"C:/Users/AI10/AppData/Local/Temp/KaleidoscopeTavern/src/generated/resources/data/kaleidoscope_tavern/recipes")

PROC_TAX = 1.2          # 加工税：卖价 = 成本 × 1.2
SELL_RATE = 0.625       # 卖价率
COST_FLOOR = 0.005      # 低于此成本视为无法核算（基料未上架），保留现价

# 不按食物重定价的条目（仅烹饪机器/功能方块；工具件要重算以堵印钞）
KEEP_ITEMS = {
    "kaleidoscope_cookery_pot", "kaleidoscope_cookery_stove", "kaleidoscope_cookery_millstone",
    "kaleidoscope_cookery_teapot", "kaleidoscope_cookery_stockpot", "kaleidoscope_cookery_chopping_board",
    "kaleidoscope_cookery_trash_can", "kaleidoscope_cookery_steamer",
}
KEEP_SUFFIX = ("_painting",)  # 画作收藏价


def main():
    wrap = json.loads(SRC_JSON.read_text(encoding="utf-8"))
    data = wrap["data"]
    items = data["systemShopItems"]
    rev, nsid = namespace_maps(data)
    ck_id, tv_id = nsid["kaleidoscope_cookery"], nsid["kaleidoscope_tavern"]
    MC = "minecraft:"

    # 商店最低单价
    shop = {}
    for row in items:
        p, n = row[0]["NIN"].split(":", 1)
        full = f"{rev.get(p, '?' + p)}:{n}"
        cnt = row[0].get("count") or 1
        if full not in shop or row[1] / cnt < shop[full]:
            shop[full] = row[1] / cnt

    def cheapest(prefs):
        best = None
        for k, p in shop.items():
            bare = k.split(":", 1)[1]
            if any(bare == x or bare.startswith(x) for x in prefs) and p > 0:
                if best is None or p < best:
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
        "forge:seeds": ["wheat_seeds", "lettuce_seed", "tomato_seed", "chili_seed"],
        "forge:crops/chilipepper": ["green_chili", "red_chili"], "forge:crops/lettuce": ["lettuce"],
        "forge:crops/tomato": ["tomato"], "forge:grain/rice": ["rice"],
        "forge:cooked_rice": ["cooked_rice"], "forge:dough": ["raw_dough"],
        "forge:flour": ["flour"], "forge:gems/diamond": ["diamond"],
        "forge:ingots/iron": ["iron_ingot"], "forge:ingots/gold": ["gold_ingot"],
        "forge:ingots/copper": ["copper_ingot"], "forge:nuggets/iron": ["iron_nugget"],
        "forge:nuggets/gold": ["gold_nugget"], "forge:string": ["string"],
        "forge:cobblestone": ["cobblestone"], "forge:stone": ["stone"],
        "forge:gravel": ["gravel"], "forge:sand/red": ["red_sand"], "forge:sand/colorless": ["sand"],
        "forge:rods/wooden": ["stick"], "forge:leather": ["leather"], "forge:glass_panes": ["glass_pane"],
        "forge:fences/wooden": ["oak_fence"], "forge:dyes/white": ["bone_meal"],
        "forge:dyes/red": ["red_dye"], "forge:dyes/blue": ["blue_dye"], "forge:dyes/yellow": ["yellow_dye"],
        "forge:dyes/lime": ["lime_dye"], "forge:dyes/purple": ["purple_dye"],
        "forge:dyes/light_blue": ["light_blue_dye"],
        "minecraft:flowers": ["poppy", "dandelion"], "minecraft:small_flowers": ["poppy", "dandelion"],
        "minecraft:planks": ["oak_planks"], "minecraft:wooden_slabs": ["oak_slab"],
        "minecraft:wooden_pressure_plates": ["oak_pressure_plate"], "minecraft:trapdoors": ["oak_trapdoor"],
        "minecraft:signs": ["oak_sign"], "minecraft:fences": ["oak_fence"],
        "kaleidoscope_cookery:caterpillars": ["caterpillar"],
        "kaleidoscope_cookery:straw_bale": ["straw_block"], "kaleidoscope_cookery:straw_hat": ["straw_block"],
    }.items():
        TAG[tag] = cheapest(prefs)
    # 鸡尾酒基料标签 = 按颜色分组的酒类；成本 = 组内成员的最低商店价
    _tag_dir = TAV.parent / "tags" / "items"
    for c in ["red", "blue", "green", "gold", "white", "yellow", "light_purple",
              "aqua", "black", "dark_aqua", "dark_blue", "dark_gray", "dark_green",
              "dark_purple", "dark_red", "gray", "light_gray"]:
        _tf = _tag_dir / f"cocktail_ingredient_{c}.json"
        if not _tf.exists():
            continue
        try:
            _vals = json.loads(_tf.read_text(encoding="utf-8")).get("values", [])
        except Exception:
            continue
        _mc = [shop[m] for m in _vals if m in shop]
        if _mc:
            TAG[f"kaleidoscope_tavern:cocktail_ingredient_{c}"] = min(_mc)

    grape = shop.get("kaleidoscope_tavern:grape", 0.0156)
    FLUID = {
        "minecraft:water": 0.0, "minecraft:lava": 0.0,
        "kaleidoscope_tavern:grape_juice": grape * 2,
        "kaleidoscope_tavern:gold_grape_juice": grape * 2,
        "kaleidoscope_tavern:ice_grape_juice": grape * 2,
        "kaleidoscope_tavern:green_grape_juice": grape * 2,
        "kaleidoscope_tavern:sweet_berries_juice": shop.get(MC + "sweet_berries", 0.05) * 2,
        "kaleidoscope_tavern:glow_berries_juice": shop.get(MC + "glow_berries", 0.1) * 2,
    }
    BOTTLE = shop.get("kaleidoscope_tavern:empty_bottle", 0.0005)
    BOWL = shop.get(MC + "bowl", 0.01)

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

    cost_cache = {res: shop.get(res) for res in variants}

    def variant_cost(matrefs, fluid, rtype, rescount):
        tot = 0.0
        for kind, key in matrefs:
            if kind == "item":
                c = cost_cache.get(key)
                if c is None:
                    c = shop.get(key, 0.0)
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

    for _ in range(30):
        changed = False
        for res, vlist in variants.items():
            make = min(variant_cost(m, f, t, c) for m, f, t, c in vlist)
            sc = shop.get(res)
            # 重锚采用真实制作成本；仅当配方成本为 0（材料无法计价）才回退商店价
            newc = make if make > 0 else sc
            old = cost_cache.get(res)
            if old is None or abs(newc - old) > 1e-9:
                cost_cache[res] = newc
                changed = True
        if not changed:
            break

    # ---------- 应用 ----------
    applied, kept = 0, 0
    for row in items:
        p, n = row[0]["NIN"].split(":", 1)
        if p not in (ck_id, tv_id):
            continue
        ns = "kaleidoscope_cookery" if p == ck_id else "kaleidoscope_tavern"
        full = f"{ns}:{n}"
        cnt = row[0].get("count") or 1
        # 保留项：机器/工具/画作/收藏后缀
        if n in KEEP_ITEMS or any(n.endswith(sfx) for sfx in KEEP_SUFFIX) or n.startswith("kaleidoscope_cookery_"):
            continue
        cost = cost_cache.get(full)
        if cost is None or cost < COST_FLOOR:
            continue  # 无法核算/近零（鸡尾酒等）→ 保留现价
        sell = round(cost * PROC_TAX, 2)
        buy = round(sell / SELL_RATE, 2)
        row[1] = round(buy * cnt, 2)
        row[2] = round(sell * cnt, 2)
        if row[2] >= row[1]:
            row[2] = round(row[1] - 0.01, 2) if row[1] > 0.01 else 0.0
        applied += 1

    bad = validate_items(items)
    zz = zero_items(items, rev)
    print(f"重锚 {applied} 条；套利违规 {len(bad)}；0/0 {len(zz)}；最终 {len(items)} 条")

    OUT_JSON.write_text(json.dumps(wrap, ensure_ascii=False, indent=2), encoding="utf-8")
    text = json.dumps(wrap, ensure_ascii=False, separators=(",", ":"))
    raw = zlib.compress(text.encode("utf-8"), level=9)
    OUT_TXT.write_text("ppcpdata2%" + base64.b64encode(raw).decode("ascii"), encoding="utf-8")
    print(f"已写出 {OUT_TXT.name} 与 {OUT_JSON.name}")


if __name__ == "__main__":
    main()
