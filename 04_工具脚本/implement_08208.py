# -*- coding: utf-8 -*-
"""08207 -> 08208：第一步基本面修复（仅 2 项明确成立）。

1. 死亡惩罚重锚：deathLoseMoney 100 -> 3（对齐 ÷30 价格尺度）。
2. 重写 noticeMsg：按真实数据重算各命名空间条数与合计。

说明：原计划中的「统一回收率」「击杀表重锚」「抽奖权重归一化」「合并标签」
经核实不成立或无需改（见落地报告），本脚本不涉及。

用法（04_工具脚本/ 下）：python implement_08208.py
"""
from collections import Counter
from pathlib import Path

from ppcp_lib import load_shop, namespace_maps, resolve_nin, save_shop, zero_items

ROOT = Path(r"C:/Users/AI10/Desktop/ppcdata")
SHOP_JSON = ROOT / "01_配置明文" / "08207_decoded.json"
OUT_JSON = ROOT / "01_配置明文" / "08208_decoded.json"
OUT_TXT = ROOT / "06_用户自行导入" / "08208.txt"
REPORT = ROOT / "03_对比报告" / "08208_落地报告.md"


def main():
    wrap, data = load_shop(SHOP_JSON)
    rev, _ = namespace_maps(data)
    items = data["systemShopItems"]
    eco = data["ecoSystemData"]

    # ---- 1. 死亡重锚
    eco["deathLoseMoney"] = 3.0

    # ---- 2. 重写 noticeMsg
    ns_count = Counter()
    for r in items:
        ns_count[resolve_nin(r[0].get("NIN", ""), rev).split(":", 1)[0]] += 1
    ench = sum(1 for r in items if "附魔书" in (r[6] or ""))
    vanilla = ns_count.get("minecraft", 0)
    farm = ns_count.get("farmer_delight_nullgr", 0) + ns_count.get("farmers_tale_nullgr", 0)

    notice = (
        f"仅金币｜原版{vanilla}(附魔书{ench})｜森罗厨{ns_count.get('kaleidoscope_cookery', 0)}"
        f"+酒{ns_count.get('kaleidoscope_tavern', 0)}+偶{ns_count.get('kaleidoscope_doll', 0)}"
        f"｜冰火{ns_count.get('bricefire', 0)}｜旅行袋{ns_count.get('ihzao', 0)}"
        f"｜车万女仆{ns_count.get('ysm_maid', 0)}｜机械{ns_count.get('create', 0)}"
        f"｜娘化{ns_count.get('breath_maid', 0)}｜农夫{farm}｜透明玻璃{ns_count.get('ws', 0)}"
        f"｜合计{len(items)}｜开局73｜在线+1/分｜基金隐藏｜死亡固定扣3｜附魔书仅满级/次顶级"
    )
    eco["noticeMsg"] = notice

    save_shop(wrap, OUT_JSON, OUT_TXT)

    lines = [
        "# 08208 落地报告（第一步基本面修复）",
        "",
        f"- 基线：08207（{len(items)} 条）→ 输出：**08208.txt**",
        "",
        "## 已应用",
        "- deathLoseMoney：100 → 3.0（对齐 ÷30 价格尺度）",
        f"- noticeMsg 重写为真实数据：{notice}",
        "",
        "## 未应用（经核实不成立，避免误改）",
        "- 统一回收率：配方物品「卖=材料成本」是故意设计（回收退材料、不退制作税，防套利），不该改成 0.625×买价。",
        "- 击杀表重锚：重锚到新配方价会变成 0.003 亚分币；击杀奖励是硬币源（0.18≈6只=1分钟在线），维持不变。",
        "- 抽奖权重归一化：各池权重池内自归一化，无需统一总和。",
        "- 合并标签：森罗菜品(菜)/厨房(厨具)、森罗酒类(酒)/酒馆(器具)是互斥子类，非重叠。",
        "",
        f"- 0/0 条目：{zero_items(items, rev) or '无'}",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"death: 100 -> 3.0")
    print(f"notice: {notice}")


if __name__ == "__main__":
    main()
