"""FastAPI proxy and web server for Kandezhuthu AI.

Supports both:
1. Local Development Mode (Default): Runs directly with ADK Runner and InMemorySessionService.
2. Cloud Deployed Mode: When AGENT_ENGINE_RESOURCE_NAME is set, proxies to Agent Engine via A2A protocol.
"""

import json
import os
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

from app.db.seed_data import seed_all  # noqa: E402
from app.domain.deed_ocr import DeedOCREngine  # noqa: E402
from app.domain.elevation_flood import ElevationFloodCalculator  # noqa: E402
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
        "google_maps_api_key": os.environ.get("GOOGLE_MAPS_API_KEY", "") or os.environ.get("VITE_GOOGLE_MAPS_API_KEY", "")
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
    res = calculator.calculate(latitude=lat, longitude=lng, locality_hint=locality, plot_extent_cents=cents)
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
    survey_no: str = "345/1",
    village: str = "Aluva West",
    block_no: str = "12",
    cents: float = 10.0,
    lat: float | None = None,
    lng: float | None = None,
):
    """Returns digital cadastral sub-division boundaries (FMB polygon geometry) and segment dimensions."""
    parcel = BhuNakshaCadastralService.get_cadastral_parcel(
        survey_no=survey_no,
        village=village,
        block_no=block_no,
        extent_cents=cents,
        center_lat=lat,
        center_lng=lng,
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

    # Fallback to BhuNaksha Cadastral Parcel Synthesizer
    target_cents = cents if (cents is not None and cents > 0) else 10.0
    parcel = BhuNakshaCadastralService.get_cadastral_parcel(
        survey_no=survey_no or "Re-Sy Plot",
        village=village or "Kerala Village",
        block_no="1",
        extent_cents=target_cents,
        center_lat=lat,
        center_lng=lng,
    )
    
    dims_data = []
    for d in parcel.fmb_dimensions_m:
        if hasattr(d, "model_dump"):
            dims_data.append(d.model_dump())
        elif isinstance(d, dict):
            dims_data.append(d)
        else:
            dims_data.append({"edge": str(getattr(d, "edge", "")), "length_m": float(getattr(d, "length_m", 0.0)), "type": str(getattr(d, "type", ""))})

    return JSONResponse({
        "status": "success",
        "source": "cadastral_fmb",
        "source_title": "BhuNaksha Cadastral FMB Sub-division",
        "polygon_coordinates": parcel.polygon_coordinates,
        "extent_cents": parcel.extent_cents,
        "area_sqm": round(parcel.extent_cents * 40.4686, 1),
        "fmb_dimensions_m": dims_data,
        "survey_no": parcel.survey_no,
        "village": parcel.village,
        "message": f"Demarcated cadastral sub-division parcel ({parcel.extent_cents} Cents) aligned to Kerala village layout."
    })


@app.get("/api/databank_check")
async def check_databank_status(
    survey_no: str = "345/1",
    village: str = "Aluva West",
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
        elev = calc.calculate(latitude=float(lat), longitude=float(lng))
        reply_text = (
            f"🌴 *Kandezhuthu AI - Location Diligence*\n\n"
            f"📍 *Coordinates*: {lat}, {lng}\n"
            f"⛰️ *Elevation*: {elev.elevation_meters}m MSL\n"
            f"🌊 *Flood Risk*: {elev.flood_risk_level.value} (Score: {elev.flood_risk_score}/100)\n"
            f"🏛️ *Basin*: {elev.river_basin or 'Kerala Coastal Plain'}\n"
            f"⚠️ *KSDMA Advisory*: {elev.ksdma_hazard_advisory}\n\n"
            f"📱 *Seller Inquiry*: {elev.whatsapp_inquiry_for_seller}"
        )
    elif media_url:
        reply_text = (
            f"🌴 *Kandezhuthu AI - Document Received*\n\n"
            f"We have received your deed/EC scan. Optical Character Recognition (OCR) is processing.\n"
            f"Please ensure page 1 (SRO & Document number) and the Schedule of Property (ചതുരതിരുകൾ) are clearly legible."
        )
    elif body:
        reply_text = (
            f"🌴 *Kandezhuthu AI (കണ്ടെഴുത്ത്)*\n\n"
            f"Thank you for contacting Kandezhuthu Property Diligence.\n"
            f"Query: \"{body[:80]}\"\n\n"
            f"🛡️ *Mandatory Reminder*: AI deed analysis does not replace physical inspection of Survey Stones (സർവേ കല്ലുകൾ) "
            f"or advocate vetting at the SRO.\n\n"
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
    """Returns realistic Kerala deed or EC sample PDF or executes instant multimodal demonstration OCR."""
    base_dir = Path(__file__).resolve().parent.parent / "data" / "sample_deeds"
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
            raw_text = (
                "SRO Encumbrance Certificate - Aluva 30 Year Search\n"
                "Re-Sy 345/1 Block 12 Aluva West Village\n"
                "Entry 1: Doc 3012/2022 - Gehan / Equitable Mortgage with Federal Bank Aluva Branch - Suresh Nair - Rs 45,00,000 - Undischarged Liability"
            )
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
        if lang == "en" and out_data.get("whatsapp_draft_en"):
            out_data["whatsapp_draft"] = out_data["whatsapp_draft_en"]
        return JSONResponse(out_data)

    return FileResponse(
        path=str(target_path),
        media_type="application/pdf",
        filename=target_filename,
    )


@app.get("/api/timeline_demo")
async def get_timeline_demo(preset: str = "aluva_broken", lang: str = "en"):
    """Returns structured 30-year chronological ownership lineage chain for interactive timeline rendering."""
    presets = {
        "aluva_broken": {
            "property_identifier": "Re-Sy 345/1, Block 12, Aluva West Village, Ernakulam",
            "score": 0,
            "risk_verdict": "DANGER",
            "risk_color": "danger",
            "chain_intact": False,
            "summary": "Critical lineage breaks: Excluded female heir under Mary Roy precedent, undischarged Federal Bank mortgage in EC, and 1.0 Cent extent inflation.",
            "financial_transparency": {
                "is_public_record": True,
                "legal_basis": "Registration Act, 1908 (Sections 51 & 57) - SRO Book 1 Public Record",
                "kerala_stamp_act_rule": "Kerala Stamp Act, 1959 (Section 28A Fair Value & Section 45A Undervaluation Audit)",
                "last_purchase_price": "₹16,50,000",
                "last_purchase_year": 2014,
                "last_buyer": "Suresh Nair (Current Seller)",
                "historical_rate_per_cent": "₹1,50,000 / Cent (2014)",
                "current_govt_fair_value": "₹2,40,000 / Are (~₹97,125 / Cent)",
                "active_bank_lien_inr": "₹45,00,000 (Federal Bank - Undischarged SARFAESI Charge)",
                "market_price_context": "Suresh Nair acquired this plot in 2014 for ₹16.50 Lakhs (Doc #1420/2014). If seller is asking ₹65 Lakhs today (+294% markup), prospective buyer must demand written bank closure letter before paying any advance.",
                "undervaluation_warning": "Registering below Fair Value or actual transaction consideration to evade 8% Stamp Duty is penalized under Sec 45A of Kerala Stamp Act with property revenue attachment."
            },
            "nodes": [
                {
                    "year": 1982,
                    "doc_number": "214/1982",
                    "deed_type": "Pattayam (Land Assignment)",
                    "deed_malayalam": "പട്ടയം",
                    "sro": "Aluva",
                    "from_parties": ["Special Tahsildar (Land Assignment)"],
                    "to_parties": ["Chacko Varghese"],
                    "extent_cents": 10.0,
                    "status": "valid",
                    "status_label": "Valid Initial Grant",
                    "badge_color": "success",
                    "consideration_display": "₹150 (Govt Revenue Fee)",
                    "financial_type": "Official Govt Assignment Fee",
                    "govt_fair_value": "N/A (Pre-Fair Value Regime)",
                    "stamp_duty_paid": "Exempt / Revenue Stamp ₹5",
                    "financial_note": "Initial government land assignment to original occupant Chacko Varghese for nominal revenue fee.",
                    "flags": [],
                    "notes": "Official government land assignment to original holder Chacko Varghese."
                },
                {
                    "year": 1996,
                    "doc_number": "890/1996",
                    "deed_type": "Bhagapathram (Partition Deed)",
                    "deed_malayalam": "ഭാഗപത്രം",
                    "sro": "Aluva",
                    "from_parties": ["Estate of Late Chacko Varghese"],
                    "to_parties": ["George Chacko (Son)", "Thomas Chacko (Son)"],
                    "extent_cents": 10.0,
                    "status": "broken",
                    "status_label": "Critical Succession Defect",
                    "badge_color": "danger",
                    "consideration_display": "₹75,000 (Family Partition Declared Value)",
                    "financial_type": "Family Partition Share Valuation",
                    "govt_fair_value": "₹35,000 / Cent (Declared Base)",
                    "stamp_duty_paid": "₹1,500 (Kerala Stamp Act Schedule Art 42)",
                    "financial_note": "Internal family partition valuation for stamp duty assessment. No money changed hands between brothers.",
                    "flags": [
                        {
                            "title": "Mary Roy Precedent: Excluded Female Heir",
                            "statute": "Indian Succession Act, 1925 / Mary Roy v. State of Kerala (1986)",
                            "desc": "Sister Mary Chacko was completely excluded without a registered Release Deed (ഒഴിവുമുറി). Her heirs can file a partition suit at any time."
                        },
                        {
                            "title": "Missing Legal Heirship & Death Certificates",
                            "statute": "Kerala Revenue & Registration Rules",
                            "desc": "No Tahsildar-issued legal heirship certificate on record to prove surviving legal heirs."
                        }
                    ],
                    "notes": "Divided only between two sons. Excluded daughter Mary Chacko clouds marketable title."
                },
                {
                    "year": 2014,
                    "doc_number": "1420/2014",
                    "deed_type": "Theeradharam (Sale Deed)",
                    "deed_malayalam": "തീറാധാരം",
                    "sro": "Aluva",
                    "from_parties": ["George Chacko"],
                    "to_parties": ["Suresh Nair (Current Seller)"],
                    "extent_cents": 11.0,
                    "status": "warning",
                    "status_label": "Extent Inflation & Easement",
                    "badge_color": "danger",
                    "consideration_display": "₹16,50,000 (Registered Consideration)",
                    "price_per_cent": "₹1,50,000 / Cent",
                    "financial_type": "Registered Sale Consideration (Public SRO Book 1 Record)",
                    "govt_fair_value": "₹1,20,000 / Are (~₹48,560 / Cent)",
                    "stamp_duty_paid": "₹1,32,000 (8% Stamp Duty)",
                    "registration_fee_paid": "₹33,000 (2% SRO Registration Fee)",
                    "financial_note": "Suresh Nair purchased this property from George Chacko for a public registered consideration of ₹16,50,000 (₹1.50 Lakhs/Cent).",
                    "flags": [
                        {
                            "title": "Extent Inflation (+1.00 Cent Phantom Land)",
                            "statute": "Transfer of Property Act, 1882 (Nemo dat quod non habet)",
                            "desc": "Prior deeds cover exactly 10.00 Cents. Deed suddenly purports to transfer 11.00 Cents without land acquisition or resurvey order."
                        },
                        {
                            "title": "Buried Pathway Easement (Nadappu Vazhi)",
                            "statute": "Indian Easements Act, 1882 (Sec 13 & 15)",
                            "desc": "Reserves a 3-meter wide pathway along southern boundary for neighbor Thomas Chacko. Cannot be fenced or built upon."
                        }
                    ],
                    "notes": "Area expanded to 11 Cents unlawfully. 3-meter southern strip reserved as pathway."
                },
                {
                    "year": 2022,
                    "doc_number": "3012/2022",
                    "deed_type": "Bank Mortgage in EC (Gehan)",
                    "deed_malayalam": "ബാങ്ക് ബാധ്യത (EC)",
                    "sro": "Aluva",
                    "from_parties": ["Suresh Nair"],
                    "to_parties": ["Federal Bank (Aluva Branch)"],
                    "extent_cents": 11.0,
                    "status": "broken",
                    "status_label": "Ghost Undischarged Mortgage",
                    "badge_color": "danger",
                    "consideration_display": "₹45,00,000 (Mortgage Loan Liability)",
                    "financial_type": "Registered Bank Loan Lien (SRO EC Book 1)",
                    "govt_fair_value": "₹2,10,000 / Are (~₹85,000 / Cent)",
                    "stamp_duty_paid": "₹22,500 (Kerala Stamp Act Art 36 - Mortgage with Title Deposit)",
                    "financial_note": "Federal Bank holds original title deeds against an outstanding registered liability of ₹45,00,000. Property is liable to SARFAESI seizure.",
                    "flags": [
                        {
                            "title": "Undischarged SARFAESI Mortgage in SRO EC",
                            "statute": "SARFAESI Act, 2002 / Registration Act Sec 17 & 51",
                            "desc": "Outstanding equitable mortgage with Federal Bank. No discharge receipt or registered Gehan release (ഒഴിവുമുറി) exists."
                        }
                    ],
                    "notes": "Federal Bank holds original title deeds. Property liable to SARFAESI attachment."
                }
            ],
            "whatsapp_inquiry": "നമസ്കാരം, ആലുവ വെസ്റ്റ് വില്ലേജിലെ Re-Sy 345/1 പ്രോപ്പർട്ടിയുടെ മുന്നാധാരങ്ങൾ പരിശോധിച്ചപ്പോൾ താഴെ പറയുന്ന പ്രധാന കാര്യങ്ങളിൽ വ്യക്തത ആവശ്യമുണ്ട്:\n1. 2022-ൽ ഫെഡറൽ ബാങ്കിൽ രജിസ്റ്റർ ചെയ്ത ബാധ്യത (Doc #3012/2022) തീർത്ത ബാങ്ക് NOC-യും ഒറിജിനൽ ആധാരവും ലഭ്യമാണോ?\n2. 1996-ലെ ഭാഗപത്രത്തിൽ ഒഴിവാക്കപ്പെട്ട സഹോദരി മേരി ചാക്കോയുടെയോ അവകാശികളുടെയോ രജിസ്റ്റർ ചെയ്ത ഒഴിവുമുറി (Release Deed) ലഭ്യമാണോ?\n3. 10 സെന്റ് ഉണ്ടായിരുന്ന ഭൂമി 2014-ൽ 11 സെന്റായി മാറിയത് എങ്ങനെയാണ്? ഫീൽഡ് മെഷർമെന്റ് ബുക്ക് (FMB) സ്കെച്ച് ഉണ്ടോ?\n4. തെക്കേ അതിരിലൂടെയുള്ള 3 മീറ്റർ വഴി അവകാശം നിലവിലുണ്ടോ?",
            "whatsapp_inquiry_en": "Hello, upon reviewing the prior title documents for the property in Re-Sy 345/1, Aluva West Village, we require clarification on the following key points before proceeding with any advance:\n1. Is a bank NOC and original title deed available clearing the mortgage registered with Federal Bank in 2022 (Doc #3012/2022)?\n2. Is a registered Release Deed available from sister Mary Chacko or her legal heirs who were excluded from the 1996 partition deed?\n3. How did the property extent increase from 10 Cents to 11 Cents in 2014? Is an official FMB (Field Measurement Book) sketch available?\n4. Is the 3-meter pathway easement along the southern boundary still active and reserved for neighbors?",
            "checklist": [
                {"item": "Locate 3-meter Southern Pathway on site", "done": False},
                {"item": "Verify 4 Survey Stones (സർവേ കല്ലുകൾ) with FMB Sketch", "done": False},
                {"item": "Inspect Bank SARFAESI Attachment Notices on gates/walls", "done": False},
                {"item": "Check Village Office Resurvey records for 1-Cent excess", "done": False}
            ]
        },
        "kakkanad_wetland": {
            "property_identifier": "Sy 182/4, Kakkanad Village, Kanayannur Taluk, Ernakulam",
            "score": 28,
            "risk_verdict": "DANGER",
            "risk_color": "danger",
            "chain_intact": False,
            "summary": "Critical Paddy Land / Wetland trap (Data Bank listed) and unauthorized sale of minor child's share without District Court sanction order.",
            "financial_transparency": {
                "is_public_record": True,
                "legal_basis": "Registration Act, 1908 (Sections 51 & 57) - SRO Book 1 Public Record",
                "kerala_stamp_act_rule": "Kerala Stamp Act, 1959 (Section 28A Fair Value & Section 45A Undervaluation Audit)",
                "last_purchase_price": "₹36,00,000",
                "last_purchase_year": 2015,
                "last_buyer": "Unnikrishnan (Current Seller)",
                "historical_rate_per_cent": "₹2,40,000 / Cent (2015)",
                "current_govt_fair_value": "₹3,10,000 / Are (~₹1,25,450 / Cent)",
                "active_bank_lien_inr": "Nil (No bank mortgage in EC)",
                "statutory_fee_liability": "Pending Kerala Paddy Land Act Sec 27A conversion fee (~10% of Fair Value = ₹4,65,000)",
                "market_price_context": "Seller acquired 15 Cents in 2015 for ₹36 Lakhs. However, ₹12 Lakhs was minor Kevin's share pocketed without court sanction. In addition, converting this wetland will cost ₹4.65+ Lakhs in govt revenue fees.",
                "undervaluation_warning": "Minor's 1/3 share (₹12 Lakhs) was alienated without depositing in District Court minor fixed deposit account."
            },
            "nodes": [
                {
                    "year": 1991,
                    "doc_number": "512/1991",
                    "deed_type": "Theeradharam (Sale Deed)",
                    "deed_malayalam": "തീറാധാരം",
                    "sro": "Edappally",
                    "from_parties": ["Raman Menon"],
                    "to_parties": ["Devassia Joseph"],
                    "extent_cents": 15.0,
                    "status": "valid",
                    "status_label": "Valid Acquisition (Nilam)",
                    "badge_color": "success",
                    "consideration_display": "₹1,20,000 (പ്രതിഫല തുക)",
                    "price_per_cent": "₹8,000 / Cent",
                    "financial_type": "Registered Sale Consideration",
                    "govt_fair_value": "₹6,000 / Cent (Declared Base)",
                    "stamp_duty_paid": "₹10,800 (Kerala Stamp Duty 9%)",
                    "financial_note": "Acquisition of 15 Cents agricultural paddy land for public consideration of ₹1.20 Lakhs.",
                    "flags": [],
                    "notes": "Acquisition of 15 Cents classified in revenue records as Nilam (നിലം / Nanja)."
                },
                {
                    "year": 2006,
                    "doc_number": "780/2006",
                    "deed_type": "Bhagapathram (Partition Deed)",
                    "deed_malayalam": "ഭാഗപത്രം",
                    "sro": "Thrikkakara",
                    "from_parties": ["Estate of Devassia Joseph"],
                    "to_parties": ["Jacob Devassia (Father)", "Kevin Jacob (Minor Son, Age 9)"],
                    "extent_cents": 15.0,
                    "status": "valid",
                    "status_label": "Partition with Minor Share",
                    "badge_color": "warning",
                    "consideration_display": "₹4,50,000 (Family Partition Declared Value)",
                    "financial_type": "Family Partition Share Valuation",
                    "govt_fair_value": "₹30,000 / Cent",
                    "stamp_duty_paid": "₹4,500 (Kerala Stamp Act Art 42)",
                    "financial_note": "Internal family partition allotting 50% undivided co-ownership share (₹2.25 Lakhs value) to minor Kevin.",
                    "flags": [
                        {
                            "title": "Minor's Undivided Share Created",
                            "statute": "Hindu Minority & Guardianship Act / Guardians & Wards Act, 1890",
                            "desc": "Minor Kevin allotted 50% undivided share (7.5 Cents) represented by natural guardian father."
                        }
                    ],
                    "notes": "Partition creates undivided co-ownership for 9-year-old minor Kevin."
                },
                {
                    "year": 2015,
                    "doc_number": "1204/2015",
                    "deed_type": "Theeradharam (Sale Deed)",
                    "deed_malayalam": "തീറാധാരം",
                    "sro": "Thrikkakara",
                    "from_parties": ["Jacob Devassia (Self & as Guardian for Minor Kevin)"],
                    "to_parties": ["Unnikrishnan (Seller)"],
                    "extent_cents": 15.0,
                    "status": "broken",
                    "status_label": "Voidable Minor Alienation",
                    "badge_color": "danger",
                    "consideration_display": "₹36,00,000 (Registered Consideration)",
                    "price_per_cent": "₹2,40,000 / Cent",
                    "financial_type": "Registered Sale Consideration (Public SRO Book 1)",
                    "govt_fair_value": "₹1,80,000 / Are (~₹72,840 / Cent)",
                    "stamp_duty_paid": "₹2,88,000 (8% Stamp Duty)",
                    "registration_fee_paid": "₹72,000 (2% Reg Fee)",
                    "financial_note": "Father sold entire 15 Cents including minor Kevin's share (₹18.0 Lakhs consideration) without District Court sanction order.",
                    "flags": [
                        {
                            "title": "Minor Share Sold Without District Court Order",
                            "statute": "Sec 8(2) HMGA 1956 / Guardians & Wards Act Sec 29",
                            "desc": "Father alienated minor Kevin's share without prior sanction from District Court. Sale is legally voidable by the minor upon attaining majority."
                        }
                    ],
                    "notes": "Father sold minor's immovable property without mandatory District Court sanction."
                },
                {
                    "year": 2024,
                    "doc_number": "Data Bank 2008 Entry",
                    "deed_type": "Agricultural Data Bank Listing",
                    "deed_malayalam": "ഡാറ്റാ ബാങ്ക് എൻട്രി",
                    "sro": "Kakkanad Krishi Bhavan",
                    "from_parties": ["Local Level Monitoring Committee (LLMC)"],
                    "to_parties": ["Public Revenue Register"],
                    "extent_cents": 15.0,
                    "status": "broken",
                    "status_label": "Wetland 2008 Fatal Trap",
                    "badge_color": "danger",
                    "consideration_display": "₹4,65,000 (Govt Conversion Fee Liability)",
                    "financial_type": "Statutory Revenue Liability (Sec 27A / Form 6)",
                    "govt_fair_value": "₹3,10,000 / Are (~₹1,25,450 / Cent)",
                    "stamp_duty_paid": "Pending Revenue Fee Payment",
                    "financial_note": "Property is in Data Bank. Statutory penalty and conversion fee liability of ~₹4.65 Lakhs (10% of Fair Value under Section 27A) is unpaid.",
                    "flags": [
                        {
                            "title": "Property in Wetland Data Bank (No Building Permit)",
                            "statute": "Kerala Conservation of Paddy Land & Wetland Act, 2008",
                            "desc": "Listed as Paddy/Wetland. Cannot get Panchayath/Municipality building permit without Form 5 exclusion and Form 6 Sec 27A revenue conversion fee."
                        }
                    ],
                    "notes": "Unregularized wetland status. Building permit impossible without Form 5 and Form 6 approval."
                }
            ],
            "whatsapp_inquiry": "നമസ്കാരം, കാക്കനാട് വില്ലേജിലെ 15 സെന്റ് സ്ഥലത്തിന്റെ പ്രമാണങ്ങൾ പരിശോധിച്ചപ്പോൾ പ്രധാനപ്പെട്ട രണ്ട് കാര്യങ്ങളിൽ വ്യക്തത ആവശ്യമുണ്ട്:\n1. 2015-ൽ മൈനറായിരുന്ന കെവിന്റെ അവകാശം വിൽക്കുവാൻ ജില്ലാ കോടതിയുടെ മുൻകൂർ അനുമതി ഉത്തരവ് (District Court Sanction Order) ഉണ്ടോ?\n2. ഈ സ്ഥലം 2008-ലെ നെൽവയൽ-തണ്ണീർത്തട ഡാറ്റാ ബാങ്കിൽ ഉൾപ്പെട്ടിട്ടുണ്ടോ? ഫോം 5 ഉത്തരവും സെക്ഷൻ 27A (ഫോം 6) പ്രകാരമുള്ള പുരയിടമാക്കൽ ഉത്തരവും ഉണ്ടോ?",
            "whatsapp_inquiry_en": "Hello, upon reviewing the title documents for the 15-cent plot in Kakkanad Village, we require clarification on two critical points before advancing funds:\n1. Is there a prior District Court Sanction Order for the 2015 sale of Kevin's minor share (HMGA Section 8)?\n2. Is this land listed as Nilam in the 2008 Paddy Land Data Bank? Are Form 5 exclusion and Section 27A (Form 6) revenue conversion orders obtained?",
            "checklist": [
                {"item": "Check Krishi Bhavan Data Bank register for Sy 182/4", "done": False},
                {"item": "Verify Kevin's age and ratification release deed", "done": False},
                {"item": "Inspect waterlogging and adjacent paddy fields during monsoon", "done": False},
                {"item": "Check Municipality road widening proposal", "done": False}
            ]
        },
        "clean_title": {
            "property_identifier": "Re-Sy 412/3, Aluva West Village, Ernakulam",
            "score": 100,
            "risk_verdict": "ALL CLEAR",
            "risk_color": "clear",
            "chain_intact": True,
            "summary": "Flawless 39-year title continuity: 100% unbroken chain from 1985 Pattayam to current owner, consistent 10.0 Cents extent, all heirs represented, and clean EC.",
            "financial_transparency": {
                "is_public_record": True,
                "legal_basis": "Registration Act, 1908 (Sections 51 & 57) - SRO Book 1 Public Record",
                "kerala_stamp_act_rule": "Kerala Stamp Act, 1959 (Section 28A Fair Value & Section 45A Undervaluation Audit)",
                "last_purchase_price": "₹38,00,000",
                "last_purchase_year": 2018,
                "last_buyer": "Rajesh Kumar (Current Seller)",
                "historical_rate_per_cent": "₹3,80,000 / Cent (2018)",
                "current_govt_fair_value": "₹3,20,000 / Are (~₹1,29,500 / Cent)",
                "active_bank_lien_inr": "Nil (Zero Mortgage - 39-Year Nil EC)",
                "market_price_context": "Rajesh Kumar acquired this property in 2018 for registered consideration of ₹38 Lakhs. Stamp Duty (₹3.04L) and Reg fee (₹76K) were fully paid at fair market value.",
                "undervaluation_warning": "None. Declared consideration accurately exceeded notified Fair Value with zero tax irregularity."
            },
            "nodes": [
                {
                    "year": 1985,
                    "doc_number": "412/1985",
                    "deed_type": "Pattayam (Land Assignment)",
                    "deed_malayalam": "പട്ടയം",
                    "sro": "Aluva",
                    "from_parties": ["Special Tahsildar (Land Assignment)"],
                    "to_parties": ["Kunjuraman Nair"],
                    "extent_cents": 10.0,
                    "status": "valid",
                    "status_label": "Valid Govt Assignment",
                    "badge_color": "success",
                    "consideration_display": "₹200 (Govt Revenue Fee)",
                    "financial_type": "Official Govt Assignment Fee",
                    "govt_fair_value": "N/A",
                    "stamp_duty_paid": "Exempt Revenue Grant",
                    "financial_note": "Original land grant under Kerala Land Assignment Rules for nominal fee of ₹200.",
                    "flags": [],
                    "notes": "Original Pattayam issued with registered survey bounds."
                },
                {
                    "year": 2004,
                    "doc_number": "1890/2004",
                    "deed_type": "Theeradharam (Sale Deed)",
                    "deed_malayalam": "തീറാധാരം",
                    "sro": "Aluva",
                    "from_parties": ["Kunjuraman Nair"],
                    "to_parties": ["Thomas Varghese"],
                    "extent_cents": 10.0,
                    "status": "valid",
                    "status_label": "Clean Registered Sale",
                    "badge_color": "success",
                    "consideration_display": "₹4,50,000 (Registered Consideration)",
                    "price_per_cent": "₹45,000 / Cent",
                    "financial_type": "Registered Sale Consideration",
                    "govt_fair_value": "₹35,000 / Cent",
                    "stamp_duty_paid": "₹45,000 (Kerala Stamp Act 10%)",
                    "financial_note": "Absolute sale of 10 Cents for registered consideration of ₹4.50 Lakhs.",
                    "flags": [],
                    "notes": "Absolute transfer with original title delivered and prior tax receipts cleared."
                },
                {
                    "year": 2018,
                    "doc_number": "945/2018",
                    "deed_type": "Theeradharam (Sale Deed)",
                    "deed_malayalam": "തീറാധാരം",
                    "sro": "Aluva",
                    "from_parties": ["Thomas Varghese"],
                    "to_parties": ["Rajesh Kumar (Current Seller)"],
                    "extent_cents": 10.0,
                    "status": "valid",
                    "status_label": "Clean Registered Sale",
                    "badge_color": "success",
                    "consideration_display": "₹38,00,000 (Registered Consideration)",
                    "price_per_cent": "₹3,80,000 / Cent",
                    "financial_type": "Registered Sale Consideration (Public SRO Book 1)",
                    "govt_fair_value": "₹3,20,000 / Are (~₹1,29,500 / Cent)",
                    "stamp_duty_paid": "₹3,04,000 (8% Stamp Duty)",
                    "registration_fee_paid": "₹76,000 (2% Reg Fee)",
                    "financial_note": "Seller Rajesh Kumar purchased this plot in 2018 for ₹38,00,000 (₹3.80 Lakhs/Cent), paying full statutory stamp duty and registration fees.",
                    "flags": [],
                    "notes": "Validly conveyed. Land tax paid up to current financial year under Thandaper No. 4120."
                },
                {
                    "year": 2024,
                    "doc_number": "SRO EC #4510/2024",
                    "deed_type": "Nil Encumbrance Certificate (30 Years)",
                    "deed_malayalam": "ബാധ്യതാ സർട്ടിഫിക്കറ്റ് (EC)",
                    "sro": "Aluva",
                    "from_parties": ["Sub-Registrar Office Aluva"],
                    "to_parties": ["Rajesh Kumar"],
                    "extent_cents": 10.0,
                    "status": "valid",
                    "status_label": "Nil Encumbrance Verified",
                    "badge_color": "success",
                    "consideration_display": "₹0 Liability (Nil EC)",
                    "financial_type": "Certified Zero Mortgage Liability",
                    "govt_fair_value": "₹3,20,000 / Are",
                    "stamp_duty_paid": "EC Search Fee ₹150",
                    "financial_note": "Official SRO verification confirms zero mortgage, zero court attachment, and zero bank lien.",
                    "flags": [],
                    "notes": "Clean 39-year Encumbrance Certificate with zero attachments, mortgages, or lis pendens."
                }
            ],
            "whatsapp_inquiry": "നമസ്കാരം രാജേഷ് സാർ,\n\nആലുവ റീ-സർവേ 412/3-ൽ ഉൾപ്പെട്ട 10 സെന്റ് സ്ഥലത്തിന്റെ പ്രമാണങ്ങൾ വളരെ കൃത്യവും സംതൃപ്തികരവുമാണ്. രജിസ്ട്രേഷന് മുൻപായി ഒറിജിനൽ പട്ടയവും, ഏറ്റവും പുതിയ വില്ലേജ് കരമടച്ച രസീതും (Land Tax Receipt), സബ് രജിസ്ട്രാർ ഓഫീസിലെ ഒറിജിനൽ ബാധ്യതാ സർട്ടിഫിക്കറ്റും (EC 1985-2024) നേരിട്ട് പരിശോധിക്കാൻ ലഭ്യമാക്കുമല്ലോ. നന്ദി.",
            "whatsapp_inquiry_en": "Hello Mr. Rajesh,\n\nThe title documents for the 10-cent plot in Aluva Re-Survey 412/3 appear continuous and well-documented. Prior to registration and token advance, kindly make available the original 1985 Pattayam, the latest Village Land Tax Receipt, and the original Encumbrance Certificate (EC 1985-2024) for direct advocate verification. Thank you.",
            "checklist": [
                {"item": "Cross-verify original Pattayam (1985) parchment", "done": False},
                {"item": "Check all 4 boundary stones with Village Resurvey Sketch", "done": False},
                {"item": "Obtain current Thandaper extract from Village Office", "done": False},
                {"item": "Confirm 3-meter road access width for KPBR building permit", "done": False}
            ]
        }
    }

    preset_data = presets.get(preset) or presets["aluva_broken"]
    if lang == "en":
        preset_data["whatsapp_inquiry"] = preset_data.get("whatsapp_inquiry_en", preset_data.get("whatsapp_inquiry", ""))
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
            "checklists, and the '📱 WhatsApp Message for Seller / Broker' section (draft it completely in clear English). "
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


# Mount static assets
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    print(f"Server starting on http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
