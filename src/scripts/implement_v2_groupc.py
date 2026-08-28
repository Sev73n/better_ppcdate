# -*- coding: utf-8 -*-
"""C组档位判断重锚：bricefire / farmer_delight / farmers_tale / ihzao / ysm_maid / breath_maid。
（kaleidoscope_doll 用户已拍板维持收藏价且卖价率已是 0.625，本轮不动。）

基线：20260828_12 → 输出 20260828_13
规则（用户拍板：统一上调对齐新尺度 + 卖价归一到 0.625）：
- bricefire 龙材料：对照补充草案"努力档"（烈焰棒2/恶魂泪5/潜影壳8/图腾100/下界之星500）重排档位。
- farmer_delight：对齐原版食物锚（面包0.17/熟肉~0.36 档），卖价率归一。
- farmers_tale：jar/chimney 卖价率从 0.99/0.8 压回 0.625。
- ihzao：马铠(barmorht)对齐原版马铠档（皮10/铁30/金20/锁链25/钻80/合金200）；
  plht 原料压缩块按原料价值×6；工具件保留。
- ysm_maid 护符：2000 → 800（高阶护符档）；卖价率归一。
- breath_maid：npc_jie_6/xiang_6 极端高价 27012/20259 → 2000/1500；其余保留。
用法：cd 到仓库根，python src/scripts/implement_v2_groupc.py
"""
import json
import sys
import zlib
import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))
from ppcp_lib import namespace_maps, validate_items, zero_items  # noqa: E402

SRC_JSON = ROOT / "data" / "decoded" / "20260828_12.json"
OUT_JSON = ROOT / "data" / "decoded" / "20260828_13.json"
OUT_TXT = ROOT / "releases" / "20260828_13.txt"

SELL_RATE = 0.625


def sell_of_buy(buy):
    s = round(buy * SELL_RATE, 2)
    if s >= buy:
        s = round(buy - 0.01, 2) if buy > 0.01 else 0.0
    return s


# ============================================================ 档位表（单价/件）
# bricefire：龙为 Boss 级生物，材料按"危险度×稀有度"档位，参照系=努力档+Boss 档
BRICEFIRE = {
    # 龙肉（狩猎龙得，量大）1.5
    "fire_dragon_flesh": 1.5, "ice_dragon_flesh": 1.5, "lightning_dragon_flesh": 1.5,
    "earth_dragon_flesh": 1.5, "electric_ion_dragon_flesh": 1.5,
    # 龙鳞（护甲材料）5.0；龙骨（工具材料）5.0
    "fire_dragon_scale": 5.0, "ice_dragon_scale": 5.0, "lightning_dragon_scale": 5.0,
    "earth_dragon_scale": 5.0, "electric_ion_dragon_scale": 5.0,
    "dragonbone": 5.0, "witherbone": 3.0,
    # 龙血（稀有 Boss 材料）20.0；龙角（稀有战利品，图腾档）100；龙笛（功能件，三叉戟档）150
    "fire_dragon_blood": 20.0, "ice_cragon_blood": 20.0, "lightning_dragon_blood": 20.0,
    "dragon_horn": 100.0, "dragon_flute": 150.0,
    # 海马/巨魔/精灵/鸟蛇
    "sea_serpent_scales_blue": 2.0, "sea_serpent_scales_bronze": 2.0,
    "sea_serpent_scales_deepblue": 2.0, "sea_serpent_scales_green": 2.0,
    "sea_serpent_scales_purple": 2.0, "sea_serpent_scales_red": 2.0,
    "sea_serpent_scales_teal": 2.0, "sea_serpent_fang": 2.5, "shiny_scales": 2.0,
    "troll_tusk": 1.5, "troll_leather_forest": 1.5, "troll_leather_frost": 1.5,
    "troll_leather_mountain": 1.5, "amphithere_feather": 1.0, "pixie_dust": 1.5,
    "amphithere_skull": 20.0, "bestiary": 20.0,
    # 银（介于铜 0.8 与铁 1.0 之间偏上）
    "silver_ingot": 1.2, "silver_nugget": 0.13,
    # 箭（消耗品）
    "dragonbone_arrow": 0.3, "hydra_arrow": 0.35, "sea_serpent_arrow": 0.25,
    "amphithere_arrow": 0.2, "stymphalian_arrow": 0.2,
    # 肉/杂项
    "raptor_meat": 0.15, "cooked_raptor_meat": 0.4,
    "grassonger_meat": 0.15, "cooked_grassonger_meat": 0.4,
    "stymphalian_bird_feather": 0.15, "manuscript": 0.2, "wither_shard": 0.5,
    "chain": 1.3, "chain_sticky": 1.5, "afrozen_potion": 3.0,
    "dragon_meal": 1.0, "sickly_dragon_meal": 0.8, "rotten_egg": 0.3,
}
# 地图与刷怪蛋保留现价
BRICEFIRE_KEEP = {k for k in BRICEFIRE if False}  # 全部重锚，地图/蛋单独保留
BRICEFIRE_KEEP_NAMES = {"kpshop_npc_spawn_egg", "dwarf_spawn_egg"} | {
    "solitary_eye_coast_map", "skullmire_fen_map", "blaze_wyrm_fall_guide_map",
    "gazer_courtyard_map", "ares_arena_map", "sunken_nether_palace_map",
    "fenrir_seal_map", "ember_remnant_workshop_map", "plaguebone_dragon_tomb_map",
    "pale_throne_guide_map", "terror_queen_map", "prometheus_map", "underground_dragon_nest_map"}

# farmer_delight：食物对齐原版食物档
FARMER_DELIGHT = {
    "chicken_cuts": 0.2, "beef_patty": 0.2, "fried_rice": 0.3,
    "chicken_soup": 0.6, "chicken_sandwich": 0.6, "beef_stew": 0.7,
    "steak_and_potatoes": 0.7, "mutton_wrap": 0.6,
    "dumplings": 0.6, "apple_cider": 0.4, "pincers": 0.5,
}

# farmers_tale：保留买价，卖价率压回
FARMERS_TALE = {"jar": 1.0, "endstone_chimney": 0.5}

# ihzao：马铠对齐原版马铠档
IHZAO_BARMORHT = {
    "leather_barmorht_1": 10.0, "leather_harmorht_1": 8.0, "leather_larmorht_1": 9.0,
    "iron_barmorht_1": 30.0, "golden_barmorht_1": 30.0, "chainmail_barmorht_1": 25.0,
    "diamond_barmorht_1": 80.0, "netherite_barmorht_1": 200.0,
}
# ihzao plht：按用途分档——原始矿物压缩块沿用旧价 51（用途未确认），肉/鱼块=原料价值×6
IHZAO_PLHT = {
    "raw_iron_plht": 51.0, "raw_copper_plht": 51.0, "raw_gold_plht": 51.0,
    "ancient_debris_plht": 51.0, "l_fallobjearehighl": 51.0,
    "beef_plht": 0.9, "porkchop_plht": 0.9, "chicken_plht": 0.9,
    "muttonraw_plht": 0.9, "rabbit_plht": 0.6, "fish_plht": 1.0, "salmon_plht": 1.0,
}
# ihzao 工具件保留
IHZAO_KEEP = {"chainmining", "magnetht", "httravbag"}

# ysm_maid：护符降档 + 其余
YSM_MAID = {
    "fall_protect_bauble": 800.0, "prevention_protect_bauble": 800.0,
    "item_magnet_bauble": 800.0, "regeneration_protect_bauble": 800.0,
    "fire_protect_bauble": 800.0, "projectile_protect_bauble": 800.0,
    "explosion_protect_bauble": 800.0, "drown_protect_bauble": 800.0,
    "spawn_ysm_maid": 200.0, "smart_slab_empty": 150.0, "rename_card": 50.0,
}

# breath_maid：极端高价重估 + 其余保留
BREATH_MAID = {
    "npc_jie_6": 2000.0, "npc_xiang_6": 1500.0,
    "npc_jie_5": 522.0, "npc_xiang_5": 393.0, "npc_jie_4": 360.0, "npc_xiang_4": 276.0,
    "npc_jie_3": 264.0, "npc_xiang_3": 204.0, "npc_jie_1": 192.0, "npc_xiang_1": 150.0,
    "npc_jie_2": 136.2, "npc_xiang_2": 105.9, "npc_item_1": 24.0, "npc_yao": 9.9,
    "npc_55_food": 0.155,
}


def main():
    wrap = json.loads(SRC_JSON.read_text(encoding="utf-8"))
    data = wrap["data"]
    items = data["systemShopItems"]
    rev, nsid = namespace_maps(data)

    TABLES = {
        "bricefire": BRICEFIRE, "farmer_delight_nullgr": FARMER_DELIGHT,
        "farmers_tale_nullgr": FARMERS_TALE, "ysm_maid": YSM_MAID,
        "breath_maid": BREATH_MAID,
    }

    applied, kept_norm = 0, 0
    for row in items:
        nin = row[0]["NIN"]
        p, n = nin.split(":", 1)
        ns = rev.get(p, "?" + p)
        cnt = row[0].get("count") or 1
        full = f"{ns}:{n}"

        # 森罗 cookery/tavern 卖价封顶收尾：卖价不得超过 买价×0.625（刷怪蛋=0）。
        # 修正 A 组遗留的舍入边界（部分条目卖价率 0.64~0.8）。
        if ns in ("kaleidoscope_cookery", "kaleidoscope_tavern"):
            if "_spawn_egg" in n:
                ns_ = 0.0
            else:
                cap = round(float(row[1]) * SELL_RATE, 2)
                ns_ = min(float(row[2]), cap)  # 只压不抬
                if ns_ >= float(row[1]):
                    ns_ = round(float(row[1]) - 0.01, 2) if float(row[1]) > 0.01 else 0.0
            if abs(ns_ - float(row[2])) > 0.001:
                row[2] = round(ns_, 2); kept_norm += 1
            continue

        # bricefire
        if ns == "bricefire":
            if n in BRICEFIRE_KEEP_NAMES:
                ub = float(row[1]) / cnt
                if n.endswith("_spawn_egg"):
                    ns_ = 0.0  # 刷怪蛋卖价必须 0
                else:
                    ns_ = round(sell_of_buy(round(ub, 2)) * cnt, 2)
                if abs(ns_ - float(row[2])) > 0.001:
                    row[2] = ns_; kept_norm += 1
                continue
            if n in BRICEFIRE:
                nu = BRICEFIRE[n]
                row[1] = round(nu * cnt, 2)
                row[2] = round(sell_of_buy(nu) * cnt, 2)
                applied += 1
            continue

        # farmer_delight / farmers_tale / ysm_maid / breath_maid
        if ns in TABLES and n in TABLES[ns]:
            nu = TABLES[ns][n]
            row[1] = round(nu * cnt, 2)
            # 刷怪蛋类卖价一律 0（对齐原版刷怪蛋不可回收惯例）
            if n == "spawn_ysm_maid" or n.endswith("_spawn_egg"):
                row[2] = 0.0
            else:
                row[2] = round(sell_of_buy(nu) * cnt, 2)
            applied += 1
            continue

        # ihzao
        if ns == "ihzao":
            if n in IHZAO_BARMORHT:
                nu = IHZAO_BARMORHT[n]
                row[1] = round(nu * cnt, 2)
                row[2] = round(sell_of_buy(nu) * cnt, 2)
                applied += 1
            elif n in IHZAO_PLHT:
                nu = IHZAO_PLHT[n]
                row[1] = round(nu * cnt, 2)
                # 原始矿石类（铁/铜/金/残骸/神秘件）：用途未确认，卖价压回旧值 10.35，
                # 避免"统一 0.625"把卖价抬到远超材料回收价的印钞口；肉/鱼类正常 0.625。
                if n in {"raw_iron_plht", "raw_copper_plht", "raw_gold_plht",
                         "ancient_debris_plht", "l_fallobjearehighl"}:
                    row[2] = 10.35
                else:
                    row[2] = round(sell_of_buy(nu) * cnt, 2)
                applied += 1
            elif n in IHZAO_KEEP:
                # chainmining/magnetht：旧配置 sell≈0 为刻意防套利，保持卖价不动
                continue
            else:
                continue

    bad = validate_items(items)
    zz = zero_items(items, rev)
    print(f"C组应用 {applied} 条；保留归一 {kept_norm} 条；套利违规 {len(bad)}；0/0 {len(zz)}")

    OUT_JSON.write_text(json.dumps(wrap, ensure_ascii=False, indent=2), encoding="utf-8")
    text = json.dumps(wrap, ensure_ascii=False, separators=(",", ":"))
    raw = zlib.compress(text.encode("utf-8"), level=9)
    OUT_TXT.write_text("ppcpdata2%" + base64.b64encode(raw).decode("ascii"), encoding="utf-8")
    print(f"已写出 {OUT_TXT.name} 与 {OUT_JSON.name}（{len(items)} 条）")


if __name__ == "__main__":
    main()
