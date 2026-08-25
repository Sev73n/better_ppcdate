# -*- coding: utf-8 -*-
"""08206 -> 08207：修复配方定价单位 bug（堆价当单价，~64× 虚高）。

只改 implement_08203.py 的 RECIPES 表覆盖的 vanilla 合成物品：
- 材料价除以 count 重算 buy = 材料×税、sell = 材料（保留「回收=材料价值」语义）。
- 级联（dispenser 用 bow、blast_furnace/smoker/furnace_minecart 用 furnace）用不动点迭代解决。
- 3 处硬编码堆价（smoker 的 0.07、lectern 的 1.7、bundle 的 6*3.0）手动修正。

用法（04_工具脚本/ 下）：python fix_08206_recipe_units.py
"""
import ast
from pathlib import Path

from ppcp_lib import load_shop, namespace_maps, resolve_nin, save_shop, zero_items

ROOT = Path(r"C:/Users/AI10/Desktop/ppcdata")
SRC = ROOT / "04_工具脚本" / "implement_08203.py"
SHOP_JSON = ROOT / "01_配置明文" / "08206_decoded.json"
OUT_JSON = ROOT / "01_配置明文" / "08207_decoded.json"
OUT_TXT = ROOT / "06_用户自行导入" / "08207.txt"
REPORT = ROOT / "03_对比报告" / "08207_落地报告.md"

ING_ITEM = {
    "iron": "iron_ingot", "gold": "gold_ingot", "diamond": "diamond",
    "cobble": "cobblestone", "plank": "oak_planks", "stick": "stick",
    "string": "string", "leather": "leather", "slime": "slime_ball",
    "redstone": "redstone", "quartz": "quartz", "wheat": "wheat",
    "egg": "egg", "sugar": "sugar", "paper": "paper", "book": "book",
    "chest": "chest", "apple": "apple", "carrot": "carrot", "potato": "potato",
    "beef": "beef", "porkchop": "porkchop", "chicken": "chicken", "mutton": "mutton",
    "rice": "rice", "gunpowder": "gunpowder", "sand": "sand", "obsidian": "obsidian",
    "flint": "flint", "glass": "glass", "kelp": "kelp", "copper": "copper_ingot",
    "zinc": "zinc_ingot", "andesite": "andesite", "cake": "cake", "bone": "bone",
    "gold_nugget": "gold_nugget", "bucket": "bucket", "bow": "bow", "furnace": "furnace",
}


def r2f(x):
    return max(0.01, round(float(x) + 1e-12, 2))


def extract_assignments(src: str):
    tree = ast.parse(src)
    ing_node = rec_node = None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id in ("ING", "RECIPES"):
                    if t.id == "ING":
                        ing_node = node.value
                    else:
                        rec_node = node.value
    if ing_node is None or rec_node is None:
        raise SystemExit("未在源码中找到 ING / RECIPES")
    return ing_node, rec_node


def main():
    src = SRC.read_text(encoding="utf-8")
    ing_node, rec_node = extract_assignments(src)
    ING = ast.literal_eval(ing_node)
    rec_code = compile(ast.Expression(rec_node), "<recipes>", "eval")

    wrap, data = load_shop(SHOP_JSON)
    rev, _ = namespace_maps(data)
    items = data["systemShopItems"]

    shop = {}  # name -> (buy, sell, count)
    for r in items:
        shop[resolve_nin(r[0].get("NIN", ""), rev)] = (r[1], r[2], r[0].get("count") or 1)

    # 每件「单价」= buy / count。raw 商品本就正确；recipe 结果用不动点迭代收敛
    per_buy = {nm: buy / cnt for nm, (buy, _, cnt) in shop.items()}

    for _ in range(20):
        ING_now = {k: per_buy.get(f"minecraft:{ING_ITEM[k]}", ING[k]) for k in ING}
        REC_now = eval(rec_code, {"ING": ING_now})
        changed = False
        for name, (mat, tax) in REC_now.items():
            full = f"minecraft:{name}"
            if full not in shop:
                continue
            new_per = r2f(mat * tax) / shop[full][2]
            if abs(new_per - per_buy.get(full, 0.0)) > 1e-9:
                per_buy[full] = new_per
                changed = True
        if not changed:
            break

    ING_final = {k: per_buy.get(f"minecraft:{ING_ITEM[k]}", ING[k]) for k in ING}
    REC_final = eval(rec_code, {"ING": ING_final})

    # 硬编码堆价的 3 条，手动用正确单价重算
    p = lambda item: per_buy.get(f"minecraft:{item}", 0.0)
    bookshelf = 6 * p("oak_planks") + 3 * p("book")
    manual = {
        "lectern": (r2f((4 * p("oak_planks") + bookshelf) * 1.5), r2f(4 * p("oak_planks") + bookshelf)),
        "smoker": (r2f((p("furnace") + 4 * p("oak_log")) * 1.8), r2f(p("furnace") + 4 * p("oak_log"))),
        "bundle": (r2f((6 * p("rabbit_hide") + 2 * p("string")) * 1.5), r2f(6 * p("rabbit_hide") + 2 * p("string"))),
    }

    changed = []
    for r in items:
        nm = resolve_nin(r[0].get("NIN", ""), rev)
        if not nm.startswith("minecraft:"):
            continue
        name = nm.split(":", 1)[1]
        if name in manual:
            nb, ns = manual[name]
        elif name in REC_final:
            mat, tax = REC_final[name]
            nb, ns = r2f(mat * tax), r2f(mat)
        else:
            continue
        old = (r[1], r[2])
        if (nb, ns) != old:
            r[1], r[2] = nb, ns
            changed.append((nm, old[0], old[1], nb, ns))

    bad = [(nm, r[1], r[2]) for r in items
           if resolve_nin(r[0].get("NIN", ""), rev) in {f"minecraft:{n}" for n in REC_final}
           and r[1] > 0 and r[2] >= r[1] and not (r[1] == r[2] == 0.01)]

    save_shop(wrap, OUT_JSON, OUT_TXT)

    lines = [
        "# 08207 落地报告（修复配方定价单位 bug）",
        "",
        f"- 基线：08206（{len(items)} 条）→ 输出：**08207.txt**",
        f"- 修复条目数：{len(changed)}",
        f"- 修复后 sell>=buy 违规：{bad or '无'}",
        f"- 0/0 条目：{zero_items(items, rev) or '无'}",
        "",
        "## 修复明细（buy / sell → 新 buy / sell）",
        "",
    ]
    for nm, ob, os_, nb, ns in sorted(changed, key=lambda x: x[1], reverse=True):
        lines.append(f"- `{nm}`：{ob}/{os_} → {nb}/{ns}")
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"fixed={len(changed)}  bad={len(bad)}")
    for nm, ob, os_, nb, ns in changed:
        print(f"  {nm}: {ob}/{os_} -> {nb}/{ns}")


if __name__ == "__main__":
    main()
