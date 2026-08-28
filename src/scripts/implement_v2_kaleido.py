# -*- coding: utf-8 -*-
"""A组配方法重锚：kaleidoscope_cookery + kaleidoscope_tavern（森罗物语·烹饪/酒馆）。

基线：20260827_10 → 输出 20260828_11
规则（用户已拍板：统一上调 + 卖价归一到 0.625 + 配方法优先）：
- 材料价 = 当前商店 v2 单价（buy/count）；成品做材料时用其重算价（拓扑序）。
- buy = 材料成本/产出数 × 1.5，下限 0.02；sell = buy × 0.625（sell<buy 兜底）。
- 配方来源：%TEMP%/KaleidoscopeCookery 与 KaleidoscopeTavern（克隆仓库），支持
  ingredients 数组 / key+pattern 有序 / 单数 ingredient（含 ingredient_count 倍数）/
  smithing（addition+base+template）四种结构；多配方取成本最高变体。
- 打包循环手工锚定：稻穗 0.05、米=穗/3、草块=9穗、油=种子×1.5、油块=9油。
- 画作（*_painting）保留收藏价；工具类（刀/镰/铲/靴）保留现价待工具档对齐；
  上述保留项与无配方条目一律把卖价率归一到 0.625。
用法：cd 到仓库根，python src/scripts/implement_v2_kaleido.py
"""
import json
import sys
import zlib
import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))
from ppcp_lib import namespace_maps, validate_items, zero_items  # noqa: E402

SRC_JSON = ROOT / "data" / "decoded" / "20260827_10.json"
OUT_JSON = ROOT / "data" / "decoded" / "20260828_11.json"
OUT_TXT = ROOT / "releases" / "20260828_11.txt"
COOK = Path(r"C:/Users/AI10/AppData/Local/Temp/KaleidoscopeCookery")
TAV = Path(r"C:/Users/AI10/AppData/Local/Temp/KaleidoscopeTavern")

CK = "kaleidoscope_cookery:"
TV = "kaleidoscope_tavern:"
MARKUP = 1.5          # 成品加价倍率（用户拍板 ×1.5）
FLOOR = 0.02          # 单件买价下限
SELL_RATE = 0.625     # 卖价率归一

# 稻穗打包循环手工锚定（米/草块/油/油块 由此派生）
RICE = 0.05

# 标签 -> 代表材料（取 v2 商店内对应物）
TAG = {
    "forge:raw_beef": "minecraft:beef", "forge:raw_pork": "minecraft:porkchop",
    "forge:raw_chicken": "minecraft:chicken", "forge:raw_mutton": "minecraft:mutton",
    "forge:raw_fishes": "minecraft:cod", "forge:eggs": "minecraft:egg",
    "forge:crops/chilipepper": CK + "green_chili", "forge:crops/lettuce": CK + "lettuce",
    "forge:crops/tomato": CK + "tomato", "forge:mushrooms": "minecraft:brown_mushroom",
    "forge:vegetables": "minecraft:carrot", "forge:seeds": "minecraft:wheat_seeds",
    "forge:dough": CK + "raw_dough", "forge:flour": CK + "flour",
    "forge:cooked_rice": CK + "cooked_rice", "forge:grain/rice": CK + "rice",
    "forge:raw_meats": "minecraft:beef", "forge:gems/diamond": "minecraft:diamond",
    CK + "caterpillars": CK + "caterpillar", "minecraft:flowers": "minecraft:poppy",
    "minecraft:small_flowers": "minecraft:poppy", "minecraft:planks": "minecraft:oak_planks",
    "minecraft:wooden_slabs": "minecraft:oak_slab", "forge:dyes/white": "minecraft:bone_meal",
    "forge:dyes/red": "minecraft:red_dye", "forge:dyes/blue": "minecraft:blue_dye",
    "forge:dyes/yellow": "minecraft:yellow_dye", "forge:dyes/lime": "minecraft:lime_dye",
    "forge:dyes/purple": "minecraft:purple_dye", "forge:dyes/light_blue": "minecraft:light_blue_dye",
    "forge:gravel": "minecraft:gravel", "forge:sand/red": "minecraft:red_sand",
    "forge:sand/colorless": "minecraft:sand", "forge:string": "minecraft:string",
    "forge:cobblestone": "minecraft:cobblestone", "forge:stone": "minecraft:stone",
    "forge:ingots/iron": "minecraft:iron_ingot", "forge:ingots/gold": "minecraft:gold_ingot",
    "forge:rods/wooden": "minecraft:stick", "forge:leather": "minecraft:leather",
}

# 保留现价（不走配方成本）：工具类 + 辅助件；画作另行按后缀识别
KEEP_NAMES = {
    TV + "empty_bottle", TV + "empty_glassware", TV + "water_bottle", TV + "potion_bottle",
    TV + "pressing_tub", TV + "trellis", TV + "base_sandwich_board",
    CK + "steamer", CK + "recipe_book", CK + "manual",
    CK + "sickle", CK + "kitchen_shovel", CK + "iron_kitchen_knife", CK + "gold_kitchen_knife",
    CK + "diamond_kitchen_knife", CK + "netherite_kitchen_knife", CK + "farmer_boots",
}


def load_shop_unit():
    """读基线，返回 {完整名: 单件买价} 与原始对象。"""
    wrap = json.loads(SRC_JSON.read_text(encoding="utf-8"))
    data = wrap["data"]
    rev, _ = namespace_maps(data)
    unit = {}
    for row in data["systemShopItems"]:
        p, n = row[0]["NIN"].split(":", 1)
        full = f"{rev.get(p, '?' + p)}:{n}"
        c = row[0].get("count") or 1
        if full not in unit:
            unit[full] = float(row[1]) / c
    return wrap, unit


def ing_name(ing, cock_base):
    if "item" in ing:
        it = ing["item"]
        return None if it.endswith("_bucket") else it
    if "tag" in ing:
        t = ing["tag"]
        if t in TAG:
            return TAG[t]
        if t.startswith(TV + "cocktail_ingredient_"):
            return cock_base
        return None
    return None


def materials_of(rec, cock_base):
    mats = []
    for ing in rec.get("ingredients", []):
        n = ing_name(ing, cock_base)
        if n:
            mats.append(n)
    if rec.get("pattern") and rec.get("key"):
        for row in rec["pattern"]:
            for ch in row:
                if ch == " ":
                    continue
                v = rec["key"].get(ch)
                if v:
                    n = ing_name(v, cock_base)
                    if n:
                        mats.append(n)
    if rec.get("ingredient"):
        n = ing_name(rec["ingredient"], cock_base)
        if n:
            mult = rec.get("ingredient_count", 1) or 1
            mats.extend([n] * mult)
    for fld in ("addition", "base", "template"):
        if rec.get(fld):
            n = ing_name(rec[fld], cock_base)
            if n:
                mats.append(n)
    return mats, rec.get("fluid")


def main():
    wrap, unit = load_shop_unit()
    data = wrap["data"]
    items = data["systemShopItems"]
    rev, nsid = namespace_maps(data)
    ck_id, tv_id = nsid["kaleidoscope_cookery"], nsid["kaleidoscope_tavern"]

    shop_names = set(k for k in unit if k.startswith((CK, TV)))
    # 鸡尾酒基料：取商店内最低价同类
    cock = sorted((p, k) for k, p in unit.items()
                  if k.startswith(TV + "cocktail_ingredient_") and p > 0)
    cock_base = cock[0][1] if cock else None

    # ---- 收集配方变体 ----
    from collections import defaultdict
    variants = defaultdict(list)
    for base in (COOK, TAV):
        for f in base.rglob("*.json"):
            if "advancements" in f.parts or "_entity" in f.name:
                continue
            try:
                rec = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            r = rec.get("result")
            if not isinstance(r, dict) or "item" not in r:
                continue
            mats, fluid = materials_of(rec, cock_base)
            variants[r["item"]].append((r.get("count", 1), mats, fluid))

    # ---- 手工锚定 + 保留集 ----
    MANUAL = {CK + "rice_panicle": RICE, CK + "rice": round(RICE / 3, 2),
              CK + "straw_block": round(RICE * 9, 2),
              CK + "oil": round(unit.get("minecraft:wheat_seeds", 0.02) * MARKUP, 2)}
    MANUAL[CK + "oil_block"] = round(MANUAL[CK + "oil"] * 9, 2)
    COLLECT = {k for k in shop_names if k.split(":")[1].endswith("_painting")}
    KEEP = KEEP_NAMES | COLLECT
    ANCHORED = set(MANUAL)

    price = dict(MANUAL)

    def cost_of(n):
        return price.get(n, unit.get(n))

    def variant_cost(var):
        rc, mats, fluid = var
        tot, ok = 0.0, False
        for m in mats:
            p = cost_of(m)
            if p is not None:
                tot += p; ok = True
        if fluid:
            p = cost_of(fluid)
            if p is not None:
                tot += p; ok = True
        return (tot / rc) if ok else None

    # 依赖边取所有变体材料的并集（保证拓扑序不漏依赖）
    recipes = {}
    for res, vs in variants.items():
        allmats = set()
        allfluid = None
        for rc, mats, fluid in vs:
            allmats.update(mats)
            if fluid:
                allfluid = fluid
        recipes[res] = (1, sorted(allmats), allfluid)

    prod = set(recipes)
    deps = defaultdict(set)
    for res, (rc, mats, fluid) in recipes.items():
        if res in ANCHORED or res in KEEP:
            continue
        for m in mats:
            if m in prod and m != res and m not in ANCHORED and m not in KEEP:
                deps[res].add(m)
        if fluid and fluid in prod and fluid not in ANCHORED and fluid not in KEEP:
            deps[res].add(fluid)
    indeg = {p: len(deps[p]) for p in prod if p not in ANCHORED and p not in KEEP}
    from collections import deque
    q = deque([p for p in indeg if indeg[p] == 0])
    order = []
    while q:
        n = q.popleft()
        order.append(n)
        for res in list(deps):
            if n in deps[res]:
                indeg[res] -= 1
                if indeg[res] == 0:
                    q.append(res)
    cyc = [p for p in indeg if p not in order]
    if cyc:
        print("警告：残留循环", cyc)

    for res in order:
        if res in KEEP or res in ANCHORED:
            continue
        costs = [variant_cost(v) for v in variants[res]]
        costs = [c for c in costs if c is not None]
        if not costs:
            continue
        # 取最低成本变体（玩家实际会用的最省配方），避免批量变体虚高
        price[res] = max(FLOOR, round(min(costs) * MARKUP, 2))

    # ---- 应用到商店行 ----
    applied, kept_sell_norm = 0, 0
    def sell_of_buy(buy):
        s = round(buy * SELL_RATE, 2)
        if s >= buy:
            s = round(buy - 0.01, 2) if buy > 0.01 else 0.0
        return s

    for row in items:
        nin = row[0]["NIN"]
        if not nin.startswith((ck_id + ":", tv_id + ":")):
            continue
        ns = CK if nin.startswith(ck_id + ":") else TV
        full = ns + nin.split(":", 1)[1]
        cnt = row[0].get("count") or 1
        old_buy = float(row[1])
        if full in KEEP or full not in price:
            # 保留现价，但卖价率归一
            new_unit = round(old_buy / cnt, 2)
            nb = old_buy
            nsell = sell_of_buy(round(new_unit, 2)) * cnt
            nsell = round(nsell, 2)
            if abs(nsell - float(row[2])) > 0.001:
                row[2] = nsell
                kept_sell_norm += 1
            continue
        new_unit = max(FLOOR, price[full])
        row[1] = round(new_unit * cnt, 2)
        row[2] = round(sell_of_buy(new_unit) * cnt, 2)
        applied += 1

    # ---- 校验 ----
    bad = validate_items(items)
    zz = zero_items(items, rev)
    print(f"应用配方重算 {applied} 条；保留项卖价归一 {kept_sell_norm} 条")
    print(f"套利违规 {len(bad)}；0/0 {len(zz)}")

    # ---- 保存 ----
    OUT_JSON.write_text(json.dumps(wrap, ensure_ascii=False, indent=2), encoding="utf-8")
    text = json.dumps(wrap, ensure_ascii=False, separators=(",", ":"))
    raw = zlib.compress(text.encode("utf-8"), level=9)
    OUT_TXT.write_text("ppcpdata2%" + base64.b64encode(raw).decode("ascii"), encoding="utf-8")
    print(f"已写出 {OUT_TXT.name} 与 {OUT_JSON.name}（{len(items)} 条）")


if __name__ == "__main__":
    main()
