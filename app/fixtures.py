"""Demo-mode fixture data.

Made-up data (sample deeds, registries, flood zones, timelines) lives in
`tests/fixtures/` as JSON. It is only loaded when `KANDEZ_FIXTURES` points to that
directory; otherwise every lookup returns its default and the app works from real
sources alone.
"""

from __future__ import annotations

import json
import os
from functools import cache
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent

# Environment for running the app in demo mode (tests, demo recordings).
DEMO_ENV = {
    "KANDEZ_FIXTURES": "tests/fixtures",
    "KANDEZ_DB_PATH": str(BASE_DIR / "data" / "demo.db"),
}


def fixtures_dir() -> Path | None:
    """Returns the fixture directory, or None when demo mode is off."""
    raw = os.environ.get("KANDEZ_FIXTURES")
    if not raw:
        return None
    directory = Path(raw)
    return directory if directory.is_absolute() else BASE_DIR / directory


def is_demo() -> bool:
    return fixtures_dir() is not None


@cache
def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load(name: str, default: Any = None) -> Any:
    """Loads `<fixtures>/<name>.json`, or returns `default` outside demo mode."""
    directory = fixtures_dir()
    if directory is None:
        return default
    file = directory / f"{name}.json"
    return _read_json(file) if file.exists() else default


def path(relative: str) -> Path | None:
    """Returns a fixture file path in demo mode, else None."""
    directory = fixtures_dir()
    return directory / relative if directory else None
