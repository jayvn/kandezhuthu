"""Kerala Cadastral Survey (BhuNaksha / ILIMS) & Agricultural Data Bank Service.

There is no live BhuNaksha / ILIMS or Data Bank integration yet. Parcels are approximate
squares of the extent at the user's pin; Data Bank entries and village coordinates come
only from demo fixtures (`KANDEZ_FIXTURES`). Without a record, Data Bank status is
reported as not on file. Covers:
1. Digital Cadastral Parcel Geometry (FMB - Field Measurement Book polygon coordinates).
2. Segment dimensions in meters (FMB side measurements).
3. Statutory Agricultural Data Bank verification under the Kerala Conservation of Paddy Land & Wetland Act, 2008.
4. Section 27A fee calculation and Form 5/6 procedural guidance.
"""

from __future__ import annotations

import math

from app import fixtures
from app.db.repository import KnowledgeRepository
from app.domain.models import (
    CadastralParcel,
    DataBankCheckResult,
    PaddyLandFeeCalculation,
)


class BhuNakshaCadastralService:
    """Provides digital cadastral sub-division boundaries and FMB dimensions."""

    @staticmethod
    def get_cadastral_parcel(
        survey_no: str,
        village: str,
        block_no: str | None = "12",
        extent_cents: float = 10.0,
        center_lat: float | None = None,
        center_lng: float | None = None,
    ) -> CadastralParcel | None:
        """Returns an approximate square outline of the extent, centred on the pin.

        Without a pin, only demo mode can place it (village coordinates are fixtures);
        otherwise returns None. It is never the FMB sketch.
        """
        villages = fixtures.load("cadastral_villages", {})
        baseline = villages.get(village.lower().strip()) or villages.get("aluva west")
        if center_lat is None or center_lng is None:
            if baseline is None:
                return None
            center_lat, center_lng = baseline["lat"], baseline["lng"]

        lat, lng = center_lat, center_lng
        district = baseline["district"] if baseline else "Kerala"
        taluk = baseline["taluk"] if baseline else ""

        # Approximate plot dimension in meters for given cents (1 cent = ~40.47 sq meters)
        area_sqm = extent_cents * 40.4686
        side_len_m = math.sqrt(area_sqm)
        delta_deg = (side_len_m / 111320.0) / 2.0

        # Square of the given extent (longitude span corrected for latitude)
        delta_lng = delta_deg / math.cos(math.radians(lat))
        poly = [
            [round(lat - delta_deg, 6), round(lng - delta_lng, 6)],  # SW
            [round(lat - delta_deg, 6), round(lng + delta_lng, 6)],  # SE
            [round(lat + delta_deg, 6), round(lng + delta_lng, 6)],  # NE
            [round(lat + delta_deg, 6), round(lng - delta_lng, 6)],  # NW
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

        # Neighbouring survey numbers are invented; demo mode only.
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
            adjacent_survey_numbers=adjacent if fixtures.is_demo() else [],
            access_road_identified=False,
            subdivision_sketch_available=False,
        )


class KeralaDataBankService:
    """Verifies land entries in the Kerala 2008 Agricultural Data Bank."""

    @staticmethod
    def check_databank(
        survey_no: str,
        village: str,
        extent_cents: float = 10.0,
        fair_value_per_are: float = 240000.0,
    ) -> DataBankCheckResult:
        clean_sy = survey_no.strip()
        reg_entry = fixtures.load("databank_registry", {}).get(clean_sy)
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
            fee_calculation=None,
            building_permit_eligibility=permit,
            risk_advisory=advisory,
            whatsapp_inquiry=wa,
            whatsapp_inquiry_en=wa_en,
        )
