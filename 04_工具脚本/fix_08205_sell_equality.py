# -*- coding: utf-8 -*-
"""08205 -> 08206：修复回收价 buy == sell 的条目。

08205 存在 132 条 buy == sell：
- 115 条是 0.01 地板项（0.625×0.01=0.00625 四舍五入回 0.01，属正常，不动）；
- 17 条是回收价遗漏 ×0.625 的真问题，统一重算 sell = buy × SELL_RATE。

用法（在 04_工具脚本/ 下运行）：python fix_08205_sell_equality.py
"""
from pathlib import Path

from ppcp_lib import (
    load_shop,
    namespace_maps,
    resolve_nin,
    save_shop,
    sell_of,
    zero_items,
)

ROOT = Path(r"C:/Users/AI10/Desktop/ppcdata")
SRC = ROOT / "01_配置明文" / "08205_decoded.json"
OUT_JSON = ROOT / "01_配置明文" / "08206_decoded.json"
OUT_TXT = ROOT / "06_用户自行导入" / "08206.txt"
REPORT = ROOT / "03_对比报告" / "08206_落地报告.md"


def main():
    wrap, data = load_shop(SRC)
    rev, _ = namespace_maps(data)
    items = data["systemShopItems"]

    fixed = []
    for r in items:
        buy, sell = r[1], r[2]
        # 仅修非地板项（buy > 0.01），0.01 地板项 sell 本就应等于 buy，不动
        if buy == sell and buy > 0.01:
            new_sell = sell_of(buy)
            if new_sell != sell:
                fixed.append((resolve_nin(r[0].get("NIN", ""), rev), buy, sell, new_sell))
                r[2] = new_sell

    save_shop(wrap, OUT_JSON, OUT_TXT)

    remaining_nonfloor = [r for r in items if r[1] == r[2] and r[1] > 0.01]
    floor = [r for r in items if r[1] == r[2] == 0.01]

    lines = [
        "# 08206 落地报告（修复回收价 buy==sell）",
        "",
        f"- 基线：08205（{len(items)} 条）→ 输出：**08206.txt**",
        f"- 修复条目数：{len(fixed)}",
        "",
        "## 修复明细（buy / 旧sell → 新sell）",
        "",
    ]
    for name, b, old_s, new_s in fixed:
        lines.append(f"- `{name}`：{b} / {old_s} → {new_s}")
    lines += [
        "",
        "## 校验",
        "",
        f"- 剩余 0.01 地板项（正常）：{len(floor)} 条",
        f"- 剩余非地板 buy==sell（应为 0）：{len(remaining_nonfloor)} 条",
        f"- 0/0 条目：{zero_items(items, rev) or '无'}",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"fixed={len(fixed)}  floor_left={len(floor)}  nonfloor_left={len(remaining_nonfloor)}")
    for name, b, old_s, new_s in fixed:
        print(f"  {name}: {b}/{old_s} -> {b}/{new_s}")


if __name__ == "__main__":
    main()
