#!/usr/bin/env python3
"""Merge hand-written tag mappings into the plugin's `data/local-tag-map.json`.

The plugin maps Danbooru tags (English) to your own library tags when auto-tagging.
This tool edits that mapping file without touching the plugin code.

Everyday use:

    python mapping_tool.py --plugin "<plugin dir>" --list
    python mapping_tool.py --plugin "<plugin dir>" --add "white hair=白发"
    python mapping_tool.py --plugin "<plugin dir>" --csv candidates.csv

The CSV needs at least a column `英文tag` (English tag) and `你的标签(在这里填)`
(the label you want to map to); other columns are ignored.

A `.bak` copy of the previous file is written next to it on every save.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import shutil

DEFAULT_PLUGIN_ID = "3c1b20c4-4e23-4474-b0d5-34361ab156ad"   # Danbooru Tag Assassin


def default_plugin_dir() -> str:
    base = os.path.join(os.environ.get("APPDATA", ""), "Eagle", "Plugins", DEFAULT_PLUGIN_ID)
    return base


def map_path(plugin: str) -> str:
    return os.path.join(plugin, "data", "local-tag-map.json")


def load_map(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with io.open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def save_map(path: str, mapping: dict) -> None:
    if os.path.exists(path):
        shutil.copyfile(path, path + ".bak")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plugin", default=default_plugin_dir(), help="installed plugin folder")
    ap.add_argument("--csv", help="candidate sheet with filled-in mappings")
    ap.add_argument("--add", action="append", default=[], help='single mapping: "english tag=your label"')
    ap.add_argument("--out", help="write to another file instead of the plugin's map")
    ap.add_argument("--list", action="store_true", help="print current mappings only")
    args = ap.parse_args()

    path = args.out or map_path(args.plugin)
    mapping = load_map(path)

    if args.list:
        rows = {k: v for k, v in mapping.items() if not k.startswith("_")}
        for k, v in sorted(rows.items()):
            print(f"{k}  ->  {v}")
        print(f"\n{len(rows)} mapping(s) in {path}")
        return

    added = 0
    if args.csv:
        with io.open(args.csv, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                en = (row.get("英文tag") or row.get("english") or "").strip()
                local = (row.get("你的标签(在这里填)") or row.get("你的标签") or row.get("label") or "").strip()
                if not en or not local or en.startswith("#"):
                    continue
                mapping[en] = local
                added += 1

    for pair in args.add:
        if "=" not in pair:
            print("skipped (expected english tag=your label):", pair)
            continue
        en, local = pair.split("=", 1)
        en, local = en.strip(), local.strip()
        if en and local:
            mapping[en] = local
            added += 1

    if added == 0 and not args.csv:
        print("nothing to add; use --add / --csv, or --list to inspect")
        return

    save_map(path, mapping)
    total = len([k for k in mapping if not k.startswith("_")])
    print(f"wrote {path}")
    print(f"added/updated {added}, total {total}")
    print("reload the plugin window (or press 重新载入) to apply")


if __name__ == "__main__":
    main()
