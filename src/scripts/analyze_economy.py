# -*- coding: utf-8 -*-
"""导出 08207 经济系统全貌（基础经济/税/抽奖/击杀/商店规模），供体检用。"""
import json
from pathlib import Path

from ppcp_lib import decode_share

ROOT = Path(r"C:/Users/AI10/Desktop/ppcdata")
d = decode_share((ROOT / "06_用户自行导入" / "08207.txt").read_text(encoding="utf-8"))["data"]
eco = d["ecoSystemData"]

print("== 基础经济 ==")
for k in ("defCoin", "preMinuteCoin", "deathLoseMoney", "deathLoseMoneyPercent",
          "ecoRanking", "killPlayerReward", "killPlayerRewardPercent",
          "taxRate", "playerEcoTransferTaxRate", "requestTaxRate",
          "exchangeShopEnabled", "projectEEnabled", "stockEnabled",
          "bulletinEnabled", "luckyDrawEnabled"):
    print(f"  {k} = {eco.get(k)}")

print("\n== 公告 ==")
print(" ", eco.get("noticeMsg"))

print("\n== 抽奖池 ==")
for p in d.get("luckyDraws", []):
    rs = p.get("rewards", [])
    wsum = sum(r.get("weight", 0) for r in rs)
    print(f"  {p['name']:12} 票={p.get('buyPrice')}  奖励={len(rs)}个 权重和={wsum}")

print("\n== 击杀表 ==")
kr = d.get("killEntityRewardMap", {})
print(f"  条目数={len(kr)}")
for k, v in list(kr.items())[:12]:
    print(f"    {k}: {v}")

print("\n== 商店规模 ==")
items = d["systemShopItems"]
from collections import Counter
ns = Counter()
tag = Counter()
for r in items:
    nin = r[0].get("NIN", "")
    nsid = nin.split(":", 1)[0] if ":" in nin else "?"
    ns[nsid] += 1
    tag[r[6] or "(空)"] += 1
print("  按命名空间ID:", dict(ns))
print("  按标签:", dict(tag))
print(f"  总条目={len(items)}")
