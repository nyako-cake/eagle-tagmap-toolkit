# eagle-tagmap-toolkit

[English](README.md) | **简体中文**

给 Eagle 插件 **[Danbooru Tag Assassin](https://community-tw.eagle.cool/plugin/3c1b20c4-4e23-4474-b0d5-34361ab156ad)** 配的一套外围工具：
简体中文界面、支持拼音的标签搜索，以及一层「标签映射」，让自动打标写回的是**你自己图库的标签**，
而不是原始的 Danbooru 英文标签。

> 本仓库只包含**原创脚本、生成的数据和说明文档**。
> 插件本体是第三方作品，请自行从 Eagle 社区安装，然后按 [`docs/features.md`](docs/features.md) 打补丁。

## 为什么需要它

插件用 `wd-v1-4-swinv2-tagger.v3` 打标，词表是 Danbooru 的英文标签（`long_hair`、`blue_eyes`、
`ganyu (genshin impact)` …）。拿去当提示词很好用，但个人图库通常有自己的词汇体系
（`长发`、`绿目`、`角色_甘雨（原神）`）。这套工具负责搭桥：

```
模型输出 ──► 英文 tag ──► [映射层] ──► 你的标签（或保留英文）
                              ▲
                自动（中文名匹配）+ 模糊建议 + 手工编辑
```

## 目录

| 路径 | 用途 |
|---|---|
| `tools/build_zh_cn.py` | 生成 `data/i18n/zh-CN.json`、`data/t2s.json`，并把 `index.html` 转成简体 |
| `tools/build_pinyin.py` | 生成 `data/pinyin.json`（汉字 → 无调拼音），让标签搜索支持 `baifa` / `bai fa` / `bf` |
| `tools/gen_candidates.py` | 离线跑模糊匹配，导出可审阅的 `英文 tag → 你的标签` 候选表 |
| `tools/mapping_tool.py` | 命令行增删改插件的 `data/local-tag-map.json` |
| `docs/features.md` | 本次对插件的全部改动，含代码锚点和踩过的坑 |

## 快速开始

```bash
pip install opencc-python-reimplemented pypinyin

PLUGIN="%APPDATA%/Eagle/Plugins/3c1b20c4-4e23-4474-b0d5-34361ab156ad"

python tools/build_zh_cn.py --plugin "$PLUGIN"     # 简体界面 + 繁简对照表
python tools/build_pinyin.py --plugin "$PLUGIN"    # 拼音表

# 先看候选，在最后一列填好，再导入
python tools/gen_candidates.py --plugin "$PLUGIN" \
       --custom-tags "$PLUGIN/data/custom-tags-xxxx.json" --out candidates.csv
python tools/mapping_tool.py --plugin "$PLUGIN" --csv candidates.csv

python tools/mapping_tool.py --plugin "$PLUGIN" --add "white hair=白发"
python tools/mapping_tool.py --plugin "$PLUGIN" --list
```

改完重开插件窗口（或点插件里的「重新载入」）。

> `custom-tags-*.json` 是插件自己按图库生成的快照，跑过一次「继承旧标签」就会出现在
> `<plugin>/data/` 下。

## 映射文件格式

`<plugin>/data/local-tag-map.json`：

```json
{
  "_comment": "英文 Danbooru tag -> 你自己的标签",
  "white hair": "白发",
  "green eyes": "绿目",
  "ponytail": "单马尾",
  "smile": ""
}
```

- key 大小写不敏感，`_` 与空格等价，`\(` 转义会被忽略
- 值为空字符串（`""`）表示**停用**该条映射，保留英文
- 手写映射永远优先于自动映射

## 依赖（全部需自行安装，本仓库一概不打包）

| 组件 | 来源 | 许可 |
|---|---|---|
| **Danbooru Tag Assassin**（Eagle 插件本体） | Eagle 社区插件页 | 未声明 —— 按「保留所有权利」对待，只能给自己已安装的副本打补丁 |
| **corkborg/wd14-tagger-standalone**（真正跑模型的 Python/ONNX CLI） | https://github.com/corkborg/wd14-tagger-standalone | 仓库未声明许可 —— 请从上游获取，不要二次打包 |
| **SmilingWolf/wd-swinv2-tagger-v3**（ONNX 权重 + 标签表） | HuggingFace 模型仓库 | 分发前请看模型卡上的许可 |

插件的自动打标面板里填的「Tagger 路径」就是 `…/wd14-tagger-standalone` 这个目录；
模型权重首次运行时会自动下载到 HuggingFace 缓存目录。

## 注意 / 限制

- 一个英文 tag 只能映射到一个本地标签，不支持一变多
- 改名同步靠「消失的名字 + 新增的名字 + 图库使用次数相同且唯一」来判定；次数变了会提示而不猜
- 插件更新会覆盖 `js/`、`index.html`、`data/`，请备份打好补丁的文件夹和你的 `local-tag-map.json`
- 在 Windows + Eagle 4.x 上验证通过；macOS / Linux 应该可用，但路径写法不同

## 致谢与许可

- 插件作者 **KiraraCape-変色君**（Eagle 社区），源码不在本仓库
- 繁简转换使用 [OpenCC](https://github.com/BYVoid/OpenCC)（Apache-2.0）
- 拼音数据由 [pypinyin](https://github.com/mozillazg/python-pinyin)（MIT）生成
- 本套工具：MIT，见 [LICENSE](LICENSE)
