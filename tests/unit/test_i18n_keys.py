"""English and Malayalam UI strings must define the same keys."""

import json
from pathlib import Path

I18N_DIR = Path(__file__).resolve().parents[2] / "frontend" / "static" / "i18n"


def _keys(obj: dict, prefix: str = "") -> set[str]:
    out: set[str] = set()
    for key, value in obj.items():
        if isinstance(value, dict):
            out |= _keys(value, f"{prefix}{key}.")
        else:
            out.add(f"{prefix}{key}")
    return out


def test_en_and_ml_have_the_same_keys():
    en = _keys(json.loads((I18N_DIR / "en.json").read_text(encoding="utf-8")))
    ml = _keys(json.loads((I18N_DIR / "ml.json").read_text(encoding="utf-8")))
    assert en - ml == set(), f"missing in ml.json: {sorted(en - ml)}"
    assert ml - en == set(), f"missing in en.json: {sorted(ml - en)}"
