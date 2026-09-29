# Kandezhuthu AI (കണ്ടെഴുത്ത് - ആധാരംനോക്കി) 🏛️📜

**Kandezhuthu AI** is a specialized Kerala property legal audit assistant built with the Google Agent Development Kit (ADK) and deployed via `agents-cli`. Its mission is to protect home buyers, Non-Resident Indians (NRIs), and families from paying token advances or earnest money on legally defective land, unauthorized sales, or title traps in Kerala real estate transactions.

---

## 🌟 Core Capabilities

1. **Multimodal Deed OCR & Ingestion (Gemini Vision)**:
   - Scans uploaded Kerala title deed documents (PDF, PNG, JPEG, WEBP) directly with zero external binary dependencies.
   - Extracts Document Number, Year, SRO, Survey / Re-Survey number, Extent in Cents and Ares, Four Boundaries (*ചതുരതിരുകൾ*), and Prior Deeds (*മുന്നാധാരം*).

2. **Single-Deed Red-Flag Audit Engine**:
   - Detects 4 fatal statutory real-estate traps:
     - **Buried Easements / Pathways** (*വഴിയവകാശം / നടപ്പുവഴി*) under the Indian Easements Act, 1882.
     - **2008 Paddy Land / Wetland Risk** (*നിലം* vs *പുരയിടം*) under the Kerala Conservation of Paddy Land & Wetland Act, 2008.
     - **Minor's Share Disposed without District Court Order** under Section 8(2) of the Hindu Minority and Guardianship Act, 1956.
     - **Senior Citizen Maintenance Covenants** under Section 23 of the Maintenance and Welfare of Parents and Senior Citizens Act, 2007.

3. **30-Year Prior Title Lineage Audit (*മുന്നാധാരം*)**:
   - Evaluates multi-decade chains of title deeds (`DeedNode`) for gaps in title continuity, extent inflation (*Nemo dat quod non habet*), and omitted legal heirs across religious succession laws (*Mary Roy v. State of Kerala, 1986*).
   - Cross-references SRO Encumbrance Certificate (EC) entries to uncover undisclosed bank mortgages or attachments.

4. **Paddy Conversion & KPBR Building Rules**:
   - Computes statutory Section 27A government conversion fees across land value slabs.
   - Queries exact Kerala Panchayat Building Rules (KPBR/KMBR 2019) for minimum road access widths and structural setbacks.

5. **Culturally Polite Bilingual Seller Inquiries**:
   - Drafts native Malayalam WhatsApp inquiry messages for buyers to ask sellers or brokers for missing release deeds, NOCs, or survey sketches before paying advance money.

6. **Interactive Satellite Georeferencing UI**:
   - Dual-pane interface with Google Satellite Inspector, interactive polygon plot measuring in Kerala cents, road width measurement, and on-site field verification checklist (*സർവേ കല്ല് / Survey Kallu*, actual road motorability, flooding history).

---

## 🏗️ Architecture

```
kandezhuthu/
├── app/
│   ├── agent.py                 # ADK Root Agent (gemini-3.8-flash) & exposed tools
│   ├── fast_api_app.py          # FastAPI backend server with A2A Protocol (/a2a/kandezhuthu)
│   ├── app_utils/               # A2A routing, sessions, and GCP services
│   ├── domain/
│   │   ├── deed_ocr.py          # Multimodal deed vision extraction using Gemini Flash
│   │   ├── single_deed_scanner.py # Deterministic 4-statutory-trap scanner & Malayalam WhatsApp generator
│   │   ├── auditor.py           # MunnadharamAuditor: multi-decade title chain continuity & EC cross-validation
│   │   └── models.py            # Pydantic schemas (DeedNode, ECRecord, RiskFlag, CleanTitleScorecard)
│   └── db/
│       ├── database.py          # SQLite WAL connection
│       ├── schema.sql           # Relational tables + FTS5 full-text search
│       ├── seed_data.py         # Seeds KPBR rules, Paddy fee slabs, landmark case laws
│       └── repository.py        # KnowledgeRepository & AuditRepository
├── frontend/
│   ├── main.py                  # Full-stack FastAPI server with Web UI and upload endpoints
│   └── static/
│       └── index.html           # Dual-pane UI (Chat, Drag-and-drop OCR, Satellite Map)
├── data/
│   ├── kandezhuthu.db           # Embedded SQLite database (auto-seeded)
│   ├── knowledge/               # Statutory diligence guides (KPBR, court rulings, paddy land act)
│   └── sample_deeds/            # Synthetic Kerala title deed PDFs
├── tests/                       # Unit, integration, and UI tests
└── pyproject.toml               # Project dependencies (uv)
```

---

## 🚀 Quick Start

### 1. Prerequisites
- **Python 3.11+**
- **uv**: [Install uv](https://docs.astral.sh/uv/getting-started/installation/)
- **Google Cloud SDK** or Google Gemini API Key

### 2. Installation
```bash
git clone https://github.com/jayvn/kandezhuthu.git
cd kandezhuthu
uv sync
```

### 3. Environment Configuration
Create a `.env` file in the root directory:
```env
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=<your-gcp-project-id>
GOOGLE_CLOUD_LOCATION=us-central1
# Or for Google AI Studio API:
# GEMINI_API_KEY=your-api-key-here
```

### 4. Running the Web Application
Launch the full-stack web application with the dual-pane UI, drag-and-drop deed uploader, and satellite map:
```bash
uv run python -m frontend.main
```
Open **`http://localhost:8080`** in your browser.

### 5. Running the ADK Agent Playground
To interact with the root agent using the Google ADK development UI:
```bash
agents-cli playground
```

---

## ⚖️ Ethical Non-AI Guardrails

Kandezhuthu strictly enforces boundaries on what artificial intelligence can verify:
- **Title reports are advisory**: AI is an initial triage and red-flag scanner, NOT a guarantee of title or a substitute for a licensed Kerala High Court / District Court advocate's formal title report.
- **Physical ground realities cannot be confirmed on paper**:
  - Verification of physical boundary stones (*Survey Kallu*) and neighbor encroachment.
  - Actual motorability of access roads on the ground.
  - Oral family agreements (*Vaymozhi udanpadi*) or unfiled caveats.
  - Soil stability, waterlogging, or seasonal monsoon flooding.

Always inspect the property on-site and consult a licensed Kerala advocate before advancing money!
