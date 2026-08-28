# -*- coding: utf-8 -*-
"""B组材料锚定重锚：create(机械动力) + ws(透明玻璃)。

基线：20260828_11 → 输出 20260828_12
规则（用户拍板：统一上调对齐新尺度 + 卖价归一到 0.625）：
- 材料价取当前商店 v2 单价；成品做材料用其重算价（拓扑序）。
- create 金属锚定：锌锭=铁锭档 1.0；黄铜=(铜0.8+锌1.0)/2=0.9；矿=锭×0.8、粗矿=锭×0.85；
  块=9锭、粒=锭/9；安山合金=安山岩+铁粒。机械按配方成本×1.5，地板=安山合金档（约0.12~0.18）。
- 收藏品/稀有：builders_tea 保留现价（稀有消耗品），卖价率归一。
- ws：透明玻璃=原版玻璃 0.05、染色透明玻璃=原版染色玻璃 0.10（卖价率归一）。
用法：cd 到仓库根，python src/scripts/implement_v2_create_ws.py
"""
import json
import sys
import zlib
import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))
from ppcp_lib import namespace_maps, validate_items, zero_items  # noqa: E402

SRC_JSON = ROOT / "data" / "decoded" / "20260828_11.json"
OUT_JSON = ROOT / "data" / "decoded" / "20260828_12.json"
OUT_TXT = ROOT / "releases" / "20260828_12.txt"

MARKUP = 1.5
FLOOR = 0.02
SELL_RATE = 0.625
CK = "create:"
MC = "minecraft:"


def load_shop_unit():
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


def main():
    wrap, unit = load_shop_unit()
    data = wrap["data"]
    items = data["systemShopItems"]
    rev, nsid = namespace_maps(data)
    cr_id, ws_id = nsid["create"], nsid["ws"]

    # ---- create 基础材料锚定 ----
    zinc_ingot = unit.get(MC + "iron_ingot", 1.0)
    copper_ingot = unit.get(MC + "copper_ingot", 0.8)
    brass_ingot = round((copper_ingot + zinc_ingot) / 2, 2)
    andesite_alloy = round(unit.get(MC + "andesite", 0.01) + unit.get(MC + "iron_nugget", 0.11), 2)
    rose_quartz = round(unit.get(MC + "quartz", 0.15) * 2, 2)
    polished_rq = round(rose_quartz * 1.2, 2)

    price = {}
    price[CK + "zinc_ingot"] = zinc_ingot
    price[CK + "zinc_ore"] = round(zinc_ingot * 0.8, 2)
    price[CK + "raw_zinc"] = round(zinc_ingot * 0.85, 2)
    price[CK + "brass_ingot"] = brass_ingot
    price[CK + "zinc_block"] = round(zinc_ingot * 9, 2)
    price[CK + "brass_block"] = round(brass_ingot * 9, 2)
    price[CK + "zinc_nugget"] = round(zinc_ingot / 9, 2)
    price[CK + "brass_nugget"] = round(brass_ingot / 9, 2)
    price[CK + "andesite_alloy"] = andesite_alloy
    price[CK + "rose_quartz"] = rose_quartz
    price[CK + "polished_rose_quartz"] = polished_rq
    for nm in ("crimsite", "asurine", "veridium", "ochrum"):
        price[CK + nm] = 0.02

    def mat_price(name):
        """材料单价：create 中间件用已算价，原版用商店价。"""
        if CK + name in price:
            return price[CK + name]
        if MC + name in unit:
            return unit[MC + name]
        if CK + name in unit:
            return unit[CK + name]
        return 0.0

    # (输出数, [(材料,数量)])
    RECIPES = {
        "shaft": (8, [("andesite_alloy", 2)]),
        "cogwheel": (8, [("andesite_alloy", 1), ("oak_button", 8)]),
        "large_cogwheel": (2, [("andesite_alloy", 1), ("oak_planks", 4), ("oak_button", 4)]),
        "gearbox": (1, [("cogwheel", 4), ("shaft", 1)]),
        "gearbox_vertical": (1, [("gearbox", 1)]),
        "gearshift": (1, [("cogwheel", 2), ("redstone", 1), ("andesite_alloy", 1)]),
        "andesite_encased_cogwheel": (1, [("cogwheel", 1), ("andesite_alloy", 1)]),
        "andesite_encased_large_cogwheel": (1, [("large_cogwheel", 1), ("andesite_alloy", 1)]),
        "brass_encased_cogwheel": (1, [("cogwheel", 1), ("brass_casing", 1)]),
        "brass_encased_large_cogwheel": (1, [("large_cogwheel", 1), ("brass_casing", 1)]),
        "belt_connector": (1, [("string", 2), ("iron_ingot", 1)]),
        "andesite_casing": (4, [("andesite_alloy", 2), ("oak_log", 1), ("oak_planks", 6)]),
        "brass_casing": (4, [("brass_ingot", 2), ("oak_log", 1), ("oak_planks", 6)]),
        "copper_casing": (4, [("copper_ingot", 2), ("oak_log", 1), ("oak_planks", 6)]),
        "sturdy_sheet": (1, [("iron_ingot", 2)]),
        "electron_tube": (1, [("iron_nugget", 1), ("polished_rose_quartz", 1), ("redstone_torch", 1)]),
        "brass_hand": (1, [("andesite_alloy", 1), ("brass_ingot", 4)]),
        "precision_mechanism": (1, [("brass_casing", 1), ("electron_tube", 2), ("cogwheel", 2)]),
        "super_glue": (1, [("slime_ball", 1), ("iron_nugget", 1)]),
        "fluid_pipe": (8, [("copper_ingot", 4)]),
        "fluid_tank": (2, [("copper_casing", 1), ("copper_ingot", 2)]),
        "fluid_valve": (1, [("fluid_pipe", 1), ("andesite_alloy", 1)]),
        "smart_fluid_pipe": (1, [("fluid_pipe", 1), ("electron_tube", 1)]),
        "hose_pulley": (1, [("copper_casing", 1), ("fluid_pipe", 2)]),
        "portable_fluid_interface": (1, [("copper_casing", 1), ("fluid_pipe", 1), ("andesite_alloy", 2)]),
        "mechanical_piston": (1, [("andesite_casing", 1), ("cogwheel", 2), ("piston", 1)]),
        "sticky_mechanical_piston": (1, [("mechanical_piston", 1), ("slime_ball", 1)]),
        "mechanical_piston_head": (1, [("andesite_alloy", 1), ("oak_planks", 4)]),
        "sticky_mechanical_piston_head": (1, [("mechanical_piston_head", 1), ("slime_ball", 1)]),
        "mechanical_bearing": (1, [("andesite_casing", 1), ("cogwheel", 2), ("iron_ingot", 2)]),
        "mechanical_press": (1, [("andesite_casing", 1), ("iron_ingot", 2), ("piston", 1)]),
        "mechanical_mixer": (1, [("andesite_casing", 1), ("cogwheel", 2), ("iron_ingot", 2)]),
        "mechanical_drill": (1, [("andesite_casing", 1), ("iron_ingot", 2), ("andesite_alloy", 1)]),
        "mechanical_saw": (1, [("andesite_casing", 1), ("iron_ingot", 2), ("andesite_alloy", 1)]),
        "mechanical_harvester": (1, [("andesite_casing", 1), ("iron_ingot", 2)]),
        "mechanical_plough": (1, [("andesite_casing", 1), ("iron_ingot", 2)]),
        "mechanical_pump": (1, [("copper_casing", 1), ("cogwheel", 2), ("iron_ingot", 1)]),
        "mechanical_crafter": (3, [("brass_casing", 1), ("cogwheel", 2), ("crafting_table", 1), ("electron_tube", 1)]),
        "mechanical_arm": (1, [("brass_casing", 1), ("brass_ingot", 3), ("electron_tube", 2), ("cogwheel", 1)]),
        "rotation_speed_controller": (1, [("brass_casing", 1), ("electron_tube", 2), ("comparator", 1)]),
        "speedometer": (1, [("andesite_casing", 1), ("cogwheel", 1), ("compass", 1)]),
        "weighted_ejector": (1, [("andesite_casing", 1), ("cogwheel", 1), ("gold_ingot", 1)]),
        "depot": (1, [("andesite_alloy", 1), ("smooth_stone", 1)]),
        "chute": (4, [("iron_ingot", 2), ("andesite_alloy", 1)]),
        "smart_chute": (1, [("chute", 1), ("electron_tube", 1)]),
        "empty_blaze_burner": (1, [("iron_ingot", 2), ("iron_bars", 4)]),
        "furnace_minecart": (1, [("minecart", 1), ("furnace", 1)]),
    }

    # 机械地板：降至 0.05。原 0.18 是成本×1.5 的 3~4 倍，导致传动轴/齿轮
    # "买合金→合成→卖回"无限套利（买 0.24 合金→8 轴卖 0.88）。0.05 仍≥成本×1.5，堵套利。
    MECH_FLOOR = 0.05

    # 拓扑序
    from collections import defaultdict, deque
    deps = defaultdict(set)
    for res, (cnt, mats) in RECIPES.items():
        for m, _ in mats:
            if m in RECIPES and m != res:
                deps[res].add(m)
    indeg = {r: len(deps[r]) for r in RECIPES}
    q = deque([r for r in RECIPES if indeg[r] == 0])
    order = []
    while q:
        n = q.popleft()
        order.append(n)
        for res in list(deps):
            if n in deps[res]:
                indeg[res] -= 1
                if indeg[res] == 0:
                    q.append(res)
    cyc = [r for r in RECIPES if r not in order]
    if cyc:
        print("警告：残留循环", cyc)

    # 简单机械 vs 复杂机械：复杂机械(用 electron_tube/precision/comparator/brass_casing 作直接材料)不加地板
    SIMPLE = {
        "shaft", "cogwheel", "large_cogwheel", "gearbox", "gearbox_vertical", "gearshift",
        "andesite_encased_cogwheel", "andesite_encased_large_cogwheel", "brass_encased_cogwheel",
        "brass_encased_large_cogwheel", "belt_connector", "super_glue", "fluid_pipe", "fluid_tank",
        "fluid_valve", "hose_pulley", "chute", "depot", "mechanical_piston_head",
        "sticky_mechanical_piston_head", "mechanical_piston", "sticky_mechanical_piston",
        "mechanical_bearing", "mechanical_press", "mechanical_mixer", "mechanical_drill",
        "mechanical_saw", "mechanical_harvester", "mechanical_plough", "mechanical_pump",
        "speedometer", "weighted_ejector", "empty_blaze_burner", "furnace_minecart",
        "portable_fluid_interface", "brass_hand",
    }
    for res in order:
        cnt, mats = RECIPES[res]
        tot = sum(mat_price(m) * k for m, k in mats)
        val = tot / cnt * MARKUP
        if res in SIMPLE:
            val = max(val, MECH_FLOOR)
        price[CK + res] = max(FLOOR, round(val, 2))

    # ---- 应用 ----
    applied = 0
    kept_norm = 0

    def sell_of_buy(buy):
        s = round(buy * SELL_RATE, 2)
        if s >= buy:
            s = round(buy - 0.01, 2) if buy > 0.01 else 0.0
        return s

    for row in items:
        nin = row[0]["NIN"]
        if nin.startswith(cr_id + ":"):
            full = CK + nin.split(":", 1)[1]
            cnt = row[0].get("count") or 1
            if full in price:
                nu = max(FLOOR, price[full])
                row[1] = round(nu * cnt, 2)
                row[2] = round(sell_of_buy(nu) * cnt, 2)
                applied += 1
            else:
                # builders_tea 等稀有品：保留买价，卖价率归一
                ub = float(row[1]) / cnt
                ns = round(sell_of_buy(round(ub, 2)) * cnt, 2)
                if abs(ns - float(row[2])) > 0.001:
                    row[2] = ns
                    kept_norm += 1
        elif nin.startswith(ws_id + ":"):
            name = nin.split(":", 1)[1]
            cnt = row[0].get("count") or 1
            nu = unit.get(MC + "glass", 0.05) if name == "clear_glass" else unit.get(MC + "stained_glass", 0.10)
            row[1] = round(nu * cnt, 2)
            row[2] = round(sell_of_buy(nu) * cnt, 2)
            applied += 1

    bad = validate_items(items)
    zz = zero_items(items, rev)
    print(f"B组应用 {applied} 条；保留归一 {kept_norm} 条；套利违规 {len(bad)}；0/0 {len(zz)}")

    OUT_JSON.write_text(json.dumps(wrap, ensure_ascii=False, indent=2), encoding="utf-8")
    text = json.dumps(wrap, ensure_ascii=False, separators=(",", ":"))
    raw = zlib.compress(text.encode("utf-8"), level=9)
    OUT_TXT.write_text("ppcpdata2%" + base64.b64encode(raw).decode("ascii"), encoding="utf-8")
    print(f"已写出 {OUT_TXT.name} 与 {OUT_JSON.name}（{len(items)} 条）")


if __name__ == "__main__":
    main()
