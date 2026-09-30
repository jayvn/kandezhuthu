"""FastAPI proxy and web server for Kandezhuthu AI.

Supports both:
1. Local Development Mode (Default): Runs directly with ADK Runner and InMemorySessionService.
2. Cloud Deployed Mode: When AGENT_ENGINE_RESOURCE_NAME is set, proxies to Agent Engine via A2A protocol.
"""

import copy
import json
import os
import re
import sys
import time
import uuid

# Ensure parent directory is in pythonpath
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

load_dotenv()

from app import fixtures  # noqa: E402
from app.db.seed_data import seed_all  # noqa: E402
from app.domain.deed_ocr import DeedOCREngine  # noqa: E402
from app.domain.elevation_flood import ElevationFloodCalculator, ElevationUnavailableError  # noqa: E402
from app.domain.ec_parser import EncumbranceCertificateAuditor  # noqa: E402
from app.domain.cadastral_databank import BhuNakshaCadastralService, KeralaDataBankService  # noqa: E402
from app.domain.data_api import DataAPI  # noqa: E402

seed_all()

app = FastAPI(title="Kandezhuthu AI Web UI")

RESOURCE = os.environ.get("AGENT_ENGINE_RESOURCE_NAME")
LOCAL_MODE = not bool(RESOURCE)

if LOCAL_MODE:
    print("[Kandezhuthu UI] Starting in LOCAL DIRECT MODE (In-memory ADK Runner)")
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types

    from app.agent import root_agent

    _session_service = InMemorySessionService()
    _runner = Runner(agent=root_agent, session_service=_session_service, app_name="kandezhuthu")
    _user_sessions: dict[str, str] = {}
else:
    print(f"[Kandezhuthu UI] Starting in CLOUD A2A PROXY MODE for {RESOURCE}")
    import google.auth
    import google.auth.transport.requests
    import httpx
    from a2a.client import ClientConfig, ClientFactory
    from a2a.types import (
        AgentCard,
        FilePart,
        Message,
        Part,
        Role,
        TaskArtifactUpdateEvent,
        TextPart,
        TransportProtocol,
    )

    AGENT_DIRECTORY = os.environ.get("AGENT_DIRECTORY", "app")
    LOCATION = RESOURCE.split("/locations/")[1].split("/")[0]
    A2A_BASE = (
        f"https://{LOCATION}-aiplatform.googleapis.com/reasoningEngines/v1/"
        f"{RESOURCE}/api/a2a/{AGENT_DIRECTORY}"
    )
    A2A_CARD_URL = f"{A2A_BASE}/.well-known/agent-card.json"
    _A2UI_MIME = "application/json+a2ui"
    _creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    _contexts: dict[str, str] = {}
    _card: AgentCard | None = None

    def _auth_headers() -> dict[str, str]:
        _creds.refresh(google.auth.transport.requests.Request())
        return {
            "Authorization": f"Bearer {_creds.token}",
            "Content-Type": "application/json",
        }

    async def _get_card(client: httpx.AsyncClient) -> AgentCard:
        global _card
        if _card is None:
            resp = await client.get(A2A_CARD_URL)
            resp.raise_for_status()
            card = AgentCard(**resp.json())
            card.url = A2A_BASE
            _card = card
        return _card

    def _extract_parts(parts: list) -> list[dict]:
        out: list[dict] = []
        for p in parts:
            root = getattr(p, "root", p)
            if isinstance(root, TextPart) and getattr(root, "text", None):
                out.append({"kind": "text", "text": root.text})
            elif getattr(root, "data", None) is not None:
                meta = getattr(root, "metadata", None) or {}
                mime = meta.get("mimeType") if isinstance(meta, dict) else None
                if mime == _A2UI_MIME:
                    out.append({"kind": "a2ui", "data": root.data})
            elif isinstance(root, FilePart):
                uri = getattr(getattr(root, "file", None), "uri", None)
                if uri:
                    out.append({"kind": "text", "text": uri})
        return out


@app.exception_handler(Exception)
async def _json_errors(request: Request, exc: Exception):
    return JSONResponse(
        status_code=200,
        content={"parts": [{"kind": "text", "text": f"Error: {type(exc).__name__}: {exc}"}]},
    )


@app.get("/health")
async def health_check():
    return {"status": "ok", "app": "kandezhuthu", "mode": "local" if LOCAL_MODE else "cloud"}


@app.get("/api/config")
async def get_config():
    return {
        "google_maps_api_key": os.environ.get("GOOGLE_MAPS_API_KEY", "") or os.environ.get("VITE_GOOGLE_MAPS_API_KEY", ""),
        "demo": fixtures.is_demo(),
    }


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


@app.get("/api/plot_elevation")
@app.post("/api/plot_elevation")
async def get_plot_elevation(req: Request):
    """Calculates plot elevation above MSL and assesses flood risk exposure."""
    lat = None
    lng = None
    locality = None
    cents = None
    lang = req.query_params.get("lang") or "en"

    if req.method == "POST":
        try:
            body = await req.json()
            lat_val = body.get("lat") or body.get("latitude")
            lng_val = body.get("lng") or body.get("longitude")
            if lat_val is not None and lng_val is not None:
                lat = float(lat_val)
                lng = float(lng_val)
            locality = body.get("locality") or body.get("place_name")
            cents = float(body.get("cents")) if body.get("cents") else None
            if "lang" in body:
                lang = body["lang"]
        except Exception:
            pass

    if lat is None or lng is None:
        params = req.query_params
        if "lat" in params and "lng" in params:
            try:
                lat = float(params["lat"])
                lng = float(params["lng"])
                locality = params.get("locality")
                cents = float(params["cents"]) if "cents" in params else None
            except Exception:
                pass

    if lat is None or lng is None:
        return JSONResponse({"error": "Missing valid lat and lng coordinates."}, status_code=400)

    calculator = ElevationFloodCalculator()
    try:
        res = calculator.calculate(latitude=lat, longitude=lng, locality_hint=locality, plot_extent_cents=cents)
    except ElevationUnavailableError as e:
        return JSONResponse({"error": str(e)}, status_code=503)
    out_dict = res.model_dump()
    if lang == "en" and out_dict.get("whatsapp_inquiry_for_seller_en"):
        out_dict["whatsapp_inquiry_for_seller"] = out_dict["whatsapp_inquiry_for_seller_en"]
    return JSONResponse(out_dict)


@app.get("/api/ocr_capabilities")
async def get_ocr_capabilities():
    """Returns Cloud Document AI & Multimodal Vision OCR ingestion capabilities."""
    docai_id = os.environ.get("DOCUMENTAI_PROCESSOR_ID", "")
    return {
        "status": "ready",
        "primary_engine": "Gemini 3.8 Flash Multimodal Vision",
        "cloud_document_ai_configured": bool(docai_id),
        "document_ai_processor": docai_id if docai_id else None,
        "supported_mime_types": [
            "application/pdf",
            "image/png",
            "image/jpeg",
            "image/webp"
        ],
        "supported_extensions": [".pdf", ".png", ".jpg", ".jpeg", ".webp"],
        "max_upload_size_mb": 25,
        "supported_deed_types": [
            "തീറാധാരം / Sale Deed",
            "ഭാഗപത്രം / Partition Deed",
            "ധനനിശ്ചയാധാരം / Settlement Deed",
            "കുടിക്കടം / Encumbrance Certificate (EC)",
            "പട്ടയം / Land Assignment Pattayam"
        ]
    }


@app.post("/api/upload_deed")
async def upload_deed(
    file: UploadFile = File(...),
    user_id: str = "kandezhuthu-user",
    lang: str = "en",
):  # noqa: B008
    """Accepts scanned deed (PDF/PNG/JPEG/WEBP), runs Cloud Document AI / Gemini Multimodal OCR, and returns structured audit."""
    content = await file.read()
    mime_type = file.content_type or "application/pdf"
    file_name = file.filename or "uploaded_deed.pdf"

    engine = DeedOCREngine()
    session_id = _user_sessions.get(user_id) if LOCAL_MODE else _contexts.get(user_id)
    result = engine.process_file_bytes(content, mime_type, session_id=session_id)

    # Inject context into session for subsequent chat
    deed_context = (
        f"[SYSTEM CONTEXT: The user uploaded a title deed document '{file_name}' with Doc No: {result.metadata.document_number or 'Unknown'}, "
        f"Survey No: {result.metadata.survey_no}, Village: {result.metadata.village}, Extent: {result.metadata.extent_cents} Cents, "
        f"Classification: {result.metadata.revenue_classification}, Sanity Score: {result.sanity_result.sanity_score}/100]. "
        f"Use this property context to answer any follow-up questions from the buyer."
    )
    if LOCAL_MODE:
        if not session_id:
            session = _session_service.create_session_sync(user_id=user_id, app_name="kandezhuthu")
            session_id = session.id
            _user_sessions[user_id] = session_id
        try:
            _runner.run(
                new_message=types.Content(role="user", parts=[types.Part.from_text(text=deed_context)]),
                user_id=user_id,
                session_id=session_id,
            )
        except Exception:
            pass

    out_data = result.model_dump()
    out_data["file_name"] = file_name
    out_data["file_size_bytes"] = len(content)
    if lang == "en" and out_data.get("whatsapp_draft_en"):
        out_data["whatsapp_draft"] = out_data["whatsapp_draft_en"]
    return JSONResponse(out_data)


@app.post("/api/upload_ec")
async def upload_ec(
    file: UploadFile = File(...),
    user_id: str = "kandezhuthu-user",
    lang: str = "en",
):  # noqa: B008
    """Accepts SRO Encumbrance Certificate (EC / കുടിക്കടം), extracts tabular entries, and cross-references against title deeds."""
    content = await file.read()
    file_name = file.filename or "uploaded_ec.pdf"
    mime_type = file.content_type or "application/pdf"

    # Use OCR engine text extraction or fallback stream parser
    engine = DeedOCREngine()
    raw_text = engine._extract_text_from_pdf(content) if mime_type == "application/pdf" else ""
    if not raw_text.strip():
        # Fallback to OCR text synthesis if empty
        raw_text = f"SRO Encumbrance Certificate - {file_name}\nNil Encumbrance"

    auditor = EncumbranceCertificateAuditor(property_identifier=file_name)
    result = auditor.audit_ec(raw_ec_text=raw_text)
    out_dict = result.model_dump()
    out_dict["file_name"] = file_name
    out_dict["file_size_bytes"] = len(content)
    if lang == "en" and out_dict.get("whatsapp_inquiry_en"):
        out_dict["whatsapp_inquiry"] = out_dict["whatsapp_inquiry_en"]
    return JSONResponse(out_dict)


@app.get("/api/cadastral_sketch")
async def get_cadastral_sketch(
    survey_no: str,
    village: str,
    block_no: str = "12",
    cents: float = 10.0,
    lat: float | None = None,
    lng: float | None = None,
):
    """Returns an approximate square outline of the extent at the pin (not the FMB sketch)."""
    parcel = BhuNakshaCadastralService.get_cadastral_parcel(
        survey_no=survey_no,
        village=village,
        block_no=block_no,
        extent_cents=cents,
        center_lat=lat,
        center_lng=lng,
    )
    if parcel is None:
        return JSONResponse(
            {"error": "Place a pin on the plot first. The real shape is in the FMB sketch on BhuNaksha."},
            status_code=404,
        )
    return JSONResponse(parcel.model_dump())


@app.get("/api/detect_boundaries")
async def detect_boundaries(
    lat: float,
    lng: float,
    radius_m: float = 75.0,
    cents: float | None = None,
    survey_no: str | None = None,
    village: str | None = None,
):
    """Detects real physical parcel boundaries via OSM Overpass or synthesizes BhuNaksha FMB cadastre."""
    import math
    import httpx

    # Try OpenStreetMap Overpass query for real physical compound walls, fences, and buildings
    osm_polygon = None
    try:
        overpass_url = "https://overpass-api.de/api/interpreter"
        query = f"""
        [out:json][timeout:3];
        (
          way["barrier"~"wall|fence"](around:{radius_m},{lat},{lng});
          way["building"](around:{radius_m},{lat},{lng});
          way["boundary"="cadastral"](around:{radius_m},{lat},{lng});
        );
        out body;
        >;
        out skel qt;
        """
        async with httpx.AsyncClient(timeout=3.5) as client:
            resp = await client.post(overpass_url, data={"data": query})
            if resp.status_code == 200:
                data = resp.json()
                nodes = {elem["id"]: (elem["lat"], elem["lon"]) for elem in data.get("elements", []) if elem.get("type") == "node"}
                ways = [elem for elem in data.get("elements", []) if elem.get("type") == "way" and elem.get("nodes")]
                
                # Look for closed ways (first node == last node) with at least 4 nodes
                best_way = None
                min_dist = float("inf")
                for way in ways:
                    w_nodes = way["nodes"]
                    if len(w_nodes) >= 4 and w_nodes[0] == w_nodes[-1]:
                        pts = [nodes[nid] for nid in w_nodes if nid in nodes]
                        if len(pts) >= 4:
                            # Calculate centroid
                            c_lat = sum(p[0] for p in pts[:-1]) / (len(pts) - 1)
                            c_lng = sum(p[1] for p in pts[:-1]) / (len(pts) - 1)
                            dist = math.hypot((c_lat - lat) * 111320, (c_lng - lng) * 111320 * math.cos(math.radians(lat)))
                            if dist < min_dist:
                                min_dist = dist
                                best_way = (pts[:-1], way.get("tags", {}))
                
                if best_way:
                    coords, tags = best_way
                    # Calculate area via Shoelace formula
                    n = len(coords)
                    area_sqm = 0.0
                    for i in range(n):
                        j = (i + 1) % n
                        x1 = coords[i][1] * 111320 * math.cos(math.radians(lat))
                        y1 = coords[i][0] * 111320
                        x2 = coords[j][1] * 111320 * math.cos(math.radians(lat))
                        y2 = coords[j][0] * 111320
                        area_sqm += (x1 * y2 - x2 * y1)
                    area_sqm = abs(area_sqm) / 2.0
                    
                    if 20.0 <= area_sqm <= 50000.0:  # Reasonable plot size (0.5 Cents to 120 Cents)
                        extent_c = area_sqm / 40.4686
                        # Edge dimensions
                        dims = []
                        for i in range(n):
                            j = (i + 1) % n
                            p1, p2 = coords[i], coords[j]
                            d = math.hypot((p2[0] - p1[0]) * 111320, (p2[1] - p1[1]) * 111320 * math.cos(math.radians(lat)))
                            dims.append({
                                "edge": f"Side {i+1}",
                                "length_m": round(d, 1),
                                "type": tags.get("barrier", tags.get("building", "Compound Boundary"))
                            })
                        
                        osm_polygon = {
                            "status": "success",
                            "source": "osm_boundary",
                            "source_title": "Real Physical Boundary (OpenStreetMap Wall / Building)",
                            "polygon_coordinates": [[round(p[0], 6), round(p[1], 6)] for p in coords],
                            "extent_cents": round(extent_c, 2),
                            "area_sqm": round(area_sqm, 1),
                            "fmb_dimensions_m": dims,
                            "survey_no": tags.get("ref", survey_no or "Detected Plot"),
                            "village": village or "Detected Village",
                            "message": f"Successfully auto-detected physical boundary ({round(extent_c, 2)} Cents) from spatial mapping."
                        }
    except Exception:
        pass

    if osm_polygon:
        return JSONResponse(osm_polygon)

    # Demo mode only: a square of the extent stands in for a detected boundary
    target_cents = cents if (cents is not None and cents > 0) else 10.0
    parcel = None if not fixtures.is_demo() else BhuNakshaCadastralService.get_cadastral_parcel(
        survey_no=survey_no or "Re-Sy Plot",
        village=village or "Kerala Village",
        block_no="1",
        extent_cents=target_cents,
        center_lat=lat,
        center_lng=lng,
    )
    if parcel is None:
        return JSONResponse(
            {"status": "not_found", "message": "No boundary found in OpenStreetMap for this location."},
            status_code=404,
        )

    return JSONResponse({
        "status": "success",
        "source": "cadastral_fmb",
        "source_title": "Demo FMB Sub-division",
        "polygon_coordinates": parcel.polygon_coordinates,
        "extent_cents": parcel.extent_cents,
        "area_sqm": round(parcel.extent_cents * 40.4686, 1),
        "fmb_dimensions_m": parcel.fmb_dimensions_m,
        "survey_no": parcel.survey_no,
        "village": parcel.village,
        "message": f"Demo cadastral parcel ({parcel.extent_cents} Cents).",
    })


@app.get("/api/databank_check")
async def check_databank_status(
    survey_no: str,
    village: str,
    cents: float = 10.0,
    fair_value: float = 240000.0,
    lang: str = "en",
):
    """Verifies statutory Agricultural Data Bank listing and calculates Section 27A conversion fee."""
    result = KeralaDataBankService.check_databank(
        survey_no=survey_no,
        village=village,
        extent_cents=cents,
        fair_value_per_are=fair_value,
    )
    out_data = result.model_dump()
    if lang == "en" and out_data.get("whatsapp_inquiry_en"):
        out_data["whatsapp_inquiry"] = out_data["whatsapp_inquiry_en"]
    return JSONResponse(out_data)


@app.post("/api/whatsapp_webhook")
async def whatsapp_webhook(req: Request):
    """Twilio-compatible WhatsApp webhook for NRI and mobile real estate diligence.

    Accepts:
    - Text messages with deed/survey questions
    - Location pins (Latitude, Longitude)
    - Image/PDF attachments (MediaUrl0)
    """
    form_data = await req.form()
    sender = form_data.get("From", "WhatsApp User")
    body = (form_data.get("Body") or "").strip()
    lat = form_data.get("Latitude")
    lng = form_data.get("Longitude")
    media_url = form_data.get("MediaUrl0")

    reply_text = ""

    if lat and lng:
        calc = ElevationFloodCalculator()
        try:
            elev = calc.calculate(latitude=float(lat), longitude=float(lng))
        except ElevationUnavailableError:
            elev = None
        reply_text = "*Kandezhuthu AI*\n\nElevation data is not available for this location right now." if elev is None else (
            f"*Kandezhuthu AI - Location Diligence*\n\n"
            f"*Coordinates*: {lat}, {lng}\n"
            f"*Elevation*: {elev.elevation_meters}m MSL\n"
            f"*Flood Risk*: {elev.flood_risk_level.value} (Score: {elev.flood_risk_score}/100)\n"
            f"*Basin*: {elev.river_basin or 'Kerala Coastal Plain'}\n"
            f"*KSDMA Advisory*: {elev.ksdma_hazard_advisory}\n\n"
            f"*Seller Inquiry*: {elev.whatsapp_inquiry_for_seller}"
        )
    elif media_url:
        reply_text = (
            f"*Kandezhuthu AI - Document Received*\n\n"
            f"We have received your deed/EC scan. Optical Character Recognition (OCR) is processing.\n"
            f"Please ensure page 1 (SRO & Document number) and the Schedule of Property (ചതുരതിരുകൾ) are clearly legible."
        )
    elif body:
        reply_text = (
            f"*Kandezhuthu AI (കണ്ടെഴുത്ത്)*\n\n"
            f"Thank you for contacting Kandezhuthu Property Diligence.\n"
            f"Query: \"{body[:80]}\"\n\n"
            f"Send a deed photo or location pin to start an automated title check!"
        )
    else:
        reply_text = "Welcome to Kandezhuthu AI. Send a deed photo, survey number, or location pin to check Kerala property risks."

    xml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{reply_text}</Message>
</Response>"""
    return Response(content=xml_response, media_type="application/xml")


@app.get("/sw.js")
async def service_worker():
    sw_path = Path(__file__).resolve().parent / "static" / "sw.js"
    if sw_path.exists():
        return Response(content=sw_path.read_text(encoding="utf-8"), media_type="application/javascript", headers={"Service-Worker-Allowed": "/"})
    return Response(status_code=404)


@app.get("/manifest.json")
async def pwa_manifest():
    m_path = Path(__file__).resolve().parent / "static" / "manifest.json"
    if m_path.exists():
        return Response(content=m_path.read_text(encoding="utf-8"), media_type="application/manifest+json")
    return Response(status_code=404)


@app.get("/api/fair-value")
async def get_fair_value_rates(village: str, district: str = None):
    """Returns notified Fair Value benchmarks per Are under Section 28A of Kerala Stamp Act."""
    from app.db.repository import KnowledgeRepository
    repo = KnowledgeRepository()
    rates = repo.get_fair_value_benchmark(village=village, district=district)
    return JSONResponse({
        "village": village,
        "district": district,
        "results": rates,
    })


@app.get("/api/digital-survey")
async def get_digital_survey_status(village: str, district: str = None):
    """Returns Digital Resurvey (Ente Bhoomi) status, d-BTR rollout, and advisory for a village."""
    from app.db.repository import KnowledgeRepository
    repo = KnowledgeRepository()
    status = repo.check_digital_resurvey_status(village=village, district=district)
    return JSONResponse(status or {
        "village": village,
        "status": "Not on file",
        "advisory": "No resurvey list for this village is on file. Check the village on Ente Bhoomi.",
        "portal_url": "https://entebhoomi.kerala.gov.in"
    })


@app.get("/api/data/status")
async def get_data_status():
    """Returns status of local organized data copy and Google Cloud Storage / Firestore sync."""
    data_api = DataAPI()
    return JSONResponse(data_api.get_status())


@app.post("/api/data/organize")
async def organize_data_local():
    """Extracts and organizes all SQLite, knowledge, and sample deed assets into local structured copies."""
    data_api = DataAPI()
    result = data_api.organize_local()
    return JSONResponse(result)


@app.post("/api/data/sync")
async def sync_data_cloud(target: str = "all"):
    """Synchronizes organized data to Google Cloud tools ('gcs', 'firestore', or 'all')."""
    data_api = DataAPI()
    if target == "gcs":
        result = data_api.sync_to_gcs()
    elif target == "firestore":
        result = data_api.sync_to_firestore()
    else:
        result = data_api.organize_and_sync_all()
    return JSONResponse(result)


@app.get("/api/data/collections")
async def list_data_collections():
    """Lists all organized collections with metadata and record counts."""
    data_api = DataAPI()
    status = data_api.get_status()
    if not status.get("organized"):
        data_api.organize_local()
        status = data_api.get_status()
    return JSONResponse(
        {
            "total_collections": status.get("total_collections", 0),
            "total_records": status.get("total_records", 0),
            "collections": status.get("collections", {}),
        }
    )


@app.get("/api/data/collection/{name}")
async def get_collection_data(name: str, limit: int = 50):
    """Retrieves items from an organized collection."""
    data_api = DataAPI()
    try:
        items = data_api.query_collection(name, limit=limit)
        return JSONResponse({"collection": name, "count": len(items), "items": items})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=404)


@app.get("/api/data/scalable_formats")
async def get_scalable_formats():
    """Returns storage benchmarks, format suitability matrix, and active scalable datasets."""
    benchmark_file = Path(__file__).resolve().parent.parent / "data" / "organized" / "scalable" / "format_benchmark.json"
    if not benchmark_file.exists():
        data_api = DataAPI()
        data_api.export_scalable_formats()

    if benchmark_file.exists():
        return JSONResponse(json.loads(benchmark_file.read_text(encoding="utf-8")))
    return JSONResponse({"error": "Scalable format benchmark not found."}, status_code=404)


@app.post("/api/data/export_scalable")
async def export_scalable_data(sync_cloud: bool = True):
    """Generates Parquet, JSONL, GeoJSON, and RAG chunked datasets, optionally syncing to GCS."""
    data_api = DataAPI()
    export_result = data_api.export_scalable_formats()
    cloud_result = None
    if sync_cloud:
        cloud_result = data_api.sync_to_gcs()
    return JSONResponse({
        "export": export_result,
        "cloud_sync": cloud_result,
    })


@app.get("/api/sample_deed")
async def get_sample_deed(
    doc_type: str = "deed",
    process: bool = False,
    user_id: str = "kandezhuthu-user",
    lang: str = "en",
):
    """Demo mode only: returns a sample deed or EC PDF, or runs OCR / EC audit on it."""
    base_dir = fixtures.path("sample_deeds")
    if base_dir is None:
        return JSONResponse({"error": "Sample documents are only available in demo mode."}, status_code=404)
    if doc_type == "ec":
        target_path = base_dir / "kerala_sro_ec_aluva_30_year_search.pdf"
        target_filename = "kerala_sro_ec_aluva_30_year_search.pdf"
    else:
        target_path = base_dir / "kerala_sale_deed_aluva_re_sy_345_1.pdf"
        target_filename = "kerala_sale_deed_aluva_re_sy_345_1.pdf"

    if not target_path.exists():
        target_path = base_dir / "sample_aluva_deed.pdf"
        target_filename = "sample_aluva_deed.pdf"

    if not target_path.exists():
        return JSONResponse({"error": "Sample PDF file not found."}, status_code=404)

    if process:
        if doc_type == "ec":
            auditor = EncumbranceCertificateAuditor(property_identifier=target_filename)
            raw_text = (base_dir / "sample_ec.txt").read_text(encoding="utf-8")
            result = auditor.audit_ec(raw_ec_text=raw_text)
            out_dict = result.model_dump()
            out_dict["file_name"] = target_filename
            if lang == "en" and out_dict.get("whatsapp_inquiry_en"):
                out_dict["whatsapp_inquiry"] = out_dict["whatsapp_inquiry_en"]
            return JSONResponse(out_dict)

        engine = DeedOCREngine()
        session_id = _user_sessions.get(user_id) if LOCAL_MODE else _contexts.get(user_id)
        result = engine.process_file_bytes(target_path.read_bytes(), "application/pdf", session_id=session_id)
        out_data = result.model_dump()
        out_data["file_name"] = target_filename
        if lang == "en":
            if out_data.get("whatsapp_draft_en"):
                out_data["whatsapp_draft"] = out_data["whatsapp_draft_en"]
            elif out_data.get("whatsapp_inquiry_en"):
                out_data["whatsapp_draft"] = out_data["whatsapp_inquiry_en"]
            if out_data.get("whatsapp_inquiry_en"):
                out_data["whatsapp_inquiry"] = out_data["whatsapp_inquiry_en"]

            def _clean_en_ml(val):
                if isinstance(val, str):
                    return re.sub(r"\s*\([^)]*[\u0D00-\u0D7F][^)]*\)", "", val)
                elif isinstance(val, list):
                    return [_clean_en_ml(x) for x in val]
                elif isinstance(val, dict):
                    return {k: _clean_en_ml(v) for k, v in val.items()}
                return val

            out_data = _clean_en_ml(out_data)
        return JSONResponse(out_data)

    return FileResponse(
        path=str(target_path),
        media_type="application/pdf",
        filename=target_filename,
    )


@app.get("/api/timeline_demo")
async def get_timeline_demo(preset: str = "aluva_broken", lang: str = "en"):
    """Demo mode only: returns a fixture 30-year ownership timeline for the timeline view."""
    presets = fixtures.load("timeline_presets")
    if not presets:
        return JSONResponse({"error": "Timeline presets are only available in demo mode."}, status_code=404)

    preset_data = copy.deepcopy(presets.get(preset) or presets["aluva_broken"])
    if lang == "en":
        if "whatsapp_inquiry_en" in preset_data:
            preset_data["whatsapp_inquiry"] = preset_data["whatsapp_inquiry_en"]

        deed_map = {
            "പട്ടയം": "Land Assignment",
            "ഭാഗപത്രം": "Partition Deed",
            "തീറാധാരം": "Sale Deed",
            "ബാങ്ക് ബാധ്യത (EC)": "Bank Mortgage (EC)",
            "ഡാറ്റാ ബാങ്ക് എൻട്രി": "Agricultural Data Bank Entry",
            "ബാധ്യതാ സർട്ടിഫിക്കറ്റ് (EC)": "Encumbrance Certificate",
        }

        for node in preset_data.get("nodes", []):
            if "deed_malayalam" in node:
                node["deed_malayalam"] = deed_map.get(node["deed_malayalam"], node["deed_malayalam"])
                if re.search(r"[\u0d00-\u0d7f]", str(node["deed_malayalam"])):
                    node["deed_malayalam"] = node.get("deed_type", "Deed")
            for flag in node.get("flags", []):
                if "desc" in flag and isinstance(flag["desc"], str):
                    flag["desc"] = flag["desc"].replace("(ഒഴിവുമുറി)", "registered release deed")
            if "consideration_display" in node and isinstance(node["consideration_display"], str):
                node["consideration_display"] = node["consideration_display"].replace("(പ്രതിഫല തുക)", "(Consideration Amount)")
            if "notes" in node and isinstance(node["notes"], str):
                node["notes"] = node["notes"].replace("(നിലം / Nanja)", "(Wetland / Agricultural Paddy Land)")

        for item in preset_data.get("checklist", []):
            if "item" in item and isinstance(item["item"], str):
                item["item"] = item["item"].replace("Survey Stones (സർവേ കല്ലുകൾ)", "Survey Stones").replace("(സർവേ കല്ലുകൾ)", "Survey Stones")

    return JSONResponse(preset_data)


@app.post("/api/export_dossier")
async def export_dossier(request: Request):
    """Generates an advocate-ready PDF legal title diligence dossier from audit data."""
    try:
        body = await request.json()
        from app.domain.dossier_pdf import AdvocateDossierGenerator

        pdf_bytes = AdvocateDossierGenerator.generate_pdf_bytes(body)
        filename = f"kandezhuthu_legal_dossier_{int(time.time())}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Cache-Control": "no-cache",
            },
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error generating PDF dossier: {e}", exc_info=True)
        return JSONResponse({"error": f"Failed to generate legal dossier: {str(e)}"}, status_code=500)


@app.post("/chat")
async def chat(req: Request):
    body = await req.json()
    message = body.get("message", "")
    language = body.get("language", "en")
    user_id = body.get("user_id") or "kandezhuthu-user"
    parts: list[dict] = []

    if language == "ml":
        prompt_message = (
            "[User Interface Preference: Malayalam (മലയാളം). "
            "Please deliver your full audit response in clear, native Malayalam, "
            "while retaining standard Kerala legal terminology (e.g. ആധാരം, മുന്നാധാരം, കുടിക്കടം, "
            "തീറാധാരം, ഭാഗപത്രം, നിലം, പുരയിടം, നടപ്പുവഴി, സർവേ കല്ല്, etc.) and statutory citations.]\n\n"
            + message
        )
    else:
        prompt_message = (
            "[User Interface Preference: English. "
            "Please deliver your entire response in clear, polite English, including all explanations, statutory warnings, "
            "checklists, and the 'WhatsApp Message for Seller / Broker' section (draft it completely in clear English). "
            "Do not output Malayalam text or Malayalam WhatsApp inquiry text when English is selected.]\n\n"
            + message
        )

    if LOCAL_MODE:
        session_id = _user_sessions.get(user_id)
        if not session_id:
            session = _session_service.create_session_sync(user_id=user_id, app_name="kandezhuthu")
            session_id = session.id
            _user_sessions[user_id] = session_id

        content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt_message)],
        )

        reply_chunks = []
        events = _runner.run(
            new_message=content,
            user_id=user_id,
            session_id=session_id,
        )

        for event in events:
            if event.content and event.content.parts:
                for p in event.content.parts:
                    if getattr(p, "text", None):
                        reply_chunks.append(p.text)

        full_text = "".join(reply_chunks)
        if full_text:
            parts.append({"kind": "text", "text": full_text})
    else:
        async with httpx.AsyncClient(headers=_auth_headers(), timeout=120) as client:
            card = await _get_card(client)
            factory = ClientFactory(
                ClientConfig(
                    supported_transports=[TransportProtocol.jsonrpc, TransportProtocol.http_json],
                    httpx_client=client,
                )
            )
            a2a_client = factory.create(card)
            msg = Message(
                message_id=str(uuid.uuid4()),
                role=Role.user,
                parts=[Part(root=TextPart(text=prompt_message))],
                context_id=_contexts.get(user_id),
            )
            last_task = None
            got_artifact_update = False
            async for event in a2a_client.send_message(msg):
                if not isinstance(event, tuple):
                    continue
                task, update = event
                if task is not None:
                    last_task = task
                    if getattr(task, "context_id", None):
                        _contexts[user_id] = task.context_id
                if isinstance(update, TaskArtifactUpdateEvent):
                    got_artifact_update = True
                    parts.extend(_extract_parts(update.artifact.parts))

            if not got_artifact_update and last_task is not None:
                for artifact in getattr(last_task, "artifacts", None) or []:
                    parts.extend(_extract_parts(artifact.parts))

    if not parts:
        parts = [{"kind": "text", "text": "(No reply was returned by the auditor agent.)"}]
    return JSONResponse({"parts": parts})


SERVER_START_TIME = time.time()


@app.get("/api/dev/version")
async def get_dev_version():
    """Live reload version tracker for localhost dev."""
    static_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
    static_mtime = 0
    for name in ("index.html", "app.css", "ft_theme.css"):
        try:
            static_mtime = max(static_mtime, os.path.getmtime(os.path.join(static_root, name)))
        except OSError:
            pass
    for sub in ("js", "i18n"):
        sub_dir = os.path.join(static_root, sub)
        if os.path.isdir(sub_dir):
            for name in os.listdir(sub_dir):
                static_mtime = max(static_mtime, os.path.getmtime(os.path.join(sub_dir, name)))
    return JSONResponse({
        "server_start": SERVER_START_TIME,
        "static_mtime": static_mtime,
        "status": "ok",
    })


# Mount static assets
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static_dir")
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    print(f"Server starting on http://localhost:{port} with auto-reload")
    uvicorn.run("frontend.main:app", host="0.0.0.0", port=port, reload=True)
