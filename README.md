# 麦设（mai-profile）

一个更加灵活的麦麦人设扩展

![Version](https://img.shields.io/badge/version-0.2.0-brightgreen)
![MaiBot](https://img.shields.io/badge/MaiBot-1.4.8%2B-2f81f7)
![SDK](https://img.shields.io/badge/SDK-2.23.0-0e8a16)
![Python](https://img.shields.io/badge/Python-3.12%2B-3776ab)
![Standalone](https://img.shields.io/badge/独立运行-支持-blue)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

## 功能介绍

- **按需加载设定**：人设条目不会整段常驻上下文，只有在聊到相关关键词或模型调用工具核对时才会读取。
- **未设定保护**：被问到档案里未填写的内容时，会提醒模型不要现场编造具体细节，而是自然带过。
- **分级公开控制**：支持 `public`（直接可答）、`shy`（按追问进度分阶段松口，支持模糊线索）与 `private`（绝不传给模型）三种公开方式。
- **双模式编辑**：支持分栏填写（`structured`）和整段文本（`freeform`）两种模式；作息习惯字段可被 `mai-day` 读取。

## 如何使用

1. 将 `mai-profile/` 放到 MaiBot 的 `plugins/` 目录并重启宿主，在 WebUI 打开 **麦设** 配置页。
2. 在 **基础设定** 中添加公开设定（如城市、专业），并填写 **作息习惯** 与 **喜好雷区**。
3. 需要保密或逐步透露的内容可放在 **保密设定** 中，将公开方式设为 `shy` 或 `private` 后保存即可。

<details>
<summary>config.toml 配置示例</summary>

```toml
enabled = true
mode = "structured"                                 # structured 分栏 | freeform 纯文本
routine_note = "平时一点前睡，上午没课会多睡一会"     # 可供 mai-day 读取
likes_and_dislikes = "喜欢喝冰美式，不吃香菜"

[[basic_fields]]
key = "城市"
value = "某南方城市"
disclosure = "public"
topics = ["哪里人", "住哪"]

[[guarded_entries]]
key = "感情状况"
value = "暂时没有对象"
disclosure = "shy"
resistance = "medium"                               # low / medium / high
teaser = "有在意的人，但还不想直说"
topics = ["对象", "恋爱", "男朋友", "女朋友"]

[[trigger_rules]]
topic = "哪里人"
words = ["老家", "哪里人", "在哪个城市"]
```

</details>

## 配置说明

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `enabled` | `true` | 插件总开关，关闭后停止注入提示并禁用查询工具 |
| `mode` | `"structured"` | 选择 `structured`（分栏填表）或 `freeform`（整段正文） |
| `basic_fields` | `[]` | 基础公开设定，支持按条目单独配置公开方式与关联话题 |
| `routine_note` | `""` | 日常作息描述，与 `mai-day` 联动时用于每日日程参考 |
| `guarded_entries` | `[]` | 存放 `shy` 或 `private` 类设定；不填 `teaser` 时不会提前泄露内容 |
| `half_life_minutes` | `30` | 高级设置：无人继续追问时，已累积追问进度的半衰期（分钟） |
| `private_multiplier` | `1.2` | 高级设置：私聊追问相对于群聊的进度倍率 |
| `unset_policy` | 内置中文提示 | 高级设置：遇到未设定话题时给模型的回复引导 |

## 命令与工具

| 类别 | 名称 | 说明 |
|---|---|---|
| 对话工具 | `query_self_profile(topic="")` | 让模型按话题查询人设档案、喜好和作息（仅读取，不推进追问进度） |
| 联动 API | `get_snapshot(topic, stream_id, user_id)` | 供其他插件读取公开设定与作息，不返回 `private` 条目 |
| WebUI 面板 | `运行状态与生效范围` | 显示公开/保密条目数量以及各会话当前的追问进度阶段 |
| WebUI 按钮 | `重置追问进度` / `刷新公共集合缓存` | 将所有会话的 `shy` 追问进度重置回初始状态 |

<details>
<summary>开发与自检</summary>

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r .github/requirements-ci.txt
.venv/bin/python scripts/check.py
```

</details>
