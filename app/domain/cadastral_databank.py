"""Kerala Cadastral Survey (BhuNaksha / ILIMS) & Agricultural Data Bank Service.

Simulates and interfaces with the Kerala Revenue Department's BhuNaksha WMS / ILIMS
cadastral sub-division system, providing:
1. Digital Cadastral Parcel Geometry (FMB - Field Measurement Book polygon coordinates).
2. Segment dimensions in meters (FMB side measurements).
3. Statutory Agricultural Data Bank verification under the Kerala Conservation of Paddy Land & Wetland Act, 2008.
4. Section 27A fee calculation and Form 5/6 procedural guidance.
"""

from __future__ import annotations

import math
from typing import Any

from app.db.repository import KnowledgeRepository
from app.domain.models import (
    CadastralParcel,
    DataBankCheckResult,
    PaddyLandFeeCalculation,
)

# Known Village Baseline Geocodes in Kerala
VILLAGE_GEO_BASELINES = {
    "aluva west": {"lat": 10.1076, "lng": 76.3516, "district": "Ernakulam", "taluk": "Aluva"},
    "aluva": {"lat": 10.1076, "lng": 76.3516, "district": "Ernakulam", "taluk": "Aluva"},
    "kakkanad": {"lat": 10.0159, "lng": 76.3419, "district": "Ernakulam", "taluk": "Kanayannur"},
    "thrikkakara": {"lat": 10.0320, "lng": 76.3280, "district": "Ernakulam", "taluk": "Kanayannur"},
    "kuttanad": {"lat": 9.4981, "lng": 76.4312, "district": "Alappuzha", "taluk": "Kuttanad"},
    "edappally": {"lat": 10.0261, "lng": 76.3125, "district": "Ernakulam", "taluk": "Kanayannur"},
    "kaloor": {"lat": 9.9980, "lng": 76.2990, "district": "Ernakulam", "taluk": "Kanayannur"},
    "chalakudy": {"lat": 10.3070, "lng": 76.3330, "district": "Thrissur", "taluk": "Chalakudy"},
    "aranmula": {"lat": 9.3175, "lng": 76.6173, "district": "Pathanamthitta", "taluk": "Kozhencherry"},
}

# Statutory Agricultural Data Bank Registry for Landmark Survey Numbers
KNOWN_DATABANK_REGISTRY = {
    "182/4": {
        "village": "Kakkanad",
        "is_listed": True,
        "status": "Nilam / Paddy Land (നെൽവയൽ)",
        "krishi_bhavan": "Kakkanad Krishi Bhavan (Thrikkakara)",
        "notified_year": 2012,
        "form": "Form 5 (Data Bank Exclusion) & Form 6 (Sec 27A Conversion)",
        "permit": "PROHIBITED until Form 5 removal and Form 6 revenue conversion order are issued.",
        "advisory": (
            "FATAL PERMIT TRAP: This survey number is officially listed in the statutory Data Bank prepared by the "
            "Local Level Monitoring Committee (LLMC). Under Section 14 of the 2008 Act, Local Self Government (LSGD) "
            "cannot issue a building permit on land included in the Data Bank, even if physically filled decades ago."
        ),
        "whatsapp": (
            "നമസ്കാരം, കാക്കനാട് വില്ലേജിലെ സർവേ 182/4 പ്രോപ്പർട്ടി കൃഷിഭവന്റെ നെൽവയൽ-തണ്ണീർത്തട ഡാറ്റാ ബാങ്കിൽ "
            "ഉൾപ്പെട്ടിട്ടുള്ളതായി കാണുന്നു. ഇത് ഡാറ്റാ ബാങ്കിൽ നിന്ന് ഒഴിവാക്കിയുള്ള ഫോം 5 ഉത്തരവും, റവന്യൂ രേഖകളിൽ "
            "പുരയിടമാക്കിയുള്ള ഫോം 6 (സെക്ഷൻ 27A) ഉത്തരവും ലഭ്യമാണോ എന്ന് ദയവായി വ്യക്തമാക്കാമോ?"
        ),
        "whatsapp_en": (
            "Hello, the property in Kakkanad Village, Survey 182/4, appears to be listed in the Krishi Bhavan Paddy Land & Wetland Data Bank. "
            "Could you kindly clarify whether a Form 5 order excluding it from the Data Bank and a Section 27A (Form 6) revenue conversion order "
            "converting it to Purayidam are available?"
        ),
    },
    "345/1": {
        "village": "Aluva West",
        "is_listed": False,
        "status": "Unnotified Land (BTR Nilam / Physically Converted prior to 2008)",
        "krishi_bhavan": "Aluva Krishi Bhavan",
        "notified_year": None,
        "form": "Form 6 (Section 27A Revenue Record Conversion)",
        "permit": "CONDITIONAL on Section 27A conversion and BTR entry alteration to Purayidam.",
        "advisory": (
            "CAUTION (Section 27A): The plot is NOT in the Data Bank, but may be described as Nilam in older BTR records. "
            "If extent is <= 25 cents, Section 27A conversion fee is 0% (statutory free). If > 25 cents, a 10% fee applies."
        ),
        "whatsapp": (
            "നമസ്കാരം, ആലുവ വെസ്റ്റ് റീ-സർവേ 345/1 വസ്തു ഡാറ്റാ ബാങ്കിൽ ഉൾപ്പെട്ടിട്ടില്ലെങ്കിലും ബി.ടി.ആർ (BTR) രേഖകളിൽ "
            "പുരയിടമാണോ എന്ന് വ്യക്തമാക്കാമോ? സെക്ഷൻ 27A പ്രകാരമുള്ള ഫോം 6 ഉത്തരവ് ലഭ്യമാണോ?"
        ),
        "whatsapp_en": (
            "Hello, regarding Aluva West Re-Survey 345/1, although it is not in the Data Bank, could you clarify whether it is recorded "
            "as Purayidam in the Village Basic Tax Register (BTR)? Is a Section 27A (Form 6) conversion order available?"
        ),
    },
    "412/3": {
        "village": "Aluva West",
        "is_listed": False,
        "status": "Clean Purayidam / Garden Land (പുരയിടം)",
        "krishi_bhavan": "Aluva Krishi Bhavan",
        "notified_year": None,
        "form": "None (Clean Residential Purayidam)",
        "permit": "FULLY PERMITTED under standard KPBR 2019 rules.",
        "advisory": (
            "ALL CLEAR: Fully verified residential Purayidam in both BTR and Krishi Bhavan records. "
            "No Section 27A fee or Form 5 application required."
        ),
        "whatsapp": (
            "നമസ്കാരം, ആലുവ വെസ്റ്റ് റീ-സർവേ 412/3 വസ്തു റവന്യൂ രേഖകളിലും കൃഷിഭവനിലും പൂർണ്ണമായും പുരയിടമായി "
            "രേഖപ്പെടുത്തിയിട്ടുള്ളതാണ്. പഞ്ചായത്ത് ബിൽഡിംഗ് പെർമിറ്റിനായി കരമടച്ച രസീത് ലഭ്യമാക്കുമല്ലോ."
        ),
        "whatsapp_en": (
            "Hello, Aluva West Re-Survey 412/3 is documented as residential Purayidam in revenue and Krishi Bhavan records. "
            "Kindly provide the latest Land Tax Receipt and Village Thandaper extract for building permit verification. Thank you."
        ),
    },
}


class BhuNakshaCadastralService:
    """Provides digital cadastral sub-division boundaries and FMB dimensions."""

    @staticmethod
    def get_cadastral_parcel(
        survey_no: str,
        village: str = "Aluva West",
        block_no: str | None = "12",
        extent_cents: float = 10.0,
        center_lat: float | None = None,
        center_lng: float | None = None,
    ) -> CadastralParcel:
        v_key = village.lower().strip()
        baseline = VILLAGE_GEO_BASELINES.get(v_key, VILLAGE_GEO_BASELINES["aluva west"])

        lat = center_lat if center_lat is not None else baseline["lat"]
        lng = center_lng if center_lng is not None else baseline["lng"]
        district = baseline["district"]
        taluk = baseline["taluk"]

        # Approximate plot dimension in meters for given cents (1 cent = ~40.47 sq meters)
        area_sqm = extent_cents * 40.4686
        side_len_m = math.sqrt(area_sqm)
        delta_deg = (side_len_m / 111320.0) / 2.0

        # Construct 4-sided cadastral polygon with slight organic skew mirroring FMB sketches
        poly = [
            [round(lat - delta_deg * 0.95, 6), round(lng - delta_deg * 1.05, 6)],  # SW
            [round(lat - delta_deg * 1.02, 6), round(lng + delta_deg * 0.98, 6)],  # SE
            [round(lat + delta_deg * 0.98, 6), round(lng + delta_deg * 1.04, 6)],  # NE
            [round(lat + delta_deg * 1.05, 6), round(lng - delta_deg * 0.96, 6)],  # NW
        ]

        def _dist(p1, p2):
            dlat = (p2[0] - p1[0]) * 111320
            dlng = (p2[1] - p1[1]) * 111320 * math.cos(math.radians(p1[0]))
            return round(math.sqrt(dlat * dlat + dlng * dlng), 1)

        fmb_dimensions = [
            {"edge": "South (തെക്ക്)", "length_m": _dist(poly[0], poly[1]), "type": "approximate"},
            {"edge": "East (കിഴക്ക്)", "length_m": _dist(poly[1], poly[2]), "type": "approximate"},
            {"edge": "North (വടക്ക്)", "length_m": _dist(poly[2], poly[3]), "type": "approximate"},
            {"edge": "West (പടിഞ്ഞാറ്)", "length_m": _dist(poly[3], poly[0]), "type": "approximate"},
        ]

        # Derive adjacent survey numbers
        clean_sy = survey_no.strip()
        parts = clean_sy.split("/")
        if len(parts) == 2 and parts[1].isdigit():
            base_sy = parts[0]
            sub_sy = int(parts[1])
            adjacent = [f"{base_sy}/{sub_sy - 1}", f"{base_sy}/{sub_sy + 1}", f"{int(base_sy)+1}/1", f"{int(base_sy)-1}/2"] if base_sy.isdigit() else [f"{clean_sy}-A", f"{clean_sy}-B"]
        else:
            adjacent = [f"{clean_sy}/1", f"{clean_sy}/2", f"{clean_sy}/3"]

        return CadastralParcel(
            district=district,
            taluk=taluk,
            village=village,
            block_no=block_no,
            survey_no=survey_no,
            resurvey_no=survey_no,
            extent_cents=extent_cents,
            polygon_coordinates=poly,
            fmb_dimensions_m=fmb_dimensions,
            adjacent_survey_numbers=adjacent,
            access_road_identified=False,
            subdivision_sketch_available=False,
        )


class KeralaDataBankService:
    """Verifies land entries in the Kerala 2008 Agricultural Data Bank."""

    @staticmethod
    def check_databank(
        survey_no: str,
        village: str = "Aluva West",
        extent_cents: float = 10.0,
        fair_value_per_are: float = 240000.0,
    ) -> DataBankCheckResult:
        clean_sy = survey_no.strip()
        reg_entry = KNOWN_DATABANK_REGISTRY.get(clean_sy)
        # Survey numbers repeat across villages; a record only applies to its own village.
        if reg_entry and reg_entry["village"].lower() != village.lower().strip():
            reg_entry = None

        knowledge_repo = KnowledgeRepository()
        fee_calc_dict = knowledge_repo.calculate_paddy_conversion_fee(
            plot_cents=extent_cents, fair_value_per_are=fair_value_per_are
        )
        fee_calc = PaddyLandFeeCalculation(**fee_calc_dict)

        if reg_entry:
            return DataBankCheckResult(
                survey_no=clean_sy,
                village=village,
                is_listed_in_databank=reg_entry["is_listed"],
                entry_status=reg_entry["status"],
                krishi_bhavan_name=reg_entry["krishi_bhavan"],
                recommended_statutory_form=reg_entry["form"],
                fee_calculation=fee_calc if "27A" in reg_entry["form"] or reg_entry["is_listed"] else None,
                building_permit_eligibility=reg_entry["permit"],
                risk_advisory=reg_entry["advisory"],
                whatsapp_inquiry=reg_entry["whatsapp"],
                whatsapp_inquiry_en=reg_entry.get("whatsapp_en", ""),
            )

        # No Data Bank record on file for this survey number: report that, don't guess.
        is_listed = None
        status = "Not on file here (ഇവിടെ രേഖയില്ല)"
        form = "Unknown until the Data Bank extract and BTR are seen"
        permit = "Unknown: depends on the Data Bank entry and the BTR classification."
        advisory = (
            f"No Data Bank record for Survey {clean_sy}, {village} is available to this tool. "
            "Get the Data Bank extract from the Krishi Bhavan and the BTR extract from the Village Office."
        )
        wa = (
            f"നമസ്കാരം, {village} വില്ലേജിലെ സർവേ {clean_sy} വസ്തു കൃഷിഭവൻ ഡാറ്റാ ബാങ്കിൽ ഉൾപ്പെട്ടിട്ടുണ്ടോ? "
            "ഡാറ്റാ ബാങ്ക് പകർപ്പും വില്ലേജ് ഓഫീസിലെ BTR പകർപ്പും അയച്ചുതരാമോ?"
        )
        wa_en = (
            f"Hello, is the property in {village} Village, Survey {clean_sy}, listed in the Krishi Bhavan Data Bank? "
            "Could you share the Data Bank extract and the Village Office BTR extract?"
        )

        return DataBankCheckResult(
            survey_no=clean_sy,
            village=village,
            is_listed_in_databank=is_listed,
            entry_status=status,
            krishi_bhavan_name=f"{village} Krishi Bhavan",
            recommended_statutory_form=form,
            fee_calculation=fee_calc if is_listed else None,
            building_permit_eligibility=permit,
            risk_advisory=advisory,
            whatsapp_inquiry=wa,
            whatsapp_inquiry_en=wa_en,
        )
