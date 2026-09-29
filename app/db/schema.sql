-- Schema definition for Kandezhuthu AI (SQLite)
-- Includes:
-- 1. Kerala Administrative / SRO master tables
-- 2. Building Rules (KPBR / KMBR 2019) dimensional tables
-- 3. Paddy Land 2008 Section 27A fee slabs
-- 4. Landmark Kerala Judicial Precedents & FTS5 full-text search
-- 5. Properties, Deed Nodes, EC Records, and Audit Scorecards

PRAGMA foreign_keys = ON;

-- 1. Administrative Master Tables
CREATE TABLE IF NOT EXISTS administrative_divisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    district TEXT NOT NULL,
    taluk TEXT NOT NULL,
    village TEXT NOT NULL,
    sro_name TEXT NOT NULL,
    sro_code TEXT
);

CREATE INDEX IF NOT EXISTS idx_admin_village ON administrative_divisions(village);
CREATE INDEX IF NOT EXISTS idx_admin_sro ON administrative_divisions(sro_name);

-- 2. Kerala Building Rules (KPBR / KMBR 2019)
CREATE TABLE IF NOT EXISTS building_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    occupancy_group TEXT NOT NULL,          -- e.g. "Group A1: Residential"
    plot_category TEXT NOT NULL,            -- "standard", "small_plot" (<=3 cents), "commercial"
    min_plot_cents REAL DEFAULT 0.0,
    max_plot_cents REAL DEFAULT 9999.0,
    max_builtup_sqm REAL,                   -- 150 for small plots, 300 for single family
    min_road_width_m REAL NOT NULL,         -- 1.2, 1.5, 3.0, 5.0, 7.0
    front_setback_m REAL NOT NULL,          -- 1.8, 3.0
    rear_setback_m REAL NOT NULL,           -- 1.0, 1.5
    side_setback_1_m REAL NOT NULL,         -- 0.9, 1.2
    side_setback_2_m REAL NOT NULL,         -- 0.6, 1.0
    well_septic_clearance_m REAL DEFAULT 7.5, -- Minimum distance between septic tank/leach pit and open well
    dead_wall_permitted INTEGER DEFAULT 0,  -- 1 if 0-setback blind wall allowed with NOC
    rule_citation TEXT NOT NULL,            -- e.g. "KPBR 2019 Rule 5 & Rule 62"
    notes TEXT
);

-- 3. Paddy Land & Wetland (Section 27A Fee Slabs)
CREATE TABLE IF NOT EXISTS paddy_land_fee_slabs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    min_cents REAL NOT NULL,
    max_cents REAL NOT NULL,
    fee_percentage_of_fair_value REAL NOT NULL, -- 0.0 for <=25 cents, 10.0 for 25-50, etc.
    description TEXT NOT NULL,
    statutory_citation TEXT NOT NULL
);

-- 4. Landmark Kerala Judicial Precedents
CREATE TABLE IF NOT EXISTS legal_precedents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_name TEXT NOT NULL,
    citation TEXT NOT NULL,
    court TEXT NOT NULL,
    year INTEGER NOT NULL,
    category TEXT NOT NULL,                 -- succession, senior_citizens, easements, minor_property, poa, etc.
    key_principle TEXT NOT NULL,
    risk_trigger TEXT NOT NULL,             -- What to look for in deeds
    remedial_action TEXT NOT NULL,          -- Recommended cure / advocate advice
    statute_reference TEXT NOT NULL
);

-- FTS5 Full-Text Search Virtual Table for Legal Precedents
CREATE VIRTUAL TABLE IF NOT EXISTS legal_precedents_fts USING fts5(
    case_name,
    category,
    key_principle,
    risk_trigger,
    remedial_action,
    statute_reference,
    content='legal_precedents',
    content_rowid='id'
);

-- FTS5 Virtual Table for Full Knowledge Corpus Articles
CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_corpus_fts USING fts5(
    topic,
    title,
    content,
    tags
);

-- 5. Property Audit Transactions
CREATE TABLE IF NOT EXISTS properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_identifier TEXT UNIQUE NOT NULL, -- e.g. "Re-Sy 345/1, Aluva West Village, Ernakulam"
    survey_no TEXT NOT NULL,
    resurvey_no TEXT,
    village TEXT,
    taluk TEXT,
    district TEXT,
    sro_name TEXT,
    extent_cents REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_properties_survey ON properties(survey_no);
CREATE INDEX IF NOT EXISTS idx_properties_resurvey ON properties(resurvey_no);

CREATE TABLE IF NOT EXISTS deed_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER,
    doc_number TEXT NOT NULL,               -- e.g. "1420/2014"
    year INTEGER NOT NULL,
    sro_name TEXT NOT NULL,
    deed_type TEXT NOT NULL,
    grantors_json TEXT NOT NULL,            -- JSON array of grantors
    grantees_json TEXT NOT NULL,            -- JSON array of grantees
    extent_cents REAL NOT NULL,
    survey_no TEXT NOT NULL,
    resurvey_no TEXT,
    consideration_inr REAL DEFAULT 0.0,
    prior_doc_referenced TEXT,
    is_minor_involved INTEGER DEFAULT 0,
    minor_court_sanction_present INTEGER DEFAULT 0,
    unrepresented_heirs_json TEXT,          -- JSON array of heirs
    easements_reserved_json TEXT,           -- JSON array of easements
    family_religion TEXT DEFAULT 'hindu',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(property_id) REFERENCES properties(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_deeds_doc ON deed_records(doc_number, sro_name, year);

CREATE TABLE IF NOT EXISTS encumbrance_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER,
    doc_number TEXT NOT NULL,
    year INTEGER NOT NULL,
    sro_name TEXT NOT NULL,
    nature TEXT NOT NULL,                   -- Sale, Mortgage, Attachment, Release
    parties_json TEXT,                      -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(property_id) REFERENCES properties(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS audit_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER,
    session_id TEXT,
    overall_score INTEGER NOT NULL,
    risk_level TEXT NOT NULL,               -- ALL CLEAR, CAUTION, DANGER
    chain_of_custody_intact INTEGER NOT NULL,
    lineage_path_json TEXT,                 -- JSON array of deed doc_numbers
    advocate_recommendations_json TEXT,    -- JSON array
    whatsapp_malayalam_draft TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(property_id) REFERENCES properties(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS risk_flags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_report_id INTEGER NOT NULL,
    category TEXT NOT NULL,
    severity TEXT NOT NULL,                 -- LOW, MEDIUM, HIGH, CRITICAL
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    legal_citation TEXT NOT NULL,
    remedial_action TEXT NOT NULL,
    FOREIGN KEY(audit_report_id) REFERENCES audit_reports(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS single_deed_scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    deed_snippet TEXT NOT NULL,
    sanity_score INTEGER NOT NULL,
    verdict TEXT NOT NULL,
    findings_json TEXT NOT NULL,            -- JSON array of findings
    whatsapp_inquiry_malayalam TEXT,
    unverified_physical_aspects_json TEXT,  -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Benchmark Land Fair Values (Notified under Section 28A of Kerala Stamp Act)
CREATE TABLE IF NOT EXISTS fair_value_benchmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    district TEXT NOT NULL,
    taluk TEXT NOT NULL,
    village TEXT NOT NULL,
    local_body_type TEXT NOT NULL,          -- Corporation, Municipality, Grama Panchayat
    land_type TEXT NOT NULL,                -- Residential with road, Residential interior, Commercial, etc.
    fair_value_per_are_inr REAL NOT NULL,
    effective_year INTEGER DEFAULT 2023,
    gazette_notification TEXT NOT NULL      -- S.R.O. No. 420/2023 (20% revised)
);

CREATE INDEX IF NOT EXISTS idx_fair_value_village ON fair_value_benchmarks(village);
CREATE INDEX IF NOT EXISTS idx_fair_value_district ON fair_value_benchmarks(district);

-- 7. Digital Resurvey ("Ente Bhoomi") Status by Village
CREATE TABLE IF NOT EXISTS digital_resurvey_villages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    district TEXT NOT NULL,
    taluk TEXT NOT NULL,
    village TEXT NOT NULL,
    phase TEXT NOT NULL,                   -- Phase 1 (Completed/Draft d-BTR), Phase 2 (Active Drone/CORS)
    status TEXT NOT NULL,                  -- "d-BTR Published", "Draft FMB Published", "Drone Survey Ongoing"
    portal_url TEXT DEFAULT 'https://entebhoomi.kerala.gov.in',
    advisory TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_digital_survey_village ON digital_resurvey_villages(village);

