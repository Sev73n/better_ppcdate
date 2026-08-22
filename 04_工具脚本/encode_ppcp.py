# -*- coding: utf-8 -*-
"""Encode/decode 泼皮工作室 更好的经济系统 (ppcp) share strings."""
import base64, zlib, json, sys
from pathlib import Path

PREFIX = "ppcpdata%"

def decode(s: str) -> dict:
    s = s.strip()
    if s.startswith(PREFIX):
        s = s[len(PREFIX):]
    pad = (-len(s)) % 4
    raw = base64.b64decode(s + "=" * pad)
    text = zlib.decompress(raw).decode("utf-8")
    return json.loads(text)

def encode(obj) -> str:
    text = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    # note: original may use different json formatting; compact is usually fine
    compressed = zlib.compress(text.encode("utf-8"), level=9)
    b64 = base64.b64encode(compressed).decode("ascii")
    return PREFIX + b64

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python encode_ppcp.py decode <share.txt> <out.json>")
        print("  python encode_ppcp.py encode <in.json> <out_share.txt>")
        sys.exit(1)
    cmd, src, dst = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    if cmd == "decode":
        data = decode(src.read_text(encoding="utf-8"))
        dst.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"decoded -> {dst}")
    elif cmd == "encode":
        data = json.loads(src.read_text(encoding="utf-8"))
        dst.write_text(encode(data), encoding="utf-8")
        print(f"encoded -> {dst}")
    else:
        sys.exit("unknown command")
