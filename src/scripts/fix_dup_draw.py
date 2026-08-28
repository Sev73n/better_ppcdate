# -*- coding: utf-8 -*-
"""审查修复收尾：删森罗重复上架/幽灵条目 + 抽奖堵印钞。

基线：20260828_13 → 输出 20260828_14
修复内容：
1. 删森罗烹饪 7 条 `kaleidoscope_cookery_*` 前缀重复上架行（仅限有无前缀正行的，保留正行）。
2. 删森罗酒馆 12 条 `kaleidoscope_tavern_*` 前缀遗留行（同上）。
3. 删幽灵条目：beer、bar_cabinet_clear（模组注册表不存在）。
   ⚠ 不删 chopping_board/pot/stockpot/stove/teapot/millstone/trash_can/cold_cut_ham_slices——
   它们只有前缀行、无前缀正行，删了物品就彻底消失。
4. 抽奖：新增 minecraft:potion NAV=9 商店行（2.0/1.25，对齐 splash_potion），
   消除武器/工具/防具三池估值黑洞；工具商店票价 135→140。
用法：cd 到仓库根，python src/scripts/fix_dup_draw.py
"""
import json
import sys
import zlib
import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))
from ppcp_lib import namespace_maps, validate_items, zero_items  # noqa: E402

SRC_JSON = ROOT / "data" / "decoded" / "20260828_13.json"
OUT_JSON = ROOT / "data" / "decoded" / "20260828_14.json"
OUT_TXT = ROOT / "releases" / "20260828_14.txt"

GHOST_NAMES = {"beer", "bar_cabinet_clear"}


def main():
    wrap = json.loads(SRC_JSON.read_text(encoding="utf-8"))
    data = wrap["data"]
    items = data["systemShopItems"]
    rev, nsid = namespace_maps(data)
    ck_id, tv_id = nsid["kaleidoscope_cookery"], nsid["kaleidoscope_tavern"]
    mc_id = nsid["minecraft"]

    # 先建无前缀裸名集合（用于判断前缀行是否有正行对应）
    plain_ck, plain_tv = set(), set()
    for row in items:
        p, n = row[0]["NIN"].split(":", 1)
        if p == ck_id and not n.startswith("kaleidoscope_cookery_"):
            plain_ck.add(n)
        if p == tv_id and not n.startswith("kaleidoscope_tavern_"):
            plain_tv.add(n)

    before = len(items)

    def keep_row(row):
        p, n = row[0]["NIN"].split(":", 1)
        # 幽灵条目
        if n in GHOST_NAMES:
            return False
        # 烹饪前缀行：仅当存在同名无前缀正行时才删
        if p == ck_id and n.startswith("kaleidoscope_cookery_"):
            base = n.replace("kaleidoscope_cookery_", "", 1)
            return base not in plain_ck  # 有正行→删前缀行；无正行→保留
        # 酒馆前缀行：同理
        if p == tv_id and n.startswith("kaleidoscope_tavern_"):
            base = n.replace("kaleidoscope_tavern_", "", 1)
            return base not in plain_tv
        return True

    items[:] = [r for r in items if keep_row(r)]
    removed = before - len(items)

    # 新增 minecraft:potion NAV=9（对齐 splash_potion 兜底价 2.0/1.25）
    has = any(r[0]["NIN"] == f"{mc_id}:potion" for r in items)
    if not has:
        items.append([{"NAV": 9, "NIN": f"{mc_id}:potion"}, 2.0, 1.25, "",
                      0, 0, "药水", False, "金币", "金币", 0, 1.0, 64, 0.0, 0.9, 0.1])

    # 工具商店票价 135→140
    ticket = None
    for draw in data.get("luckyDraws", []):
        if draw.get("name") == "工具商店" and abs(draw.get("buyPrice", 0) - 135.0) < 0.01:
            draw["buyPrice"] = 140.0
            ticket = draw["name"]

    # 补卖价封顶：森罗两模组的卖价率不得超 0.625（刷怪蛋=0），只压不抬
    capped = 0
    for row in items:
        p, n = row[0]["NIN"].split(":", 1)
        if p in (ck_id, tv_id):
            if "_spawn_egg" in n:
                if float(row[2]) != 0:
                    row[2] = 0.0; capped += 1
            elif float(row[1]) > 0 and float(row[2]) > 0:
                cap = round(float(row[1]) * 0.625, 2)
                if float(row[2]) > cap + 0.001:
                    row[2] = cap; capped += 1

    bad = validate_items(items)
    zz = zero_items(items, rev)
    print(f"删除 {removed} 条；新增 potion {'是' if not has else '已存在'}；工具商店票价 {'已改140' if ticket else '未匹配'}；森罗卖价封顶 {capped} 条")
    print(f"套利违规 {len(bad)}；0/0 {len(zz)}；最终 {len(items)} 条")

    OUT_JSON.write_text(json.dumps(wrap, ensure_ascii=False, indent=2), encoding="utf-8")
    text = json.dumps(wrap, ensure_ascii=False, separators=(",", ":"))
    raw = zlib.compress(text.encode("utf-8"), level=9)
    OUT_TXT.write_text("ppcpdata2%" + base64.b64encode(raw).decode("ascii"), encoding="utf-8")
    print(f"已写出 {OUT_TXT.name} 与 {OUT_JSON.name}")


if __name__ == "__main__":
    main()
