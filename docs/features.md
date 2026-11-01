# What was changed in the plugin (and why)

This repo does **not** ship the plugin's source (it is third-party, unlicensed).
It ships the data files and the tooling, plus this description of every edit so
you can apply the same changes to **your own** installed copy.

Plugin: *Danbooru Tag Assassin* (`3c1b20c4-4e23-4474-b0d5-34361ab156ad`), v1.1.2,
installed from the Eagle community. All edits live in `js/plugin.js`,
`index.html`, `data/*.json`. Nothing touches the tagger side (`run.py`, venv).

---

## 1. Simplified Chinese UI (`build_zh_cn.py`)

The plugin ships `zh-TW / ja / ko / en` only.

* generate `data/i18n/zh-CN.json` from `zh-TW.json`
* generate `data/t2s.json` (Traditional → Simplified, chars + phrases) so labels
  inside `all-tags.json` can be converted at runtime without rewriting the data
* `index.html`: `lang="zh-Hans"`, static text converted, language `<select>` gets
  a `zh-CN` entry

`plugin.js` anchors:

```js
const SUPPORTED_LANGS = ['zh-CN', 'zh-TW', 'ja', 'ko', 'en'];
const DEFAULT_LANG = 'zh-CN';
```

`loadT2S()` + `toSimplified()` are loaded before `setLanguage()`, and `pickLabel()`
returns the converted label when `currentLang === 'zh-CN'` (caching into
`labels['zh-CN']` so it is not recomputed on every render).

> Gotcha found the hard way: `toSimplified()` must not call `Object.keys(t2sMap)`
> on every invocation — with ~11k labels that alone cost ~7 s of plugin start-up.
> Keep a `t2sSize` counter instead.

## 2. Tag-map panel (`topbar` button + modal)

Adds `index.html`:

```html
<button id="tagmap-btn" class="btn btn-orange-light" data-i18n="topbar.tagMap">标签映射</button>
```

and `openLocalTagMapModal()` in `plugin.js`: a searchable table of
`english tag | your label | source (manual/auto/disabled) | save | delete`,
persisted to `data/local-tag-map.json` (falls back to `localStorage` if the file
cannot be written).

## 3. Multi-language + pinyin autocomplete

The left input accepts English, Chinese, Japanese, Korean **and pinyin**:

* `ltmTagIndex()` builds `{en, zh, ja, ko, enLabel, py, pyi, pyStarts}` for every
  tag in `all-tags.json`
* `ltmSearchTags()` ranks: exact english → exact label → prefix → substring →
  pinyin (prefix at a syllable boundary first, then anywhere)
* `ltmResolveTagInput()` converts a Chinese/Japanese/Korean typed string to the
  canonical English tag when you press “添加” without picking a candidate

Pinyin needs `data/pinyin.json` (see `tools/build_pinyin.py`). Matching must be
**syllable aligned** (`pyStarts`), otherwise `yanjing` also hits `闭着眼睛`
(`bi|zhe|yan|jing`).

The dropdown itself is `position: fixed`, anchored to the focused input
(`positionSuggest()`), max 56 % of the viewport, closes on outside click / `Esc`.

## 4. Fuzzy “auto match” suggestions

`tools/…` equivalent runs inside the plugin as `openLocalTagMapModal` →「自动匹配」:

* inverted index `bigram -> [labelId]`, entries hold the label's bigram count
* score = Sørensen–Dice over the local tag's core (prefix/parenthetical/類 stripped)
* `+0.12` when one contains the other; when both sides carry parentheticals the
  score is averaged with the full-string Dice, so `白露(口袋妖怪)` does not match
  `白露(星穹铁道)`
* results are shown green (already mapped) / plain, and are applied only when you
  click「采用」 — nothing is written automatically

Index build ≈ 150 ms for 10.8k tags (43k labels); a run ≈ 100 ms.

## 5. Write-back filter: “skip unmatched tags”

In the auto-tag modal (`openTaggerModal`) a checkbox persists as
`meiax_btp_wd14_settings_v1.onlyMapped`; `WD14Tagger.writeTagsToEagleItems()`
drops every tag whose `mapTagToLocal(tag) === tag`.

## 6. Rename tracking

When a library tag is renamed, mappings must follow:

* `applyTagRenames(oldList, newList)` pairs *removed* with *added* tags whose
  library usage count is identical and unique → rewrites mapping values, saves
  the file, returns the affected keys
* `customTagSnapshot` keeps the tag list **as loaded**, because the plugin's
  “sweep empty tags” pass deletes the old name (0 items after a rename) and the
  rename would otherwise be invisible
* synced rows are highlighted red (`#ff8a8a`, `rgba(232,90,90,.10)`, badge
  `改名`) and sorted to the top until you edit them
* the scan aborts if `eagle.item.get()` comes back empty, so a not-yet-loaded
  library cannot wipe the tag table

---

## Applying this yourself

1. Install the plugin in Eagle, close Eagle.
2. `python tools/build_zh_cn.py --plugin "<plugin dir>"`
3. `python tools/build_pinyin.py --plugin "<plugin dir>"`
4. Apply the `plugin.js` / `index.html` edits described above (or use the
   `plugin-work` folder from the original patch as a reference).
5. Re-open Eagle.

Keep a copy of the original plugin folder — a plugin update overwrites all of it.
