import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
NAME = "test_" + ROOT.name.replace("-", "_")
spec = importlib.util.spec_from_file_location(
    NAME, ROOT / "plugin.py", submodule_search_locations=[str(ROOT)]
)
module = importlib.util.module_from_spec(spec)
sys.modules[NAME] = module
spec.loader.exec_module(module)


@pytest.fixture
def plugin_class():
    return module.Plugin
