#!/usr/bin/env python3
"""Build Simplified-Chinese assets for the Danbooru Tag Assassin Eagle plugin.

What it does (writes into the plugin's own `data/` directory):

  1. `data/i18n/zh-CN.json`  — Simplified dict generated from `zh-TW.json`
  2. `data/t2s.json`         — Traditional→Simplified mapping (chars + phrases, from OpenCC)
  3. `index.html`            — static text converted to Simplified

Usage:
    python build_zh_cn.py --plugin "%APPDATA%/Eagle/Plugins/<plugin-id>"
    python build_zh_cn.py --plugin ... --dry-run      # only report, write nothing

Requirements: opencc-python-reimplemented  (pip install opencc-python-reimplemented)
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys

try:
    from opencc import OpenCC
except ImportError:
    sys.exit("missing dependency: pip install opencc-python-reimplemented")

cc = OpenCC("t2s")

# Mainland-IT vocabulary fixes applied after character conversion.
# (OpenCC only maps characters, it does not localise Taiwan IT vocabulary.)
TERMS = [
    ("资料夹", "文件夹"), ("档案", "文件"), ("设定", "设置"), ("预设", "默认"),
    ("记忆体", "内存"), ("硬碟", "硬盘"), ("网路", "网络"), ("软体", "软件"),
    ("硬体", "硬件"), ("萤幕", "屏幕"), ("解析度", "分辨率"), ("品质", "质量"),
    ("支援", "支持"), ("选单", "菜单"), ("滑鼠", "鼠标"), ("快取", "缓存"),
    ("汇入", "导入"), ("汇出", "导出"), ("载入", "加载"), ("储存", "保存"),
    ("资料", "数据"), ("资讯", "信息"), ("物件", "对象"), ("介面", "界面"),
    ("最佳化", "优化"), ("搜寻", "搜索"), ("检视", "查看"), ("影像", "图像"),
    ("相片", "照片"), ("群组", "组"), ("专案", "项目"), ("清单", "列表"),
    ("讯息", "消息"), ("连结", "链接"), ("执行", "运行"), ("视窗", "窗口"),
    ("智慧型", "智能"), ("智慧", "智能"), ("暂存", "临时"), ("取得", "获取"),
    ("建立", "创建"), ("开启", "打开"), ("拖曳", "拖动"), ("选取", "选择"),
    ("透过", "通过"), ("张贴", "粘贴"), ("贴上", "粘贴"), ("帐号", "账号"),
    ("登入", "登录"), ("模组", "模块"), ("函式", "函数"), ("栏位", "字段"),
    ("设置档", "配置文件"), ("设定档", "配置文件"), ("日本语", "日本語"),
]

OVERRIDES = {
    "panel.search.placeholder": "输入繁体/简体中文或英文搜索（例如：领带、necktie、bow）",
}


def to_simplified(text: str) -> str:
    out = cc.convert(text)
    for a, b in TERMS:
        out = out.replace(a, b)
    return out


def build_t2s(opencc_dict_dir: str) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for name in ("TSCharacters.txt", "TSPhrases.txt"):
        path = os.path.join(opencc_dict_dir, name)
        if not os.path.exists(path):
            continue
        with io.open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or "\t" not in line:
                    continue
                src, dst = line.split("\t", 1)
                dst = dst.split(" ")[0]
                if src and dst and src != dst:
                    mapping[src] = dst
    return mapping


def load_json(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with io.open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception as e:
        print(f"skip unreadable {os.path.basename(path)}: {e}")
        return {}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plugin", required=True, help="path to the installed plugin folder")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    plugin = os.path.abspath(args.plugin)
    data = os.path.join(plugin, "data")
    i18n = os.path.join(data, "i18n")
    src_dict = os.path.join(i18n, "zh-TW.json")
    if not os.path.exists(src_dict):
        sys.exit(f"not a Danbooru Tag Assassin plugin folder: {src_dict} missing")

    # 1) t2s table (read OpenCC's own dictionary files from the installed package)
    try:
        import opencc as _opencc
        opencc_dir = os.path.dirname(os.path.abspath(_opencc.__file__))
        t2s = build_t2s(os.path.join(opencc_dir, "dictionary"))
    except Exception as e:  # pragma: no cover
        print("t2s.json: skipped:", e)
        t2s = {}
    if t2s:
        if not args.dry_run:
            with io.open(os.path.join(data, "t2s.json"), "w", encoding="utf-8", newline="\n") as f:
                json.dump(t2s, f, ensure_ascii=False, separators=(",", ":"))
        print(f"t2s.json: {len(t2s)} entries")
    else:
        print("t2s.json: skipped (vendor/opencc/dictionary not found)")

    # 2) zh-CN dictionary (base conversion + feature keys + anything you added)
    with io.open(src_dict, "r", encoding="utf-8") as f:
        tw = json.load(f)
    cn = {}
    for k, v in tw.items():
        if k == "_lang":
            cn[k] = "zh-CN"
        elif k == "_displayName":
            cn[k] = "简体中文"
        elif isinstance(v, str):
            cn[k] = OVERRIDES.get(k, to_simplified(v))
        else:
            cn[k] = v

    assets = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
    extra = load_json(os.path.join(assets, "i18n-extra.zh-CN.json"))
    cn.update(extra)                      # keys for the patched features
    existing = load_json(os.path.join(i18n, "zh-CN.json"))
    for k, v in existing.items():         # never drop keys the user added
        cn.setdefault(k, v)

    if not args.dry_run:
        with io.open(os.path.join(i18n, "zh-CN.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(cn, f, ensure_ascii=False, indent=2)
    print(f"zh-CN.json: {len(cn)} keys")

    # 3) same feature keys for the English dictionary
    en_path = os.path.join(i18n, "en.json")
    en = load_json(en_path)
    if en:
        before = len(en)
        en.update(load_json(os.path.join(assets, "i18n-extra.en.json")))
        if not args.dry_run and len(en) != before:
            with io.open(en_path, "w", encoding="utf-8", newline="\n") as f:
                json.dump(en, f, ensure_ascii=False, indent=2)
        print(f"en.json: +{len(en) - before} key(s)")

    # 3) index.html static text
    html_path = os.path.join(plugin, "index.html")
    with io.open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
    original = html
    html = html.replace('<html lang="zh-Hant">', '<html lang="zh-Hans">')
    html = re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+", lambda m: to_simplified(m.group(0)), html)
    html = re.sub(
        r'(<select id="lang-select"[^>]*>)(.*?)(</select>)',
        lambda m: m.group(1)
        + '\n                <option value="zh-CN">简体中文</option>'
        + '\n                <option value="zh-TW">繁體中文</option>'
        + '\n                <option value="ja">日本語</option>'
        + '\n                <option value="ko">한국어</option>'
        + '\n                <option value="en">English</option>\n            '
        + m.group(3),
        html, flags=re.S,
    )
    if not args.dry_run and html != original:
        with io.open(html_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(html)
    print("index.html: " + ("updated" if html != original else "already simplified"))
    if args.dry_run:
        print("(dry-run: nothing written)")


if __name__ == "__main__":
    main()
