from conftest import module


def make(**config):
    instance = module.Plugin()
    instance.set_plugin_config({"plugin": {"config_version": "0.1.0"}, **config})
    return instance


def test_private_entries_never_leave_snapshot_or_tool():
    plugin = make(
        entries=[
            {"key": "school", "value": "公开学校"},
            {"key": "address", "value": "SECRET", "visibility": "private"},
        ]
    )
    assert "SECRET" not in str(plugin.snapshot())
    assert "SECRET" not in str(plugin.snapshot("address"))


def test_triggered_fields_require_matching_topic():
    plugin = make(
        entries=[{"key": "food", "value": "按时吃饭", "visibility": "triggered", "topics": ["健康"]}],
        trigger_words={"健康": ["低血糖"]},
    )
    assert plugin.snapshot()["entries"] == []
    assert plugin.snapshot("天气")["entries"] == []
    assert plugin.snapshot("低血糖")["entries"][0]["key"] == "food"


def test_push_requires_actual_inbound_hit_and_preserves_boundary():
    plugin = make(
        entries=[{"key": "school", "value": "公开学校", "topics": ["学校"]}],
        trigger_words={"学校": ["学校"]},
        privacy_boundary="不说住址",
        hint_chars=20,
    )
    kwargs = {
        "session_id": "s",
        "items": [{"item_type": "UserMessageItem", "parts": [{"type": "text", "text": "学校"}]}],
    }
    assert plugin.hint(kwargs) == ""
    plugin.recent.add({"message_id": "m", "session_id": "s", "processed_plain_text": "你在哪所学校？"})
    assert "不说住址" in plugin.hint(kwargs)
    assert len(plugin.hint(kwargs)) <= 20


async def test_visible_tool_and_disabled_plugin():
    plugin = make(enabled=False, entries=[{"key": "name", "value": "名字"}])
    assert (await plugin.query_profile())["data"]["entries"] == []
    tool = next(c for c in plugin.get_components() if c["name"] == "query_self_profile")
    assert tool["metadata"]["visibility"] == "visible"


def test_sdk_schema_keeps_first_use_form_small():
    schema = module.Plugin.build_config_schema()
    fields = schema["sections"]["general"]["fields"]
    basic = [name for name, field in fields.items() if not field.get("depends_on")]
    assert len(basic) <= 5
    assert fields["privacy_boundary"]["depends_on"] == "show_advanced"
