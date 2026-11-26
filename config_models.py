from typing import Literal

from maibot_sdk import Field, PluginConfigBase


class ProfileEntry(PluginConfigBase):
    key: str = Field(default="", description="稳定字段名")
    value: str = Field(default="", description="字段内容")
    visibility: Literal["public", "private", "triggered"] = Field(
        default="public", description="公开、私有或命中触发词后可用"
    )
    topics: list[str] = Field(default_factory=list, description="命中主题；为空表示不限制")


class PluginInfo(PluginConfigBase):
    config_version: str = Field(default="0.1.0", description="配置版本，由 Runner 管理")


class Config(PluginConfigBase):
    show_advanced: bool = Field(default=False, description="显示高级设置")
    plugin: PluginInfo = Field(default_factory=PluginInfo)
    enabled: bool = Field(default=True, description="启用插件")
    entries: list[ProfileEntry] = Field(default_factory=list, description="部署实例的人设字段")
    trigger_words: dict[str, list[str]] = Field(default_factory=dict, description="主题到触发词")
    privacy_boundary: str = Field(default="只公开配置为 public 的字段。", description="隐私边界摘要")
    snapshot_template: str = Field(default="{key}：{value}", description="字段渲染模板")
    hint_chars: int = Field(default=55, ge=0, le=120, description="提示字数上限，优先保留隐私边界")


# SDK 2.23 supports conditional fields; keep the first-use form small.
_BASIC_FIELDS = ["enabled", "entries", "show_advanced", "trigger_words"]
for _name, _field in Config.model_fields.items():
    if _name not in _BASIC_FIELDS and _name != "plugin":
        _field.json_schema_extra = {
            **(_field.json_schema_extra or {}),
            "depends_on": "show_advanced",
            "depends_value": True,
        }
Config.model_rebuild(force=True)
