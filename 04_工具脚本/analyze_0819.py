# -*- coding: utf-8 -*-
"""Decode 0819 user share and produce a full-system analysis vs 0815 / rebuilt."""
import base64
import json
import zlib
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(r"C:/Users/AI10/Desktop/ppcdata")
USER_0819 = ROOT / "06_用户自行导入" / "0819.txt"
USER_0815 = ROOT / "06_用户自行导入" / "0815.txt"
USER_0818 = ROOT / "06_用户自行导入" / "0818.txt"
OURS_JSON = ROOT / "01_配置明文" / "最终配置_rebuilt.json"
OUT_USER = ROOT / "01_配置明文" / "0819_decoded.json"
OUT_REPORT = ROOT / "03_对比报告" / "0819_全面解析.json"
OUT_TXT = ROOT / "03_对比报告" / "0819_全面解析.txt"


def decode_share(s: str):
    s = s.strip()
    if "%" in s[:20]:
        s = s.split("%", 1)[1]
    pad = (-len(s)) % 4
    raw = base64.b64decode(s + "=" * pad)
    return json.loads(zlib.decompress(raw).decode("utf-8"))


def unwrap(raw):
    wrapper = {}
    if isinstance(raw, dict) and "data" in raw and "formatVersion" in raw:
        wrapper = {
            "formatVersion": raw.get("formatVersion"),
            "sections": raw.get("sections"),
            "extra_keys": sorted(set(raw) - {"data", "formatVersion", "sections"}),
        }
        return raw["data"], wrapper
    return raw, wrapper


def item_id(row, rev):
    item = row[0] if isinstance(row[0], dict) else {}
    nin = item.get("NIN", "")
    pref, name = nin.split(":", 1) if ":" in nin else ("", nin)
    ns = rev.get(pref, pref)
    dur = item.get("durability", 0)
    count = item.get("count", 1)
    return f"{ns}:{name}|d{dur}|c{count}"


def short_name(row, rev):
    item = row[0] if isinstance(row[0], dict) else {}
    nin = item.get("NIN", "")
    pref, name = nin.split(":", 1) if ":" in nin else ("", nin)
    ns = rev.get(pref, pref)
    return f"{ns}:{name}"


def shop_fields(row):
    item = row[0] if isinstance(row[0], dict) else {}
    return {
        "buy": row[1] if len(row) > 1 else None,
        "sell": row[2] if len(row) > 2 else None,
        "note": row[3] if len(row) > 3 else None,
        "stock": row[4] if len(row) > 4 else None,
        "limit": row[5] if len(row) > 5 else None,
        "tag": row[6] if len(row) > 6 else None,
        "recycle": row[7] if len(row) > 7 else None,
        "buyCoin": row[8] if len(row) > 8 else None,
        "sellCoin": row[9] if len(row) > 9 else None,
        "extra10": row[10] if len(row) > 10 else None,
        "stack": row[12] if len(row) > 12 else None,
        "durability": item.get("durability", 0),
        "count": item.get("count", 1),
    }


def summarize_value(v, depth=0):
    if isinstance(v, dict):
        if depth >= 2:
            return f"<dict keys={len(v)}>"
        return {k: summarize_value(x, depth + 1) for k, x in list(v.items())[:40]}
    if isinstance(v, list):
        if not v:
            return []
        if all(not isinstance(x, (dict, list)) for x in v):
            return v if len(v) <= 20 else v[:20] + [f"... +{len(v)-20}"]
        return f"<list n={len(v)} first={type(v[0]).__name__}>"
    return v


def flatten_scalars(obj, prefix=""):
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                out.update(flatten_scalars(v, p))
            elif isinstance(v, list):
                out[p] = f"<list n={len(v)}>"
            else:
                out[p] = v
    else:
        out[prefix] = obj
    return out


def ns_count(items, rev):
    c = Counter()
    for r in items:
        nin = r[0].get("NIN", "") if isinstance(r[0], dict) else ""
        pref = nin.split(":", 1)[0]
        c[rev.get(pref, pref)] += 1
    return dict(c)


def main():
    raw_0819 = decode_share(USER_0819.read_text(encoding="utf-8"))
    OUT_USER.write_text(json.dumps(raw_0819, ensure_ascii=False, indent=2), encoding="utf-8")
    user, wrapper = unwrap(raw_0819)

    raw_0815 = decode_share(USER_0815.read_text(encoding="utf-8"))
    u15, w15 = unwrap(raw_0815)

    raw_0818 = decode_share(USER_0818.read_text(encoding="utf-8"))
    u18, w18 = unwrap(raw_0818)

    ours = json.loads(OURS_JSON.read_text(encoding="utf-8"))

    user_rev = {str(v): k for k, v in user.get("nameSpaceMap", {}).items()}
    o15_rev = {str(v): k for k, v in u15.get("nameSpaceMap", {}).items()}
    o18_rev = {str(v): k for k, v in u18.get("nameSpaceMap", {}).items()}
    ours_rev = {str(v): k for k, v in ours.get("nameSpaceMap", {}).items()}

    report = {
        "source": "0819.txt",
        "prefix": USER_0819.read_text(encoding="utf-8")[:16],
        "wrapper": wrapper,
        "top_keys": list(user.keys()),
        "keys_only_vs_0815": sorted(set(user) - set(u15)),
        "keys_only_in_0815": sorted(set(u15) - set(user)),
        "keys_only_vs_ours": sorted(set(user) - set(ours)),
        "keys_only_in_ours": sorted(set(ours) - set(user)),
        "wrapper_0815": w15,
        "wrapper_0818": w18,
        "0818_top_keys": list(u18.keys()) if isinstance(u18, dict) else type(u18).__name__,
    }

    # ---- eco ----
    eco = user.get("ecoSystemData", {})
    eco15 = u15.get("ecoSystemData", {})
    eco18 = u18.get("ecoSystemData", {})
    eco_ours = ours.get("ecoSystemData", {})

    eco_vs_0815 = []
    for k in sorted(set(eco) | set(eco15)):
        if eco.get(k) != eco15.get(k):
            eco_vs_0815.append({"field": k, "0815": eco15.get(k), "0819": eco.get(k)})
    eco_vs_ours = []
    for k in sorted(set(eco) | set(eco_ours)):
        if eco.get(k) != eco_ours.get(k):
            eco_vs_ours.append({"field": k, "ours": eco_ours.get(k), "0819": eco.get(k)})
    eco_vs_0818 = []
    for k in sorted(set(eco) | set(eco18)):
        if eco.get(k) != eco18.get(k):
            eco_vs_0818.append({"field": k, "0818": eco18.get(k), "0819": eco.get(k)})

    report["eco_0819"] = eco
    report["eco_vs_0815"] = eco_vs_0815
    report["eco_vs_0818_count"] = len(eco_vs_0818)
    report["eco_vs_ours"] = eco_vs_ours

    # group eco by prefix
    groups = defaultdict(dict)
    for k, v in eco.items():
        if k.startswith("luckyDraw"):
            g = "抽奖"
        elif k.startswith("residence"):
            g = "领地"
        elif k.startswith("teleport"):
            g = "传送"
        elif k.startswith("bulletin"):
            g = "公告"
        elif k.startswith("projectE"):
            g = "等价交换"
        elif k.startswith("playerShop") or k.startswith("request") or k in ("taxRate", "playerEcoTransferAble", "playerEcoTransferTaxRate"):
            g = "玩家商店/转账/税"
        elif k.startswith("exchange"):
            g = "兑换商店"
        elif k.startswith("stock"):
            g = "股市"
        elif k.startswith("mainButton"):
            g = "主界面按钮"
        elif "death" in k.lower() or k in ("defCoin", "preMinuteCoin", "ecoRanking", "killPlayerReward", "killPlayerRewardPercent"):
            g = "基础经济"
        else:
            g = "其他系统"
        groups[g][k] = v
    report["eco_groups"] = {k: v for k, v in groups.items()}

    # ---- lottery / other large structures ----
    interesting = {}
    for k, v in user.items():
        if k in ("systemShopItems",):
            continue
        interesting[k] = summarize_value(v)
    report["non_shop_summary"] = interesting

    # hunt lottery-like keys anywhere
    lottery_hits = []

    def walk(obj, path=""):
        if isinstance(obj, dict):
            for kk, vv in obj.items():
                p = f"{path}.{kk}" if path else kk
                if any(x in kk.lower() for x in ("lucky", "draw", "lottery", "gacha", "prize", "pool")):
                    lottery_hits.append({"path": p, "type": type(vv).__name__, "summary": summarize_value(vv)})
                walk(vv, p)
        elif isinstance(obj, list) and obj and isinstance(obj[0], dict):
            walk(obj[0], path + "[0]")

    walk(raw_0819)
    report["lottery_hits"] = lottery_hits

    # ---- coins / tags / ns / kill ----
    report["coins_0819"] = user.get("customCoinTypes", [])
    report["coins_0815"] = u15.get("customCoinTypes", [])
    report["coins_ours"] = ours.get("customCoinTypes", [])
    report["tags_0819"] = user.get("customItemTags", [])
    report["tags_0815"] = u15.get("customItemTags", [])
    report["tags_ours"] = ours.get("customItemTags", [])
    report["type_map_0819"] = user.get("customItemTypeMap", {})
    report["ns_0819"] = user.get("nameSpaceMap", {})
    report["kill_0819"] = user.get("killEntityRewardMap", {})
    report["kill_0815"] = u15.get("killEntityRewardMap", {})
    report["kill_ours"] = ours.get("killEntityRewardMap", {})
    report["kill_vs_0815"] = {
        "added": {k: user.get("killEntityRewardMap", {}).get(k) for k in set(user.get("killEntityRewardMap", {})) - set(u15.get("killEntityRewardMap", {}))},
        "removed": {k: u15.get("killEntityRewardMap", {}).get(k) for k in set(u15.get("killEntityRewardMap", {})) - set(user.get("killEntityRewardMap", {}))},
        "changed": {
            k: {"0815": u15["killEntityRewardMap"][k], "0819": user["killEntityRewardMap"][k]}
            for k in set(user.get("killEntityRewardMap", {})) & set(u15.get("killEntityRewardMap", {}))
            if user["killEntityRewardMap"][k] != u15["killEntityRewardMap"][k]
        },
    }
    report["exchange_0819"] = user.get("exchangeShopData", {})
    report["exchange_0815"] = u15.get("exchangeShopData", {})
    report["notice_0819"] = eco.get("noticeMsg")
    report["notice_0815"] = eco15.get("noticeMsg")
    report["notice_ours"] = eco_ours.get("noticeMsg")

    # ---- shop vs 0815 / ours / 0818 ----
    def shop_diff(a, a_rev, b, b_rev):
        amap, bmap = {}, {}
        for r in a:
            amap[item_id(r, a_rev)] = r
        for r in b:
            bmap[item_id(r, b_rev)] = r
        added = sorted(set(amap) - set(bmap))
        removed = sorted(set(bmap) - set(amap))
        changed = []
        for k in sorted(set(amap) & set(bmap)):
            af, bf = shop_fields(amap[k]), shop_fields(bmap[k])
            diffs = {f: {"from": bf[f], "to": af[f]} for f in af if af[f] != bf[f]}
            if diffs:
                changed.append({"id": k, "name": short_name(amap[k], a_rev), "diffs": diffs})
        price_only = [c for c in changed if set(c["diffs"]) <= {"buy", "sell"}]
        tag_only = [c for c in changed if set(c["diffs"]) <= {"tag"}]
        recycle_only = [c for c in changed if set(c["diffs"]) <= {"recycle"}]
        mixed = [c for c in changed if c not in price_only and c not in tag_only and c not in recycle_only]
        field_c = Counter()
        for c in changed:
            for f in c["diffs"]:
                field_c[f] += 1
        return {
            "a_count": len(a),
            "b_count": len(b),
            "a_by_ns": ns_count(a, a_rev),
            "b_by_ns": ns_count(b, b_rev),
            "added": added,
            "removed": removed,
            "changed": changed,
            "price_only": price_only,
            "tag_only": tag_only,
            "recycle_only": recycle_only,
            "mixed": mixed,
            "changed_fields": dict(field_c),
        }

    vs15 = shop_diff(user.get("systemShopItems", []), user_rev, u15.get("systemShopItems", []), o15_rev)
    vs18 = shop_diff(user.get("systemShopItems", []), user_rev, u18.get("systemShopItems", []), o18_rev)
    vsours = shop_diff(user.get("systemShopItems", []), user_rev, ours.get("systemShopItems", []), ours_rev)

    def brief_shop(diff):
        def row_brief(c):
            d = c["diffs"]
            out = {"name": c["name"]}
            for f in ("buy", "sell", "tag", "recycle", "stock", "limit"):
                if f in d:
                    out[f] = f"{d[f]['from']} -> {d[f]['to']}"
            extra = [k for k in d if k not in ("buy", "sell", "tag", "recycle", "stock", "limit")]
            if extra:
                out["other"] = extra
            return out

        return {
            "a_count": diff["a_count"],
            "b_count": diff["b_count"],
            "a_by_ns": diff["a_by_ns"],
            "b_by_ns": diff["b_by_ns"],
            "added_n": len(diff["added"]),
            "removed_n": len(diff["removed"]),
            "changed_n": len(diff["changed"]),
            "price_only_n": len(diff["price_only"]),
            "tag_only_n": len(diff["tag_only"]),
            "recycle_only_n": len(diff["recycle_only"]),
            "mixed_n": len(diff["mixed"]),
            "changed_fields": diff["changed_fields"],
            "added": diff["added"][:80],
            "removed": diff["removed"][:80],
            "price_changes": [row_brief(c) for c in diff["price_only"][:80]],
            "tag_changes": [row_brief(c) for c in diff["tag_only"][:40]],
            "recycle_changes": [row_brief(c) for c in diff["recycle_only"][:40]],
            "mixed_changes": [row_brief(c) for c in diff["mixed"][:80]],
            "added_all": diff["added"],
            "removed_all": diff["removed"],
            "price_changes_all": [row_brief(c) for c in diff["price_only"]],
            "mixed_changes_all": [row_brief(c) for c in diff["mixed"]],
        }

    report["shop_vs_0815"] = brief_shop(vs15)
    report["shop_vs_0818"] = brief_shop(vs18)
    report["shop_vs_ours"] = brief_shop(vsours)

    # price stats
    items = user.get("systemShopItems", [])
    buys, sells, ratios, rec_off, rec_on, zero_buy, zero_sell, no_sell = [], [], [], 0, 0, 0, 0, 0
    tag_c = Counter()
    for r in items:
        f = shop_fields(r)
        tag_c[f["tag"] or ""] += 1
        if f["recycle"]:
            rec_on += 1
        else:
            rec_off += 1
        if f["buy"] in (None, 0, 0.0):
            zero_buy += 1
        else:
            buys.append(f["buy"])
        if f["sell"] in (None,):
            no_sell += 1
        elif f["sell"] in (0, 0.0):
            zero_sell += 1
        else:
            sells.append(f["sell"])
        if f["buy"] and f["sell"] and f["buy"] > 0:
            ratios.append(f["sell"] / f["buy"])

    report["shop_stats"] = {
        "count": len(items),
        "by_ns": ns_count(items, user_rev),
        "by_tag": dict(tag_c),
        "recycle_on": rec_on,
        "recycle_off": rec_off,
        "zero_buy": zero_buy,
        "zero_sell": zero_sell,
        "no_sell": no_sell,
        "buy_min": min(buys) if buys else None,
        "buy_max": max(buys) if buys else None,
        "buy_median": sorted(buys)[len(buys)//2] if buys else None,
        "sell_ratio_median": sorted(ratios)[len(ratios)//2] if ratios else None,
        "sell_ratio_mean": sum(ratios)/len(ratios) if ratios else None,
    }

    # other top-level diffs vs 0815
    other = []
    for k in set(user) & set(u15):
        if k in ("systemShopItems", "ecoSystemData"):
            continue
        if user[k] != u15[k]:
            other.append({
                "field": k,
                "0815": summarize_value(u15[k]),
                "0819": summarize_value(user[k]),
            })
    report["other_top_vs_0815"] = other

    # write json (trim huge shop lists in the json? keep them, but maybe heavy)
    slim = dict(report)
    for key in ("shop_vs_0815", "shop_vs_0818", "shop_vs_ours"):
        slim[key] = {kk: vv for kk, vv in slim[key].items() if not kk.endswith("_all")}
    OUT_REPORT.write_text(json.dumps(slim, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    # ---- text report ----
    L = []
    def p(*a):
        L.append(" ".join(str(x) for x in a))

    p("0819 用户导入分享码 全面解析")
    p("=" * 56)
    p(f"前缀: {report['prefix']}")
    p(f"formatVersion: {wrapper.get('formatVersion')}  sections: {wrapper.get('sections')}")
    p(f"顶层键: {report['top_keys']}")
    p(f"相对0815多出的键: {report['keys_only_vs_0815']}")
    p(f"相对0815缺失的键: {report['keys_only_in_0815']}")
    p(f"相对我们配置多出: {report['keys_only_vs_ours']}")
    p(f"相对我们配置缺失: {report['keys_only_in_ours']}")
    p("")
    p(f"公告文案 0819: {report['notice_0819']}")
    p(f"公告文案 0815: {report['notice_0815']}")
    p(f"公告文案 我们: {report['notice_ours']}")
    p("")
    p("【自定义货币】")
    p(json.dumps(report["coins_0819"], ensure_ascii=False, indent=2))
    p("")
    p("【标签】", report["tags_0819"])
    p("【命名空间】", report["ns_0819"])
    p("")
    p("【经济系统 全量】")
    for g, kv in groups.items():
        p(f"  -- {g} --")
        for k, v in kv.items():
            mark = ""
            if eco15.get(k) != v:
                mark = f"  <<相对0815: {eco15.get(k)!r}>>"
            p(f"    {k} = {v!r}{mark}")
    p("")
    p(f"【经济系统 vs 0815 差异条数】 {len(eco_vs_0815)}")
    for d in eco_vs_0815:
        p(f"  {d['field']}: 0815={d['0815']!r}  ->  0819={d['0819']!r}")
    p("")
    p("【击杀奖励 vs 0815】")
    p("  新增", report["kill_vs_0815"]["added"])
    p("  删除", report["kill_vs_0815"]["removed"])
    p("  改动", report["kill_vs_0815"]["changed"])
    p("  0819全量", report["kill_0819"])
    p("")
    p("【兑换商店】")
    p("  0819 recipes", len(user.get("exchangeShopData", {}).get("recipes", []) or []))
    p("  0815 recipes", len(u15.get("exchangeShopData", {}).get("recipes", []) or []))
    p("  categories", [c.get("name") for c in user.get("exchangeShopData", {}).get("categories", [])])
    p("")
    p("【抽奖相关命中】")
    for h in lottery_hits:
        p(f"  {h['path']} ({h['type']}) {h['summary']}")
    if not lottery_hits:
        p("  未发现独立奖池结构，仅 ecoSystemData 开关字段")
    p("")
    p("【商店规模】")
    p("  0819", report["shop_stats"]["count"], report["shop_stats"]["by_ns"])
    p("  按标签", report["shop_stats"]["by_tag"])
    p("  可回收", report["shop_stats"]["recycle_on"], "不可回收", report["shop_stats"]["recycle_off"])
    p("  买价0", report["shop_stats"]["zero_buy"], "卖价0", report["shop_stats"]["zero_sell"])
    p("  买价范围", report["shop_stats"]["buy_min"], "~", report["shop_stats"]["buy_max"], "中位", report["shop_stats"]["buy_median"])
    p("  回收比 中位", report["shop_stats"]["sell_ratio_median"], "均值", report["shop_stats"]["sell_ratio_mean"])
    p("")

    def dump_shop(title, d):
        p(title)
        p(f"  条目 {d['a_count']} vs {d['b_count']}")
        p(f"  命名空间 A={d['a_by_ns']}  B={d['b_by_ns']}")
        p(f"  新增 {d['added_n']}  删除 {d['removed_n']}  改动 {d['changed_n']}")
        p(f"  仅改价 {d['price_only_n']}  仅标签 {d['tag_only_n']}  仅回收 {d['recycle_only_n']}  混合 {d['mixed_n']}")
        p(f"  改动字段 {d['changed_fields']}")
        if d["added"]:
            p("  新增:")
            for x in d["added"]:
                p("   +", x)
        if d["removed"]:
            p("  删除:")
            for x in d["removed"]:
                p("   -", x)
        if d["price_changes"]:
            p("  改价(最多80):")
            for x in d["price_changes"]:
                p("   ~", x)
        if d["tag_changes"]:
            p("  改标签:")
            for x in d["tag_changes"]:
                p("   ~", x)
        if d["recycle_changes"]:
            p("  改回收:")
            for x in d["recycle_changes"]:
                p("   ~", x)
        if d["mixed_changes"]:
            p("  混合改动(最多80):")
            for x in d["mixed_changes"]:
                p("   ~", x)
        p("")

    dump_shop("【商店 vs 0815 用户上一版】", report["shop_vs_0815"])
    dump_shop("【商店 vs 0818】", report["shop_vs_0818"])
    dump_shop("【商店 vs 我们最终配置】", report["shop_vs_ours"])

    p("【其他顶层 vs 0815】")
    for d in other:
        p(f"  {d['field']}: 0815={d['0815']}  0819={d['0819']}")

    OUT_TXT.write_text("\n".join(L), encoding="utf-8")
    print("decoded", OUT_USER)
    print("shop 0819", report["shop_stats"]["count"], report["shop_stats"]["by_ns"])
    print("eco vs 0815", len(eco_vs_0815))
    print("shop vs 0815 added/removed/changed", report["shop_vs_0815"]["added_n"], report["shop_vs_0815"]["removed_n"], report["shop_vs_0815"]["changed_n"])
    print("shop vs ours added/removed/changed", report["shop_vs_ours"]["added_n"], report["shop_vs_ours"]["removed_n"], report["shop_vs_ours"]["changed_n"])
    print("lottery hits", len(lottery_hits), [h["path"] for h in lottery_hits])
    print("keys only vs 0815", report["keys_only_vs_0815"])
    print("wrapper sections", wrapper.get("sections"))
    print("written", OUT_TXT)


if __name__ == "__main__":
    main()
