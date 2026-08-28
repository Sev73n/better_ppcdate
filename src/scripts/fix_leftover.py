# -*- coding: utf-8 -*-
"""遗留项修复：httravbag 卖价率 0.767 → 0.625（对齐全局卖价归一规则）。

基线：20260828_16 → 输出 20260828_17
说明：httravbag（旅行袋）是功能/合成品，按 v2 回收分级应为 0.625；旧值 207（0.767）
     是重锚前遗留，本轮归一。若该旅行袋可拆解还原为材料，需另行确认（见报告）。
用法：cd 到仓库根，python src/scripts/fix_leftover.py
"""
import json
import sys
import zlib
import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))
from ppcp_lib import namespace_maps, validate_items, zero_items  # noqa: E402

SRC_JSON = ROOT / "data" / "decoded" / "20260828_16.json"
OUT_JSON = ROOT / "data" / "decoded" / "20260828_17.json"
OUT_TXT = ROOT / "releases" / "20260828_17.txt"

SELL_RATE = 0.625


def main():
    wrap = json.loads(SRC_JSON.read_text(encoding="utf-8"))
    data = wrap["data"]
    items = data["systemShopItems"]
    rev, nsid = namespace_maps(data)

    fixed = []
    for row in items:
        p, n = row[0]["NIN"].split(":", 1)
        ns = rev.get(p, "?" + p)
        if ns == "ihzao" and n == "httravbag":
            buy = float(row[1])
            new_sell = round(buy * SELL_RATE, 2)
            if new_sell >= buy:
                new_sell = round(buy - 0.01, 2)
            old_sell = float(row[2])
            row[2] = new_sell
            fixed.append((f"{ns}:{n}", buy, old_sell, new_sell))

    bad = validate_items(items)
    zz = zero_items(items, rev)
    print(f"修复 {len(fixed)} 条：")
    for name, buy, os_, ns_ in fixed:
        print(f"    {name}: buy={buy} sell {os_} -> {ns_} (率 {os_/buy:.3f} -> {ns_/buy:.3f})")
    print(f"套利违规 {len(bad)}；0/0 {len(zz)}；最终 {len(items)} 条")

    OUT_JSON.write_text(json.dumps(wrap, ensure_ascii=False, indent=2), encoding="utf-8")
    text = json.dumps(wrap, ensure_ascii=False, separators=(",", ":"))
    raw = zlib.compress(text.encode("utf-8"), level=9)
    OUT_TXT.write_text("ppcpdata2%" + base64.b64encode(raw).decode("ascii"), encoding="utf-8")
    print(f"已写出 {OUT_TXT.name} 与 {OUT_JSON.name}")


if __name__ == "__main__":
    main()
