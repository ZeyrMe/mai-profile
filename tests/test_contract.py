import json
from pathlib import Path


def test_declared_components_and_config(plugin_class):
    instance = plugin_class()
    instance.set_plugin_config({})
    assert instance.config is not None
    assert plugin_class.build_config_schema()["sections"]
    manifest = json.loads((Path(__file__).resolve().parents[1] / "_manifest.json").read_text())
    assert manifest["id"].startswith("zeyr.")
    assert manifest["host_application"]["min_version"] == "1.4.8"
    names = [c["name"] for c in instance.get_components()]
    assert len(names) == len(set(names))
