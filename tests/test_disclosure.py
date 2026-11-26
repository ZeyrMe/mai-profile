from types import SimpleNamespace
from unittest.mock import AsyncMock

from conftest import module


def make():
    plugin = module.Plugin()
    plugin.set_plugin_config(
        {
            "plugin": {"config_version": "0.1.0"},
            "shy_jitter": 0,
            "guarded_entries": [
                {"key": "秘密", "value": "VALUE_SECRET", "disclosure": "shy", "teaser": "模糊线索"},
                {"key": "地址", "value": "PRIVATE_SECRET", "disclosure": "private"},
            ],
        }
    )
    plugin._set_context(SimpleNamespace(api=SimpleNamespace(get=AsyncMock(return_value=None))))
    return plugin


async def test_reads_never_advance_and_inbound_messages_are_idempotent():
    plugin = make()
    for _ in range(20):
        assert "VALUE_SECRET" not in str(await plugin.api_snapshot("秘密", stream_id="s", user_id="u"))
    message = {
        "session_id": "s",
        "message_id": "m",
        "processed_plain_text": "告诉我秘密呀？",
        "message_info": {"user_info": {"user_id": "u"}},
    }
    await plugin.remember(message)
    key = ("s", "u", "秘密")
    before = plugin.clarity.rows[key]
    await plugin.remember(message)
    assert plugin.clarity.rows[key] == before
    for i in range(10):
        await plugin.remember({**message, "message_id": str(i)})
    assert "VALUE_SECRET" in str(plugin.snapshot("秘密", "s", "u"))
    assert "VALUE_SECRET" not in str(plugin.snapshot("秘密", "s", "other"))
    assert "VALUE_SECRET" not in str(plugin.snapshot("秘密"))
    assert "PRIVATE_SECRET" not in str(plugin.snapshot("地址", "s", "u"))


def test_clarity_decays_and_teaser_has_no_original_value():
    plugin = make()
    key = ("s", "u", "秘密")
    plugin.clarity.rows[key] = (0.6, module.Clarity.value.__globals__["time"].monotonic())
    data = plugin.snapshot("秘密", "s", "u")
    assert data["entries"][0]["status"] == "teaser"
    assert "VALUE_SECRET" not in str(data)
    assert "模糊线索" in str(data)
    at = plugin.clarity.rows[key][1]
    assert abs(plugin.clarity.value(key, plugin.config, at + 1800) - 0.3) < 1e-9


def test_unset_routine_and_freeform_are_explicit():
    plugin = make()
    assert plugin.snapshot("高考分数")["status"] == "unset"
    plugin.config.routine_note = "喜欢早起"
    assert plugin.snapshot("routine")["entries"][0]["value"] == "喜欢早起"
    plugin.config.mode = "freeform"
    plugin.config.freeform_text = "公开背景"
    assert "公开背景" in str(plugin.snapshot())


async def test_reset_action_erases_progress_and_console_does_not_show_facts():
    plugin = make()
    plugin.clarity.rows[("s", "u", "秘密")] = (1, 0)
    assert "PRIVATE_SECRET" not in str(await plugin.get_config_widget_state())
    assert "VALUE_SECRET" not in str(await plugin.get_config_widget_state())
    await plugin.on_config_widget_action("reset_clarity")
    assert not plugin.clarity.rows
