# -*- coding: utf-8 -*-
"""Parse Kaleidoscope Cookery/Tavern recipes (cloned repos) and compute
new dish/drink prices: materials = kept ingredients (old price) + /30 crops,
buy = materials x3 (+5 complex), sell = materials. Writes kaleido_prices.py."""
import json, re
from pathlib import Path

ROOT = Path(r"C:/Users/AI10/Desktop/ppcdata")
COOK = Path(r"C:/Users/AI10/AppData/Local/Temp/KaleidoscopeCookery")
TAV = Path(r"C:/Users/AI10/AppData/Local/Temp/KaleidoscopeTavern")

# ---- load 08202 shop -> per-piece old price
def decode(p):
    s = Path(p).read_text(encoding="utf-8").strip()
    if "%" in s[:20]:
        s = s.split("%", 1)[1]
    pad = (-len(s)) % 4
    import base64, zlib
    return json.loads(zlib.decompress(base64.b64decode(s + "=" * pad)))["data"]

d02 = decode(ROOT / "06_用户自行导入" / "08202.txt")
rev = {str(v): k for k, v in d02["nameSpaceMap"].items()}
shop = {}
for r in d02["systemShopItems"]:
    nin = r[0].get("NIN", "")
    p, n = nin.split(":", 1) if ":" in nin else ("", nin)
    ns = rev.get(p, "?" + p)
    cnt = r[0].get("count") or 1
    shop[f"{ns}:{n}"] = (r[1], r[2], cnt)

KEEP_MC = set("""
enchanted_book netherite_ingot netherite_scrap netherite_block netherite_sword
netherite_pickaxe netherite_axe netherite_shovel netherite_hoe netherite_helmet
netherite_chestplate netherite_leggings netherite_boots
netherite_upgrade_smithing_template ancient_debris bone bone_meal rotten_flesh
gunpowder string spider_eye slime_ball leather rabbit_hide feather egg milk_bucket
honey_bottle honeycomb beef porkchop chicken mutton rabbit cod salmon tropical_fish
pufferfish cooked_beef cooked_porkchop cooked_chicken cooked_mutton cooked_rabbit
cooked_cod cooked_salmon blaze_rod blaze_powder ghast_tear magma_cream ender_pearl
phantom_membrane nautilus_shell heart_of_the_sea nether_star beacon elytra
totem_of_undying trident shulker_shell shulker_box ender_chest dragon_breath
prismarine_shard prismarine_crystals echo_shard goat_horn skull wither_rose saddle
name_tag lead chainmail_helmet chainmail_chestplate chainmail_leggings chainmail_boots
recovery_compass ominous_bottle trial_key breeze_rod heavy_core pufferfish_bucket
tropical_fish_bucket cod_bucket salmon_bucket axolotl_bucket tadpole_bucket
""".split())

# 种植物生长约束：快熟 ÷3 / 慢熟 ÷2（连锁只省采收不省生长）
CROP_DIV3 = set("""
wheat carrot potato beetroot melon pumpkin melon_slice sweet_berries glow_berries
kelp bamboo sugar_cane sugar nether_wart wheat_seeds melon_seeds pumpkin_seeds
beetroot_seeds torchflower_seeds pitcher_pod rice rice_panicle wild_rice tomato
lettuce green_chili red_chili chili_seed tomato_seed lettuce_seed wild_rice_seed
fresh_tea_leaves oil grape green_grape gold_grape ice_grape wild_grape grape_crop
green_grape_crop gold_grape_crop ice_grape_crop grapevine wild_grapevine
wild_grapevine_plant gold_grapevine_trellis grapevine_trellis ice_grapevine_trellis
""".split())
CROP_DIV2 = set("""cocoa_beans""".split())


def is_kept(name):
    ns = name.split(":", 1)[0]
    n = name.split(":", 1)[1] if ":" in name else name
    if ns == "minecraft":
        return (n in KEEP_MC or n.endswith("_spawn_egg") or n.startswith("music_disc")
                or "skull" in n or n.endswith("_head") or n == "painting")
    if ns in ("bricefire", "ysm_maid"):
        return True
    return False


def unit_new_price(name):
    """per-piece new price for an ingredient."""
    if name not in shop:
        return 0.0
    buy, sell, cnt = shop[name]
    unit_old = buy / cnt
    if is_kept(name):
        return unit_old
    bare = name.split(":", 1)[-1]
    if bare in CROP_DIV2:
        return unit_old / 2.0
    if bare in CROP_DIV3:
        return unit_old / 3.0
    return unit_old / 30.0


def resolve_ingredient(ing):
    if "item" in ing:
        if ing["item"].endswith("_bucket"):
            return None  # vessels return after crafting
        return ing["item"]
    if "tag" in ing:
        suffix = ing["tag"].split("/")[-1]
        for ns in ("kaleidoscope_cookery", "kaleidoscope_tavern", "minecraft"):
            if f"{ns}:{suffix}" in shop:
                return f"{ns}:{suffix}"
        return None
    return None


L3 = re.compile(r"blaze_|golden_salad|buddha|nether_style|end_style|pan_seared|stargazy|"
                r"sweet_and_sour_ender|chorus_fried|fondant_spider|molotov|nether_special|"
                r"sculk_special|dragon_breath|miners_star")

COOKING_TYPES = ("flex_stockpot", "stockpot", "flex_pot", "teapot", "steamer",
                 "rice_bowl", "chopping_board", "barrel", "shaker", "pressing_tub", "pot")

out = {}
for base in (COOK, TAV):
    for f in base.rglob("*.json"):
        if "advancements" in f.parts or "_entity" in f.name:
            continue
        try:
            rec = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        result = rec.get("result")
        if not isinstance(result, dict) or "item" not in result:
            continue
        resname = result["item"]
        if resname not in shop:
            continue
        rescount = result.get("count", 1)
        mat = 0.0
        for ing in rec.get("ingredients", []):
            nm = resolve_ingredient(ing)
            if nm:
                mat += unit_new_price(nm)
        fluid = rec.get("fluid")
        if fluid and fluid in shop:
            mat += unit_new_price(fluid)
        if not rec.get("ingredients") and not (fluid and fluid in shop):
            continue
        mat_per = mat / rescount
        rtype = rec.get("type", "").split(":")[-1]
        tax = 3.0 if rtype in COOKING_TYPES else 1.8
        buy = mat_per * tax
        if L3.search(resname):
            buy += 5.0
        buy = max(0.01, round(buy, 2))
        sell = max(0.01, round(mat_per, 2))
        # keep the largest-materials variant per dish (conservative)
        if resname not in out or sell > out[resname][1]:
            out[resname] = (buy, sell)

lines = ["# auto-generated by parse_kaleido_recipes.py",
         "KALEIDO_PRICES = {"]
for k in sorted(out):
    lines.append(f'    "{k}": ({out[k][0]}, {out[k][1]}),')
lines.append("}")
(ROOT / "04_工具脚本" / "kaleido_prices.py").write_text("\n".join(lines), encoding="utf-8")
print(f"generated {len(out)} kaleido dish prices -> 04_工具脚本/kaleido_prices.py")
for k in ("kaleidoscope_cookery:pufferfish_soup", "kaleidoscope_cookery:dumpling",
          "kaleidoscope_cookery:buddha_jumps_over_the_wall",
          "kaleidoscope_tavern:honey_wine", "kaleidoscope_tavern:plum_wine",
          "kaleidoscope_cookery:bamboo_tube_rice", "kaleidoscope_cookery:raw_noodles",
          "kaleidoscope_cookery:butter_tea", "kaleidoscope_cookery:tea_egg"):
    if k in out:
        print(f"  {k}: {out[k]}")
