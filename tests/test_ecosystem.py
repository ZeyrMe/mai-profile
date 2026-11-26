"""Scope safety is exercised identically by each standalone installation."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from conftest import module
from maibot_sdk.config_widgets import ConfigWidgetSnapshot

ScopeConfig = module.ScopeConfig if hasattr(module, "ScopeConfig") else module.config_models.ScopeConfig
ChatIdentity = module.EcosystemMixin.in_scope.__globals__["ChatIdentity"]
ScopeGate = module.EcosystemMixin.in_scope.__globals__["ScopeGate"]


def chat(platform="qq", user="person", group="room", stream="stream"):
    return ChatIdentity(platform, user, group, stream)


async def test_default_scope_allows_group_and_private():
    gate = ScopeGate()
    assert await gate.allows(ScopeConfig(), chat())
    assert await gate.allows(ScopeConfig(), chat(group=""))


async def test_private_default_off_still_allows_explicit_private():
    gate = ScopeGate()
    config = ScopeConfig(allow_private=False, privates=["private:friend"])
    assert not await gate.allows(config, chat(user="stranger", group=""))
    assert await gate.allows(config, chat(user="friend", group=""))
    assert await gate.allows(config, chat())


async def test_whitelist_group_private_user_platform_and_unknown_are_distinct():
    gate = ScopeGate()
    config = ScopeConfig(mode="whitelist", groups=["group:room"], users=["telegram:user:friend"])
    assert await gate.allows(config, chat())
    assert not await gate.allows(config, chat(group="elsewhere"))
    assert not await gate.allows(config, chat(user="room", group=""))
    assert await gate.allows(config, chat("telegram", "friend", "elsewhere"))
    assert not await gate.allows(config, chat("qq", "friend", "elsewhere"))
    assert not await gate.allows(config, ChatIdentity(stream_id="unknown"))


async def test_blacklist_and_explicit_exclude_take_priority():
    gate = ScopeGate()
    assert not await gate.allows(ScopeConfig(mode="blacklist", groups=["room"]), chat())
    config = ScopeConfig(mode="whitelist", groups=["room"], exclude=["user:person"])
    assert not await gate.allows(config, chat())
    assert await gate.allows(ScopeConfig(groups=["other"]), chat())


async def test_unavailable_reference_warns_once_and_never_fills_whitelist():
    gate = ScopeGate()
    ctx = SimpleNamespace(api=SimpleNamespace(get=AsyncMock(return_value=None)), logger=Mock())
    config = ScopeConfig(mode="whitelist", groups=["@set:friends"])
    assert not await gate.allows(config, chat(), ctx)
    assert not await gate.allows(config, chat(), ctx)
    assert ctx.api.get.await_count == 1
    assert ctx.logger.warning.call_count == 1


async def test_public_reference_envelope_and_local_resolver_do_not_recurse():
    gate = ScopeGate()
    ctx = SimpleNamespace(
        api=SimpleNamespace(
            get=AsyncMock(return_value=True),
            call=AsyncMock(
                return_value={
                    "success": True,
                    "result": {
                        "schema_version": 1,
                        "success": True,
                        "data": {"groups": ["telegram:group:room"]},
                    },
                }
            ),
        )
    )
    config = ScopeConfig(mode="whitelist", groups=["@set:friends"])
    assert await gate.allows(config, chat("telegram"), ctx)
    assert not await gate.allows(config, chat("qq"), ctx)

    def local(ref):
        return {"groups": ["qq:group:room"]}

    assert await ScopeGate().allows(config, chat(), local=local)


async def test_all_reference_lookups_share_one_deadline():
    gate = ScopeGate()

    async def delayed(*args, **kwargs):
        await asyncio.sleep(1)

    ctx = SimpleNamespace(api=SimpleNamespace(get=delayed), logger=Mock())
    config = ScopeConfig(mode="whitelist", groups=["@set:a", "@set:b"], api_timeout_seconds=0.01)
    async with asyncio.timeout(0.1):
        assert not await gate.allows(config, chat(), ctx)
    assert ctx.logger.warning.call_count == 1


async def test_console_snapshot_is_complete_and_refresh_does_not_need_host():
    plugin = module.Plugin()
    plugin.set_plugin_config({})
    states = await plugin.get_config_widget_state()
    snapshot = ConfigWidgetSnapshot(widgets=plugin.config_widgets, states=states)
    assert snapshot.states["ecosystem_status"].text
    plugin.scope_gate.cache["ref"] = (0, {})
    await plugin.on_config_widget_action("refresh_scope")
    assert not plugin.scope_gate.cache
    with pytest.raises(ValueError):
        await plugin.on_config_widget_action("unregistered")


async def test_stream_identity_is_bounded_and_recovers_for_later_hooks():
    plugin = module.Plugin()
    plugin.set_plugin_config(
        {
            "plugin": {"config_version": "0.1.0"},
            "scope": {
                "mode": "whitelist",
                "groups": ["room"],
                "max_tracked_streams": 1,
            },
        }
    )
    message = {
        "platform": "qq",
        "session_id": "stream",
        "message_info": {
            "user_info": {"user_id": "person"},
            "group_info": {"group_id": "room"},
        },
    }
    assert await plugin.in_scope(message)
    assert await plugin.in_scope(session_id="stream")
    assert not await plugin.in_scope(session_id="elsewhere")
    await plugin.in_scope({**message, "session_id": "new"})
    assert len(plugin.scope_gate.routes) == 1
    assert not await plugin.in_scope(session_id="stream")


def test_scope_rejects_malformed_anchors_and_config_has_no_top_level_dict():
    with pytest.raises(ValueError):
        ScopeConfig(groups=["unknown:value"])
    with pytest.raises(ValueError):
        ScopeConfig(users=["@set:"])
    schema = module.Config.model_json_schema()
    for name, field in schema["properties"].items():
        assert not (field.get("type") == "object" and "additionalProperties" in field), name


async def test_unknown_chat_cannot_bypass_private_default_off():
    assert not await ScopeGate().allows(ScopeConfig(allow_private=False), ChatIdentity())


def test_scope_section_is_native_collapsed_with_chinese_labels():
    schema = module.Plugin.build_config_schema()
    assert schema["sections"]["scope"]["collapsed"]
    assert schema["sections"]["scope"]["fields"]["mode"]["label"] != "mode"
