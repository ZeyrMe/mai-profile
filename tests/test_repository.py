"""Repository contracts that must also hold in an isolated plugin checkout."""

import json
import tomllib
from importlib.metadata import version
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parents[1]


def test_example_matches_sdk_defaults(plugin_class):
    actual = tomllib.loads((ROOT / "config.toml.example").read_text())
    assert actual == plugin_class.build_default_config(), "Update config.toml.example to match SDK defaults"


def test_manifest_matches_project_metadata():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    manifest = json.loads((ROOT / "_manifest.json").read_text())
    assert manifest["id"] == f"zeyr.{project['name']}"
    assert manifest["version"] == project["version"]
    requirements = {
        canonicalize_name(req.name): req
        for raw in project["dependencies"]
        if canonicalize_name((req := Requirement(raw)).name) != "maibot-plugin-sdk"
    }
    declared = {
        canonicalize_name(item["name"]): Requirement(f"{item['name']}{item['version_spec']}")
        for item in manifest.get("dependencies", [])
        if item["type"] == "python_package"
    }
    assert requirements.keys() == declared.keys(), "Runtime dependencies must match the host manifest"
    for name, requirement in requirements.items():
        assert requirement.specifier == declared[name].specifier, name


def test_installed_dependencies_satisfy_project():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    requirements = [*project["dependencies"], *project["optional-dependencies"]["dev"]]
    for raw in requirements:
        requirement = Requirement(raw)
        if requirement.marker is None or requirement.marker.evaluate():
            assert version(requirement.name) in requirement.specifier, raw
