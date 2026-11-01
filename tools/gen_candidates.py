#!/usr/bin/env python3
"""Turn the plugin's fuzzy-match suggestions into a reviewable CSV.

Runs the same scoring the in-plugin「自动匹配」panel uses (bigram similarity over
the zh/ja/ko/en labels), but offline, so you can review candidates in a
spreadsheet and hand the filled sheet back to `mapping_tool.py --csv`.

Usage:
    python gen_candidates.py --custom-tags "<library custom-tags-xxxx.json>" \
                             --plugin "<plugin dir>" --out candidates.csv --top 400

`--custom-tags` is the plugin's per-library snapshot, written when you run
「继承旧标签」; you can find it under <plugin>/data/custom-tags-*.json.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re

PREFIX = re.compile(r"^(角色|游戏|地區|地区|Artist|Coser|拍摄机构|拍攝機構|作品|画师|畫師)\s*[_：:\-]\s*", re.I)
PAREN = re.compile(r"[（(][^）)]*[）)]")
SUFFIX = re.compile(r"(類|类)$")


def bigrams(s: str) -> list[str]:
    s = s.strip().lower()
    if len(s) < 2:
        return [s] if s else []
    return [s[i:i + 2] for i in range(len(s) - 1)]


def dice(a: str, b: str) -> float:
    A, B = bigrams(a), bigrams(b)
    if not A or not B:
        return 0.0
    Bs = set(B)
    inter = sum(1 for x in A if x in Bs)
    return 2.0 * inter / (len(A) + len(B))


def core(s: str) -> str:
    return SUFFIX.sub("", PAREN.sub("", s)).strip().lower()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plugin", required=True)
    ap.add_argument("--custom-tags", required=True)
    ap.add_argument("--out", default="candidates.csv")
    ap.add_argument("--top", type=int, default=400, help="how many popular Danbooru tags to consider")
    ap.add_argument("--threshold", type=float, default=0.75)
    args = ap.parse_args()

    data = os.path.join(os.path.abspath(args.plugin), "data")
    with io.open(os.path.join(data, "all-tags.json"), encoding="utf-8") as f:
        tags = json.load(f)["tags"]
    with io.open(args.custom_tags, encoding="utf-8-sig") as f:
        local = [t["name"] for t in json.load(f)["tags"] if t.get("name")]

    # popularity (used to order the sheet by how likely a tag is to appear)
    counts = {}
    csv_counts = os.path.join(data, "wd-tag-counts.csv")
    if os.path.exists(csv_counts):
        with io.open(csv_counts, encoding="utf-8") as f:
            f.readline()
            for line in f:
                p = line.strip().split(",")
                if len(p) >= 4:
                    try:
                        counts[p[1]] = int(p[3])
                    except ValueError:
                        pass

    labels = {}
    for t in tags:
        L = t.get("labels") or {}
        labels[t["en"]] = {k: str(L.get(k) or "") for k in ("zh-TW", "ja", "ko", "en")}

    local_cores = set()
    for n in local:
        stripped = PREFIX.sub("", n).strip().lower()
        for v in {stripped, core(stripped)}:
            if v:
                local_cores.add(v)

    rows = []
    for en, L in labels.items():
        score, best = 0.0, ""
        for key in ("zh-TW", "ja", "ko", "en"):
            lab = L.get(key, "")
            if not lab:
                continue
            c = core(lab)
            for v in local_cores:
                if not v:
                    continue
                sc = dice(v, c)
                if sc > score:
                    score, best = sc, lab
        if best and score >= args.threshold:
            rows.append((en, counts.get(en, 0), best, score))

    rows.sort(key=lambda r: -r[1])
    rows = rows[: args.top]

    with io.open(args.out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["英文tag", "Danbooru热度", "命中的 label", "相似度", "你的标签(在这里填)"])
        for en, cnt, lab, sc in rows:
            w.writerow([en, cnt, lab, f"{sc:.2f}", ""])

    print(f"{len(rows)} candidate(s) -> {args.out}")


if __name__ == "__main__":
    main()
