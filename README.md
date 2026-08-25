# PPCP 商店定价工作流

Minecraft 服务器（PPEC）系统商店的定价配置工程。围绕「分享码」做解码 → 定价重锚 → 编码 → 校验的完整工作流，目标是驱动玩家在游戏中持续采集 → 制作 → 卖出换钱 → 便利购买材料，同时满足建筑与机械的购买需求。

## 核心概念

- **分享码**：插件导入/导出的配置串，格式 `ppcpdata%…` 或 `ppcpdata2%…`，编码方式为 `base64(zlib(JSON))`。
- **回收率**：`SELL_RATE = 0.625`，即回收价 sell ≈ 买价 buy × 0.625（防套利时强制 sell < buy）。
- **金币锚**：开局 73 金币、在线 +1/分钟；价格尺度 0.01 地板、两位小数。
- **采集口径**：可连锁资源（石头/原木/作物/矿脉）按稀有度降倍；不连锁（怪物掉落、肉/奶/蛋/蜜、下界合金、稀有掉落）不降。
- **人工价值**：配方物品卖价 = 材料 × (1 + 人工率)，分级 简单 10% / 多步 15% / 料理 20% / 饰品 25%（制作卖出微利，回收退材料不退制作税）。
- **合成税**：买价倍率 简单 1.5× / 多步 1.8× / 料理 3× / 饰品 5×。

详见 [docs/新价格体系提案.md](docs/新价格体系提案.md) 与 [docs/价格锚点.json](docs/价格锚点.json)。

## 目录结构

```
ppcdata/
├── README.md                  本说明
├── CHANGELOG.md               版本变更记录（每版改动要点）
├── .gitignore
├── docs/                       文档与定价规则
│   ├── 新价格体系提案.md        定价规则总览
│   ├── 价格锚点.json            价格锚点配置
│   ├── 原版建筑阶梯定价说明.txt
│   ├── 项目简介.txt
│   └── 用户备注_简介摘录.txt
├── src/                        源代码
│   ├── ppcp_lib.py             共享库（编解码/命名空间/价格工具/校验，可复用核心）
│   ├── kaleido_prices.py       万花筒料理价格表（由 parse_kaleido_recipes.py 生成）
│   ├── encode_ppcp.py          分享码编码工具
│   └── scripts/                各版本实现/修复脚本（历史归档）
│       ├── implement_08202.py … implement_08209.py
│       └── fix_08205_*.py 等历史脚本
├── data/                       配置数据
│   ├── decoded/                各版本解码 JSON 快照（保留最新 3 份）
│   ├── backups/                原始备份（原始分享串/原始解码配置）
│   └── cookery_tree.json        料理配方树（研究资料）
├── releases/                   发布的分享码（最终产物，按 日期_版本号 命名）
│   └── 20260824_08209.txt
└── reports/                    分析报告
    ├── 落地报告/                每版本落地报告（保留最新 3 份）
    └── 审计分析/                一次性审计 CSV/TXT（套利扫描、缺口补齐等）
```

## 用法

### 解码 / 编码分享码

```python
from ppcp_lib import decode_share, encode_share, load_shop, save_shop

# 分享码 → dict
wrap = decode_share(open("releases/20260824_08209.txt").read())

# dict → 分享码（默认前缀 ppcdata2；旧格式用 prefix="ppcpdata"）
share = encode_share(wrap)

# 读写 decoded.json
wrap, data = load_shop("data/decoded/08209.json")
save_shop(wrap, "out.json", "out.txt")  # 内部调用 encode_share 生成 out.txt
```

### 命名空间

各版本的 `nameSpaceMap` ID 会动态重排，**切勿硬编码 0/1/2/3**，必须动态解析：

```python
from ppcp_lib import namespace_maps, resolve_nin
rev, nsid = namespace_maps(data)      # rev[id]=命名空间, nsid[命名空间]=id
name = resolve_nin("4:iron_ingot", rev)  # → "minecraft:iron_ingot"
```

### 校验

```python
from ppcp_lib import validate_items, zero_items
bad = validate_items(items)           # 违规列表（非两位小数 / 卖≥买 / 蛋可回收）
zeros = zero_items(items, rev)        # 0/0 条目（疑似遗漏定价）
```

## 版本约定

- 版本号 `0820X` 对应日期 08-20，迭代第 X 版。
- 分享码命名 `YYYYMMDD_0820X.txt`。
- 每版本改动要点见 [CHANGELOG.md](CHANGELOG.md)，详细落地见 `reports/落地报告/`。
- 历史脚本按「输入基线」命名（如 `implement_08209.py` 读 08202 作为原始价基线），仅作参考，含绝对路径，复用时需调整路径与 `from ppcp_lib import` 的搜索路径。

## 数据保留策略

- `data/decoded/`、`releases/`、`reports/落地报告/` 仅保留**最新 3 份**版本，旧版本定期清理。
- `reports/审计分析/` 保留历次审计决策记录。
- `data/backups/` 保留原始导入数据。
