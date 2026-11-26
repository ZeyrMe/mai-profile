from typing import Any

from maibot_sdk import API, HookHandler, MaiBotPlugin, Tool
from maibot_sdk.types import HookOrder, ToolParameterInfo

from .config_models import Config
from .ecosystem import EcosystemMixin
from .runtime import RecentMessages, inject, render, result


class Plugin(EcosystemMixin, MaiBotPlugin):
    config_model = Config

    def __init__(self):
        super().__init__()
        self.recent = RecentMessages()

    def console_text(self):
        return f"档案条目：{len(self.config.entries)}；入站消息索引：{len(self.recent.rows)}"

    async def on_load(self):
        self.ctx.logger.info("麦设已加载")

    async def on_unload(self):
        self.recent = RecentMessages()

    async def on_config_update(self, scope, config_data, version):
        pass

    def snapshot(self, topic: str = "") -> dict[str, Any]:
        if not self.config.enabled:
            return {"entries": [], "boundary": ""}
        topic = topic.strip().casefold()
        trigger_topics = {
            key.casefold()
            for key, words in self.config.trigger_words.items()
            if any(word and word.casefold() in topic for word in words)
        }
        rows = []
        for entry in self.config.entries:
            if not entry.key.strip() or not entry.value.strip() or entry.visibility == "private":
                continue
            topics = {item.casefold() for item in entry.topics}
            hit = bool(topic and (any(item in topic for item in topics) or trigger_topics & topics))
            if entry.visibility == "triggered" and not hit:
                continue
            if topic and topics and not hit:
                continue
            rows.append({"key": entry.key, "value": entry.value})
        return {"entries": rows, "boundary": self.config.privacy_boundary}

    @API("get_snapshot", description="公开人设摘要，永不返回 private 字段", version="1", public=True)
    async def api_snapshot(self, topic: str = "", **kwargs):
        if kwargs.get("stream_id") and not await self.in_scope(**kwargs):
            return result(error="当前会话不在插件生效范围")
        return result(self.snapshot(topic))

    @Tool(
        "query_self_profile",
        description="查自己的公开人设档案与隐私留白；需要人物设定细节时使用。",
        parameters=[ToolParameterInfo(name="topic", description="要查询的话题", required=False, default="")],
        visibility="visible",
    )
    async def query_profile(self, topic: str = "", **kwargs):
        if not await self.in_scope(**kwargs):
            return result(error="当前会话不在插件生效范围")
        return result(self.snapshot(topic))

    @HookHandler("chat.receive.after_process")
    async def remember(self, message=None, **kwargs):
        if self.config.enabled and await self.in_scope(message, **kwargs):
            self.recent.add(message or {})
        return {"action": "continue"}

    def hint(self, kwargs: dict) -> str:
        messages = self.recent.matched(kwargs)
        # Match actual inbound text, never the host's static prompt instructions.
        text = "\n".join(str(message.get("processed_plain_text") or "") for message in messages[-3:])
        if not self.config.enabled or not any(
            word and word.casefold() in text.casefold()
            for words in self.config.trigger_words.values()
            for word in words
        ):
            return ""
        data = self.snapshot(text)
        rows = [render(self.config.snapshot_template, **entry) for entry in data["entries"]]
        boundary = data["boundary"][: self.config.hint_chars]
        content = "；".join(rows)[: max(0, self.config.hint_chars - len(boundary) - 1)]
        return "；".join(filter(None, [content, boundary]))

    @HookHandler("maisaka.planner.before_request", order=HookOrder.NORMAL)
    async def planner(self, **kwargs):
        if not await self.in_scope(**kwargs):
            return {"action": "continue"}
        return inject(kwargs, "mai-profile", self.hint(kwargs), self.config.hint_chars)

    @HookHandler("maisaka.replyer.before_request", order=HookOrder.NORMAL)
    async def replyer(self, **kwargs):
        if not await self.in_scope(**kwargs):
            return {"action": "continue"}
        return inject(kwargs, "mai-profile", self.hint(kwargs), self.config.hint_chars)


def create_plugin():
    return Plugin()
