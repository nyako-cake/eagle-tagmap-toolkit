# eagle-tagmap-toolkit

**English** | [简体中文](README.zh-CN.md)

Companion toolkit for the Eagle plugin **[Danbooru Tag Assassin](https://community-tw.eagle.cool/plugin/3c1b20c4-4e23-4474-b0d5-34361ab156ad)**
— Simplified-Chinese UI, pinyin-aware tag search, and a mapping layer that teaches
auto-tagging to write *your own* library tags instead of raw Danbooru English tags.

> This repository contains **only original scripts, generated data and notes**.
> The plugin itself is third-party work; install it from the Eagle community and
> patch your own copy (see [`docs/features.md`](docs/features.md)).

## Why

The plugin tags images with `wd-v1-4-swinv2-tagger.v3`, whose vocabulary is
Danbooru English tags (`long_hair`, `blue_eyes`, `ganyu (genshin impact)` …).
That is great for prompts, but a personal library usually has its own vocabulary
(`长发`, `绿目`, `角色_甘雨（原神）`). This toolkit builds the bridge:

```
model output ──► english tag ──► [mapping layer] ──► your tag (or keep english)
                                      ▲
                     auto (label match) + fuzzy suggestions + manual edits
```

## What's inside

| Path | Purpose |
|---|---|
| `tools/build_zh_cn.py` | generate `data/i18n/zh-CN.json`, `data/t2s.json`, and convert `index.html` to Simplified Chinese |
| `tools/build_pinyin.py` | generate `data/pinyin.json` (Han → toneless pinyin) so the tag search accepts `baifa` / `bai fa` / `bf` |
| `tools/gen_candidates.py` | offline fuzzy match → reviewable CSV of `english tag → your label` candidates |
| `tools/mapping_tool.py` | edit / import the plugin's `data/local-tag-map.json` from the CLI |
| `docs/features.md` | every code change that was made, with anchors, so you can apply it yourself |

## Quick start

```bash
pip install opencc-python-reimplemented pypinyin

PLUGIN="%APPDATA%/Eagle/Plugins/3c1b20c4-4e23-4474-b0d5-34361ab156ad"

python tools/build_zh_cn.py --plugin "$PLUGIN"     # Simplified UI + t2s table
python tools/build_pinyin.py --plugin "$PLUGIN"    # pinyin table

# review candidates, fill the last column, then import
python tools/gen_candidates.py --plugin "$PLUGIN" \
       --custom-tags "$PLUGIN/data/custom-tags-xxxx.json" --out candidates.csv
python tools/mapping_tool.py --plugin "$PLUGIN" --csv candidates.csv

python tools/mapping_tool.py --plugin "$PLUGIN" --add "white hair=白发"
python tools/mapping_tool.py --plugin "$PLUGIN" --list
```

Re-open the plugin window afterwards (or press 重新载入).

> `custom-tags-*.json` appears after you run the plugin's **继承旧标签** once for a
> library — it is the plugin's own per-library snapshot of your tags.

## Mapping file format

`<plugin>/data/local-tag-map.json`:

```json
{
  "_comment": "english Danbooru tag -> your own tag",
  "white hair": "白发",
  "green eyes": "绿目",
  "ponytail": "单马尾",
  "smile": ""
}
```

* keys are case-insensitive, `_` and space are equivalent, `\(` escapes are ignored
* an empty value (`""`) means **disable** that mapping — keep the English tag
* the manual layer always wins over the automatic one

## Notes / limits

* English tag → one local tag; no one-to-many.
* Renames are detected by matching removed/added tags with the same library usage
  count — if the count changed, the sync reports it instead of guessing.
* A plugin update overwrites `js/`, `index.html` and `data/`; keep a backup of the
  patched folder and your `local-tag-map.json`.
* Tested on Windows with Eagle 4.x. macOS/Linux should work, the paths differ.

## Credits & licence

* Plugin by **KiraraCape-変色君** (Eagle community) — not included here.
* Traditional→Simplified conversion powered by [OpenCC](https://github.com/BYVoid/OpenCC) (Apache-2.0).
* Pinyin data generated with [pypinyin](https://github.com/mozillazg/python-pinyin) (MIT).
* This toolkit: MIT, see [LICENSE](LICENSE).
