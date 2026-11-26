<div align="center">

# 麦设 · `zeyr.mai-profile`

**让 Bot 有稳定的客观设定的同时，学会“没记过就含糊带过，秘密被缠着问才松口”**

![Version](https://img.shields.io/badge/version-0.2.0-brightgreen)
![MaiBot](https://img.shields.io/badge/MaiBot-1.4.8%2B-2f81f7)
![SDK](https://img.shields.io/badge/SDK-2.23.0-0e8a16)
![Standalone](https://img.shields.io/badge/独立运行-支持-blue)

[为什么用它](#为什么用它) · [3 步快速开始](#3-步快速开始) · [配置项说明](#常用配置项说明) · [工具与控制台](#工具接口与控制台) · [FAQ](#常见疑问)

</div>

---

## 为什么用它

| 常见问题 | 传统写法（全塞进人设 Prompt） | **麦设（`zeyr.mai-profile`）** |
|---|---|---|
| 闲聊时一惊一乍 | 设定全天候常驻上下文，动不动触发“自我介绍腔” | **平时 0 字数占用**，只有撞见关键词或模型需要核对时才带出 |
| 问到没写过的细节 | 大模型现场自由发挥，昨天说养猫今天说住校自相矛盾 | 查不到时明确返回“未设定”，引导模型**按人设含糊带过或反问**，不编新设定 |
| 不想一问就抖出来的秘密 | 全靠提示词祈祷“不要说”，多半一绕就全漏光 | **`private` 在代码层死锁永不传给模型**；`shy` 项由程序控制“浓雾 → 漏点模糊线索 → 松口” |

---

## 核心功能

- **两种填法二选一**：推荐 `structured` 分栏（基础档案、作息习惯、喜好雷区、兜着/保密项），也支持直接贴一整段文本的 `freeform`，WebUI 切换后自动切换界面。
- **渐进式“兜着/嘴硬”（`shy`）**：不设死板“问 3 次”硬门槛，而是按同人同会话真实追问做非线性阻尼升温（带轻微波动）；长时间不问会自动降温回防备，支持私聊与熟人加速松口。
- **作息偏好自动共享**：填好的 `routine_note` 会自动供「麦的一天」读取。

---

## 3 步快速开始

### WebUI 上手（推荐）
1. 将 `mai-profile/` 放到 MaiBot 的 `plugins/` 目录并重启宿主，在 WebUI 打开 **麦设** 配置页。
2. 在 **基础档案** 添几条问起时要答的事实（如城市、专业）；填好 **作息习惯** 与 **喜好雷区**。
3. 把不想直接说破的事写进 **兜着/保密项**，口风选 `shy`，想在半路漏点风声就写上 **模糊线索**，保存即生效。

<details>
<summary>手改 config.toml 示例（附完整注释）</summary>

```toml
enabled = true
mode = "structured"                                 # structured 分栏 | freeform 纯正文
routine_note = "平时一点前睡，上午没课喜欢赖床"     # 会被麦的一天自动读取
likes_and_dislikes = "爱喝冰美式，讨厌香菜"

[[basic_fields]]
key = "城市"
value = "某南方城市"
disclosure = "public"                               # 问到即可公开回答
topics = ["哪里人", "住哪"]                         # 留空代表任何话题都可查到

[[guarded_entries]]
key = "感情状况"
value = "根本没对象，纯粹嘴硬"
disclosure = "shy"                                  # 先兜着，反复追问才逐渐松口
resistance = "medium"                               # low / medium / high
teaser = "好像心里有点在意的人，但嘴上绝对不认"     # 动摇阶段允许漏出的模糊线索
topics = ["对象", "恋爱", "男朋友", "女朋友"]

[[trigger_rules]]
topic = "哪里人"
words = ["老家", "哪里人", "在哪个城市"]            # 聊天提到这些词时顺手带出轻量提示
```

</details>

---

## 常用配置项说明

| 配置项 | 默认值 | 怎么填与效果说明 |
|---|---|---|
| `enabled` | `true` | 总开关，关闭后停止注入与档案查询 |
| `mode` | `"structured"` | `structured`（分栏填表，推荐）/ `freeform`（纯大段正文，仅放可公开信息） |
| `basic_fields` | `[]` | 公开档案卡片；`disclosure` 可选 `public`（公开）/ `shy`（兜着）/ `private`（绝不外传） |
| `routine_note` | `""` | 平时的作息倾向，供 `mai-day` 生成当日日程参考 |
| `guarded_entries` | `[]` | 建议把 `shy` / `private` 的敏感设定集中放在这里；`teaser` 不填时不会泄露任何原文 |
| `half_life_minutes` | `30` | 高级设置：多久没人再追问后，被撬松的口风会恢复一半防备（分钟） |
| `private_multiplier` | `1.2` | 高级设置：私聊一对一追问比在群里起哄更容易松口的倍率 |
| `unset_policy` | 内置中文引导 | 高级设置：查到档案里未填写的话题时，教模型怎么圆过去不瞎编 |

---

## 工具、接口与控制台

| 类别 | 名称 | 说明 |
|---|---|---|
| **对话工具** | `query_self_profile(topic="")` | 模型按话题查询自身设定与口风引导（工具只读，不会自己刷自己松口） |
| **联动 API** | `get_snapshot(topic, stream_id, user_id)` | 供 `zeyr.mai-day` 等读取公开设定与 `routine` 作息，永不吐出 `private` |
| **WebUI 面板** | `运行状态与生效范围` | 显示公开/保密条数，以及各会话当前松口阶段（浓雾 / 动摇中 / 已松口） |
| **WebUI 按钮** | `重置全部兜着进度` / `刷新公共集合缓存` | 一键把所有追问进度重置回初始防备状态 |

---

## 生态联动

- **可单装运行**：无需依赖其他插件。
- **同装 `mai-circle`**：生效范围 `[scope]` 可用 `@set:` / `@tag:`，并读取对方熟人标签的 `privacy_relax` 松口加成。
- **同装 `mai-day`**：每日生成生活底稿时自动读取 `routine_note`。

---

## 常见疑问

- **Q：`teaser` 留空，到半透明阶段会不会漏出真实答案的前几个字？**
  不会。未填 `teaser` 时插件仍然扣住完整真实 `value`，只下发半透明态度提示。
- **Q：个人隐私资料会不会被提交到仓库？**
  `config.toml` 只保存在运行插件目录，且已被工具与 `.gitignore` 忽略；开源代码内没有任何个人档案。

<details>
<summary>开发、门禁与安全审计</summary>

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r .github/requirements-ci.txt
.venv/bin/python scripts/check.py
```

- 包含 UTF-8/LF/尾随空格文本检查、Ruff、26 项 pytest、依赖一致性检查以及 `pip_audit` / `gitleaks` CI。

</details>
