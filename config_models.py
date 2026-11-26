from typing import Literal

from maibot_sdk import Field, PluginConfigBase
from pydantic import model_validator

from .ecosystem import ScopeConfig


class ProfileEntry(PluginConfigBase):
    key: str = Field(default="", description="稳定字段名")
    value: str = Field(default="", description="字段内容")
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
    entries: list[ProfileEntry] = Field(default_factory=list, description="部署实例的人设字段")
    trigger_rules: list[TriggerRule] = Field(default_factory=list, description="主题与关键词对应条目")
    privacy_boundary: str = Field(default="只公开配置为 public 的字段。", description="隐私边界摘要")
    snapshot_template: str = Field(default="{key}：{value}", description="字段渲染模板")
    hint_chars: int = Field(default=55, ge=0, le=120, description="提示字数上限，优先保留隐私边界")

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

    @property
    def trigger_words(self):
        return {row.topic: row.words for row in self.trigger_rules}


# SDK 2.23 supports conditional fields; keep the first-use form small.
_BASIC_FIELDS = ["enabled", "entries", "show_advanced", "trigger_rules"]
for _name, _field in Config.model_fields.items():
    if _name not in _BASIC_FIELDS and _name != "plugin":
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
