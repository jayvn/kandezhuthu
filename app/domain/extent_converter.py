"""Kerala Land Measure Extent Converter and Arithmetic Validator.

Provides deterministic conversions between statutory and customary units used in Kerala:
- Hectares (ഹെക്ടർ) & Ares (ആർ) (used in Post-1960s Survey, Revenue records, BTR, Thandaper)
- Cents (സെന്റ്) & Acres (ഏക്കർ) (used in customary Kerala title deeds)
- Square Meters (ചതുരശ്ര മീറ്റർ) & Square Feet (ചതുരശ്ര അടി) (used in KPBR/KMBR plinth and setbacks)

Also provides extent discrepancy and inflation detection (Nemo Dat Quod Non Habet).
"""

from __future__ import annotations

import re
from typing import NamedTuple, Tuple

# Statutory and standard conversion constants for Kerala
CENTS_PER_ARE: float = 2.4710538       # 1 Are = 2.47105 Cents
ARES_PER_CENT: float = 0.40468564      # 1 Cent = 0.404686 Ares
ARES_PER_HECTARE: float = 100.0        # 1 Hectare = 100 Ares
CENTS_PER_HECTARE: float = 247.10538   # 1 Hectare = 247.105 Cents
SQM_PER_CENT: float = 40.468564        # 1 Cent = 40.4686 Sq. Meters
SQFT_PER_CENT: float = 435.6           # 1 Cent = 435.6 Sq. Feet
SQFT_PER_SQM: float = 10.7639104       # 1 Sq. Meter = 10.7639 Sq. Feet
SQM_PER_ARE: float = 100.0             # 1 Are = 100 Sq. Meters
SQM_PER_HECTARE: float = 10000.0       # 1 Hectare = 10,000 Sq. Meters
CENTS_PER_ACRE: float = 100.0          # 1 Acre = 100 Cents


def cents_to_ares(cents: float) -> float:
    """Converts Kerala Cents to Ares."""
    return round(cents * ARES_PER_CENT, 4)


def ares_to_cents(ares: float) -> float:
    """Converts Ares to Kerala Cents."""
    return round(ares * CENTS_PER_ARE, 4)


def hectares_to_ares(hectares: float) -> float:
    """Converts Hectares to Ares."""
    return round(hectares * ARES_PER_HECTARE, 4)


def ares_to_hectares(ares: float) -> float:
    """Converts Ares to Hectares."""
    return round(ares / ARES_PER_HECTARE, 6)


def hectares_to_cents(hectares: float) -> float:
    """Converts Hectares to Kerala Cents."""
    return round(hectares * CENTS_PER_HECTARE, 4)


def cents_to_hectares(cents: float) -> float:
    """Converts Kerala Cents to Hectares."""
    return round(cents / CENTS_PER_HECTARE, 6)


def cents_to_sqm(cents: float) -> float:
    """Converts Kerala Cents to Square Meters."""
    return round(cents * SQM_PER_CENT, 4)


def sqm_to_cents(sqm: float) -> float:
    """Converts Square Meters to Kerala Cents."""
    return round(sqm / SQM_PER_CENT, 4)


def cents_to_sqft(cents: float) -> float:
    """Converts Kerala Cents to Square Feet."""
    return round(cents * SQFT_PER_CENT, 2)


def sqft_to_cents(sqft: float) -> float:
    """Converts Square Feet to Kerala Cents."""
    return round(sqft / SQFT_PER_CENT, 4)


def sqm_to_sqft(sqm: float) -> float:
    """Converts Square Meters to Square Feet."""
    return round(sqm * SQFT_PER_SQM, 2)


def sqft_to_sqm(sqft: float) -> float:
    """Converts Square Feet to Square Meters."""
    return round(sqft / SQFT_PER_SQM, 4)


class ParsedExtent(NamedTuple):
    cents: float | None = None
    ares: float | None = None
    hectares: float | None = None
    sq_meters: float | None = None
    sq_feet: float | None = None


def parse_extents_from_text(text: str) -> ParsedExtent:
    """Extracts all mentioned land extent figures from bilingual Malayalam/English text."""
    cents = None
    ares = None
    hectares = None
    sqm = None
    sqft = None

    # 1. Cents (സെന്റ്)
    cents_m = re.search(r"(\d+(?:\.\d+)?)\s*(?:cents?|സെന്റ്|സെന്റ[്ി])", text, re.I)
    if cents_m:
        cents = float(cents_m.group(1))

    # 2. Ares (ആർ)
    ares_m = re.search(r"(\d+(?:\.\d+)?)\s*(?:ares?|ആർ|ആറ[്ി])(?!\w)", text, re.I)
    if ares_m:
        ares = float(ares_m.group(1))

    # 3. Hectares (ഹെക്ടർ)
    ha_m = re.search(r"(\d+(?:\.\d+)?)\s*(?:hectares?|ഹെക്ടർ|ഹെക്ടറ[്ി]|ha\b)", text, re.I)
    if ha_m:
        hectares = float(ha_m.group(1))

    # 4. Square Meters (ചതുരശ്ര മീറ്റർ)
    sqm_m = re.search(r"(\d+(?:\.\d+)?)\s*(?:sq\.?\s*m(?:eters?)?|ചതുരശ്ര\s*മീറ്റർ|ച\.മീ|sqm\b)", text, re.I)
    if sqm_m:
        sqm = float(sqm_m.group(1))

    # 5. Square Feet (ചതുരശ്ര അടി)
    sqft_m = re.search(r"(\d+(?:\.\d+)?)\s*(?:sq\.?\s*ft|sq\.?\s*feet|ചതുരശ്ര\s*അടി|ച\.അടി|sqft\b)", text, re.I)
    if sqft_m:
        sqft = float(sqft_m.group(1))

    return ParsedExtent(
        cents=cents,
        ares=ares,
        hectares=hectares,
        sq_meters=sqm,
        sq_feet=sqft,
    )


def verify_extent_inflation(
    prior_cents: float,
    subsequent_cents: float,
    tolerance: float = 0.05,
) -> Tuple[bool, float]:
    """Detects whether subsequent deed purports to convey more land than held in prior deed.

    Returns:
        (is_inflated, excess_cents)
    """
    if subsequent_cents > prior_cents + tolerance:
        excess = round(subsequent_cents - prior_cents, 4)
        return True, excess
    return False, 0.0


def verify_internal_extent_consistency(
    cents: float,
    ares: float | None = None,
    hectares: float | None = None,
    sq_meters: float | None = None,
    tolerance_pct: float = 3.0,
) -> Tuple[bool, float, str]:
    """Checks whether the deed's own stated units (e.g. Ares vs Cents) agree within tolerance.

    Returns:
        (is_inconsistent, discrepancy_cents, explanation)
    """
    if cents <= 0:
        return False, 0.0, "Zero or negative extent"

    # Compare with Ares if available
    if ares is not None and ares > 0:
        expected_cents = ares_to_cents(ares)
        diff = abs(cents - expected_cents)
        pct_diff = (diff / expected_cents) * 100.0
        if pct_diff > tolerance_pct:
            return (
                True,
                round(diff, 2),
                f"Stated {cents:.2f} Cents conflicts with stated {ares:.2f} Ares (equiv to {expected_cents:.2f} Cents, delta {diff:.2f} Cents / {pct_diff:.1f}%)",
            )

    # Compare with Hectares if available
    if hectares is not None and hectares > 0:
        expected_cents = hectares_to_cents(hectares)
        diff = abs(cents - expected_cents)
        pct_diff = (diff / expected_cents) * 100.0
        if pct_diff > tolerance_pct:
            return (
                True,
                round(diff, 2),
                f"Stated {cents:.2f} Cents conflicts with stated {hectares:.4f} Hectares (equiv to {expected_cents:.2f} Cents, delta {diff:.2f} Cents / {pct_diff:.1f}%)",
            )

    # Compare with Sq.Meters if available
    if sq_meters is not None and sq_meters > 0:
        expected_cents = sqm_to_cents(sq_meters)
        diff = abs(cents - expected_cents)
        pct_diff = (diff / expected_cents) * 100.0
        if pct_diff > tolerance_pct:
            return (
                True,
                round(diff, 2),
                f"Stated {cents:.2f} Cents conflicts with stated {sq_meters:.1f} Sq.M (equiv to {expected_cents:.2f} Cents, delta {diff:.2f} Cents / {pct_diff:.1f}%)",
            )

    return False, 0.0, "Consistent"
