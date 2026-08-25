# -*- coding: utf-8 -*-
"""审计 implement_08203.py 的配方定价单位 bug。

背景：RECIPES 里的材料价 ING 用的是「堆价」（如 iron=1.2 是 64 锭的价），
但配方把它当「单价」用（铁剑 = 2×1.2+…），导致所有合成物品 ~64× 虚高，
形成「买廉价原料→合成→卖成品」印钞套利。

本脚本只读不改价，输出：
- 03_对比报告/配方单价审计.csv（全量对比）
- 控制台摘要（受影响条数 + 最大偏差样例）

用法（04_工具脚本/ 下）：python audit_recipe_units.py
"""
import ast
import csv
from pathlib import Path

from ppcp_lib import decode_share, namespace_maps, resolve_nin, r2

ROOT = Path(r"C:/Users/AI10/Desktop/ppcdata")
SRC = ROOT / "04_工具脚本" / "implement_08203.py"
SHOP_TXT = ROOT / "06_用户自行导入" / "08206.txt"
OUT_CSV = ROOT / "03_对比报告" / "配方单价审计.csv"

# ING 键 -> 对应 minecraft 物品名（用于查 shop 里的 count）
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


def extract_assignments(src: str):
    """从源码里用 AST 精确定位 ING 与 RECIPES 两个赋值表达式节点。"""
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

    ING = ast.literal_eval(ing_node)  # ING 全是字面量
    rec_expr = ast.Expression(rec_node)
    rec_code = compile(rec_expr, "<recipes>", "eval")

    # shop：name -> (buy, sell, count)
    wrap = decode_share(SHOP_TXT.read_text(encoding="utf-8"))
    data = wrap["data"]
    rev, _ = namespace_maps(data)
    shop = {}
    for r in data["systemShopItems"]:
        nin = r[0].get("NIN", "")
        nm = resolve_nin(nin, rev)
        shop[nm] = (r[1], r[2], r[0].get("count") or 1)

    # 每个 ING 键的正确单价 = 堆价 / count
    ing_count = {}
    missing = []
    for k, item in ING_ITEM.items():
        full = f"minecraft:{item}"
        if full in shop:
            ing_count[k] = shop[full][2]
        else:
            ing_count[k] = 64
            missing.append(full)

    ING_per = {k: v / ing_count[k] for k, v in ING.items()}

    # 用原始 ING（当前 buggy）与 ING_per（正确）分别求材料成本
    REC_buggy = eval(rec_code, {"ING": ING})
    REC_correct = eval(rec_code, {"ING": ING_per})

    rows = []
    for name, (mat_buggy, tax) in REC_buggy.items():
        mat_correct = REC_correct[name][0]
        full = f"minecraft:{name}"
        cur_buy, cur_sell, cur_cnt = shop.get(full, (None, None, None))
        correct_buy = r2(mat_correct * tax)
        correct_sell = r2(mat_correct)
        ratio = (cur_buy / correct_buy) if (cur_buy and correct_buy) else 0.0
        ing_based = mat_buggy != mat_correct  # 是否真的用了 ING（受影响）
        rows.append({
            "item": full, "tax": tax, "count": cur_cnt,
            "cur_buy": cur_buy, "cur_sell": cur_sell,
            "correct_buy": correct_buy, "correct_sell": correct_sell,
            "ratio": round(ratio, 1), "ing_based": ing_based,
        })

    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["item", "tax", "count", "cur_buy", "cur_sell",
                    "correct_buy", "correct_sell", "ratio", "ing_based"])
        for r in rows:
            w.writerow([r["item"], r["tax"], r["count"], r["cur_buy"], r["cur_sell"],
                        r["correct_buy"], r["correct_sell"], r["ratio"], r["ing_based"]])

    affected = [r for r in rows if r["ing_based"]]
    print(f"配方条目总数：{len(rows)}；受 ING 堆价 bug 影响（ing_based）：{len(affected)}")
    print(f"未在 shop 找到的材料（默认按 count=64 估）：{missing or '无'}")
    print(f"\n=== 受影响条目（当前买价 -> 正确买价，按虚高倍数降序）===")
    for r in sorted(affected, key=lambda x: -x["ratio"])[:40]:
        flag = "" if r["cur_buy"] is not None else "  [shop未命中]"
        print(f"  {r['item']:34} {r['cur_buy']:>8} -> {r['correct_buy']:>8}  (~{r['ratio']:>4}x)  税{r['tax']}{flag}")
    print(f"\nCSV 已写入：{OUT_CSV}")


if __name__ == "__main__":
    main()
