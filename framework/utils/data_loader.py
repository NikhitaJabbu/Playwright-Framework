"""
Loads test data from JSON/YAML instead of inlining fixtures in test code.

Why: a data-driven test (via pytest.mark.parametrize) should be able to
grow from 3 cases to 30 without touching the test function -- only the
data file changes. Keeping data out of the test body is also what lets a
non-engineer (or a future PR) add a new checkout-error case by editing
JSON, not Python.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "tests" / "data"


def load_json(filename: str) -> Any:
    with open(DATA_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


def load_yaml(filename: str) -> Any:
    with open(DATA_DIR / filename, encoding="utf-8") as f:
        return yaml.safe_load(f)
