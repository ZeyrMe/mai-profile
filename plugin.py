from typing import Any

from maibot_sdk import API, HookHandler, MaiBotPlugin, Tool
from maibot_sdk.config_widgets import ConfigWidget, ConfigWidgetState
from maibot_sdk.types import HookOrder, ToolParameterInfo

from .config_models import Config
from .disclosure import Clarity
from .ecosystem import ChatIdentity, EcosystemMixin
from .runtime import RecentMessages, inject, optional_api, render, result


class Plugin(EcosystemMixin, MaiBotPlugin):
    config_model = Config
    config_widgets = EcosystemMixin.config_widgets + [
        ConfigWidget(
            id="reset_clarity",
            kind="action",
            label="重置全部兜着进度",
            confirmation="重置所有会话的松口进度？",
        ),
    ]

    def __init__(self):
        super().__init__()
        self.recent = RecentMessages()
        self.clarity = Clarity()

    def console_text(self):
        entries = self.profile_entries()
        stages = {"浓雾": 0, "动摇中": 0, "已松口": 0}
        progress = []
        for key in self.clarity.rows:
            value = self.clarity.value(key, self.config)
            stage = (
                "已松口"
                if value >= self.config.reveal_threshold
                else "动摇中"
                if value >= self.config.teaser_threshold
                else "浓雾"
            )
            stages[stage] += 1
            progress.append(f"{key[2]}（{stage} {value:.0%}）")
        public_count = sum(row.disclosure == "public" and row.visibility != "private" for row in entries)
        guarded_count = sum(
            row.disclosure in ("shy", "private") or row.visibility == "private" for row in entries
        )
        stage_summary = (
            f"浓雾 {stages['浓雾']} 项、动摇中 {stages['动摇中']} 项、已松口 {stages['已松口']} 项"
            if progress
            else "暂无正在被追问的兜着项"
        )
        return (
            f"档案条目：公开 {public_count} 条，兜着/保密 {guarded_count} 条 · 作息偏好：{'已填写' if self.config.routine_note else '未填写'}\n"
            f"兜着松口进度：{stage_summary}" + (f"（{'；'.join(progress[:6])}）" if progress else "")
        )

    async def get_config_widget_state(self):
        return {**await super().get_config_widget_state(), "reset_clarity": ConfigWidgetState()}

    async def on_config_widget_action(self, action_id):
        if action_id == "reset_clarity":
            self.clarity = Clarity()
            return
        await super().on_config_widget_action(action_id)

    def profile_entries(self):
        return self.config.entries + self.config.basic_fields + self.config.guarded_entries

    async def on_load(self):
        self.ctx.logger.info("麦设已加载")

    async def on_unload(self):
        self.recent = RecentMessages()

    async def on_config_update(self, scope, config_data, version):
        pass

    def matching(self, entry, topic):
        words = [entry.key, *entry.topics]
        for rule in self.config.trigger_rules:
            if rule.topic in entry.topics or rule.topic == entry.key:
                words.extend(rule.words)
        return any(word and word.casefold() in topic.casefold() for word in words)

    def snapshot(self, topic: str = "", stream_id="", user_id="") -> dict[str, Any]:
        if not self.config.enabled:
            return {"entries": [], "boundary": "", "status": "disabled"}
        rows = []
        topic = topic.strip()
        for entry in self.profile_entries():
            if not entry.key.strip() or not entry.value.strip():
                continue
            hit = bool(topic and self.matching(entry, topic))
            if topic and not hit:
                continue
            if entry.visibility == "private" or entry.disclosure == "private":
                if hit:
                    rows.append({"key": entry.key, "status": "private", "policy": self.config.private_policy})
                continue
            if entry.visibility == "triggered" and not hit:
                continue
            if entry.disclosure == "shy":
                clarity = (
                    self.clarity.value((stream_id, user_id, entry.key), self.config)
                    if stream_id and user_id
                    else 0
                )
                row = {"key": entry.key, "status": "withheld", "policy": self.config.withheld_policy}
                if clarity >= self.config.reveal_threshold:
                    row.update(status="revealed", value=entry.value, policy=self.config.revealed_policy)
                elif clarity >= self.config.teaser_threshold:
                    row.update(status="teaser", teaser=entry.teaser, policy=self.config.teaser_policy)
                rows.append(row)
            else:
                rows.append({"key": entry.key, "value": entry.value, "status": "public"})
        routine = topic.casefold() in ("routine", "作息", "作息偏好")
        if self.config.routine_note and (not topic or routine):
            rows.append({"key": "routine", "value": self.config.routine_note, "status": "public"})
        if self.config.likes_and_dislikes and (
            not topic or any(word in topic for word in ("喜好", "雷区", "喜欢"))
        ):
            rows.append(
                {"key": "likes_and_dislikes", "value": self.config.likes_and_dislikes, "status": "public"}
            )
        if self.config.mode == "freeform" and self.config.freeform_text:
            rows.append({"key": "freeform", "value": self.config.freeform_text, "status": "public"})
        return {
            "entries": rows,
            "boundary": self.config.privacy_boundary,
            "status": "ok" if rows else "unset",
            "policy": "" if rows else self.config.unset_policy,
        }

    def request_identity(self, kwargs):
        chat = ChatIdentity.from_message(
            kwargs.get("message") or kwargs, kwargs.get("stream_id") or kwargs.get("session_id") or ""
        )
        if not chat.user_id:
            messages = self.recent.matched(kwargs)
            if messages:
                chat = ChatIdentity.from_message(messages[-1])
        return chat

    @API("get_snapshot", description="公开人设摘要，永不返回 private 字段", version="1", public=True)
    async def api_snapshot(self, topic: str = "", **kwargs):
        if kwargs.get("stream_id") and not await self.in_scope(**kwargs):
            return result(error="当前会话不在插件生效范围")
        return result(
            self.snapshot(topic, str(kwargs.get("stream_id") or ""), str(kwargs.get("user_id") or ""))
        )

    @Tool(
        "query_self_profile",
        description="查自己的公开人设档案与隐私留白；需要人物设定细节时使用。",
        parameters=[ToolParameterInfo(name="topic", description="要查询的话题", required=False, default="")],
        visibility="visible",
    )
    async def query_profile(self, topic: str = "", **kwargs):
        if not await self.in_scope(**kwargs):
            return result(error="当前会话不在插件生效范围")
        chat = self.request_identity(kwargs)
        return result(self.snapshot(topic, chat.stream_id, chat.user_id))

    @HookHandler("chat.receive.after_process")
    async def remember(self, message=None, **kwargs):
        if self.config.enabled and await self.in_scope(message, **kwargs):
            self.recent.add(message or {})
            chat = ChatIdentity.from_message(message)
            text = str((message or {}).get("processed_plain_text") or "").strip()
            if chat.stream_id and chat.user_id and len(text) >= self.config.followup_min_chars:
                candidates = [
                    row
                    for row in self.profile_entries()
                    if row.disclosure == "shy" and row.visibility != "private" and self.matching(row, text)
                ]
                if candidates:
                    relation = await optional_api(
                        self.ctx,
                        "zeyr.mai-circle.get_chat_weight",
                        platform=chat.platform,
                        user_ids=[chat.user_id],
                        scope_kind=chat.kind,
                    )
                    multiplier = (self.config.private_multiplier if chat.kind == "private" else 1) * (
                        1 + float((relation or {}).get("relax_bonus", 0)) * self.config.relation_multiplier
                    )
                    for row in candidates:
                        self.clarity.advance(
                            (chat.stream_id, chat.user_id, row.key),
                            str((message or {}).get("message_id") or ""),
                            row.resistance,
                            multiplier,
                            self.config,
                        )
        return {"action": "continue"}

    def hint(self, kwargs: dict) -> str:
        messages = self.recent.matched(kwargs)
        # Match actual inbound text, never the host's static prompt instructions.
        text = "\n".join(str(message.get("processed_plain_text") or "") for message in messages[-3:])
        if (
            not self.config.enabled
            or not any(
                word and word.casefold() in text.casefold()
                for words in self.config.trigger_words.values()
                for word in words
            )
            and not any(self.matching(entry, text) for entry in self.profile_entries())
        ):
            return ""
        chat = self.request_identity(kwargs)
        data = self.snapshot(text, chat.stream_id, chat.user_id)
        rows = [
            render(self.config.snapshot_template, **entry)
            if "value" in entry
            else str(entry.get("teaser") or entry.get("policy") or "")
            for entry in data["entries"]
        ]
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
