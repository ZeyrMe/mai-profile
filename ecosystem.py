"""Vendored v2 scope/console boundary. Keep identical across standalone repositories."""

from __future__ import annotations

import asyncio
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Literal

from maibot_sdk import Field, PluginConfigBase
from maibot_sdk.config_widgets import ConfigWidget, ConfigWidgetState
from pydantic import field_validator


def anchor(value: str, default_kind: str = "group") -> tuple[str, str, str]:
    """Parse explicit anchors; identifiers remain strings and never become stream IDs."""
    parts = value.strip().split(":")
    if len(parts) == 1:
        parts = ["qq", default_kind, parts[0]]
    elif len(parts) == 2:
        parts = ["qq", *parts]
    if len(parts) != 3 or parts[1] not in ("group", "private", "user") or not all(parts):
        raise ValueError("对象请填写 group:标识、private:标识、user:标识或 平台:类型:标识")
    return tuple(parts)


@dataclass(frozen=True)
class ChatIdentity:
    platform: str = "qq"
    user_id: str = ""
    group_id: str = ""
    stream_id: str = ""

    @property
    def kind(self):
        return "group" if self.group_id else "private" if self.user_id else "unknown"

    @classmethod
    def from_message(cls, message=None, stream_id=""):
        message = message or {}
        info = message.get("message_info") or {}
        user = info.get("user_info") or message.get("user_info") or {}
        group = info.get("group_info") or message.get("group_info") or {}
        return cls(
            str(message.get("platform") or user.get("platform") or "qq"),
            str(user.get("user_id") or message.get("user_id") or ""),
            str(group.get("group_id") or message.get("group_id") or ""),
            str(stream_id or message.get("session_id") or message.get("stream_id") or ""),
        )


class ScopeConfig(PluginConfigBase):
    __ui_label__ = "生效范围"
    __ui_icon__ = "filter"
    __ui_order__ = 90
    mode: Literal["all", "whitelist", "blacklist"] = Field(
        default="all",
        description="默认对全部聊天生效；可改成只对下面填的名单生效，或把名单里的人和群屏蔽掉。",
        json_schema_extra={"label": "范围模式"},
    )
    groups: list[str] = Field(
        default_factory=list,
        description="直接填 QQ 群号，也可以填群关系里配好的集合（如 @set:观察群）。",
        json_schema_extra={"label": "群聊名单", "placeholder": "例如 123456 或 @set:观察群"},
    )
    privates: list[str] = Field(
        default_factory=list,
        description="直接填私聊对方的 QQ 号。",
        json_schema_extra={"label": "私聊名单", "placeholder": "例如 987654"},
    )
    users: list[str] = Field(
        default_factory=list,
        description="跨群按人识别，直接填 QQ 号或关系标签（如 @tag:同行Bot）。",
        json_schema_extra={"label": "用户名单", "placeholder": "例如 987654 或 @tag:同行Bot"},
    )
    exclude: list[str] = Field(
        default_factory=list,
        description="无论上面怎么选，这里填到的群或人都一律跳过。",
        json_schema_extra={"label": "强制排除", "placeholder": "例如 123456 或 @tag:同行Bot"},
    )
    allow_private: bool = Field(
        default=True,
        description="关闭后，除了白名单里点名的人之外，私聊不会触发本插件。",
        json_schema_extra={"label": "允许私聊"},
    )
    reference_cache_seconds: float = Field(
        default=60,
        ge=0,
        le=3600,
        description="公共集合缓存秒数",
        json_schema_extra={"label": "集合缓存秒数", "hidden": True},
    )
    api_timeout_seconds: float = Field(
        default=0.4,
        gt=0,
        le=0.4,
        description="本轮公共集合发现及调用总超时",
        json_schema_extra={"label": "调用超时秒数", "hidden": True},
    )
    max_tracked_streams: int = Field(
        default=256,
        ge=1,
        le=10000,
        description="内存会话身份缓存上限",
        json_schema_extra={"label": "会话缓存上限", "hidden": True},
    )

    @field_validator("groups", "privates", "users", "exclude")
    @classmethod
    def valid_anchors(cls, values, info):
        default = {"groups": "group", "privates": "private", "users": "user"}.get(info.field_name, "group")
        for value in values:
            if value.startswith(("@set:", "@tag:")):
                if not value.split(":", 1)[1].strip():
                    raise ValueError("集合或标签名不能为空")
            else:
                anchor(value, default)
        return list(dict.fromkeys(values))


class ScopeGate:
    def __init__(self):
        self.routes = OrderedDict()
        self.cache = {}
        self.warned = set()

    def remember(self, chat, limit):
        if chat.stream_id and chat.kind != "unknown":
            self.routes[chat.stream_id] = chat
            self.routes.move_to_end(chat.stream_id)
            while len(self.routes) > limit:
                self.routes.popitem(last=False)

    async def resolve(self, ref, ctx, config, local=None):
        if local is not None:
            return local(ref)
        cached = self.cache.get(ref)
        if cached and time.monotonic() < cached[0]:
            return cached[1]
        data = None
        try:
            if await ctx.api.get("zeyr.mai-circle.resolve_scope_ref", version="1"):
                payload = await ctx.api.call("zeyr.mai-circle.resolve_scope_ref", version="1", ref=ref)
                while isinstance(payload, dict) and "result" in payload and "schema_version" not in payload:
                    if not payload.get("success"):
                        break
                    payload = payload["result"]
                if (
                    isinstance(payload, dict)
                    and payload.get("schema_version") == 1
                    and payload.get("success")
                ):
                    data = payload.get("data")
        except asyncio.CancelledError:
            raise
        except Exception:
            pass
        if not isinstance(data, dict):
            data = {"groups": [], "privates": [], "users": []}
            if ref not in self.warned:
                logger = getattr(ctx, "logger", None)
                if logger:
                    logger.warning("公共范围引用 %s 暂不可用，按空集合处理", ref)
                self.warned.add(ref)
        self.cache[ref] = (time.monotonic() + config.reference_cache_seconds, data)
        return data

    async def allows(self, config, chat, ctx=None, local=None):
        targets, excluded = set(), set()
        refs = {}
        for name, default in (
            ("groups", "group"),
            ("privates", "private"),
            ("users", "user"),
            ("exclude", "group"),
        ):
            destination = excluded if name == "exclude" else targets
            for value in getattr(config, name):
                if value.startswith("@"):
                    refs.setdefault(value, []).append(destination)
                else:
                    destination.add(anchor(value, default))
        # All references share one deadline; a long list cannot multiply ingress latency.
        try:
            async with asyncio.timeout(config.api_timeout_seconds):
                for ref, destinations in refs.items():
                    data = await self.resolve(ref, ctx, config, local)
                    values = set()
                    for name, kind in (("groups", "group"), ("privates", "private"), ("users", "user")):
                        for value in data.get(name, []):
                            try:
                                values.add(anchor(value, kind))
                            except (TypeError, ValueError):
                                continue
                    for destination in destinations:
                        destination.update(values)
        except TimeoutError:
            for ref in refs:
                if ref not in self.cache:
                    self.cache[ref] = (
                        time.monotonic() + config.reference_cache_seconds,
                        {"groups": [], "privates": [], "users": []},
                    )
            logger = getattr(ctx, "logger", None)
            if logger and "timeout" not in self.warned:
                logger.warning("公共范围引用查询超时，未解析引用按空集合处理")
                self.warned.add("timeout")
        if chat.kind == "unknown" and (
            config.mode == "whitelist"
            or not config.allow_private
            or excluded
            or (config.mode == "blacklist" and (targets or refs))
        ):
            return False
        candidates = {(chat.platform, "user", chat.user_id)} if chat.user_id else set()
        if chat.kind == "group":
            candidates.add((chat.platform, "group", chat.group_id))
        elif chat.kind == "private":
            candidates.add((chat.platform, "private", chat.user_id))
        if candidates & excluded:
            return False
        hit = bool(candidates & targets)
        if config.mode == "blacklist" and hit:
            return False
        if chat.kind == "private" and not config.allow_private and not (hit and config.mode != "blacklist"):
            return False
        return hit if config.mode == "whitelist" else True


class EcosystemMixin:
    """No entrypoint interception: each caller explicitly checks its affected operation."""

    config_widgets = [
        ConfigWidget(id="ecosystem_status", kind="status", label="运行状态与生效范围"),
        ConfigWidget(id="refresh_scope", kind="action", label="刷新公共集合缓存"),
    ]

    @classmethod
    def build_config_schema(cls, **kwargs):
        schema = super().build_config_schema(**kwargs)
        # SDK does not propagate depends_on from a model field into its section.
        # Use its supported collapsed flag instead of promising a hidden section.
        for section_name, section in schema.get("sections", {}).items():
            field = cls.config_model.model_fields.get(section_name)
            extra = (field.json_schema_extra or {}) if field else {}
            if section_name == "scope" or extra.get("depends_on") == "show_advanced":
                section["collapsed"] = True
        return schema

    def normalize_plugin_config(self, config_data):
        # Migrate aliases before SDK default merging masks whether a new field was supplied.
        normalize = getattr(self.config_model, "normalize_legacy", None)
        prepared = normalize(dict(config_data)) if normalize and config_data else config_data
        config, changed = super().normalize_plugin_config(prepared)
        return config, changed or prepared != config_data

    @property
    def scope_gate(self):
        if not hasattr(self, "_scope_gate"):
            self._scope_gate = ScopeGate()
        return self._scope_gate

    async def in_scope(self, message=None, **kwargs):
        stream = str(kwargs.get("session_id") or kwargs.get("stream_id") or "")
        chat = ChatIdentity.from_message(message if message is not None else kwargs, stream)
        if chat.kind == "unknown" and chat.stream_id:
            chat = self.scope_gate.routes.get(chat.stream_id, chat)
        self.scope_gate.remember(chat, self.config.scope.max_tracked_streams)
        return await self.scope_gate.allows(
            self.config.scope, chat, getattr(self, "_ctx", None), getattr(self, "resolve_scope_ref", None)
        )

    async def target_in_scope(self, platform, group_id="", user_id="", stream_id=""):
        return await self.scope_gate.allows(
            self.config.scope,
            ChatIdentity(platform, user_id, group_id, stream_id),
            getattr(self, "_ctx", None),
            getattr(self, "resolve_scope_ref", None),
        )

    def console_text(self):
        return ""

    async def get_config_widget_state(self):
        scope = self.config.scope
        text = (
            f"插件：{'启用' if self.config.enabled else '停用'}\n"
            f"范围：{scope.mode}；默认私聊：{'允许' if scope.allow_private else '关闭'}\n"
            f"已识别会话：{len(self.scope_gate.routes)}；公共引用缓存：{len(self.scope_gate.cache)}\n"
            + self.console_text()
        )
        return {
            "ecosystem_status": ConfigWidgetState(text=text[:2000], tone="neutral"),
            "refresh_scope": ConfigWidgetState(text="下次使用时重新解析公共集合"),
        }

    async def on_config_widget_action(self, action_id):
        if action_id != "refresh_scope":
            raise ValueError("未知控制台操作")
        self.scope_gate.cache.clear()
        self.scope_gate.warned.clear()
