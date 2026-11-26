"""Local SDK boundary helpers; vendored so every repository installs independently."""

from __future__ import annotations

import asyncio
import json
import os
import re
import tempfile
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from string import Formatter
from typing import Any


def result(data: Any = None, *, error: str = "") -> dict:
    return {
        "schema_version": 1,
        "success": not bool(error),
        "data": data,
        "error": error,
        "content": error or json.dumps(data, ensure_ascii=False),
    }


def render(template: str, **values: Any) -> str:
    # Only plain named fields; never execute expressions or traverse Python objects.
    fields = [field for _, field, _, _ in Formatter().parse(template) if field is not None]
    if any(not re.fullmatch(r"[a-z_]+", field) for field in fields):
        raise ValueError("模板只支持 {name} 形式的命名字段")
    return template.format_map({key: str(value) for key, value in values.items()})


def item_text(items: list[dict]) -> str:
    return "\n".join(
        str(part.get("text", ""))
        for item in items
        if item.get("item_type") == "UserMessageItem"
        and not str(item.get("meta", {}).get("item_id", "")).startswith("zeyr:")
        for part in item.get("parts", [])
        if part.get("type") == "text"
    )


def inject(kwargs: dict, plugin_id: str, text: str, limit: int) -> dict:
    if not text:
        return {"action": "continue"}
    if "items" in kwargs:
        # Context Items v1, not OpenAI wire messages. Replace only our own transient item.
        if kwargs.get("item_schema_version", 1) != 1:
            return {"action": "continue"}
        identity = f"zeyr:{plugin_id}:context"
        items = [item for item in kwargs["items"] if item.get("meta", {}).get("item_id") != identity]
        items.append(
            {
                "item_type": "UserMessageItem",
                "meta": {
                    "item_id": identity,
                    "logical_turn_id": None,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                "parts": [{"type": "text", "text": text[:limit]}],
            }
        )
        kwargs = {**kwargs, "items": items}
    else:
        kwargs = {
            **kwargs,
            "extra_prompt": "\n".join(filter(None, [kwargs.get("extra_prompt", ""), text[:limit]])),
        }
    return {"action": "continue", "modified_kwargs": kwargs}


def identity(message: dict) -> tuple[str, str, str, str]:
    info = message.get("message_info") or {}
    user = info.get("user_info") or {}
    group = info.get("group_info") or {}
    return (
        str(message.get("platform") or user.get("platform") or ""),
        str(user.get("user_id") or ""),
        str(group.get("group_id") or ""),
        str(message.get("session_id") or message.get("stream_id") or ""),
    )


class RecentMessages:
    """Bounded transient message index. No chat text is persisted by this helper."""

    def __init__(self, limit: int = 256):
        self.limit = limit
        self.rows: OrderedDict[str, dict] = OrderedDict()

    def add(self, message: dict) -> None:
        key = str(message.get("message_id") or "")
        if key:
            self.rows[key] = message
            self.rows.move_to_end(key)
            while len(self.rows) > self.limit:
                self.rows.popitem(last=False)

    def matched(self, kwargs: dict) -> list[dict]:
        session = str(kwargs.get("session_id") or kwargs.get("stream_id") or "")
        anchor = str(kwargs.get("reply_message_id") or "")
        if anchor in self.rows:
            return [self.rows[anchor]]
        text = item_text(kwargs.get("items", []))
        return [
            message
            for key, message in self.rows.items()
            if (session and identity(message)[3] == session) or key in text
        ][-20:]


class StateFile:
    """Atomic replace: a corrupt file raises instead of silently erasing a life timeline."""

    def __init__(self, path: Path, initial: dict):
        self.path = path
        self.data = json.loads(json.dumps(initial))
        if path.exists():
            loaded = json.loads(path.read_text())
            if loaded.get("schema_version") != initial["schema_version"]:
                raise ValueError("不支持的状态文件版本")
            self.data = loaded

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix=".state-", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w") as handle:
                json.dump(self.data, handle, ensure_ascii=False)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(name, self.path)
        finally:
            if os.path.exists(name):
                os.unlink(name)


async def optional_api(ctx: Any, full_name: str, **kwargs: Any) -> Any:
    try:
        async with asyncio.timeout(0.4):
            if not await ctx.api.get(full_name, version="1"):
                return None
            payload = await ctx.api.call(full_name, version="1", **kwargs)
        # Installed SDK exposes Host's outer success/result envelope.
        while isinstance(payload, dict) and "result" in payload and "schema_version" not in payload:
            if not payload.get("success", False):
                return None
            payload = payload["result"]
        if not isinstance(payload, dict) or not payload.get("success"):
            return None
        return payload.get("data")
    except (Exception, TimeoutError):
        return None
