"""Regression tests for real-world deed phrasings the scanner previously missed.

A missed trap yields ALL_CLEAR, which is worse than no tool, so recall on
common drafting styles matters more than exotic cases.
"""

import pytest

from app.domain.single_deed_scanner import SingleDeedScanner, TrapCategory

T = TrapCategory
scanner = SingleDeedScanner()


def categories(text: str) -> set[TrapCategory]:
    return {f.trap_type for f in scanner.scan(text).findings}


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("ടി വസ്തുവിന്റെ കിഴക്കുവശത്തുകൂടി വടക്കുള്ള വസ്തുക്കാർക്ക് "
         "പോക്കുവരവിനുള്ള അവകാശം ഉണ്ടായിരിക്കുന്നതാണ്.", T.EASEMENT_RIGHT_OF_WAY),
        # pre-2009 chillu encoding: ര + virama + ZWJ
        ("കിണര\u0d4d\u200d അവകാശം വടക്കേ വസ്തുക്കാർക്ക് ഉണ്ട്.", T.EASEMENT_RIGHT_OF_WAY),
        ("Classified as wet land in the Basic Tax Register.", T.WETLAND_NILAM_RISK),
        ("Executant No.3, Anu, aged 14, represented by her mother and "
         "natural guardian Latha.", T.MINOR_RIGHTS_DEFECT),
        ("3-ാം നമ്പർ എഴുതിക്കൊടുക്കുന്നയാൾ 14 വയസ്സുള്ള അനു, അമ്മയും "
         "രക്ഷാകർത്താവുമായ ലത മുഖേന.", T.MINOR_RIGHTS_DEFECT),
        ("Executed on condition that the donee shall look after the settlor "
         "during her lifetime.", T.MAINTENANCE_CONDITIONAL_CLAUSE),
    ],
)
def test_common_phrasings_are_flagged(text, expected):
    assert expected in categories(text)


@pytest.mark.parametrize(
    "text",
    [
        "There is no right of way or easement over the scheduled property.",
        "The property is free from all encumbrances and easements.",
        "The property abuts the 6 metre PWD road on the south.",
        # പോക്കുവരവ് alone = revenue mutation, not a passage right
        "വില്ലേജ് ഓഫീസിൽ പോക്കുവരവ് നടത്തി കരം അടച്ചുവരുന്നു.",
        # Balan / Neelam are common personal names
        "Sold by Balan, aged 62, S/o Kumaran, to Neelam, aged 35.",
    ],
)
def test_clean_text_is_not_flagged(text):
    assert categories(text) == set()


def test_negated_clause_does_not_hide_later_real_one():
    text = ("No right of way exists on the south. However, the northern "
            "owner retains a 3 feet passage along the east.")
    assert T.EASEMENT_RIGHT_OF_WAY in categories(text)
