from typing import Literal

from maibot_sdk import Field, PluginConfigBase
from pydantic import model_validator

from .ecosystem import ScopeConfig


class ProfileEntry(PluginConfigBase):
    key: str = Field(default="", description="稳定字段名")
    value: str = Field(default="", description="字段内容")
    disclosure: Literal["public", "private", "shy"] = Field(default="public", description="披露等级")
    resistance: Literal["low", "medium", "high"] = Field(default="medium", description="嘴硬程度")
    teaser: str = Field(default="", description="动摇阶段允许公开的模糊线索；空值不泄漏原文")
    visibility: Literal["public", "private", "triggered"] = Field(
        default="public", description="公开、私有或命中触发词后可用"
    )
    topics: list[str] = Field(default_factory=list, description="命中主题；为空表示不限制")


class TriggerRule(PluginConfigBase):
    topic: str = Field(default="", description="档案主题")
    words: list[str] = Field(default_factory=list, description="入站触发关键词")


class PluginInfo(PluginConfigBase):
    config_version: str = Field(default="0.1.0", description="配置版本，由 Runner 管理")


class Config(PluginConfigBase):
    scope: ScopeConfig = Field(default_factory=ScopeConfig, description="独立会话与用户生效范围")
    show_advanced: bool = Field(default=False, description="显示高级设置")
    plugin: PluginInfo = Field(default_factory=PluginInfo)
    enabled: bool = Field(default=True, description="启用插件")
    mode: Literal["structured", "freeform"] = Field(default="structured", description="结构化资料或公开文本")
    freeform_text: str = Field(
        default="",
        description="公开背景文本；敏感事实请使用保密条目",
        json_schema_extra={"x-widget": "textarea", "depends_on": "mode", "depends_value": "freeform"},
    )
    basic_fields: list[ProfileEntry] = Field(default_factory=list, description="基础键值资料")
    routine_note: str = Field(default="", description="公开作息偏好，供生活插件参考")
    likes_and_dislikes: str = Field(default="", description="喜好与雷区")
    guarded_entries: list[ProfileEntry] = Field(default_factory=list, description="保密或兜着的事实")
    unset_policy: str = Field(
        default="档案中未设定此事实；顺着当前人设模糊带过、吐槽或反问，不要编造具体数字、学校或家庭硬事实。",
        description="未设定事实的处理要求",
    )
    private_policy: str = Field(
        default="这是明确隐私红线，拒绝或岔开，不提供真实内容。", description="永久保密要求"
    )
    withheld_policy: str = Field(
        default="心里有数但现在不想直接说，可以装傻或卖关子。", description="浓雾阶段引导"
    )
    teaser_policy: str = Field(
        default="有点动摇但还嘴硬，最多透露允许的模糊线索。", description="半透明阶段引导"
    )
    revealed_policy: str = Field(default="可以勉强或不好意思地承认。", description="松口阶段引导")
    half_life_minutes: float = Field(default=30, gt=0, le=1440, description="清晰度半衰期分钟")
    shy_increment: float = Field(default=0.25, gt=0, le=1, description="实质追问的基础非线性增量")
    shy_jitter: float = Field(default=0.04, ge=0, le=0.5, description="每次增量轻微抖动")
    resistance_low: float = Field(default=1.4, gt=0, le=5, description="低倔强增速")
    resistance_medium: float = Field(default=1.0, gt=0, le=5, description="中倔强增速")
    resistance_high: float = Field(default=0.6, gt=0, le=5, description="高倔强增速")
    private_multiplier: float = Field(default=1.2, ge=1, le=3, description="私聊追问加速")
    relation_multiplier: float = Field(default=1.0, ge=0, le=3, description="关系松口加成倍率")
    teaser_threshold: float = Field(default=0.4, ge=0, le=1, description="线索阶段阈值")
    reveal_threshold: float = Field(default=0.8, gt=0, le=1, description="松口阶段阈值")
    followup_min_chars: int = Field(default=4, ge=1, le=100, description="有效追问最短字数")
    max_clarity_entries: int = Field(default=512, ge=1, le=10000, description="清晰度状态上限")
    max_seen_messages: int = Field(default=1024, ge=1, le=10000, description="追问消息去重上限")
    entries: list[ProfileEntry] = Field(default_factory=list, description="部署实例的人设字段")
    trigger_rules: list[TriggerRule] = Field(default_factory=list, description="主题与关键词对应条目")
    privacy_boundary: str = Field(default="只公开配置为 public 的字段。", description="隐私边界摘要")
    snapshot_template: str = Field(default="{key}：{value}", description="字段渲染模板")
    hint_chars: int = Field(default=80, ge=0, le=200, description="提示字数上限，优先保留隐私边界")

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


# SDK 2.23 supports conditional fields; keep the first-use form small.
_BASIC_FIELDS = ["enabled", "mode", "basic_fields", "show_advanced"]
for _name, _field in Config.model_fields.items():
    if _name not in _BASIC_FIELDS and _name != "plugin" and _name != "freeform_text":
        _field.json_schema_extra = {
            **(_field.json_schema_extra or {}),
            "depends_on": "show_advanced",
            "depends_value": True,
        }
Config.model_rebuild(force=True)


# SDK labels otherwise fall back to Python field names in top-level sections.
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
