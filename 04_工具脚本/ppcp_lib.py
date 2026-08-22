# -*- coding: utf-8 -*-
"""PPCP 分享码与商店配置的共享工具库。

把散落在各脚本里的重复逻辑收敛到一处，避免硬编码前缀 / 命名空间 ID：

- decode_share / encode_share：分享码编解码，自动识别 ppcpdata%/ppcpdata2% 前缀。
- load_shop / save_shop：读写 decoded.json 与分享码 txt，兼容新旧两种结构
  （旧格式顶层即 data；新格式为 {"data": {...}, ...} 包裹）。
- namespace_maps / resolve_nin / row_name：nameSpaceMap 的 ID 与命名空间互转。
  各版本的 nameSpaceMap ID 会动态重排，必须动态解析，切勿硬编码 0/1/2/3。
- r2 / sell_of：两位小数、回收价 sell = buy × SELL_RATE。
- make_row：构造一条系统商店行（字段顺序/默认值对齐插件当前格式）。
- validate_items / zero_items：价格合法性校验与 0/0 审计。

约定：脚本放在 04_工具脚本/ 下运行时，`from ppcp_lib import ...` 即可。
"""
from __future__ import annotations

import base64
import json
import zlib
from pathlib import Path

SELL_RATE = 0.625
DEFAULT_PREFIX = "ppcpdata2"


# ---------------------------------------------------------------- 编解码
def decode_share(text: str) -> dict:
    """分享码 -> dict。前缀（ppcpdata%/ppcpdata2%）自动剥离，base64 自动补 padding。"""
    s = text.strip()
    if "%" in s[:24]:
        s = s.split("%", 1)[1]
    pad = (-len(s)) % 4
    raw = base64.b64decode(s + "=" * pad)
    return json.loads(zlib.decompress(raw).decode("utf-8"))


def encode_share(obj: dict, prefix: str = DEFAULT_PREFIX) -> str:
    """dict -> 分享码。紧凑 JSON + zlib(level 9) + base64。"""
    text = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    raw = zlib.compress(text.encode("utf-8"), level=9)
    return f"{prefix}%{base64.b64encode(raw).decode('ascii')}"


# ---------------------------------------------------------------- 配置读写
def load_json(path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_shop(path):
    """读取 decoded.json，返回 (wrap, data)。兼容无 data 包裹的旧格式。"""
    wrap = load_json(path)
    data = wrap.get("data", wrap)
    return wrap, data


def save_shop(wrap: dict, out_json, out_txt, prefix: str = DEFAULT_PREFIX):
    """写回 decoded.json（缩进便于 diff）与分享码 txt（压缩）。"""
    Path(out_json).write_text(json.dumps(wrap, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(out_txt).write_text(encode_share(wrap, prefix), encoding="utf-8")


# ---------------------------------------------------------------- 命名空间
def namespace_maps(data: dict):
    """返回 (rev, nsid)：rev[id]=命名空间，nsid[命名空间]=id。ID 动态，必须从这里取。"""
    nsmap = data["nameSpaceMap"]
    rev = {str(v): k for k, v in nsmap.items()}
    nsid = {k: str(v) for k, v in nsmap.items()}
    return rev, nsid


def resolve_nin(nin: str, rev: dict) -> str:
    """'4:iron_ingot' -> 'minecraft:iron_ingot'；未知 id 用 '?id' 表示。"""
    p, n = nin.split(":", 1) if ":" in nin else ("", nin)
    return f"{rev.get(p, '?' + p)}:{n}"


def row_name(row, rev: dict) -> str:
    """取一条商店行的可读名 'namespace:name'。"""
    return resolve_nin(row[0].get("NIN", ""), rev)


# ---------------------------------------------------------------- 价格工具
def r2(x) -> float:
    """四舍五入到两位小数（+1e-12 抵消浮点尾差）。0.01 地板等策略由调用方决定。"""
    return round(float(x) + 1e-12, 2)


def sell_of(buy, zero: bool = False) -> float:
    """回收价 = buy × SELL_RATE；zero=True 强制 0（刷怪蛋不可回收）。"""
    if zero:
        return 0.0
    s = r2(buy * SELL_RATE)
    if s >= buy and buy > 0:
        s = r2(buy - 0.01) if buy > 0.01 else 0.0
    return s


# ---------------------------------------------------------------- 行构造
def make_row(nin: str, count, buy, tag: str = "", sell_zero: bool = False):
    """构造一条系统商店行，字段顺序/默认值对齐插件当前格式。"""
    buy = r2(buy)
    sell = sell_of(buy, zero=sell_zero)
    f12, f13, f14, f15 = 1, 0.2, 0.9, 0.1
    if count and count >= 16:
        f12 = min(count, 64)
        f13 = 0.0
    return [
        {
            "NIN": nin,
            "count": count if count is not None else 1,
            "durability": 0,
            "modEnchantData": [],
        },
        buy, sell, "", 0, 0, tag, False, "金币", "金币", 0, 1.0,
        f12, f13, f14, f15,
    ]


# ---------------------------------------------------------------- 校验
def validate_items(items):
    """返回违规列表 [(NIN, reason, buy, sell), ...]。

    规则：两位小数；刷怪蛋 sell 必须为 0；其余必须 buy > sell >= 0。
    """
    bad = []
    for r in items:
        nin = r[0].get("NIN", "")
        b, s = r[1], r[2]
        if round(b, 2) != b or round(s, 2) != s:
            bad.append((nin, "not-2dp", b, s))
        if "_spawn_egg" in nin:
            if s != 0:
                bad.append((nin, "egg-sell", b, s))
        elif not (b > s >= 0):
            bad.append((nin, "buy<=sell", b, s))
    return bad


def zero_items(items, rev: dict):
    """0/0 条目（买价卖价均为 0），用于审计是否遗漏定价。返回可读名列表。"""
    return [resolve_nin(r[0].get("NIN", ""), rev) for r in items if r[1] == 0.0 and r[2] == 0.0]
