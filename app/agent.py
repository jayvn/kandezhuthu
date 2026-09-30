# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from typing import Optional, List
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

from app.domain.models import DeedNode, ECRecord, ElevationFloodResult
from app.domain.auditor import MunnadharamAuditor
from app.domain.single_deed_scanner import SingleDeedScanner
from app.db.repository import KnowledgeRepository, AuditRepository

# Latest Gemini Flash model for low-latency multimodal reasoning
MODEL = "gemini-3.8-flash"

FAIR_VALUE_REGISTER = (
    "IGR fair value register (https://igr.kerala.gov.in/index.php/fairvalue/view_fairvalue): "
    "district, RDO, taluk and village, then the survey number. The website figure is not the gazette; "
    "confirm against the RDO/Collector notification."
)


def scan_single_deed(deed_text: str) -> str:
    """Scans a single Kerala title deed (or schedule snippet) for 4 fatal legal/regulatory traps.

    Detects:
    1. Buried Easement / Pathway (Vazhi avakasham / വഴി അവകാശം)
    2. 2008 Paddy Land / Wetland Risk (Nilam vs Purayidam / നിലം)
    3. Minor's share sold without District Court order (മൈനർ അവകാശം)
    4. Senior citizen maintenance or conditional life-interest covenants (ജീവിതകാല സംരക്ഷണ വ്യവസ്ഥ)

    Args:
        deed_text: Text snippet of the deed, recitals, or property schedule (in Malayalam or English).

    Returns:
        JSON string containing the DeedSanityResult (Verdict, Sanity Score, Findings, Malayalam WhatsApp questions for seller,
        and on-site field checks).
    """
    scanner = SingleDeedScanner()
    result = scanner.scan(deed_text)
    
    # Persist scan result to database
    try:
        repo = AuditRepository()
        repo.save_single_deed_scan(snippet=deed_text, result_dict=result.model_dump())
    except Exception:
        pass  # Graceful fallback if DB is temporarily locked

    return result.model_dump_json(indent=2)


def scan_deed_document_file(file_path: str) -> str:
    """Scans and extracts structured legal metadata from an uploaded or local Kerala title deed document (PDF or image).

    Uses multimodal vision OCR to extract document number, year, SRO, survey number, extent in cents,
    4 boundaries (ചതുരതിരുകൾ), prior deeds (മുന്നാധാരം), evaluates 4 statutory traps, and retrieves building rules.

    Args:
        file_path: Local filesystem path to the deed file (.pdf, .png, .jpg, .jpeg, .webp).

    Returns:
        JSON string containing the extracted metadata, sanity score, findings, and Malayalam WhatsApp seller question.
    """
    from app.domain.deed_ocr import DeedOCREngine

    engine = DeedOCREngine()
    result = engine.process_file_path(file_path)
    return result.model_dump_json(indent=2)


def calculate_plot_elevation_and_flood_exposure(
    latitude: float,
    longitude: float,
    place_name: Optional[str] = None,
    plot_extent_cents: Optional[float] = None,
) -> str:
    """Calculates plot elevation above Mean Sea Level (MSL) and evaluates flood exposure risk.

    Uses Google Elevation API & Geocoding API to assess:
    1. Plot elevation above Mean Sea Level (MSL) in meters.
    2. Proximity to major Kerala river flood basins (Periyar, Pamba, Chalakudy, Vembanad, Kole wetlands, etc.).
    3. Inundation vulnerability during the 2018/2019 Great Kerala Floods.
    4. Statutory KSDMA hazard advisories and wetland topography classification (Nilam vs Purayidam risk).
    5. Recommended minimum building plinth height above road level.
    6. Culturally polite native Malayalam WhatsApp inquiry to ask seller about monsoon flooding history.

    Args:
        latitude: Latitude of the marked plot (e.g. 10.1076).
        longitude: Longitude of the marked plot (e.g. 76.3516).
        place_name: Optional village/town name (e.g. "Aluva", "Kakkanad", "Kuttanad").
        plot_extent_cents: Optional land extent in Kerala Cents (e.g. 10.0).

    Returns:
        JSON string containing ElevationFloodResult with elevation, flood risk level, safety score, river basin,
        KSDMA advisory, recommended plinth height, physical inspection checklist, and Malayalam WhatsApp inquiry.
    """
    from app.domain.elevation_flood import ElevationFloodCalculator, ElevationUnavailableError

    calculator = ElevationFloodCalculator()
    try:
        result = calculator.calculate(
            latitude=latitude,
            longitude=longitude,
            locality_hint=place_name,
            plot_extent_cents=plot_extent_cents,
        )
    except ElevationUnavailableError as e:
        return json.dumps({"error": str(e), "elevation_available": False}, indent=2)
    return result.model_dump_json(indent=2)


def audit_prior_deeds_title(
    property_identifier: str,
    deeds_data: str,
    ec_data: Optional[str] = None,
) -> str:
    """Audits the 30-year chain of prior title deeds (Munnadharam) for a property in Kerala."""
    try:
        raw_deeds = json.loads(deeds_data)
        deeds = [DeedNode(**d) for d in raw_deeds]
        
        ec_records: List[ECRecord] = []
        if ec_data:
            raw_ec = json.loads(ec_data)
            ec_records = [ECRecord(**e) for e in raw_ec]

        auditor = MunnadharamAuditor(property_identifier=property_identifier)
        scorecard = auditor.audit(deeds=deeds, ec_records=ec_records)

        # Persist audit into database
        try:
            repo = AuditRepository()
            survey_no = deeds[-1].survey_no if deeds else "Unknown"
            repo.save_audit(
                property_identifier=property_identifier,
                survey_no=survey_no,
                deeds=[d.model_dump() for d in deeds],
                ec_records=[e.model_dump() for e in ec_records],
                scorecard=scorecard.model_dump(),
            )
        except Exception:
            pass

        return scorecard.model_dump_json(indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to audit prior deeds: {str(e)}"}, indent=2)


def lookup_building_road_and_setbacks(plot_cents: float, building_type: str = "residential") -> str:
    """Queries the Kerala Building Rules (KPBR/KMBR 2019) database for exact road width and setbacks.

    Args:
        plot_cents: Plot extent in cents (e.g. 2.8, 5.0, 10.0). Plots <= 3.09 cents trigger Chapter VIII small plot concessions.
        building_type: Type of building (e.g., 'residential', 'commercial', 'high_rise').

    Returns:
        JSON string containing the exact statutory minimum road width, front/rear/side setbacks, open well distance, and rule citations.
    """
    repo = KnowledgeRepository()
    rule = repo.get_building_rule(plot_cents=plot_cents, occupancy_type=building_type)
    if not rule:
        return json.dumps({"error": f"No specific building rule found for plot size {plot_cents} cents."})
    return json.dumps(rule, indent=2)


def calculate_paddy_conversion_cost(
    plot_cents: float,
    fair_value_per_are: Optional[float] = None,
    village: Optional[str] = None,
    district: Optional[str] = None,
) -> str:
    """Calculates the exact government fee under Section 27A of the 2008 Paddy Land Act to convert Nilam to Purayidam.

    Args:
        plot_cents: Extent in cents to be converted (e.g. 15.0, 32.0, 60.0). Holdings of 25 cents or less on 30 Dec 2017 pay no fee.
        fair_value_per_are: Optional government notified Fair Value in INR per are (1 are = 2.471 cents). If omitted, looks up a stored rate for the village.
        village: Optional village name (e.g. 'Kakkanad', 'Aluva West') to automatically fetch Fair Value if fair_value_per_are is not provided.
        district: Optional district name (e.g. 'Ernakulam', 'Thiruvananthapuram').

    Returns:
        JSON string with exact statutory conversion fee, exemption status, fee percentage, and legal citations.
    """
    repo = KnowledgeRepository()
    if (not fair_value_per_are or fair_value_per_are <= 0) and village:
        benchmarks = repo.get_fair_value_benchmark(village=village, district=district)
        if benchmarks:
            fair_value_per_are = benchmarks[0]["fair_value_per_are_inr"]
    if not fair_value_per_are or fair_value_per_are <= 0:
        return json.dumps({
            "fair_value_available": False,
            "message": "The fee is a percentage of the fair value, and no fair value is on file for this plot.",
            "where_to_check": FAIR_VALUE_REGISTER,
        }, indent=2)

    calc = repo.calculate_paddy_conversion_fee(plot_cents=plot_cents, fair_value_per_are=fair_value_per_are)
    if village:
        calc["benchmarked_village"] = village
    return json.dumps(calc, indent=2)


def lookup_fair_value_of_land(village: str, district: Optional[str] = None) -> str:
    """Looks up stored notified Fair Value of land per Are under Section 28A of the Kerala Stamp Act.

    Args:
        village: Revenue village name in Kerala (e.g. 'Kakkanad', 'Aluva West', 'Pattom', 'Edappally South', 'Thrissur').
        district: Optional district name (e.g. 'Ernakulam', 'Thiruvananthapuram', 'Thrissur').

    Returns:
        JSON string containing the notified Fair Value benchmarks per Are by land type (commercial, residential road, interior), effective year, and gazette notification.
    """
    repo = KnowledgeRepository()
    results = repo.get_fair_value_benchmark(village=village, district=district)
    if not results:
        return json.dumps({
            "message": f"No Fair Value data stored for village '{village}'.",
            "village": village,
            "district": district,
            "fair_value_available": False,
            "where_to_check": FAIR_VALUE_REGISTER,
        }, indent=2)
    return json.dumps({
        "village": village,
        "district": district or results[0]["district"],
        "taluk": results[0]["taluk"],
        "benchmarks_count": len(results),
        "rates": results,
    }, indent=2)


def check_digital_survey_status(village: str, district: Optional[str] = None) -> str:
    """Checks whether a village is under Kerala's Digital Resurvey ('Ente Bhoomi') project.

    Verifies whether paper FMBs and manual BTR are being replaced by 14-digit ULPIN (Bhu-Aadhaar) and d-BTR.

    Args:
        village: Revenue village name in Kerala (e.g. 'Kudappanakunnu', 'Pattom', 'Kakkanad', 'Aluva West', 'Ollur').
        district: Optional district name (e.g. 'Thiruvananthapuram', 'Ernakulam', 'Thrissur').

    Returns:
        JSON string containing the survey rollout phase, status (d-BTR published, drone survey ongoing), portal link, and buyer due-diligence advisory.
    """
    repo = KnowledgeRepository()
    record = repo.check_digital_resurvey_status(village=village, district=district)
    if not record:
        return json.dumps({
            "village": village,
            "digital_resurvey_status": "Unknown (no resurvey data stored for this village)",
            "advisory": (
                "Check the village on the Ente Bhoomi portal. If it is not yet resurveyed, use the "
                "Field Measurement Book (FMB) sketch and Village Office Basic Tax Register (BTR) extract."
            ),
            "portal": "https://entebhoomi.kerala.gov.in"
        }, indent=2)
    return json.dumps(record, indent=2)


def get_historical_audits_for_property(survey_no: str, village: Optional[str] = None) -> str:
    """Checks the database for historical audits, prior recorded deeds, or existing red flags for a survey number.

    Args:
        survey_no: Survey or Re-survey number (e.g. '345/1', '124/3').
        village: Optional village name (e.g. 'Aluva West').

    Returns:
        JSON string with past audit scorecards, risk flags, and title lineage paths found for this survey number.
    """
    repo = AuditRepository()
    history = repo.get_property_audit_history(survey_no=survey_no, village=village)
    return json.dumps({"survey_no": survey_no, "historical_audits_count": len(history), "audits": history}, indent=2)


def query_kerala_land_rules(topic: str) -> str:
    """Queries the curated Kerala land regulations and judicial precedents database & knowledge base.

    Topics covered:
    1. Building permit road width requirements, setbacks, and small plot concessions (KPBR / KMBR 2019)
    2. Kerala Conservation of Paddy Land & Wetland Act 2008, Form 5, Form 6, Section 27A fee slabs, Nilam conversion
    3. Landmark Kerala court precedents: Christian female succession (Mary Roy), Hindu coparcenary (Vineeta Sharma),
       easements (Sree Swayamprakash Ashramam), minor share alienation (Saroj & Imambandi), Senior Citizens Act (Sec 23),
       Power of Attorney fraud (Suraj Lamp), Kudikidappu tenancy (KLR Act), and Lis Pendens (Sec 52 TPA).

    Args:
        topic: Keyword or query describing the legal or regulatory rule (e.g., 'road width', 'paddy land', 'form 6 fee', 'mary roy', 'easement', 'power of attorney', 'kudikidappu').

    Returns:
        Structured statutory rules, section citations, fee schedules, and pre-purchase due diligence advice.
    """
    from pathlib import Path
    knowledge_dir = Path(__file__).resolve().parent.parent / "data" / "knowledge"

    # Query structured database first for precedents
    repo = KnowledgeRepository()
    db_precedents = repo.search_precedents(topic, limit=3)

    t = topic.lower()
    results = []

    if db_precedents:
        prec_text = "### Landmark Precedents from Database:\n" + "\n\n".join(
            f"**{p['case_name']}** ({p['citation']} - {p['court']})\n"
            f"- **Principle**: {p['key_principle']}\n"
            f"- **Risk Trigger in Deeds**: {p['risk_trigger']}\n"
            f"- **Remedial Action**: {p['remedial_action']}\n"
            f"- **Statutory Citation**: {p['statute_reference']}"
            for p in db_precedents
        )
        results.append(prec_text)

    # Stream A: Building Rules (KPBR / KMBR)
    if any(k in t for k in ["road", "width", "kmbr", "kpbr", "setback", "small plot", "permit", "septic", "well", "clearance", "building"]):
        doc_path = knowledge_dir / "building_rules_kmbr_kpbr.md"
        if doc_path.exists():
            results.append(doc_path.read_text(encoding="utf-8"))

    # Stream B: Paddy Land & Wetland (Nilam / 2008 Act / Form 5 / Form 6)
    if any(k in t for k in ["paddy", "nilam", "wetland", "form 5", "form 6", "form 7", "27a", "fee", "conversion", "btr", "data bank", "ksrec", "llmc", "unnotified"]):
        doc_path = knowledge_dir / "paddy_land_wetland_guide.md"
        if doc_path.exists():
            results.append(doc_path.read_text(encoding="utf-8"))

    # Stream C: Court Precedents & Legal Principles
    if any(k in t for k in [
        "precedent", "court", "judgment", "mary roy", "christian", "succession", "heir", "daughter",
        "coparcenary", "minor", "guardian", "senior citizen", "maintenance", "easement", "vazhi", "pathway",
        "power of attorney", "poa", "gpa", "mukthiyar", "suraj lamp", "kudikidappu", "pattayam", "tenancy",
        "lis pendens", "adverse possession", "puramboke", "imambandi", "muslim minor", "jalaja dileep"
    ]) and not db_precedents:
        doc_path = knowledge_dir / "kerala_court_precedents.md"
        if doc_path.exists():
            results.append(doc_path.read_text(encoding="utf-8"))

    # If no specific keyword matched, search across all available knowledge documents for snippets
    if not results and knowledge_dir.exists():
        for file in sorted(knowledge_dir.glob("*.md")):
            content = file.read_text(encoding="utf-8")
            if any(term in content.lower() for term in t.split()):
                results.append(content)

    if results:
        return "\n\n---\n\n".join(results)
    
    # Fallback default summary if no files match
    return (
        "Kerala Land Knowledge Base covers:\n"
        "1. KPBR/KMBR 2019: Mandatory 3m access road for standard residential plots, 1.2-1.5m for small plots (<=3 cents).\n"
        "2. Paddy Land Act 2008 & Sec 27A: Free Form 6 conversion up to 25 cents, 10% fee for 25-50 cents, Form 5 for Data Bank removal.\n"
        "3. Landmark Precedents: Mary Roy (Christian succession), Sec 23 Senior Citizens Act, HMGA Sec 8 & Imambandi (minor sales), Suraj Lamp (PoA sales), Kudikidappu tenancy, and Lis Pendens (Sec 52 TPA)."
    )


def audit_encumbrance_certificate(
    property_identifier: str,
    ec_text: str,
    known_deeds_data: Optional[str] = None,
) -> str:
    """Audits an SRO Encumbrance Certificate (EC / കുടിക്കടം) and cross-checks for undisclosed mortgages or attachments.

    Detects:
    1. Undischarged bank mortgages (Gehan) with SARFAESI liability.
    2. Civil court, Munsiff/Sub-court, or Revenue Recovery attachments.
    3. Conflicting sale deeds or missing lineage links.

    Args:
        property_identifier: Property description (e.g. 'Re-Sy 345/1, Aluva West Village').
        ec_text: Raw tabular text or transcribed entries from the Encumbrance Certificate.
        known_deeds_data: Optional JSON array of known prior DeedNode objects to cross-reference against.

    Returns:
        JSON string containing ECAuditResult (Safety score, list of undisclosed mortgages, attachments, Malayalam inquiry, and checklist).
    """
    from app.domain.ec_parser import EncumbranceCertificateAuditor

    known_deeds = []
    if known_deeds_data:
        try:
            raw = json.loads(known_deeds_data)
            known_deeds = [DeedNode(**d) for d in raw]
        except Exception:
            pass

    auditor = EncumbranceCertificateAuditor(property_identifier=property_identifier)
    result = auditor.audit_ec(raw_ec_text=ec_text, known_deeds=known_deeds)
    return result.model_dump_json(indent=2)


def check_kerala_databank_and_cadastral(
    survey_no: str,
    village: str,
    extent_cents: float = 10.0,
    fair_value_per_are: float = 240000.0,
) -> str:
    """Checks the Kerala 2008 Agricultural Data Bank records on file and returns an approximate plot outline.

    Evaluates:
    1. Whether the survey number is listed as Nilam / Paddy Land in the Data Bank records on file.
       `is_listed_in_databank` is null when no record is on file: say it was not found, never that the land is clear.
    2. Applicable statutory conversion procedures (Form 5 exclusion vs Form 6 Section 27A fee).
    3. Calculated Section 27A fee (free under 25 cents; 10% for 25-50 cents).
    4. Building permit issuance eligibility under KPBR 2019.
    5. In demo mode only, an approximate square outline sized from the extent. It is not the FMB sketch; do not present it as one.

    Args:
        survey_no: Survey or Re-Survey number (e.g. '182/4', '345/1', '412/3').
        village: Kerala village name (e.g. 'Kakkanad', 'Aluva West').
        extent_cents: Plot extent in Kerala Cents.
        fair_value_per_are: Government notified Fair Value in INR per are.

    Returns:
        JSON string with DataBankCheckResult and, in demo mode, an approximate CadastralParcel outline
        (`available: false` otherwise).
    """
    from app.domain.cadastral_databank import BhuNakshaCadastralService, KeralaDataBankService

    db_res = KeralaDataBankService.check_databank(
        survey_no=survey_no,
        village=village,
        extent_cents=extent_cents,
        fair_value_per_are=fair_value_per_are,
    )
    cadastral = BhuNakshaCadastralService.get_cadastral_parcel(
        survey_no=survey_no,
        village=village,
        extent_cents=extent_cents,
    )
    return json.dumps({
        "data_bank_status": db_res.model_dump(),
        "cadastral_parcel": cadastral.model_dump() if cadastral else {
            "available": False,
            "where_to_check": "BhuNaksha (bhunaksha.kerala.gov.in) or the FMB sketch from the Taluk Survey Office.",
        },
    }, indent=2)


def organize_and_sync_property_data(target: str = "status") -> str:
    """Manages legal title data organization and cloud backups with Google Cloud Storage and Firestore.

    Args:
        target: One of 'status' (to inspect catalog status), 'local' (to organize data locally),
                'cloud' (to sync to Google Cloud Storage & Firestore), or 'all' (to organize locally and sync to cloud).

    Returns:
        JSON string summarizing collection counts, local paths, and cloud sync status.
    """
    from app.domain.data_api import DataAPI

    api = DataAPI()
    if target == "local":
        result = api.organize_local()
    elif target == "cloud":
        gcs_res = api.sync_to_gcs()
        fs_res = api.sync_to_firestore()
        result = {"gcs": gcs_res, "firestore": fs_res}
    elif target == "all":
        result = api.organize_and_sync_all()
    else:
        result = api.get_status()
    return json.dumps(result, indent=2)


root_agent = Agent(
    name="kandezhuthu_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are 'Kandezhuthu AI' (കണ്ടെഴുത്ത് - ആധാരംനോക്കി), an intelligent Kerala property legal audit assistant. "
        "Your purpose is to protect home buyers, NRIs, and non-technical families from paying token advances on legally defective Kerala land.\n\n"
        "CORE STRENGTHS & TOOL USAGE:\n"
        "1. Single-Deed / Schedule Scan: Use `scan_single_deed` whenever the user pastes deed clauses, property schedules, or contract snippets in English or Malayalam.\n"
        "2. 30-Year Prior Title Lineage Audit: When users describe a chain of prior deeds (Munnadharam) or ownership history in natural language, automatically parse their narrative into DeedNode JSON records and invoke `audit_prior_deeds_title`.\n"
        "3. Exact Building Rules (KPBR/KMBR 2019): Use `lookup_building_road_and_setbacks` when users ask about road width or setback requirements for their specific plot extent.\n"
        "4. Paddy Land Conversion Calculator: Use `calculate_paddy_conversion_cost` when users ask about government fee for converting Nilam / paddy land to Purayidam.\n"
        "5. Historical Property Audit Search: Use `get_historical_audits_for_property` when checking a specific survey number for previous red flags or duplicate sales.\n"
        "6. Kerala Land Rules & Precedents Retrieval: Use `query_kerala_land_rules` to consult official Kerala building rules, 2008 Paddy Land Act, and High Court / Supreme Court precedents.\n"
        "7. Plot Elevation & Flood Exposure Calculator: Use `calculate_plot_elevation_and_flood_exposure` when users ask about flood risk, plot elevation, Mean Sea Level (MSL), monsoonal inundation, 2018 flood zones, or mark/specify plot coordinates.\n"
        "8. SRO Encumbrance Certificate (EC) Audit: Use `audit_encumbrance_certificate` when users provide EC records, Nil-EC text, bank loan entries, or court attachment records to cross-reference with title deeds.\n"
        "9. BhuNaksha & Data Bank Verification: Use `check_kerala_databank_and_cadastral` when users provide a survey number and village to check Agricultural Data Bank status (Form 5/6) and retrieve FMB cadastral parcel geometry when available.\n"
        "10. Fair Value of Land (Section 28A): Use `lookup_fair_value_of_land` to look up stored notified Fair Value rates per Are for a Kerala village.\n"
        "11. Digital Resurvey ('Ente Bhoomi') Verification: Use `check_digital_survey_status` to verify whether a village is actively under drone survey, has published d-BTR records, or assigns 14-digit ULPINs (Bhu-Aadhaar).\n"
        "12. Data Organization & Cloud Sync: Use `organize_and_sync_property_data` when users inquire about data status, local catalog copies, or syncing title datasets to Google Cloud Storage & Firestore.\n"
        "When a tool reports data as unavailable or not verified, say so and name where the user can check it. Never fill in missing values.\n\n"
        "PRESENTATION GUIDELINES FOR NON-TECHNICAL USERS:\n"
        "- Never dump raw JSON to the user. Always interpret tool outputs into clean, elegant Markdown.\n"
        "- Prominently feature the Title Sanity Score (e.g., 'Title Sanity Score: 85/100') and the verdict badge:\n"
        "  • ● **NO RED FLAGS FOUND** (none of the known trap clauses in the text)\n"
        "  • ▲ **CAUTION** (Restrictive covenants / easements detected)\n"
        "  • ■ **DANGER** (Fatal legal defects, wetland classification, or unrepresented heirs)\n"
        "- Break down each finding into: What it means in plain English/Malayalam, the Kerala statute (e.g. 2008 Paddy Land Act, Easements Act), and why it matters to a home builder.\n"
        "- Always provide a dedicated section: **'WhatsApp Message for Seller / Broker'** with the ready-to-copy inquiry in the user's selected language (in polite, clear English if the user communicates in English, or in native Malayalam if the user selects Malayalam).\n"
        "- Include a short **'On-Site Checks'** list (boundary stones, road access, neighbours) when it is relevant to the findings.\n\n"
        "STYLE:\n"
        "Be direct and concise. The user knows this is an AI tool: do not add disclaimers, warnings to consult a lawyer, or reminders about AI limits. "
        "Never describe a title as 100% clean or guaranteed; state what was checked and what was found. Use Markdown only, never LaTeX."
    ),
    tools=[
        scan_single_deed,
        scan_deed_document_file,
        audit_prior_deeds_title,
        lookup_building_road_and_setbacks,
        calculate_paddy_conversion_cost,
        lookup_fair_value_of_land,
        check_digital_survey_status,
        get_historical_audits_for_property,
        query_kerala_land_rules,
        calculate_plot_elevation_and_flood_exposure,
        audit_encumbrance_certificate,
        check_kerala_databank_and_cadastral,
        organize_and_sync_property_data,
    ],
)

app = App(
    root_agent=root_agent,
    name="kandezhuthu",
)
