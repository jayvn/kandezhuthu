"""Kerala Cadastral Survey (BhuNaksha / ILIMS) & Agricultural Data Bank Service.

There is no live BhuNaksha / ILIMS or Data Bank integration yet. Parcel sketches and
Data Bank entries come only from demo fixtures (`KANDEZ_FIXTURES`); otherwise parcels are
unavailable and Data Bank status is reported as unverified. Covers:
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
        village: str = "Aluva West",
        block_no: str | None = "12",
        extent_cents: float = 10.0,
        center_lat: float | None = None,
        center_lng: float | None = None,
    ) -> CadastralParcel | None:
        """Returns a demo FMB-style sketch in demo mode; None otherwise (no BhuNaksha feed)."""
        villages = fixtures.load("cadastral_villages", {})
        if not villages:
            return None
        v_key = village.lower().strip()
        baseline = villages.get(v_key, villages["aluva west"])

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
            {"edge": "South (തെക്ക്)", "length_m": _dist(poly[0], poly[1]), "type": "Compound Wall / Boundary"},
            {"edge": "East (കിഴക്ക്)", "length_m": _dist(poly[1], poly[2]), "type": "Neighbor Plot"},
            {"edge": "North (വടക്ക്)", "length_m": _dist(poly[2], poly[3]), "type": "Subdivision Boundary"},
            {"edge": "West (പടിഞ്ഞാറ്)", "length_m": _dist(poly[3], poly[0]), "type": "3.5m Panchayat Road Access"},
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
            access_road_identified=True,
            subdivision_sketch_available=True,
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
        reg_entry = fixtures.load("databank_registry", {}).get(clean_sy)

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

        return DataBankCheckResult(
            survey_no=clean_sy,
            village=village,
            is_listed_in_databank=None,
            entry_status="Not verified (ഡാറ്റാ ബാങ്ക് പരിശോധിച്ചിട്ടില്ല)",
            krishi_bhavan_name=f"{village} Krishi Bhavan",
            recommended_statutory_form="Depends on the Data Bank entry and Village BTR classification",
            fee_calculation=None,
            building_permit_eligibility="Unknown until the Data Bank entry and BTR classification are confirmed.",
            risk_advisory=(
                f"Data Bank listing for Survey {clean_sy} in {village} was not checked. Look it up in the "
                "Krishi Bhavan Data Bank register and get the Village Office BTR extract."
            ),
            whatsapp_inquiry=(
                f"നമസ്കാരം, {village} വില്ലേജിലെ സർവേ {clean_sy} വസ്തു കൃഷിഭവൻ ഡാറ്റാ ബാങ്കിൽ ഉൾപ്പെട്ടിട്ടുണ്ടോ? "
                "പുരയിടമാണെന്ന് കാണിക്കുന്ന ഏറ്റവും പുതിയ കരം രസീതും BTR പകർപ്പും ലഭ്യമാക്കാമോ?"
            ),
            whatsapp_inquiry_en=(
                f"Hello, is the property in {village} Village, Survey {clean_sy}, listed in the Krishi Bhavan "
                "Agricultural Data Bank? Could you share the latest land tax receipt and BTR extract showing its classification?"
            ),
        )
