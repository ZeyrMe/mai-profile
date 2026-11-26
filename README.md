# 麦设 · `zeyr.mai-profile`

> 为 MaiBot 提供独立的客观设定底账、未设定防胡编兜底，以及“先兜着、被多问才逐渐松口”的拟真披露体验。

![Version](https://img.shields.io/badge/version-0.2.0-green)
![MaiBot](https://img.shields.io/badge/MaiBot-1.4.8%2B-blue)
![SDK](https://img.shields.io/badge/SDK-2.23.0-teal)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

## 核心特性

- **双规格任选，告别大段杂烩**：支持 `structured` 结构化分栏（基础资料、作息习惯、喜好雷区、保密/兜着条目）与 `freeform` 纯文本正文，在 WebUI 切换模式时自动显示对应输入区。
- **未设定事实兜底，不胡编乱造**：查到档案里没写过的问题时，返回明确的引导信号而非空值，提醒模型按平时人设含糊带过或反问，不现场编造具体年龄、学校或家庭硬事实。
- **三级披露与模糊渐进松口**：
  - `public`：可正常回答；
  - `private`：代码层永不泄漏真实 `value`，守住隐私底线；
  - `shy`（兜着/嘴硬）：基于**浓雾 → 动摇（只吐模糊线索 `teaser`）→ 松口**三段清晰度衰减状态机，由真实入站追问按非线性阻尼 + 轻微抖动推进（无死板“问 3 次”硬编码），私聊与高亲密关系可配置松口加速。
- **日常 0 占用，问起才提示**：不在群里当“自我介绍话痨”。仅当入站消息命中设定关键词时注入极轻提醒；完整细节交由工具按需查询。

---

## 安装与快速配置

将 `mai-profile/` 目录放入宿主的 `plugins/` 目录下并重启 MaiBot；插件可独立安装使用。建议直接在 **WebUI 插件配置页**填表（旧版兼容字段与算法细节已在界面隐藏）。

若手动编辑运行目录 `config.toml`，典型配置如下：

```toml
enabled = true
mode = "structured"
routine_note = "平时稍微熬夜，中午偶尔犯困"
likes_and_dislikes = "爱喝冰美式，讨厌香菜和被人当客服"

[[basic_fields]]
key = "城市"
value = "某南方城市"
disclosure = "public"
topics = ["哪里人", "住哪"]

[[guarded_entries]]
key = "暗恋对象"
value = "其实根本没有，纯粹嘴硬"
disclosure = "shy"         # public | shy | private
resistance = "medium"      # low | medium | high
teaser = "好像心里有点在意的人，但嘴上绝对不认"
topics = ["对象", "恋爱"]

[[trigger_rules]]
topic = "哪里人"
words = ["老家", "哪里人", "在哪个城市"]
```

---

## 工具、接口与 WebUI 控制台

### 对话工具（`@Tool`）
| 工具名 | 参数 | 作用 |
|---|---|---|
| `query_self_profile` | `topic=""` | 按话题查询自己的公开底账、口风引导或未设定兜底提示（工具只读，不推进 `shy` 松口） |

### 对外联动接口（`@API(..., version="1")`）
- `get_snapshot(topic="", stream_id="", user_id="")`：向 `zeyr.mai-day` 等伙伴插件提供公开设定与作息偏好（`topic="routine"`），永不返回 `private` 字段。

### WebUI 运行时控制台（`config_widgets`）
| 控件 | 类型 | 说明 |
|---|---|---|
| `运行状态与生效范围` | 实时状态 | 显示已加载的公开条目、兜着/保密项数量、当前正在跟踪的松口会话数及 `[scope]` 状态 |
| `刷新公共集合缓存` | 一键按钮 | 清除 `@set:` / `@tag:` 范围引用缓存 |
| `重置全部兜着进度` | 二次确认按钮 | 清空当前所有会话的 `shy` 清晰度进度，重新回到防备状态 |

---

## 生态联动与范围边界

- **独立运行**：不依赖任何其他 `zeyr.*` 插件；未装 `mai-circle` 时直接使用默认关系加成倍率 `1.0`。
- **与 `mai-circle` 联动**：若同装群关系插件，支持在 `[scope]` 中直接填写 `@set:集合名` / `@tag:标签名`，并在追问 `shy` 条目时自动读取对方的亲密松口加成。
- **与 `mai-day` 联动**：在每天生成作息底稿时提供 `routine` 作息偏好摘要。
- **消息保护**：绝不在 `chat.receive.*` 入口丢消息；个人设定仅存于运行目录 `config.toml`，请勿提交至代码仓库。

<details>
<summary>开发、门禁与安全审计（独立仓库维护）</summary>

此目录由 MaiBot 直接加载，不使用 `pip install .`。单独检出本仓即可运行完整 CI 检查：

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r .github/requirements-ci.txt
.venv/bin/python scripts/check.py
```

- `scripts/check.py`：校验 Git 已跟踪文本的 UTF-8 / LF / 末尾换行 / 尾随空格，并运行 Ruff lint、Ruff 格式检查与全量 `pytest`。
- 安全与锁文件更新：

```bash
.venv/bin/python -m pip_audit --strict --require-hashes --disable-pip -r .github/requirements-ci.txt
gitleaks git --redact --log-opts="--all" .
uv pip compile pyproject.toml --extra dev --universal --python-version 3.12 --generate-hashes --output-file .github/requirements-ci.txt
```

</details>
