from typing import Literal

from maibot_sdk import Field, PluginConfigBase
from pydantic import model_validator

from .ecosystem import ScopeConfig


class ProfileEntry(PluginConfigBase):
    key: str = Field(
        default="",
        description="条目名称，例如 年龄、学校、城市。",
        json_schema_extra={"label": "设定名称", "placeholder": "例如 城市"},
    )
    value: str = Field(
        default="",
        description="这条设定的真实内容。",
        json_schema_extra={"label": "设定内容", "placeholder": "例如 杭州"},
    )
    disclosure: Literal["public", "private", "shy"] = Field(
        default="public",
        description="public 正常可答；shy 会先兜着、被多问才松口；private 死守不说。",
        json_schema_extra={"label": "口风松紧"},
    )
    resistance: Literal["low", "medium", "high"] = Field(
        default="medium",
        description="仅对 shy 生效：被追问时有多嘴硬。",
        json_schema_extra={"label": "嘴硬程度"},
    )
    teaser: str = Field(
        default="",
        description="被追问松动时，允许隐约透露的一句模糊线索（不写也不会漏原话）。",
        json_schema_extra={"label": "模糊线索", "placeholder": "例如 在南方一座很爱吃辣的城市"},
    )
    visibility: Literal["public", "private", "triggered"] = Field(
        default="public",
        description="旧版兼容可见性。",
        json_schema_extra={"label": "兼容可见性", "hidden": True},
    )
    topics: list[str] = Field(
        default_factory=list,
        description="聊到哪些关键词或话题时才想起这条设定，留空表示不限话题。",
        json_schema_extra={"label": "关联话题", "placeholder": "例如 老家、住哪"},
    )


class TriggerRule(PluginConfigBase):
    topic: str = Field(
        default="",
        description="对应档案条目的话题名。",
        json_schema_extra={"label": "话题名", "placeholder": "例如 作息"},
    )
    words: list[str] = Field(
        default_factory=list,
        description="聊天里出现这些词时，轻轻提醒自己记住对应设定。",
        json_schema_extra={"label": "触发关键词", "placeholder": "例如 几点睡、熬夜"},
    )


class PluginInfo(PluginConfigBase):
    config_version: str = Field(default="0.1.0", description="配置版本，由 Runner 管理")


class Config(PluginConfigBase):
    scope: ScopeConfig = Field(default_factory=ScopeConfig, description="独立控制哪些群或人启用麦设")
    show_advanced: bool = Field(
        default=False,
        description="展开高阶调节项与提示词模板。",
        json_schema_extra={"label": "显示高级设置"},
    )
    plugin: PluginInfo = Field(default_factory=PluginInfo)
    enabled: bool = Field(
        default=True,
        description="开启后，问到自身设定时有底账可查。",
        json_schema_extra={"label": "启用麦设"},
    )
    mode: Literal["structured", "freeform"] = Field(
        default="structured",
        description="structured 用分栏条目填（推荐）；freeform 用一整段纯文本写。",
        json_schema_extra={"label": "档案形式"},
    )
    freeform_text: str = Field(
        default="",
        description="整段写清公开身份、喜好和日常习惯；不想被直接抖出的秘密仍建议放到保密条目里。",
        json_schema_extra={
            "label": "人设正文",
            "placeholder": "用几句话写清自己是谁、平时什么作息、喜欢和讨厌什么……",
            "x-widget": "textarea",
            "depends_on": "mode",
            "depends_value": "freeform",
        },
    )
    basic_fields: list[ProfileEntry] = Field(
        default_factory=list,
        description="可直接聊到的基础档案，如昵称、年龄、所在地等。",
        json_schema_extra={"label": "基础档案"},
    )
    routine_note: str = Field(
        default="",
        description="写清平时的作息习惯，生活日程插件会自动来参考。",
        json_schema_extra={"label": "作息习惯", "placeholder": "例如 平时微夜猫，中午容易犯困"},
    )
    likes_and_dislikes: str = Field(
        default="",
        description="喜欢吃喝玩的东西与讨厌的雷区。",
        json_schema_extra={"label": "喜好雷区", "placeholder": "例如 爱喝冰美式，讨厌香菜"},
    )
    guarded_entries: list[ProfileEntry] = Field(
        default_factory=list,
        description="不想随便直接回答的设定：可以设为一直兜着，或者被追问多了才松口。",
        json_schema_extra={"label": "兜着/保密项"},
    )
    unset_policy: str = Field(
        default="没记过这件事，按平时说话的习惯含糊带过或反问一句，别现场瞎编具体数字或经历。",
        description="被问到档案里根本没写过的问题时怎么圆过去。",
        json_schema_extra={"label": "未设定兜底"},
    )
    private_policy: str = Field(
        default="这事不想往外说，自然拒绝或者换个话题。",
        description="对方触及永久保密项时的态度要求。",
        json_schema_extra={"label": "保密引导"},
    )
    withheld_policy: str = Field(
        default="心里其实有数，但眼下还不想直说，装傻、卖个关子或者先不告诉对方。",
        description="兜着阶段刚被问到时的反应要求。",
        json_schema_extra={"label": "初问遮掩语"},
    )
    teaser_policy: str = Field(
        default="被追问得有点松动，但还想端着，最多隐约露一点边角，别直接抖出来。",
        description="被连问几次快顶不住时的反应要求。",
        json_schema_extra={"label": "动摇提示语"},
    )
    revealed_policy: str = Field(
        default="被缠着问了好几回，可以有点不好意思地顺口说出来。",
        description="终于松口说出答案时的语气引导。",
        json_schema_extra={"label": "松口语气语"},
    )
    half_life_minutes: float = Field(
        default=30,
        gt=0,
        le=1440,
        description="隔了多少分钟没人再追问后，被撬开的口风会慢慢恢复一半防备。",
        json_schema_extra={"label": "松口冷却分钟"},
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
        description="一对一私聊追问比大群里更容动摇的倍率。",
        json_schema_extra={"label": "私聊松口加速"},
    )
    relation_multiplier: float = Field(
        default=1.0,
        ge=0,
        le=3,
        description="关系亲近带来的松口加速倍率。",
        json_schema_extra={"label": "熟人松口加成"},
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
        json_schema_extra={"label": "关键词触发"},
    )
    privacy_boundary: str = Field(
        default="只聊允许公开的设定，不想说的事顺着语气带过。",
        description="附在设定提示后面的一句说话边界提醒。",
        json_schema_extra={"label": "口风边界提醒"},
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
        json_schema_extra={"label": "轻提示字数上限"},
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
