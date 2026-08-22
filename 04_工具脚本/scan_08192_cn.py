# -*- coding: utf-8 -*-
import base64, json, zlib
from pathlib import Path

src = Path(r"C:/Users/AI10/Desktop/ppcdata/06_用户自行导入/08192.txt")
out = Path(r"C:/Users/AI10/Desktop/ppcdata/03_对比报告/08192_shop_names.txt")
s = src.read_text(encoding="utf-8").strip()
if "%" in s[:20]:
    s = s.split("%", 1)[1]
raw = json.loads(zlib.decompress(base64.b64decode(s + "=" * 4)))
data = raw["data"] if "data" in raw else raw
rev = {str(v): k for k, v in data.get("nameSpaceMap", {}).items()}

lines = []
hits = []
needles = ("膏", "戒", "项链", "项鍊", "链", "娘", "多彩", "花膏", "戒指", "饰品", "首饰")

for i, r in enumerate(data["systemShopItems"]):
    item = r[0]
    nin = item.get("NIN", "")
    pref, name = nin.split(":", 1) if ":" in nin else ("", nin)
    ns = rev.get(pref, pref)
    extras = {
        "r3": r[3],
        "r6tag": r[6],
        "r8": r[8],
        "r9": r[9],
        "NAV": item.get("NAV"),
    }
    blob = json.dumps(extras, ensure_ascii=False)
    line = f"{i:4} {ns}:{name:40} buy={r[1]} sell={r[2]} {blob}"
    lines.append(line)
    text = f"{ns}:{name} {blob}"
    if any(n in text for n in needles) or any(n in name.lower() for n in ("ring", "neck", "cream", "paste", "gao", "oint")):
        hits.append(line)

# also print unique r8/r9 values
r8s = sorted({r[8] for r in data["systemShopItems"]})
r9s = sorted({r[9] for r in data["systemShopItems"]})
r3s = sorted({str(r[3]) for r in data["systemShopItems"] if r[3]})

header = []
header.append("unique r8: " + json.dumps(r8s, ensure_ascii=False))
header.append("unique r9: " + json.dumps(r9s, ensure_ascii=False))
header.append("nonempty r3 count " + str(len(r3s)))
header.append("nonempty r3 sample " + json.dumps(r3s[:30], ensure_ascii=False))
header.append("HITS " + str(len(hits)))
header.append("---HITS---")
header.extend(hits)
header.append("---ALL NAV nonempty---")
for r in data["systemShopItems"]:
    if r[0].get("NAV"):
        nin = r[0].get("NIN")
        header.append(f"{nin} NAV={r[0].get('NAV')} buy={r[1]} sell={r[2]}")

out.write_text("\n".join(header + ["", "---ALL---"] + lines), encoding="utf-8")
print("wrote", out)
print("hits", len(hits))
for h in hits:
    print(h)
print("r8", r8s)
print("r9", r9s)
print("r3 nonempty", len(r3s), r3s[:20])
