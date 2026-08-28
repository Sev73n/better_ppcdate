# -*- coding: utf-8 -*-
"""修复抽奖"森罗美食/森罗酒馆"两池悬空奖励。

基线：20260828_15 → 输出 20260828_16
问题：两池奖励引用了已被删除的前缀重复行（kaleidoscope_cookery_xxx / kaleidoscope_tavern_xxx），
     这些物品已不在商店（悬空）。做法：把奖励物品名归一到商店实际存在的形态——
     优先去前缀（kaleidoscope_cookery_X → X）；若去前缀后仍不在商店则保留原名（交给后续人工）。
用法：cd 到仓库根，python src/scripts/fix_draw_rewards.py
"""
import json
import sys
import zlib
import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))
from ppcp_lib import namespace_maps  # noqa: E402

SRC_JSON = ROOT / "data" / "decoded" / "20260828_15.json"
OUT_JSON = ROOT / "data" / "decoded" / "20260828_16.json"
OUT_TXT = ROOT / "releases" / "20260828_16.txt"

POOLS = {"森罗美食", "森罗酒馆"}


def main():
    wrap = json.loads(SRC_JSON.read_text(encoding="utf-8"))
    data = wrap["data"]
    rev, nsid = namespace_maps(data)

    # 商店存在的完整物品名集合
    shop_names = set()
    for row in data["systemShopItems"]:
        p, n = row[0]["NIN"].split(":", 1)
        shop_names.add(f"{rev.get(p, '?' + p)}:{n}")

    def normalize(nin):
        """把可能带冗余前缀的物品名归一到商店实际形态。"""
        if nin not in shop_names:
            ns, name = nin.split(":", 1)
            for pref in ("kaleidoscope_cookery_", "kaleidoscope_tavern_"):
                if name.startswith(pref):
                    cand = f"{ns}:{name[len(pref):]}"
                    if cand in shop_names:
                        return cand
        return nin

    fixed, removed = 0, []
    for draw in data.get("luckyDraws", []):
        if draw.get("name") not in POOLS:
            continue
        new_rewards = []
        for rw in draw.get("rewards", []):
            keep_items = []
            for it in rw.get("items", []):
                old = it.get("newItemName", "")
                new = normalize(old)
                if new != old:
                    it["newItemName"] = new
                    fixed += 1
                if new in shop_names:
                    keep_items.append(it)
                else:
                    removed.append(new)
            if keep_items:
                rw["items"] = keep_items
                new_rewards.append(rw)
            # 若该 reward 的物品全被移除，则丢弃整条 reward
        draw["rewards"] = new_rewards

    print(f"归一奖励 {fixed} 条；移除悬空奖励物品 {len(removed)} 条:")
    for u in sorted(set(removed)):
        print(f"    {u}")

    OUT_JSON.write_text(json.dumps(wrap, ensure_ascii=False, indent=2), encoding="utf-8")
    text = json.dumps(wrap, ensure_ascii=False, separators=(",", ":"))
    raw = zlib.compress(text.encode("utf-8"), level=9)
    OUT_TXT.write_text("ppcpdata2%" + base64.b64encode(raw).decode("ascii"), encoding="utf-8")
    print(f"已写出 {OUT_TXT.name} 与 {OUT_JSON.name}")


if __name__ == "__main__":
    main()
