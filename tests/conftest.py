"""Shared import helper for loading hyphenated hook modules by path."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).parent.parent / "plugins" / "do-cc-forge" / "hooks"

# hook modules import sibling modules (e.g. hook_utils) via
# `sys.path.insert(0, str(Path(__file__).parent))`, so make sure that
# still resolves when tests import them directly.
sys.path.insert(0, str(HOOKS_DIR))


def load_hook_module(name: str):
    spec = importlib.util.spec_from_file_location(name, HOOKS_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module
