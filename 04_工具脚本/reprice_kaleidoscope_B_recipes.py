# -*- coding: utf-8 -*-
"""Kaleidoscope B-pricing: recipe material costs (no stacked labor) × C labor on finals."""
from __future__ import annotations

import base64
import csv
import json
import zlib
from collections import Counter
from pathlib import Path

BASE = Path(r"C:/Users/AI10/Desktop/ppcdata")
CFG = BASE / "01_配置明文" / "最终配置_rebuilt.json"
REC_COOK = Path(r"C:/Users/AI10/AppData/Local/Temp/ppcp_decode/kaleido_recipes/cookery_recipes")
REC_TAV = Path(r"C:/Users/AI10/AppData/Local/Temp/ppcp_decode/kaleido_recipes/tavern_recipes")
TAGS = Path(r"C:/Users/AI10/AppData/Local/Temp/ppcp_decode/kaleido_recipes/tags")
SELL = 0.625

L1, L2, L3 = 3.0, 4.0, 5.0
FLAT = {"L0": 0.15, "L1": 1.2, "L2": 2.0, "L3": 3.5}
BOWL_SHARE = 0.35  # serving vessel share so it doesn't dominate crops
BOTTLE_MB = 250

TYPE_LABOR = {
    "kaleidoscope_cookery:pot": ("L1", L1),
    "kaleidoscope_cookery:flex_pot": ("L1", L1),
    "kaleidoscope_cookery:stockpot": ("L2", L2),
    "kaleidoscope_cookery:flex_stockpot": ("L2", L2),
    "kaleidoscope_cookery:teapot": ("L1", L1),
    "kaleidoscope_cookery:rice_bowl": ("L2", L2),
    "kaleidoscope_cookery:steamer": ("L2", L2),
    "kaleidoscope_cookery:millstone": ("L0", 1.5),
    "kaleidoscope_cookery:chopping_board": ("L1", 2.5),
    "kaleidoscope_tavern:barrel": ("L2", L2),
    "kaleidoscope_tavern:shaker": ("L2", L2),
    "kaleidoscope_tavern:pressing_tub": ("L1", L1),
    "minecraft:crafting_shaped": ("EQ", 1.8),
    "minecraft:crafting_shapeless": ("EQ", 1.8),
}

L3_KEYS = (
    "blaze_",
    "golden_salad",
    "buddha",
    "nether_style",
    "end_style",
    "pan_seared_knight",
    "stargazy",
    "sweet_and_sour_ender",
    "chorus_fried",
    "fondant_spider",
    "molotov",
    "nether_special",
    "sculk_special",
    "dragon_breath_bottle",
    "miners_star",
)

KEEP_EXACT = {
    "manual",
    "recipe_book",
    "recipe_item",
    "tomato",
    "lettuce",
    "red_chili",
    "green_chili",
    "rice",
    "rice_panicle",
    "wild_rice",
    "oil",
    "caterpillar",
    "sashimi",
    "empty_cup",
    "empty_bottle",
    "empty_glassware",
    "vinegar",
    "trellis",
    "pressing_tub",
    "grapevine",
    "green_grape",
    "gold_grape",
    "ice_grape",
    "wild_grape",
    "flour",  # keep cheap unless millstone resolves nicer
    "raw_dough",  # made via millstone UI, no JSON recipe
    "stuffed_dough_food",
}
KEEP_CONTAINS = (
    "stove",
    "pot",
    "stockpot",
    "chopping",
    "millstone",
    "steamer",
    "shawarma",
    "teapot",
    "trash",
    "enamel",
    "kitchenware",
    "fruit_basket",
    "scarecrow",
    "oil_pot",
    "oil_block",
    "straw",
    "chili_ristra",
    "strung",
    "transmutation",
    "cook_stool",
    "chair_",
    "table_",
    "kitchen_knife",
    "kitchen_shovel",
    "sickle",
    "farmer_",
    "straw_hat",
    "sofa",
    "stool",
    "cabinet",
    "counter",
    "lamp",
    "rack",
    "holder",
    "chalkboard",
    "sandwich_board",
    "stepladder",
    "string_lights",
    "incense",
    "painting",
    "tap",
    "shaker",
    "glassware",
    "bar_",
    "pendant",
    "barrel",
)

RECIPE_RAWS = {
    "raw_noodles",
    "raw_dough",
    "stuffed_dough_food",
    "raw_zongzi",
    "raw_bamboo_tube_rice",
    "raw_meatball",
    "raw_cut_small_meats",
    "raw_pork_belly",
    "raw_cow_offal",
}

TAG_FALLBACK = {
    "forge:eggs": "minecraft:egg",
    "forge:raw_beef": "minecraft:beef",
    "forge:raw_pork": "minecraft:porkchop",
    "forge:raw_chicken": "minecraft:chicken",
    "forge:raw_mutton": "minecraft:mutton",
    "forge:raw_fishes": "minecraft:cod",
    "forge:raw_fishes/cod": "minecraft:cod",
    "forge:raw_fishes/salmon": "minecraft:salmon",
    "forge:cooked_rice": "kaleidoscope_cookery:cooked_rice",
    "forge:crops/chilipepper": "kaleidoscope_cookery:red_chili",
    "forge:crops/tomato": "kaleidoscope_cookery:tomato",
    "forge:crops/lettuce": "kaleidoscope_cookery:lettuce",
    "forge:crops/rice": "kaleidoscope_cookery:rice",
    "forge:grain/rice": "kaleidoscope_cookery:rice",
    "forge:fruits/grapes": "kaleidoscope_tavern:green_grape",
    "minecraft:small_flowers": "minecraft:poppy",
    "forge:dough": "kaleidoscope_cookery:raw_dough",
    "forge:doughs": "kaleidoscope_cookery:raw_dough",
    "forge:flour": "kaleidoscope_cookery:flour",
}


def r2(x):
    return round(float(x) + 1e-12, 2)


def sell_of(buy):
    s = r2(buy * SELL)
    if s >= buy and buy > 0:
        s = r2(buy - 0.01) if buy > 0.01 else 0.0
    return s


def short_id(item: str) -> str:
    return item.split(":", 1)[-1]


def should_keep(name: str) -> bool:
    if name in KEEP_EXACT:
        return True
    if name.endswith("_seed") or name.endswith("_seeds"):
        return True
    if name.startswith("raw_") and name not in RECIPE_RAWS:
        return True
    return any(x in name for x in KEEP_CONTAINS)


def load_tags():
    """Load item tags. Paths look like tags/<ns>/tags/items/<name>.json — use the
    *inner* tags/items segment (not the outer kaleido_recipes/tags root)."""
    tags = {}
    for p in TAGS.rglob("*.json"):
        parts = list(p.parts)
        # find .../<ns>/tags/items/<...>
        idx = None
        for i in range(len(parts) - 2):
            if parts[i] == "tags" and parts[i + 1] == "items":
                idx = i
        if idx is None or idx < 1:
            continue
        ns = parts[idx - 1]
        name = "/".join(parts[idx + 2 :])[:-5]
        key = f"{ns}:{name}"
        data = json.loads(p.read_text(encoding="utf-8"))
        vals = []
        for v in data.get("values", []):
            if isinstance(v, str):
                vals.append(v)
            elif isinstance(v, dict) and "id" in v:
                vals.append(v["id"])
        tags[key] = vals
    return tags


def expand_tag_members(tags: dict, ref: str, depth=0) -> list[str]:
    """Expand tag values, including nested #tag references."""
    if depth > 8:
        return []
    key = ref[1:] if ref.startswith("#") else ref
    out = []
    for v in tags.get(key, []):
        if isinstance(v, str) and v.startswith("#"):
            out.extend(expand_tag_members(tags, v, depth + 1))
        elif isinstance(v, str):
            out.append(v)
    return out


def extract_ingredient(obj, default_count=1):
    if obj is None:
        return
    if isinstance(obj, list):
        for x in obj:
            yield from extract_ingredient(x, default_count)
        return
    if not isinstance(obj, dict):
        return
    cnt = obj.get("count", obj.get("ingredient_count", default_count)) or default_count
    if "item" in obj:
        yield ("item", obj["item"], int(cnt))
    elif "tag" in obj:
        yield ("tag", obj["tag"], int(cnt))


def parse_recipe(path: Path):
    d = json.loads(path.read_text(encoding="utf-8"))
    typ = d.get("type", "")
    if typ == "kaleidoscope_tavern:pressing_tub":
        return {
            "type": typ,
            "out": None,
            "out_count": 1,
            "ings": list(extract_ingredient(d.get("ingredient"))),
            "fluid_out": d.get("fluid"),
            "fluid_amount": int(d.get("fluid_amount", 125) or 125),
            "carrier": None,
            "fluid_in": None,
        }
    result = d.get("result")
    if isinstance(result, dict):
        out = result.get("item")
        out_count = int(result.get("count", 1) or 1)
    elif isinstance(result, str):
        out, out_count = result, 1
    else:
        return None
    if not out:
        return None
    ings = []
    if "ingredients" in d:
        ings.extend(extract_ingredient(d["ingredients"]))
    if "ingredient" in d:
        ings.extend(
            extract_ingredient(d["ingredient"], default_count=d.get("ingredient_count", 1))
        )
    if "key" in d and "pattern" in d:
        key = d["key"]
        counts = Counter()
        for row in d["pattern"]:
            for ch in row:
                if ch.strip() and ch in key:
                    counts[ch] += 1
        for ch, n in counts.items():
            ings.extend(extract_ingredient(key[ch], default_count=n))
    carrier = None
    if isinstance(d.get("carrier"), dict) and "item" in d["carrier"]:
        carrier = d["carrier"]["item"]
    return {
        "type": typ,
        "out": out,
        "out_count": out_count,
        "ings": ings,
        "fluid_out": None,
        "fluid_amount": 0,
        "carrier": carrier,
        "fluid_in": d.get("fluid") or d.get("soup_base") or d.get("tea_fluid"),
    }


def labor_for(typ: str, out_name: str):
    if any(k in out_name for k in L3_KEYS):
        return "L3", L3
    return TYPE_LABOR.get(typ, ("L1", L1))


def listing_count(name: str, typ: str) -> int:
    # finished dishes/drinks as 16 for readable, varied prices
    if typ in (
        "kaleidoscope_cookery:pot",
        "kaleidoscope_cookery:flex_pot",
        "kaleidoscope_cookery:stockpot",
        "kaleidoscope_cookery:flex_stockpot",
        "kaleidoscope_cookery:teapot",
        "kaleidoscope_cookery:rice_bowl",
        "kaleidoscope_cookery:steamer",
        "kaleidoscope_tavern:barrel",
        "kaleidoscope_tavern:shaker",
    ):
        return 16
    if name.endswith("_tea") or name.endswith("_plate") or name.endswith("_platter"):
        return 16
    if "juice" in name or "bucket" in name:
        return 16
    return 64


def main():
    data = json.loads(CFG.read_text(encoding="utf-8"))
    rev = {str(v): k for k, v in data["nameSpaceMap"].items()}

    shop_unit = {}
    shop_rows = {}
    for r in data["systemShopItems"]:
        pref, name = r[0]["NIN"].split(":", 1)
        mod = rev.get(pref, pref)
        abs_id = f"{mod}:{name}"
        cnt = max(int(r[0].get("count") or 1), 1)
        shop_unit[abs_id] = float(r[1]) / cnt
        shop_rows[abs_id] = r

    # mat_only: only seed base goods (vanilla + kept raws + prep intermediates).
    # Do NOT seed finished dish/drink shop prices or cocktail tags pick leftovers.
    mat_only = {}
    for abs_id, u in shop_unit.items():
        mod, name = abs_id.split(":", 1)
        if mod == "minecraft" or should_keep(name) or name in RECIPE_RAWS:
            mat_only[abs_id] = u
    mat_only.setdefault("minecraft:bowl", 1.0)
    mat_only.setdefault("minecraft:glass_bottle", 2.0 / 16)
    mat_only.setdefault("minecraft:potion", 0.5)
    mat_only.setdefault("minecraft:water", 0.05)
    mat_only.setdefault("minecraft:poppy", shop_unit.get("minecraft:poppy", 1.0 / 16))

    tags = load_tags()
    recipes = []
    for folder in (REC_COOK, REC_TAV):
        for p in folder.rglob("*.json"):
            rec = parse_recipe(p)
            if rec:
                recipes.append(rec)

    fluid_mb = {"minecraft:water": 0.0002}

    def resolve_mat(kind, ref) -> float | None:
        if kind == "item":
            return mat_only.get(ref)
        if kind == "tag":
            members = expand_tag_members(tags, ref)
            # Cocktail color tags: ignore vanilla potion filler so spirits/wines win
            if "cocktail_ingredient" in ref:
                members = [
                    m
                    for m in members
                    if not m.startswith("minecraft:")
                ] or members
            prices = [mat_only[m] for m in members if m in mat_only]
            if prices:
                return min(prices)
            fb = TAG_FALLBACK.get(ref)
            if fb and fb in mat_only:
                return mat_only[fb]
        return None

    def carrier_cost(item: str | None) -> float:
        if not item:
            return 0.0
        base = mat_only.get(item, 1.0)
        if "bowl" in item:
            return base * BOWL_SHARE
        if "bottle" in item or "cup" in item or "glass" in item:
            return base
        return base * 0.5

    # iterative mat_only
    for _ in range(30):
        changed = 0
        # pressing fluids
        for rec in recipes:
            if rec["type"] != "kaleidoscope_tavern:pressing_tub" or not rec.get("fluid_out"):
                continue
            costs = []
            ok = True
            for kind, ref, cnt in rec["ings"]:
                m = resolve_mat(kind, ref)
                if m is None:
                    ok = False
                    break
                costs.append(m * cnt)
            if not ok:
                continue
            amt = max(rec["fluid_amount"], 1)
            per_mb = sum(costs) / amt
            if fluid_mb.get(rec["fluid_out"]) != per_mb:
                fluid_mb[rec["fluid_out"]] = per_mb
                changed += 1
            # juice / bucket items
            fname = short_id(rec["fluid_out"])
            for name, mb in ((fname, BOTTLE_MB), (fname.replace("_juice", "_bucket"), 1000)):
                abs_id = f"kaleidoscope_tavern:{name}"
                if abs_id in shop_rows:
                    m = per_mb * mb
                    if mat_only.get(abs_id) != m:
                        mat_only[abs_id] = m
                        changed += 1

        for rec in recipes:
            if rec["type"] == "kaleidoscope_tavern:pressing_tub":
                continue
            out = rec["out"]
            if not out:
                continue
            name = short_id(out)
            if should_keep(name):
                continue
            total = 0.0
            ok = True
            for kind, ref, cnt in rec["ings"]:
                m = resolve_mat(kind, ref)
                if m is None:
                    ok = False
                    break
                total += m * cnt
            if not ok:
                continue
            total += carrier_cost(rec.get("carrier"))
            fl = rec.get("fluid_in")
            if fl:
                if fl in fluid_mb:
                    total += fluid_mb[fl] * BOTTLE_MB
                elif fl == "minecraft:water":
                    total += 0.05
            if rec["type"] == "kaleidoscope_cookery:rice_bowl":
                cr = "kaleidoscope_cookery:cooked_rice"
                if cr in mat_only:
                    total += mat_only[cr]
            per = total / max(rec["out_count"], 1)
            old = mat_only.get(out)
            if old is None or per < old - 1e-12:
                mat_only[out] = per
                changed += 1
        if changed == 0:
            break

    # cooked_rice etc. are intermediates: price with mild L0 when applying shop
    INTERMEDIATE_MULT = {
        "cooked_rice": ("L0", 1.5),
        "fried_egg": ("L1", L1),
    }
    for raw in RECIPE_RAWS:
        INTERMEDIATE_MULT[raw] = ("L0", 1.5)

    # shop sell price from mat_only × labor (once)
    report = []
    # pick a representative recipe type per output (prefer cooking types over crafting)
    out_types = {}
    for rec in recipes:
        if not rec.get("out"):
            continue
        out = rec["out"]
        typ = rec["type"]
        prev = out_types.get(out)
        rank = 0
        if "pot" in typ or "stockpot" in typ or "teapot" in typ or "rice_bowl" in typ:
            rank = 3
        elif "barrel" in typ or "shaker" in typ:
            rank = 3
        elif "steamer" in typ or "chopping" in typ or "millstone" in typ:
            rank = 2
        elif "pressing" in typ:
            rank = 2
        else:
            rank = 1
        if prev is None or rank >= prev[0]:
            out_types[out] = (rank, typ)

    KALEIDO_NS = ("kaleidoscope_cookery", "kaleidoscope_tavern")

    for abs_id, r in shop_rows.items():
        mod, name = abs_id.split(":", 1)
        # NEVER rewrite vanilla / ice / dolls — only森罗厨房+酒馆
        if mod not in KALEIDO_NS:
            continue
        if should_keep(name):
            continue
        if abs_id not in mat_only:
            continue
        # only update if we have a cook/tavern recipe path or juice from pressing
        typ = out_types.get(abs_id, (0, ""))[1]
        if abs_id in out_types:
            typ = out_types[abs_id][1]
        elif name.endswith("_juice") or name.endswith("_bucket"):
            typ = "kaleidoscope_tavern:pressing_tub"
        else:
            continue

        tier, mult = labor_for(typ, name)
        if typ.startswith("minecraft:crafting"):
            if not (name.endswith("_plate") or name.endswith("_platter") or "cup" in name):
                continue
            tier, mult = "L1", L1
        if name in INTERMEDIATE_MULT:
            tier, mult = INTERMEDIATE_MULT[name]
        # stir-fries / noodles used as inputs: milder if not rice_bowl/tea/wine
        if typ in (
            "kaleidoscope_cookery:pot",
            "kaleidoscope_cookery:flex_pot",
        ) and not name.endswith("_rice_bowl"):
            # still L1 finals for stir-fry sold as food
            pass

        m = mat_only[abs_id]
        flat = FLAT.get(tier, FLAT["L1"])
        # cheap chopping/millstone intermediates: flat must not dominate ×64 stacks
        if name in RECIPE_RAWS or typ in (
            "kaleidoscope_cookery:chopping_board",
            "kaleidoscope_cookery:millstone",
        ):
            flat = FLAT["L0"]
            tier, mult = "L0", 1.5
        unit = m * mult + flat
        cnt = listing_count(name, typ)
        if name == "cooked_rice" or name in RECIPE_RAWS:
            cnt = 64  # staple / prep stack
        buy = r2(unit * cnt)
        if tier == "L1":
            buy = max(buy, 14.0)
        elif tier == "L2":
            buy = max(buy, 22.0)
        elif tier == "L3":
            buy = max(buy, 40.0)
        # barrel / shaker drinks: soft floor above plain tea stir-fries
        if typ in ("kaleidoscope_tavern:barrel", "kaleidoscope_tavern:shaker"):
            buy = max(buy, 28.0 if typ.endswith("barrel") else 36.0)
        old = r[1]
        r[0]["count"] = cnt
        r[1] = buy
        r[2] = sell_of(buy)
        report.append((abs_id, tier, r2(m), mult, r2(unit), old, buy, r[2], cnt, typ))

    # empty_cup lock
    for abs_id, r in shop_rows.items():
        if short_id(abs_id) == "empty_cup":
            r[1], r[2] = 10.0, 2.0
            r[0]["count"] = 16

    counts = Counter()
    for r in data["systemShopItems"]:
        pref = r[0]["NIN"].split(":", 1)[0]
        counts[rev.get(pref, pref)] += 1
    mc = counts.get("minecraft", 0)
    cook = counts.get("kaleidoscope_cookery", 0)
    tav = counts.get("kaleidoscope_tavern", 0)
    doll = counts.get("kaleidoscope_doll", 0)
    ice = counts.get("bricefire", 0)
    total = len(data["systemShopItems"])
    data["ecoSystemData"]["noticeMsg"] = (
        f"仅金币｜原版{mc}｜森罗厨{cook}+酒{tav}+偶{doll}｜冰火{ice}｜合计{total}｜"
        f"死亡扣30%｜森罗按配方材料×人工C"
    )

    CFG.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    share = "ppcpdata%" + base64.b64encode(
        zlib.compress(
            json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode(), 9
        )
    ).decode()
    (BASE / "分享码.txt").write_text(share, encoding="utf-8")
    (BASE / "05_原始备份" / "最终分享串_副本.txt").write_text(share, encoding="utf-8")

    rep = BASE / "03_对比报告" / "森罗配方B档调价.csv"
    with open(rep, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "id",
                "tier",
                "mat_only",
                "mult",
                "unit",
                "old_buy",
                "new_buy",
                "new_sell",
                "count",
                "recipe_type",
            ]
        )
        for row in sorted(report):
            w.writerow(row)

    ap = BASE / "02_定价锚点与说明" / "price_anchors.json"
    try:
        anchors = json.loads(ap.read_text(encoding="utf-8"))
    except Exception:
        anchors = {}
    anchors["labor"] = {"L0": 1.5, "L1": 3.0, "L2": 4.0, "L3": 5.0}
    anchors["labor_note"] = (
        "方案B：官方配方材料单价(mat_only不叠人工)×最终人工C+flat；原料/厨具保持原价"
    )
    ap.write_text(json.dumps(anchors, ensure_ascii=False, indent=2), encoding="utf-8")

    (BASE / "02_定价锚点与说明" / "简介.txt").write_text(
        f"""分享码简介（当前版）

【货币】仅金币
【数量】原版{mc}｜森罗厨{cook}+酒{tav}+偶{doll}｜冰火{ice}｜合计{total}
【森罗定价】方案B：按官方配方材料成本×人工C（×3/×4/×5）+flat；中间产物不叠人工
【公告】{data['ecoSystemData']['noticeMsg']}
""",
        encoding="utf-8",
    )

    print(f"updated={len(report)} share={len(share)}")
    samples = [
        "empty_cup",
        "barley_tea",
        "flower_tea",
        "egg_fried_rice",
        "stir_fried_pork_with_peppers",
        "stir_fried_pork_with_peppers_rice_bowl",
        "braised_beef_rice_bowl",
        "pan_seared_knight_steak",
        "cooked_rice",
        "sakura_wine",
        "rum",
        "mojito",
        "grape_juice",
        "molotov",
        "donkey_burger",
    ]
    for s in samples:
        for mod in ("kaleidoscope_cookery", "kaleidoscope_tavern"):
            abs_id = f"{mod}:{s}"
            if abs_id in shop_rows:
                r = shop_rows[abs_id]
                print(
                    f"  {s:40s} buy={r[1]:8} sell={r[2]:8} count={r[0].get('count')} mat={mat_only.get(abs_id)}"
                )


if __name__ == "__main__":
    main()
