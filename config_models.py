from typing import Literal

from maibot_sdk import Field, PluginConfigBase
from pydantic import model_validator

from .ecosystem import ScopeConfig


class ProfileEntry(PluginConfigBase):
    key: str = Field(
        default="",
        description="条目名称，例如 年龄、学校、城市。",
        json_schema_extra={
            "label": "设定名称",
            "placeholder": "写设定的名字，如：所在地、专业、最喜欢的食物",
        },
    )
    value: str = Field(
        default="",
        description="这条设定的真实内容。",
        json_schema_extra={"label": "设定内容", "placeholder": "写设定的真实答案，如：杭州、计算机、冰美式"},
    )
    disclosure: Literal["public", "private", "shy"] = Field(
        default="public",
        description="public 直接可答；shy 追问后逐步公开；private 始终保密。",
        json_schema_extra={
            "label": "公开方式",
            "enum_labels": {
                "public": "public（公开）",
                "shy": "shy（追问后公开）",
                "private": "private（保密）",
            },
        },
    )
    resistance: Literal["low", "medium", "high"] = Field(
        default="medium",
        description="仅对 shy 生效：被追问时公开的难易程度。",
        json_schema_extra={
            "label": "追问难度",
            "enum_labels": {
                "low": "low（容易松口）",
                "medium": "medium（一般）",
                "high": "high（较难松口）",
            },
        },
    )
    teaser: str = Field(
        default="",
        description="追问到线索阶段时可透露的提示内容，留空不泄露原设定。",
        json_schema_extra={
            "label": "提示线索",
            "placeholder": "如：南方一座爱吃辣的城市（留空则不透露具体内容）",
        },
    )
    visibility: Literal["public", "private", "triggered"] = Field(
        default="public",
        description="旧版兼容可见性。",
        json_schema_extra={"label": "兼容可见性", "hidden": True},
    )
    topics: list[str] = Field(
        default_factory=list,
        description="聊到哪些关键词或话题时才想起这条设定，留空表示不限话题。",
        json_schema_extra={
            "label": "关联话题",
            "placeholder": "填聊到时才触发的话题词，如：老家、住哪；留空表示随时可查",
        },
    )


class TriggerRule(PluginConfigBase):
    topic: str = Field(
        default="",
        description="对应档案条目的话题名。",
        json_schema_extra={"label": "话题名", "placeholder": "要关联的设定或话题名，如：作息、老家"},
    )
    words: list[str] = Field(
        default_factory=list,
        description="聊天里出现这些词时，轻轻提醒自己记住对应设定。",
        json_schema_extra={"label": "触发关键词", "placeholder": "群友怎么问会触发，如：几点睡、熬夜、住哪"},
    )


class PluginInfo(PluginConfigBase):
    config_version: str = Field(default="0.1.0", description="配置版本，由 Runner 管理")


class Config(PluginConfigBase):
    scope: ScopeConfig = Field(default_factory=ScopeConfig, description="独立控制哪些群或人启用麦设")
    show_advanced: bool = Field(
        default=False,
        description="展开高阶调节项与提示词模板。",
        json_schema_extra={
            "label": "显示高级设置",
            "order": 9,
            "hint": "日常只需填写基础设定和保密设定；需要修改回复引导、冷却时间或关键词触发时再展开。",
        },
    )
    plugin: PluginInfo = Field(default_factory=PluginInfo)
    enabled: bool = Field(
        default=True,
        description="开启后支持在对话中按需查询人设与保密控制。",
        json_schema_extra={
            "label": "启用麦设",
            "order": 1,
            "hint": "关闭后不再向聊天注入人设提示，也不响应查询工具。",
        },
    )
    mode: Literal["structured", "freeform"] = Field(
        default="structured",
        description="选择结构化分栏填表，或使用整段自由文本。",
        json_schema_extra={
            "label": "档案形式",
            "order": 2,
            "enum_labels": {
                "structured": "structured（分栏填写，推荐，支持联动日常作息）",
                "freeform": "freeform（纯文本正文）",
            },
            "hint": "推荐选 structured，字段清晰且可联动 mai-day；习惯写整段设定可选 freeform，保密内容请放到“保密设定”中。",
        },
    )
    freeform_text: str = Field(
        default="",
        description="整段写清公开身份、喜好和日常习惯。",
        json_schema_extra={
            "label": "人设正文",
            "order": 3,
            "placeholder": "写清楚公开背景、平时作息、喜欢和讨厌什么；不要把保密内容写进这里。",
            "hint": "仅 freeform 模式生效。此处内容默认可查，保密条目请放到“保密设定”中。",
            "x-widget": "textarea",
            "depends_on": "mode",
            "depends_value": "freeform",
        },
    )
    basic_fields: list[ProfileEntry] = Field(
        default_factory=list,
        description="基础人物设定条目，如年龄、学校、城市等。",
        json_schema_extra={
            "label": "基础设定",
            "order": 4,
            "hint": "每条填“设定名称 + 设定内容”，如城市、专业；公开方式可选 public（公开）/ shy（追问后公开）/ private（保密）。",
        },
    )
    routine_note: str = Field(
        default="",
        description="平时的作息习惯，开启作息插件时会自动参考。",
        json_schema_extra={
            "label": "作息习惯",
            "order": 5,
            "placeholder": "例如：平时一点前睡，上午没课会多睡一会",
            "hint": "填写日常作息规律；与 mai-day 同时使用时，每日生成日程会自动读取此项作为参考。",
        },
    )
    likes_and_dislikes: str = Field(
        default="",
        description="喜欢的事物与讨厌的雷区。",
        json_schema_extra={
            "label": "喜好雷区",
            "order": 6,
            "placeholder": "例如：喜欢冰美式和吃辣，不吃香菜",
            "hint": "概括喜好与忌口；平时不占用上下文，聊到相关话题时才会读取。",
        },
    )
    guarded_entries: list[ProfileEntry] = Field(
        default_factory=list,
        description="不希望直接回答的设定，可设为始终保密或多次追问后公开。",
        json_schema_extra={
            "label": "保密设定",
            "order": 7,
            "hint": "公开方式选 shy（随追问进度逐步透露，可附带提示线索）或 private（始终不传给模型）；追问难度选 low / medium / high。",
        },
    )
    unset_policy: str = Field(
        default="没有记录过这件事，按平时说话的习惯自然带过或反问一句，不要编造具体数字或经历。",
        description="被问到未填写过的细节时的回复引导。",
        json_schema_extra={
            "label": "未设定提示",
            "hint": "避免模型在遇到未填写的设定时自行编造新背景。",
        },
    )
    private_policy: str = Field(
        default="这件事不想往外说，自然拒绝或者换个话题。",
        description="触发永久保密项时的回复引导。",
        json_schema_extra={
            "label": "保密提示",
            "hint": "遇到 private 条目时，真实内容不会传给模型，仅下发此引导语。",
        },
    )
    withheld_policy: str = Field(
        default="心里清楚，但眼下还不想直说，可以先绕开或者卖个关子。",
        description="shy 设定初次被问到时的回复引导。",
        json_schema_extra={
            "label": "初次追问提示",
            "hint": "未透露阶段被问及 shy 设定时下发给模型的行为提示。",
        },
    )
    teaser_policy: str = Field(
        default="被追问多次后有点松动，可以隐约透露一点线索，但先别直接说破。",
        description="shy 设定到达线索阶段时的回复引导。",
        json_schema_extra={
            "label": "线索阶段提示",
            "hint": "已给线索阶段下发：若条目填了“提示线索”，模型仅按线索提示。",
        },
    )
    revealed_policy: str = Field(
        default="被反复追问后可以顺着话头说出来。",
        description="shy 设定最终松口时的语气引导。",
        json_schema_extra={
            "label": "公开阶段提示",
            "hint": "追问进度达标后，与真实设定内容一并交给模型。",
        },
    )
    half_life_minutes: float = Field(
        default=30,
        gt=0,
        le=1440,
        description="无人继续追问后，追问进度减半所需的分钟数。",
        json_schema_extra={
            "label": "进度冷却分钟",
            "hint": "单位：分钟（默认 30）。过一段时间没人追问后，已累积的进度会逐渐回落。",
        },
    )
    shy_increment: float = Field(
        default=0.25,
        gt=0,
        le=1,
        description="实质追问的基础非线性增量",
        json_schema_extra={"label": "单次松动步长", "hidden": True},
    )
    shy_jitter: float = Field(
        default=0.04,
        ge=0,
        le=0.5,
        description="每次增量轻微抖动",
        json_schema_extra={"label": "松动随机抖动", "hidden": True},
    )
    resistance_low: float = Field(
        default=1.4,
        gt=0,
        le=5,
        description="低倔强增速",
        json_schema_extra={"label": "低倔强倍率", "hidden": True},
    )
    resistance_medium: float = Field(
        default=1.0,
        gt=0,
        le=5,
        description="中倔强增速",
        json_schema_extra={"label": "中倔强倍率", "hidden": True},
    )
    resistance_high: float = Field(
        default=0.6,
        gt=0,
        le=5,
        description="高倔强增速",
        json_schema_extra={"label": "高倔强倍率", "hidden": True},
    )
    private_multiplier: float = Field(
        default=1.2,
        ge=1,
        le=3,
        description="一对一私聊追问比大群里更容易动摇的倍率。",
        json_schema_extra={
            "label": "私聊松口加速",
            "hint": "填 1.0 表示和群聊完全一样；填 1.2–1.5 表示一对一私聊更容易被追问得松口。",
        },
    )
    relation_multiplier: float = Field(
        default=1.0,
        ge=0,
        le=3,
        description="关系亲近带来的松口加速倍率。",
        json_schema_extra={
            "label": "熟人松口加成",
            "hint": "配合群关系插件生效：0 关闭熟人优待，1.0 正常应用群关系标签里的松口加成。",
        },
    )
    teaser_threshold: float = Field(
        default=0.4,
        ge=0,
        le=1,
        description="线索阶段阈值",
        json_schema_extra={"label": "透底阈值", "hidden": True},
    )
    reveal_threshold: float = Field(
        default=0.8,
        gt=0,
        le=1,
        description="松口阶段阈值",
        json_schema_extra={"label": "松口阈值", "hidden": True},
    )
    followup_min_chars: int = Field(
        default=4,
        ge=1,
        le=100,
        description="有效追问最短字数",
        json_schema_extra={"label": "追问最短字数", "hidden": True},
    )
    max_clarity_entries: int = Field(
        default=512,
        ge=1,
        le=10000,
        description="清晰度状态上限",
        json_schema_extra={"label": "清晰度缓存上限", "hidden": True},
    )
    max_seen_messages: int = Field(
        default=1024,
        ge=1,
        le=10000,
        description="追问消息去重上限",
        json_schema_extra={"label": "去重消息上限", "hidden": True},
    )
    entries: list[ProfileEntry] = Field(
        default_factory=list,
        description="旧版人设条目兼容字段。",
        json_schema_extra={"label": "兼容旧条目", "hidden": True},
    )
    trigger_rules: list[TriggerRule] = Field(
        default_factory=list,
        description="设定聊到哪些关键词时，顺手把对应资料贴到当前思考里。",
        json_schema_extra={
            "label": "关键词触发",
            "hint": "只有群友消息里撞见这里的关键词时，麦设才会把对应条目轻提示给模型；普通闲聊零字数占用。",
        },
    )
    privacy_boundary: str = Field(
        default="只聊可以说的设定，不想说的事顺着话头带过。",
        description="附在设定提示后面的边界提醒。",
        json_schema_extra={
            "label": "回复边界提示",
            "hint": "触发档案注入时附在结尾，提醒模型注意保密边界。",
        },
    )
    snapshot_template: str = Field(
        default="{key}：{value}",
        description="单条设定的拼装写法。",
        json_schema_extra={"label": "设定拼装格式", "hidden": True},
    )
    hint_chars: int = Field(
        default=80,
        ge=0,
        le=200,
        description="单轮往对话里轻提示的最多字数。",
        json_schema_extra={
            "label": "轻提示字数上限",
            "hint": "默认 80 字，设为 0 可关闭主动提示（仅保留按需查询工具）。",
        },
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy(cls, values):
        if isinstance(values, dict) and "trigger_words" in values and "trigger_rules" not in values:
            values = {
                **values,
                "trigger_rules": [
                    {"topic": key, "words": words} for key, words in values["trigger_words"].items()
                ],
            }
        return values

    @model_validator(mode="after")
    def valid_thresholds(self):
        if self.teaser_threshold >= self.reveal_threshold:
            raise ValueError("线索阈值必须小于松口阈值")
        keys = [row.key for row in self.entries + self.basic_fields + self.guarded_entries if row.key]
        if len(keys) != len(set(keys)):
            raise ValueError("档案条目 key 不能重复")
        return self

    @property
    def trigger_words(self):
        return {row.topic: row.words for row in self.trigger_rules}


_BASIC_FIELDS = ["enabled", "mode", "basic_fields", "show_advanced"]
for _name, _field in Config.model_fields.items():
    if _name not in _BASIC_FIELDS and _name != "plugin" and _name != "freeform_text":
        _field.json_schema_extra = {
            **(_field.json_schema_extra or {}),
            "depends_on": "show_advanced",
            "depends_value": True,
        }
Config.model_rebuild(force=True)

for _model in list(globals().values()):
    if isinstance(_model, type) and issubclass(_model, PluginConfigBase):
        for _field_name, _field_info in _model.model_fields.items():
            _field_info.json_schema_extra = {
                "label": _field_info.description or _field_name,
                **(_field_info.json_schema_extra or {}),
            }
        _model.model_rebuild(force=True)

for _name in ("basic_fields", "routine_note", "likes_and_dislikes"):
    Config.model_fields[_name].json_schema_extra = {
        **(Config.model_fields[_name].json_schema_extra or {}),
        "depends_on": "mode",
        "depends_value": "structured",
    }
Config.model_rebuild(force=True)
