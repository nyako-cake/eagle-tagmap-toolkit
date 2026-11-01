#!/usr/bin/env python3
"""Generate `data/pinyin.json` (Han char -> toneless pinyin) for the tag-map search.

The plugin's tag-map autocomplete can match pinyin (full / spaced / initials),
but it needs a per-character lookup table. This script builds it from the
Chinese labels that actually exist in the plugin's `all-tags.json`, plus the
simplified forms the UI displays, so the table stays small (~40 KB).

Usage:
    python build_pinyin.py --plugin "%APPDATA%/Eagle/Plugins/<plugin-id>"

Requirements: pypinyin  (pip install pypinyin)
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys

try:
    from pypinyin import lazy_pinyin
except ImportError:
    sys.exit("missing dependency: pip install pypinyin")


def to_simplified_loader(t2s_path: str):
    if not os.path.exists(t2s_path):
        return lambda s: s
    with io.open(t2s_path, encoding="utf-8") as f:
        table = json.load(f)
    maxlen = max(len(k) for k in table)

    def conv(s: str) -> str:
        out, i, n = [], 0, len(s)
        while i < n:
            for ln in range(min(maxlen, n - i), 1, -1):
                hit = table.get(s[i:i + ln])
                if hit:
                    out.append(hit)
                    i += ln
                    break
            else:
                out.append(table.get(s[i], s[i]))
                i += 1
        return "".join(out)

    return conv


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plugin", required=True, help="path to the installed plugin folder")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data = os.path.join(os.path.abspath(args.plugin), "data")
    tags_path = os.path.join(data, "all-tags.json")
    if not os.path.exists(tags_path):
        sys.exit(f"missing {tags_path}")

    with io.open(tags_path, encoding="utf-8") as f:
        tags = json.load(f)["tags"]

    conv = to_simplified_loader(os.path.join(data, "t2s.json"))

    chars: set[str] = set()
    for t in tags:
        for key in ("zh-TW", "ja", "ko"):
            raw = (t.get("labels") or {}).get(key)
            if not raw:
                continue
            text = conv(str(raw)) if key == "zh-TW" else str(raw)
            for ch in str(raw) + text:
                if "\u4e00" <= ch <= "\u9fff":
                    chars.add(ch)

    # also cover part labels used by the body-diagram panels
    for name in ("composition.json", "associations.json", "config-female.json", "config-male.json"):
        p = os.path.join(data, name)
        if not os.path.exists(p):
            continue
        with io.open(p, encoding="utf-8") as f:
            for ch in f.read():
                if "\u4e00" <= ch <= "\u9fff":
                    chars.add(ch)

    table = {}
    for ch in sorted(chars):
        py = lazy_pinyin(ch)
        if py and py[0]:
            table[ch] = py[0].lower()

    dest = os.path.join(data, "pinyin.json")
    if not args.dry_run:
        with io.open(dest, "w", encoding="utf-8", newline="\n") as f:
            json.dump(table, f, ensure_ascii=False, separators=(",", ":"))
    print(f"pinyin.json: {len(table)} chars -> {dest}" if not args.dry_run
          else f"pinyin.json: {len(table)} chars (dry-run, not written)")


if __name__ == "__main__":
    main()
