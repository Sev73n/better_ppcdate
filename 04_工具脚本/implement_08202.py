# -*- coding: utf-8 -*-
"""08201 -> 08202:
1) Add 23 Create items (logistics + core materials; no trains, no extra machines).
2) Two new pools: 齿轮杂货铺 (generic engineering parts, ticket 60),
   钓鱼佬的日常 (fishing loot, ticket 80).
3) Cooking audit (3x material floor): raise the new teas/farmer foods below 3x
   materials; existing 森罗 dishes/wines already >=3x -> untouched.
4) Preserve user's icons, bulletins, auto-open, all pools otherwise.
"""
import base64, json, math, uuid, zlib
from collections import Counter
from pathlib import Path

ROOT = Path(r"C:/Users/AI10/Desktop/ppcdata")
SRC = ROOT / "01_配置明文" / "08201_decoded.json"
OUT_JSON = ROOT / "01_配置明文" / "08202_decoded.json"
OUT_TXT = ROOT / "06_用户自行导入" / "08202.txt"
REPORT = ROOT / "03_对比报告" / "08202_落地报告.md"

wrap = json.loads(SRC.read_text(encoding="utf-8"))
data = wrap["data"]
rev = {str(v): k for k, v in data["nameSpaceMap"].items()}
nsid = {k: str(v) for k, v in data["nameSpaceMap"].items()}
log = []


def res(r):
    nin = r[0].get("NIN", "")
    p, n = nin.split(":", 1) if ":" in nin else ("", nin)
    return f"{rev.get(p, '?' + p)}:{n}"


def price(ns, name, buy, sell, tag=None, count=None):
    hits = [r for r in data["systemShopItems"] if res(r) == f"{ns}:{name}"]
    if not hits:
        log.append(("MISS", f"{ns}:{name}", f"{buy}/{sell}"))
        return None
    for r in hits:
        r[1], r[2] = buy, sell
        if tag is not None:
            r[6] = tag
        if count is not None:
            r[0]["count"] = count
    return hits[0]


def template(nin, extra=None):
    item = {"NIN": nin}
    if extra:
        item.update(extra)
    return [item, 0.0, 0.0, "", 0, 0, "", False, "金币", "金币", 0, 1.0, 64, 0.0, 0.9, 0.1]


def add_item(ns, name, buy, sell, tag, count=None):
    r = template(f"{nsid[ns]}:{name}", {"count": count} if count else None)
    r[1], r[2], r[6] = float(buy), float(sell), tag
    data["systemShopItems"].append(r)
    log.append(("ADD", f"{ns}:{name}", f"{buy}/{sell} tag={tag}"))


# ================================================================ 1. create items
LOGISTICS = [
    ("shaft", 10, 6.25, None),
    ("belt_connector", 15, 9.4, None),
    ("chute", 25, 15.6, None),
    ("smart_chute", 50, 31.25, None),
    ("depot", 40, 25, None),
    ("weighted_ejector", 45, 28.13, None),
    ("fluid_pipe", 20, 12.5, None),
    ("smart_fluid_pipe", 60, 37.5, None),
    ("fluid_valve", 30, 18.75, None),
    ("fluid_tank", 80, 50, None),
    ("hose_pulley", 70, 43.75, None),
    ("portable_fluid_interface", 90, 56.25, None),
]
MATERIALS = [
    ("rose_quartz", 15, 9.38, 64),
    ("polished_rose_quartz", 20, 12.5, 64),
    ("electron_tube", 60, 37.5, 64),
    ("brass_hand", 30, 18.75, 64),
    ("precision_mechanism", 120, 75, 64),
    ("andesite_casing", 25, 15.63, 64),
    ("copper_casing", 40, 25, 64),
    ("brass_casing", 70, 43.75, 64),
    ("sturdy_sheet", 50, 31.25, 64),
    ("super_glue", 30, 18.75, 64),
    ("zinc_nugget", 3, 1.88, 64),
    ("brass_nugget", 5, 3.13, 64),
]
for name, b, s, cnt in LOGISTICS:
    add_item("create", name, b, s, "机械动力", cnt)
for name, b, s, cnt in MATERIALS:
    add_item("create", name, b, s, "机械动力", cnt)
log.append(("CREATE", "logistics+materials", f"{len(LOGISTICS)}+{len(MATERIALS)} items"))
# ================================================================ 2. cooking audit (3x material floor)
AUDIT = [
    # (ns, name, new_buy, new_sell, reason)
    ("kaleidoscope_cookery", "butter_tea", 35, 10, "材料10(茶包8+奶) x3 +5复杂"),
    ("kaleidoscope_cookery", "mystery_tea", 30, 10, "材料10 x3"),
    ("kaleidoscope_cookery", "tea_egg", 20, 6, "材料6(蛋+茶) x3"),
    ("farmer_delight_nullgr", "beef_stew", 30, 10, "材料10(牛肉4+土豆3+胡萝卜3) x3"),
    ("farmer_delight_nullgr", "beef_patty", 15, 5, "材料5(牛肉4+面粉1) x3"),
    ("farmer_delight_nullgr", "chicken_cuts", 12, 3.5, "材料3.5(鸡肉) x3"),
    ("farmer_delight_nullgr", "chicken_soup", 20, 6.5, "材料6.5(鸡3.5+胡萝卜3) x3"),
    ("farmer_delight_nullgr", "fried_rice", 27, 9, "材料9(米4+蛋2+菜3) x3"),
]
for ns, name, b, s, why in AUDIT:
    price(ns, name, b, s)
    log.append(("AUDIT", f"{ns}:{name}", f"{b}/{s} <- {why}"))

# ================================================================ 3. pools
def it(name, count=1, aux=0, userdata=None):
    d = {"count": count, "newAuxValue": aux, "newItemName": name}
    if userdata is not None:
        d["userData"] = userdata
    return d


def reward(weight, quality, *items):
    return {"items": list(items), "quality": quality, "weight": weight}


def pool(name, price, rewards, icon):
    return {
        "buyPrice": float(price), "coinType": "金币",
        "freeDrawCount": 1, "freeDrawType": 4,
        "iconTexture": icon, "id": uuid.uuid4().hex,
        "limitCount": 10, "limitType": 1,
        "name": name, "requestItem": None, "rewards": rewards,
    }


def book(eid, lvl):
    return it("minecraft:enchanted_book", 1, 0,
              {"ench": [{"id": {"__type__": 2, "__value__": eid},
                         "lvl": {"__type__": 2, "__value__": lvl}}]})


def build_gears():
    """齿轮杂货铺: generic engineering parts, weighted by value."""
    entries = [
        ("legendary", [("create:precision_mechanism", 1, 2), ("create:smart_fluid_pipe", 2, 2),
                       ("create:brass_casing", 2, 2)]),
        ("rare", [("create:electron_tube", 2, 3), ("create:brass_hand", 2, 3),
                  ("create:copper_casing", 2, 4), ("create:fluid_tank", 1, 3),
                  ("create:hose_pulley", 1, 3), ("create:gearbox", 1, 4),
                  ("create:smart_chute", 1, 3)]),
        ("common", [("create:shaft", 8, 8), ("create:belt_connector", 8, 8),
                    ("create:fluid_pipe", 8, 8), ("create:cogwheel", 4, 8),
                    ("create:andesite_alloy", 8, 8), ("create:super_glue", 2, 6),
                    ("create:chute", 2, 6), ("create:depot", 1, 5),
                    ("create:andesite_casing", 2, 6), ("create:fluid_valve", 1, 5),
                    ("create:weighted_ejector", 1, 5), ("create:zinc_ingot", 4, 6),
                    ("create:brass_ingot", 4, 6)]),
    ]
    rewards = []
    for q, es in entries:
        for nm, cnt, w in es:
            rewards.append(reward(w, q, it(nm, cnt)))
    return pool("齿轮杂货铺", 60, rewards, "textures/ui/ppeco_lucky_draw_box_variants_v2/ppeco_icon_luckeydraw_anim")


def build_fishing():
    """钓鱼佬的日常: fishing loot."""
    rod = it("minecraft:fishing_rod", 1, 0,
             {"ench": [{"id": {"__type__": 2, "__value__": 24},
                        "lvl": {"__type__": 2, "__value__": 3}}]})  # 饵钓III
    rewards = [
        reward(1, "legendary", it("minecraft:heart_of_the_sea", 1)),
        reward(3, "legendary", rod),
        reward(3, "rare", book(23, 3)),   # 海之眷顾III
        reward(3, "rare", book(24, 3)),   # 饵钓III
        reward(6, "rare", it("minecraft:nautilus_shell", 4)),
        reward(20, "common", it("minecraft:cod", 12)),
        reward(20, "common", it("minecraft:salmon", 12)),
        reward(12, "common", it("minecraft:tropical_fish", 6)),
        reward(6, "common", it("minecraft:pufferfish", 4)),
        reward(10, "common", it("minecraft:kelp", 16)),
        reward(8, "common", it("minecraft:fishing_rod", 1)),
        reward(8, "common", it("minecraft:ink_sac", 8)),
    ]
    return pool("钓鱼佬的日常", 80, rewards, "textures/ui/ppeco_lucky_draw_box_variants_v2/ppeco_icon_luckeydraw_anim")


old = [p for p in data["luckyDraws"]]
new_pools = old + [build_gears(), build_fishing()]
data["luckyDraws"] = new_pools
log.append(("DRAW", "new pools", "齿轮杂货铺 60 / 钓鱼佬的日常 80"))

# ================================================================ 4. save + report
OUT_JSON.write_text(json.dumps(wrap, ensure_ascii=False, indent=2), encoding="utf-8")
text = json.dumps(wrap, ensure_ascii=False, separators=(",", ":"))
raw = zlib.compress(text.encode("utf-8"), level=9)
OUT_TXT.write_text("ppcpdata2%" + base64.b64encode(raw).decode("ascii"), encoding="utf-8")

zero = [res(r) for r in data["systemShopItems"] if r[1] == 0.0 and r[2] == 0.0]
lines = ["# 08202 落地报告", "",
         f"- 基线：08201（{len(data['systemShopItems'])} 条前）→ 输出：**08202.txt**（{len(data['systemShopItems'])} 条）",
         f"- 新增机械动力 {len(LOGISTICS) + len(MATERIALS)} 条（物流 {len(LOGISTICS)} + 核心材料 {len(MATERIALS)}）",
         f"- 剩余 0/0 条目：{zero or '无'}",
         "", "## 抽奖池（13 个）", ""]
for p in data["luckyDraws"]:
    lines.append(f"- {p['name']}（票 {p['buyPrice']}）：{len(p['rewards'])} 个奖励，权重和 {sum(r['weight'] for r in p['rewards'])}")
lines += ["", "## 料理审计（3× 材料保底，卖价=材料）", ""]
for act, name, detail in log:
    if act == "AUDIT":
        lines.append(f"- `{name}`：{detail}")
lines += ["", "## 变更日志", ""]
for act, name, detail in log:
    lines.append(f"- **{act}** `{name}`：{detail}")
lines += ["", "## 说明与待确认", "",
          "1. 老森罗菜/酒水（L1 3×、L2 4×、L3 5× 起步）全部 ≥3× 材料保底，未下调——只拉高了新加的茶和农夫菜里低于 3× 的条目。",
          "2. 齿轮杂货铺：通用工程件（轴/传送带/管道/机壳/合金/胶水等 23 种），不含精密机器；权重按价值反比。",
          "3. 钓鱼佬的日常：海洋之心+附魔钓鱼竿(饵钓III)头奖、海之眷顾/饵钓III书、鹦鹉螺壳、鱼和钓竿保底。",
          "4. 新 Create 物品 ID 请在游戏里核对（创造模式搜索），不对发我改。",
          ""]
REPORT.write_text("\n".join(lines), encoding="utf-8")
print(f"OK items={len(data['systemShopItems'])} zero={len(zero)}")
for p in new_pools:
    print(f"  {p['name']:10} {p['buyPrice']:>5} rew={len(p['rewards'])} wsum={sum(r['weight'] for r in p['rewards'])}")
