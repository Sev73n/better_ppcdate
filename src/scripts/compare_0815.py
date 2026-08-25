# -*- coding: utf-8 -*-
"""Decode 0815 user share and diff against latest generated config."""
import base64
import json
import zlib
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(r"C:/Users/AI10/Desktop/ppcdata")
USER_SHARE = ROOT / "06_用户自行导入" / "0815.txt"
OURS_JSON = ROOT / "01_配置明文" / "最终配置_rebuilt.json"
OUT_USER = ROOT / "01_配置明文" / "0815_decoded.json"
OUT_REPORT = ROOT / "03_对比报告" / "0815_vs_最新生成.json"
OUT_TXT = ROOT / "03_对比报告" / "0815_vs_最新生成.txt"


def decode_share(s: str):
    s = s.strip()
    if "%" in s[:20]:
        s = s.split("%", 1)[1]
    pad = (-len(s)) % 4
    raw = base64.b64decode(s + "=" * pad)
    return json.loads(zlib.decompress(raw).decode("utf-8"))


def item_id(row, rev):
    nin = row[0].get("NIN", "")
    pref, name = nin.split(":", 1) if ":" in nin else ("", nin)
    ns = rev.get(pref, pref)
    dur = row[0].get("durability", 0)
    count = row[0].get("count", 1)
    return f"{ns}:{name}|d{dur}|c{count}"


def short_name(row, rev):
    nin = row[0].get("NIN", "")
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
        "extra11": row[11] if len(row) > 11 else None,
        "stack": row[12] if len(row) > 12 else None,
        "extra13": row[13] if len(row) > 13 else None,
        "extra14": row[14] if len(row) > 14 else None,
        "extra15": row[15] if len(row) > 15 else None,
        "durability": item.get("durability", 0),
        "count": item.get("count", 1),
        "modEnchantData": item.get("modEnchantData"),
        "itemKeys": sorted(item.keys()),
    }


def flatten(obj, prefix=""):
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{prefix}.{k}" if prefix else k
            if isinstance(v, (dict, list)) and not (
                isinstance(v, list) and v and not isinstance(v[0], (dict, list))
            ):
                if isinstance(v, list) and k in ("systemShopItems",):
                    continue
                out.update(flatten(v, p))
            else:
                out[p] = v
    elif isinstance(obj, list):
        out[prefix] = obj
    else:
        out[prefix] = obj
    return out


def main():
    user_raw = decode_share(USER_SHARE.read_text(encoding="utf-8"))
    OUT_USER.write_text(
        json.dumps(user_raw, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    wrapper = {}
    if isinstance(user_raw, dict) and "data" in user_raw and "formatVersion" in user_raw:
        wrapper = {
            "formatVersion": user_raw.get("formatVersion"),
            "sections": user_raw.get("sections"),
            "extra_keys": sorted(set(user_raw) - {"data", "formatVersion", "sections"}),
        }
        user = user_raw["data"]
    else:
        user = user_raw
    ours = json.loads(OURS_JSON.read_text(encoding="utf-8"))

    user_rev = {str(v): k for k, v in user.get("nameSpaceMap", {}).items()}
    ours_rev = {str(v): k for k, v in ours.get("nameSpaceMap", {}).items()}

    report = {
        "user_prefix": USER_SHARE.read_text(encoding="utf-8")[:12],
        "wrapper": wrapper,
        "user_top_keys": list(user.keys()),
        "ours_top_keys": list(ours.keys()),
        "keys_only_user": sorted(set(user) - set(ours)),
        "keys_only_ours": sorted(set(ours) - set(user)),
    }

    # eco / tags / coins / ns
    eco_diffs = []
    u_eco = user.get("ecoSystemData", {})
    o_eco = ours.get("ecoSystemData", {})
    for k in sorted(set(u_eco) | set(o_eco)):
        if u_eco.get(k) != o_eco.get(k):
            eco_diffs.append({"field": k, "ours": o_eco.get(k), "user": u_eco.get(k)})
    report["eco_diffs"] = eco_diffs

    report["tags_only_user"] = sorted(
        set(user.get("customItemTags", [])) - set(ours.get("customItemTags", []))
    )
    report["tags_only_ours"] = sorted(
        set(ours.get("customItemTags", [])) - set(user.get("customItemTags", []))
    )
    report["type_map_only_user"] = sorted(
        set(user.get("customItemTypeMap", {})) - set(ours.get("customItemTypeMap", {}))
    )
    report["type_map_only_ours"] = sorted(
        set(ours.get("customItemTypeMap", {})) - set(user.get("customItemTypeMap", {}))
    )
    report["ns_user"] = user.get("nameSpaceMap", {})
    report["ns_ours"] = ours.get("nameSpaceMap", {})
    report["coins_user"] = user.get("customCoinTypes", [])
    report["coins_ours"] = ours.get("customCoinTypes", [])
    report["kill_user"] = user.get("killEntityRewardMap", {})
    report["kill_ours"] = ours.get("killEntityRewardMap", {})

    # shop items
    u_items = user.get("systemShopItems", [])
    o_items = ours.get("systemShopItems", [])
    u_map = {}
    o_map = {}
    u_dups = []
    o_dups = []
    for r in u_items:
        k = item_id(r, user_rev)
        if k in u_map:
            u_dups.append(k)
        u_map[k] = r
    for r in o_items:
        k = item_id(r, ours_rev)
        if k in o_map:
            o_dups.append(k)
        o_map[k] = r

    added = sorted(set(u_map) - set(o_map))
    removed = sorted(set(o_map) - set(u_map))
    common = sorted(set(u_map) & set(o_map))

    changed = []
    for k in common:
        uf, of = shop_fields(u_map[k]), shop_fields(o_map[k])
        diffs = {f: {"ours": of[f], "user": uf[f]} for f in uf if uf[f] != of[f]}
        if diffs:
            changed.append({"id": k, "name": short_name(u_map[k], user_rev), "diffs": diffs})

    # classify added/removed by namespace
    def ns_of(key):
        return key.split(":", 1)[0]

    added_by_ns = Counter(ns_of(k) for k in added)
    removed_by_ns = Counter(ns_of(k) for k in removed)
    changed_by_ns = Counter(c["name"].split(":")[0] for c in changed)
    changed_fields = Counter()
    for c in changed:
        for f in c["diffs"]:
            changed_fields[f] += 1

    # price-only vs tag-only vs other
    price_only = []
    tag_only = []
    recycle_only = []
    mixed = []
    for c in changed:
        keys = set(c["diffs"])
        if keys <= {"buy", "sell"}:
            price_only.append(c)
        elif keys <= {"tag"}:
            tag_only.append(c)
        elif keys <= {"recycle"}:
            recycle_only.append(c)
        else:
            mixed.append(c)

    def brief_row(k, row, rev):
        f = shop_fields(row)
        return {
            "id": k,
            "name": short_name(row, rev),
            "buy": f["buy"],
            "sell": f["sell"],
            "tag": f["tag"],
            "recycle": f["recycle"],
            "durability": f["durability"],
            "count": f["count"],
        }

    added_rows = [brief_row(k, u_map[k], user_rev) for k in added]
    removed_rows = [brief_row(k, o_map[k], ours_rev) for k in removed]

    # counts by ns
    def count_ns(items, rev):
        c = Counter()
        for r in items:
            nin = r[0].get("NIN", "")
            pref = nin.split(":", 1)[0]
            c[rev.get(pref, pref)] += 1
        return dict(c)

    report["shop"] = {
        "user_count": len(u_items),
        "ours_count": len(o_items),
        "user_by_ns": count_ns(u_items, user_rev),
        "ours_by_ns": count_ns(o_items, ours_rev),
        "added": len(added),
        "removed": len(removed),
        "changed": len(changed),
        "unchanged": len(common) - len(changed),
        "user_dups": u_dups,
        "ours_dups": o_dups,
        "added_by_ns": dict(added_by_ns),
        "removed_by_ns": dict(removed_by_ns),
        "changed_by_ns": dict(changed_by_ns),
        "changed_fields": dict(changed_fields),
        "price_only": len(price_only),
        "tag_only": len(tag_only),
        "recycle_only": len(recycle_only),
        "mixed": len(mixed),
    }
    report["added_items"] = added_rows
    report["removed_items"] = removed_rows
    report["price_changes"] = [
        {
            "id": c["id"],
            "name": c["name"],
            "ours_buy": c["diffs"].get("buy", {}).get("ours", shop_fields(o_map[c["id"]])["buy"]),
            "user_buy": c["diffs"].get("buy", {}).get("user", shop_fields(u_map[c["id"]])["buy"]),
            "ours_sell": c["diffs"].get("sell", {}).get("ours", shop_fields(o_map[c["id"]])["sell"]),
            "user_sell": c["diffs"].get("sell", {}).get("user", shop_fields(u_map[c["id"]])["sell"]),
            "fields": list(c["diffs"]),
        }
        for c in price_only
    ]
    report["tag_changes"] = [
        {
            "name": c["name"],
            "ours": c["diffs"]["tag"]["ours"],
            "user": c["diffs"]["tag"]["user"],
        }
        for c in tag_only
    ]
    report["recycle_changes"] = [
        {
            "name": c["name"],
            "ours": c["diffs"]["recycle"]["ours"],
            "user": c["diffs"]["recycle"]["user"],
        }
        for c in recycle_only
    ]
    report["mixed_changes"] = [
        {
            "name": c["name"],
            "diffs": {k: v for k, v in c["diffs"].items()},
        }
        for c in mixed
    ]

    # other top-level scalar diffs
    other = []
    for k in set(user) & set(ours):
        if k in ("systemShopItems", "ecoSystemData", "customItemTags", "customItemTypeMap", "nameSpaceMap", "customCoinTypes", "killEntityRewardMap"):
            continue
        if user[k] != ours[k]:
            other.append({"field": k, "ours": ours[k], "user": user[k]})
    report["other_top_diffs"] = other

    # type map value diffs
    tm_diffs = []
    for k in set(user.get("customItemTypeMap", {})) & set(ours.get("customItemTypeMap", {})):
        if user["customItemTypeMap"][k] != ours["customItemTypeMap"][k]:
            tm_diffs.append(
                {
                    "tag": k,
                    "ours": ours["customItemTypeMap"][k],
                    "user": user["customItemTypeMap"][k],
                }
            )
    report["type_map_value_diffs"] = tm_diffs

    OUT_REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = []
    lines.append("0815 用户导入 vs 最新生成")
    lines.append("=" * 48)
    lines.append(f"用户前缀: {report['user_prefix']}")
    lines.append(f"用户条目: {len(u_items)}  我们: {len(o_items)}")
    lines.append(f"用户按命名空间: {report['shop']['user_by_ns']}")
    lines.append(f"我们按命名空间: {report['shop']['ours_by_ns']}")
    lines.append("")
    lines.append(f"新增 {len(added)}  删除 {len(removed)}  改动 {len(changed)}  未变 {len(common)-len(changed)}")
    lines.append(f"  仅改价 {len(price_only)}  仅改标签 {len(tag_only)}  仅改回收 {len(recycle_only)}  混合 {len(mixed)}")
    lines.append(f"改动字段: {dict(changed_fields)}")
    lines.append("")
    lines.append("【经济系统差异】")
    for d in eco_diffs:
        lines.append(f"  {d['field']}: 我们={d['ours']!r}  用户={d['user']!r}")
    if not eco_diffs:
        lines.append("  无")
    lines.append("")
    lines.append("【标签】")
    lines.append(f"  用户多: {report['tags_only_user']}")
    lines.append(f"  我们多: {report['tags_only_ours']}")
    lines.append("")
    lines.append("【新增物品】")
    for r in added_rows:
        lines.append(
            f"  + {r['name']:50} buy={r['buy']} sell={r['sell']} tag={r['tag']} rec={r['recycle']} d={r['durability']} c={r['count']}"
        )
    lines.append("")
    lines.append("【删除物品】")
    for r in removed_rows:
        lines.append(
            f"  - {r['name']:50} buy={r['buy']} sell={r['sell']} tag={r['tag']} rec={r['recycle']} d={r['durability']} c={r['count']}"
        )
    lines.append("")
    lines.append("【仅改价】")
    for c in report["price_changes"]:
        lines.append(
            f"  ~ {c['name']:50} buy {c['ours_buy']}->{c['user_buy']}  sell {c['ours_sell']}->{c['user_sell']}"
        )
    lines.append("")
    lines.append("【仅改标签】")
    for c in report["tag_changes"]:
        lines.append(f"  ~ {c['name']:50} {c['ours']} -> {c['user']}")
    lines.append("")
    lines.append("【仅改回收】")
    for c in report["recycle_changes"]:
        lines.append(f"  ~ {c['name']:50} {c['ours']} -> {c['user']}")
    lines.append("")
    lines.append("【混合改动】")
    for c in report["mixed_changes"]:
        parts = []
        for f, v in c["diffs"].items():
            parts.append(f"{f}:{v['ours']}->{v['user']}")
        lines.append(f"  ~ {c['name']:50} {'; '.join(parts)}")
    lines.append("")
    lines.append("【其他顶层】")
    for d in other:
        lines.append(f"  {d['field']}")
    lines.append(f"类型图仅用户: {report['type_map_only_user']}")
    lines.append(f"类型图仅我们: {report['type_map_only_ours']}")
    lines.append(f"类型图值差异: {len(tm_diffs)}")
    for d in tm_diffs:
        lines.append(f"  {d['tag']}: {d['ours']} -> {d['user']}")

    OUT_TXT.write_text("\n".join(lines), encoding="utf-8")
    print("added", len(added), "removed", len(removed), "changed", len(changed))
    print("price_only", len(price_only), "tag_only", len(tag_only), "recycle_only", len(recycle_only), "mixed", len(mixed))
    print("eco_diffs", len(eco_diffs))
    print("keys_only_user", report["keys_only_user"])
    print("keys_only_ours", report["keys_only_ours"])
    print("wrapper", wrapper)
    print("written", str(OUT_TXT))


if __name__ == "__main__":
    main()
