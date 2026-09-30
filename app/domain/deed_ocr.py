"""Multimodal Deed OCR & Document Ingestion Engine for Kerala Real Estate Deeds.

Uses Gemini Vision models via Google GenAI SDK to read scanned Malayalam & English
deed documents (PDF, PNG, JPG, WEBP), extract 4 boundaries (ചതുരതിരുകൾ),
extent (വിസ്തീർണ്ണം), prior deeds (മുന്നാധാരം), and pipe them directly into
deterministic legal sanity auditing and database persistence.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
from typing import Any
import zlib

from dotenv import load_dotenv
from google.genai import Client, types
from pydantic import BaseModel, Field

from app.db.repository import AuditRepository, KnowledgeRepository
from app.domain.single_deed_scanner import DeedSanityResult, SingleDeedScanner

load_dotenv()
logger = logging.getLogger(__name__)

# Primary OCR vision models supported on Vertex AI / Gemini API
OCR_MODEL_CANDIDATES = [
    "gemini-3.8-flash",
    "gemini-2.5-flash",
    "gemini-1.5-flash",
]


class DeedBoundary(BaseModel):
    direction: str = Field(description="Direction: East (കിഴക്ക്), South (തെക്ക്), West (പടിഞ്ഞാറ്), or North (വടക്ക്)")
    boundary_description: str = Field(description="Boundary description (e.g. 'Road / പഞ്ചായത്ത് വഴി', 'Canal / തോട്', 'Property of...')")


class PriorDeedReference(BaseModel):
    doc_number: str = Field(description="Document registration number (e.g. '1420/2014')")
    year: int | None = Field(default=None, description="Year of registration")
    sro_name: str | None = Field(default=None, description="Sub-Registrar Office name")
    deed_type: str | None = Field(default=None, description="Deed type (e.g. 'Theeradharam', 'Bhagapathram', 'Pattayam')")
    grantor: str | None = Field(default=None, description="Grantor or prior owner name")
    grantee: str | None = Field(default=None, description="Grantee or acquirer name")
    notes: str | None = Field(default=None, description="Any specific recitals regarding this prior title")


class ExtractedDeedMetadata(BaseModel):
    document_number: str | None = Field(default=None, description="Document number of the current deed (e.g. '892/2018')")
    year: int | None = Field(default=None, description="Registration year")
    sro_name: str | None = Field(default=None, description="Sub-Registrar Office (SRO) name (e.g. 'Aluva', 'Ernakulam')")
    deed_type: str | None = Field(default=None, description="Nature of deed (e.g. 'തീറാധാരം / Sale Deed', 'ഭാഗപത്രം / Partition Deed')")
    survey_no: str = Field(default="Unknown", description="Survey or Re-Survey number (e.g. '345/1', '120/4B')")
    re_survey_no: str | None = Field(default=None, description="Re-survey number if differentiated")
    village: str = Field(default="Unknown", description="Village name")
    taluk: str | None = Field(default=None, description="Taluk name")
    district: str | None = Field(default=None, description="District name in Kerala")
    extent_cents: float = Field(default=0.0, description="Total land area in Kerala Cents")
    extent_ares: float | None = Field(default=None, description="Land area in Ares (1 Cent = 0.404686 Ares)")
    revenue_classification: str = Field(default="Purayidam", description="BTR / Revenue classification: 'Purayidam' (Garden/Dry land) or 'Nilam' (Paddy/Wetland)")
    is_paddy_wetland_risk: bool = Field(default=False, description="True if text mentions Nilam, Nanja, Punja, Thanneerthadam, or paddy land history")
    boundaries: list[DeedBoundary] = Field(default_factory=list, description="4 boundaries of the property schedule")
    grantors: list[str] = Field(default_factory=list, description="Names of sellers / transferors")
    grantees: list[str] = Field(default_factory=list, description="Names of buyers / transferees")
    prior_deeds: list[PriorDeedReference] = Field(default_factory=list, description="All prior deeds (Munnadharam) mentioned in recitals")
    easements_reserved: list[str] = Field(default_factory=list, description="Pathways, right-of-way, well access, or servitude clauses reserved")
    minor_involvement: str | None = Field(default=None, description="Any mention of minor children, guardians, or District Court orders")
    maintenance_covenants: str | None = Field(default=None, description="Any condition to maintain parents/donors or life interest reservation")
    raw_schedule_snippet: str = Field(default="", description="Verbatim Malayalam or English text snippet of property schedule and recitals")
    malayalam_summary: str = Field(default="", description="Concise bilingual summary of the property in Malayalam & English")
    ocr_engine_used: str = Field(default="Gemini 3.8 Flash Multimodal Vision", description="OCR/Vision Engine utilized")
    source_format: str = Field(default="PDF/Scan", description="Document input format")


class DeedOCRResult(BaseModel):
    metadata: ExtractedDeedMetadata
    sanity_result: DeedSanityResult
    building_rules: dict[str, Any] | None = None
    paddy_conversion: dict[str, Any] | None = None
    whatsapp_draft: str = ""
    whatsapp_draft_en: str = ""
    field_verification_checklist: list[str] = Field(default_factory=list)
    ocr_engine_used: str = "Gemini 3.8 Flash Multimodal Vision"
    document_type_detected: str = "Title Deed (ആധാരം)"


def _get_genai_client() -> Client:
    """Instantiates a Google GenAI Client targeting Vertex AI or API key."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if api_key:
        return Client(api_key=api_key)

    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    return Client(vertexai=True, project=project, location=location)


class DeedOCREngine:
    """Multimodal document understanding engine for Kerala real estate deeds."""

    EXTRACTION_PROMPT = """
You are a senior Kerala High Court Property Document Expert and Malayalam Paleographer.
Analyze the attached scanned Kerala Title Deed (ആധാരം) / Encumbrance Certificate (കുടിക്കടം) image or PDF document.

TASK:
Perform high-precision Optical Character Recognition (OCR) on the Malayalam and English text.
Extract the legal deed particulars, parties, property schedule (ഷെഡ്യൂൾ), four boundaries (ചതുരതിരുകൾ),
prior deeds lineage (മുന്നാധാരം), pathways/easements (നടപ്പുവഴി / വഴിയവകാശം), land nature (നിലം vs പുരയിടം),
and any restrictive covenants into the specified structured JSON schema.

KEY KERALA LEGAL GUIDELINES:
1. Four Boundaries (ചതുരതിരുകൾ):
   - കിഴക്ക് (East), തെക്ക് (South), പടിഞ്ഞാറ് (West), വടക്ക് (North).
   - Accurately record if any boundary specifies a pathway (വഴി), road (റോഡ്), or canal (തോട്).
2. Land Classification (ഭൂമി തരംതിരിവ്):
   - Check if described as പുരയിടം (Purayidam/Garden Land), തോട്ടം (Dry land) OR നിലം (Nilam/Paddy land), നഞ്ച (Nanja), പുഞ്ച (Punja), തണ്ണീർത്തടം (Wetland).
3. Prior Title Lineage (മുന്നാധാരം):
   - Extract any previous deed numbers, registration years, and SRO names cited in the preamble/recitals.
4. Encumbrances & Easements:
   - Carefully extract any pathway reservations (e.g., "3 മീറ്റർ വീതിയിൽ വഴി അവകാശം", "നടപ്പുവഴി"), well access (കിണർ അവകാശം), or senior citizen maintenance conditions.
5. Area & Units:
   - Convert or record extent in Cents (സെന്റ്) and Ares (ആർ). (1 Cent = 0.404686 Ares).

Extract all details faithfully without fabrication. If a field is not mentioned in the document, leave it as null or empty list.
"""

    def __init__(self, client: Client | None = None):
        self.client = client or _get_genai_client()
        self.scanner = SingleDeedScanner()
        self.knowledge_repo = KnowledgeRepository()
        self.audit_repo = AuditRepository()

    @staticmethod
    def _extract_text_from_pdf(pdf_bytes: bytes) -> str:
        lines: list[str] = []
        idx = pdf_bytes.find(b"stream")
        while idx != -1:
            end = pdf_bytes.find(b"endstream", idx)
            if end == -1:
                break
            chunk = pdf_bytes[idx + 6 : end].strip()
            for candidate in [chunk, b"<~" + chunk, chunk + b"~>", b"<~" + chunk + b"~>"]:
                try:
                    a85 = base64.a85decode(candidate, adobe=True)
                    decomp = zlib.decompress(a85)
                    texts = re.findall(rb"\(([^\)]+)\)", decomp)
                    for t in texts:
                        clean = (
                            t.decode("latin1", errors="ignore")
                            .replace(r"\(", "(")
                            .replace(r"\)", ")")
                        )
                        lines.append(clean)
                    break
                except Exception:
                    pass
            idx = pdf_bytes.find(b"stream", end)
        return "\n".join(lines)

    @staticmethod
    def _extract_metadata_from_text(raw_text: str) -> ExtractedDeedMetadata:
        meta = ExtractedDeedMetadata(raw_schedule_snippet=raw_text)

        doc_match = re.search(r"Document\s*No[:\s]+(\d+)\s*/\s*(\d+)", raw_text, re.I)
        if doc_match:
            meta.document_number = f"{doc_match.group(1)}/{doc_match.group(2)}"
            meta.year = int(doc_match.group(2))

        sro_match = re.search(r"Sub-Registrar\s*Office[:\s]+([^\n|]+)", raw_text, re.I)
        if sro_match:
            meta.sro_name = sro_match.group(1).strip()

        type_match = re.search(r"Nature[:\s]+([^\n|]+)", raw_text, re.I)
        if type_match:
            meta.deed_type = type_match.group(1).strip()

        resy_match = re.search(r"Re-Survey\s*No[:\s]+([^\n|]+)", raw_text, re.I)
        if resy_match:
            meta.re_survey_no = resy_match.group(1).strip()
            meta.survey_no = meta.re_survey_no
        else:
            sy_match = re.search(r"Survey\s*No[:\s]+([^\n|]+)", raw_text, re.I)
            if sy_match:
                meta.survey_no = sy_match.group(1).strip()

        vil_match = re.search(r"Village[:\s]+([^\n|]+)", raw_text, re.I)
        if vil_match:
            meta.village = vil_match.group(1).strip()
        tal_match = re.search(r"Taluk[:\s]+([^\n|]+)", raw_text, re.I)
        if tal_match:
            meta.taluk = tal_match.group(1).strip()
        dist_match = re.search(r"District[:\s]+([^\n|]+)", raw_text, re.I)
        if dist_match:
            meta.district = dist_match.group(1).strip()

        cents_match = re.search(r"(\d+(?:\.\d+)?)\s*Cents?", raw_text, re.I)
        if cents_match:
            meta.extent_cents = float(cents_match.group(1))
        ares_match = re.search(r"(\d+(?:\.\d+)?)\s*Ares?", raw_text, re.I)
        if ares_match:
            meta.extent_ares = float(ares_match.group(1))

        if re.search(r"Nilam|Nanja|Punja|Wetland|Paddy", raw_text, re.I):
            meta.revenue_classification = "Nilam"
            meta.is_paddy_wetland_risk = True
        else:
            meta.revenue_classification = "Purayidam"

        boundaries: list[DeedBoundary] = []
        east_match = re.search(r"East\s*(?:\([^)]+\))?[:\s]+([^\n]+)", raw_text, re.I)
        if east_match:
            boundaries.append(DeedBoundary(direction="East (കിഴക്ക്)", boundary_description=east_match.group(1).strip()))
        south_match = re.search(r"South\s*(?:\([^)]+\))?[:\s]+([^\n]+)", raw_text, re.I)
        if south_match:
            boundaries.append(DeedBoundary(direction="South (തെക്ക്)", boundary_description=south_match.group(1).strip()))
        west_match = re.search(r"West\s*(?:\([^)]+\))?[:\s]+([^\n]+)", raw_text, re.I)
        if west_match:
            boundaries.append(DeedBoundary(direction="West (പടിഞ്ഞാറ്)", boundary_description=west_match.group(1).strip()))
        north_match = re.search(r"North\s*(?:\([^)]+\))?[:\s]+([^\n]+)", raw_text, re.I)
        if north_match:
            boundaries.append(DeedBoundary(direction="North (വടക്ക്)", boundary_description=north_match.group(1).strip()))
        meta.boundaries = boundaries

        priors: list[PriorDeedReference] = []
        for line in raw_text.splitlines():
            if re.search(r"Partition Deed|Sale Deed|Pattayam|Theeradharam|Bhagapathram", line, re.I):
                num_m = re.search(r"No\.?\s*(\d+(?:/\d+)?)", line, re.I)
                priors.append(PriorDeedReference(
                    doc_number=num_m.group(1) if num_m else "Prior Doc",
                    deed_type="Munnadharam",
                    notes=line.strip(),
                ))
        meta.prior_deeds = priors

        for line in raw_text.splitlines():
            if re.search(r"pathway|vazhi|right\s*of\s*way|road|നടപ്പുവഴി|വഴി", line, re.I) and not re.search(r"East|South|West|North", line, re.I):
                meta.easements_reserved.append(line.strip())
            elif re.search(r"vazhi\s*avakasham", line, re.I):
                meta.easements_reserved.append(line.strip())

        minor_m = re.search(r"[^\n]*(?:minor|മൈനർ)[^\n]*", raw_text, re.I)
        if minor_m:
            meta.minor_involvement = minor_m.group(0).strip()

        maint_m = re.search(r"[^\n]*(?:maintenance|സംരക്ഷണം|senior\s*citizen)[^\n]*", raw_text, re.I)
        if maint_m:
            meta.maintenance_covenants = maint_m.group(0).strip()

        meta.malayalam_summary = (
            f"{meta.village} വില്ലേജിൽ സർവേ നമ്പർ {meta.survey_no}-ൽപ്പെട്ട {meta.extent_cents} സെന്റ് വസ്തു "
            f"({meta.revenue_classification})."
        )
        return meta

    def _try_documentai_ocr(self, file_bytes: bytes, mime_type: str) -> str | None:
        """Attempts Google Cloud Document AI processing if processor is configured."""
        processor_id = os.getenv("DOCUMENTAI_PROCESSOR_ID")
        if not processor_id:
            return None
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("DOCUMENTAI_LOCATION", "us")
        try:
            from google.cloud import documentai
            client = documentai.DocumentProcessorServiceClient()
            name = client.processor_path(project, location, processor_id)
            raw_document = documentai.RawDocument(content=file_bytes, mime_type=mime_type)
            request = documentai.ProcessRequest(name=name, raw_document=raw_document)
            result = client.process_document(request=request)
            logger.info("Successfully extracted text via Google Cloud Document AI processor")
            return result.document.text
        except Exception as e:
            logger.warning(f"Google Cloud Document AI invocation skipped or unavailable: {e}")
            return None

    def process_file_bytes(
        self,
        file_bytes: bytes,
        mime_type: str,
        session_id: str | None = None,
    ) -> DeedOCRResult:
        """Processes deed bytes (PDF or Image), performs multimodal OCR, evaluates legal traps, and persists findings."""
        part = types.Part.from_bytes(data=file_bytes, mime_type=mime_type)

        last_error = None
        extracted_metadata: ExtractedDeedMetadata | None = None
        engine_label = "Gemini 3.8 Flash Multimodal Vision"

        # Check for Google Cloud Document AI processor if configured
        docai_text = self._try_documentai_ocr(file_bytes, mime_type)
        if docai_text and docai_text.strip():
            try:
                extracted_metadata = self._extract_metadata_from_text(docai_text)
                engine_label = "Google Cloud Document AI (Processor OCR)"
                logger.info("Successfully utilized Cloud Document AI extracted text")
            except Exception as d_err:
                logger.warning(f"Failed parsing DocAI extracted text: {d_err}")

        if not extracted_metadata:
            for model_name in OCR_MODEL_CANDIDATES:
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=[part, self.EXTRACTION_PROMPT],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=ExtractedDeedMetadata,
                            temperature=0.1,
                        ),
                    )
                    if response.text:
                        parsed_json = json.loads(response.text)
                        extracted_metadata = ExtractedDeedMetadata(**parsed_json)
                        engine_label = f"Cloud Multimodal Vision ({model_name})"
                        logger.info(f"Successfully extracted deed metadata using {model_name}")
                        break
                except Exception as e:
                    logger.warning(f"Failed OCR extraction with model {model_name}: {e}")
                    last_error = e

        if not extracted_metadata:
            # Deterministic fallback for PDF documents
            if "pdf" in mime_type.lower() or file_bytes.startswith(b"%PDF"):
                try:
                    pdf_text = self._extract_text_from_pdf(file_bytes)
                    if pdf_text.strip():
                        extracted_metadata = self._extract_metadata_from_text(pdf_text)
                        engine_label = "Deterministic PDF Stream Parser"
                        logger.info("Successfully extracted deed metadata using local PDF text parser fallback")
                except Exception as fb_err:
                    logger.warning(f"PDF fallback parser failed: {fb_err}")

        if not extracted_metadata:
            raise RuntimeError(f"Multimodal OCR extraction failed across all model candidates: {last_error}")

        # Record engine and format
        extracted_metadata.ocr_engine_used = engine_label
        extracted_metadata.source_format = "PDF Document" if ("pdf" in mime_type.lower() or file_bytes.startswith(b"%PDF")) else "Image Scan"

        # Deterministic Legal Sanity Scan
        scan_payload = (
            f"Property Schedule:\n"
            f"Survey No: {extracted_metadata.survey_no}, Village: {extracted_metadata.village}\n"
            f"Extent: {extracted_metadata.extent_cents} Cents\n"
            f"Classification: {extracted_metadata.revenue_classification}\n"
            f"Boundaries:\n"
            + "\n".join(f"- {b.direction}: {b.boundary_description}" for b in extracted_metadata.boundaries)
            + f"\nEasements: {', '.join(extracted_metadata.easements_reserved) if extracted_metadata.easements_reserved else 'None'}\n"
            f"Minor: {extracted_metadata.minor_involvement or 'None'}\n"
            f"Maintenance: {extracted_metadata.maintenance_covenants or 'None'}\n\n"
            f"Verbatim Snippet:\n{extracted_metadata.raw_schedule_snippet}"
        )

        sanity_result = self.scanner.scan(scan_payload)

        # Lookup KPBR 2019 Building Rules for the plot extent
        building_rule = None
        if extracted_metadata.extent_cents > 0:
            building_rule = self.knowledge_repo.get_building_rule(
                plot_cents=extracted_metadata.extent_cents,
                occupancy_type="residential",
            )

        # Calculate Paddy Conversion Fee if classified as Nilam or flagged as wetland
        paddy_calc = None
        if extracted_metadata.revenue_classification.lower() == "nilam" or extracted_metadata.is_paddy_wetland_risk:
            paddy_calc = self.knowledge_repo.calculate_paddy_conversion_fee(
                plot_cents=extracted_metadata.extent_cents or 10.0,
                fair_value_per_are=200000.0,  # Benchmark default fair value
            )

        # Generate culturally polite WhatsApp draft for seller (Malayalam & English)
        whatsapp_draft = ""
        whatsapp_draft_en = ""
        for finding in sanity_result.findings:
            if finding.whatsapp_question_for_seller and not whatsapp_draft:
                whatsapp_draft = finding.whatsapp_question_for_seller
            if getattr(finding, "whatsapp_question_for_seller_en", None) and not whatsapp_draft_en:
                whatsapp_draft_en = finding.whatsapp_question_for_seller_en

        if not whatsapp_draft:
            whatsapp_draft = (
                f"നമസ്കാരം, സർവേ നമ്പർ {extracted_metadata.survey_no}-ൽപ്പെട്ട {extracted_metadata.extent_cents} സെന്റ് "
                f"വസ്തുവിന്റെ മുൻ ആധാരങ്ങളുടെ പകർപ്പും (മുന്നാധാരം), പുതിയ കുടിക്കട സർട്ടിഫിക്കറ്റും (EC - കഴിഞ്ഞ 30 വർഷത്തെ) "
                f"അഡ്വാൻസ് നൽകുന്നതിന് മുൻപായി ഒന്ന് അയച്ചുതരുമോ? നന്ദി."
            )
        if not whatsapp_draft_en:
            whatsapp_draft_en = (
                f"Hello, regarding the {extracted_metadata.extent_cents} Cents plot in Survey No {extracted_metadata.survey_no}, "
                f"could you please share copies of the prior title deeds (Munnadharam) and the latest 30-year Encumbrance Certificate (EC) "
                f"before we proceed with token advance? Thank you."
            )

        # Persist scan into database
        try:
            self.audit_repo.save_single_deed_scan(
                snippet=scan_payload,
                result_dict=sanity_result.model_dump(),
                session_id=session_id,
                language="en",
            )
        except Exception:
            try:
                self.audit_repo.save_single_deed_scan(
                    snippet=scan_payload,
                    result_dict=sanity_result.model_dump(),
                    session_id=session_id,
                )
            except Exception as e:
                logger.warning(f"Could not persist deed scan to database: {e}")

        return DeedOCRResult(
            metadata=extracted_metadata,
            sanity_result=sanity_result,
            building_rules=building_rule,
            paddy_conversion=paddy_calc,
            whatsapp_draft=whatsapp_draft,
            whatsapp_draft_en=whatsapp_draft_en,
            field_verification_checklist=sanity_result.field_checks,
            ocr_engine_used=extracted_metadata.ocr_engine_used,
            document_type_detected=extracted_metadata.deed_type or "Title Deed (ആധാരം)",
        )

    def process_file_path(self, file_path: str, session_id: str | None = None) -> DeedOCRResult:
        """Reads a local or uploaded deed file path and processes it via vision OCR."""
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        mime_type = "application/pdf"
        lower = file_path.lower()
        if lower.endswith(".png"):
            mime_type = "image/png"
        elif lower.endswith((".jpg", ".jpeg")):
            mime_type = "image/jpeg"
        elif lower.endswith(".webp"):
            mime_type = "image/webp"
        return self.process_file_bytes(file_bytes=file_bytes, mime_type=mime_type, session_id=session_id)

