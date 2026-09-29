"""Repository layer for Kandezhuthu database queries.

Provides structured access to:
- Knowledge lookups (KPBR/KMBR building rules, Paddy land conversion fee calculations, FTS precedents)
- Audit transaction persistence and historical prior deed/EC searches
"""

import json
from typing import Any

from app.db.database import get_db_connection


class KnowledgeRepository:
    """Provides fast deterministic queries and full-text searches over Kerala land law."""

    def get_building_rule(self, plot_cents: float, occupancy_type: str = "residential") -> dict[str, Any] | None:
        """Finds matching Kerala Building Rule (KPBR/KMBR 2019) dimensional standards for a plot extent."""
        with get_db_connection() as conn:
            # Check for ultra-small plot concession first if <= 2.0 cents (<= 81 sqm)
            if plot_cents <= 2.0:
                cursor.execute(
                    "SELECT * FROM building_rules WHERE plot_category = 'ultra_small_plot' LIMIT 1"
                )
            # Check for small plot concession if <= 3.09 cents
            elif plot_cents <= 3.09:
                cursor.execute(
                    "SELECT * FROM building_rules WHERE plot_category = 'small_plot' LIMIT 1"
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM building_rules
                    WHERE min_plot_cents <= ? AND max_plot_cents >= ?
                    ORDER BY min_plot_cents ASC LIMIT 1
                    """,
                    (plot_cents, plot_cents),
                )
            row = cursor.fetchone()
            if row:
                return dict(row)
            # Default fallback to standard residential
            cursor.execute("SELECT * FROM building_rules WHERE plot_category = 'standard' LIMIT 1")
            row = cursor.fetchone()
            return dict(row) if row else None

    def calculate_paddy_conversion_fee(self, plot_cents: float, fair_value_per_are: float) -> dict[str, Any]:
        """Calculates exact statutory fee under Section 27A of Paddy Land Act 2008.

        Conversion: 1 Cent = 0.404686 Ares.
        """
        area_ares = plot_cents * 0.404686
        total_fair_value = area_ares * fair_value_per_are

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM paddy_land_fee_slabs
                WHERE min_cents <= ? AND max_cents >= ?
                LIMIT 1
                """,
                (plot_cents, plot_cents),
            )
            row = cursor.fetchone()
            if not row:
                percentage = 30.0
                desc = "Exceeds 100 cents (Standard maximum slab)"
                citation = "Section 27A(3) Schedule"
            else:
                percentage = row["fee_percentage_of_fair_value"]
                desc = row["description"]
                citation = row["statutory_citation"]

            statutory_fee = (percentage / 100.0) * total_fair_value

            return {
                "extent_cents": plot_cents,
                "extent_ares": round(area_ares, 4),
                "fair_value_per_are_inr": fair_value_per_are,
                "total_property_fair_value_inr": round(total_fair_value, 2),
                "applicable_fee_percentage": percentage,
                "statutory_conversion_fee_inr": round(statutory_fee, 2),
                "is_fee_exempt": (percentage == 0.0),
                "description": desc,
                "statutory_citation": citation,
                "supreme_court_ruling_warning": (
                    "Under Supreme Court of India precedent (State of Kerala v. Landowner, 2025), "
                    "there is NO pro-rata deduction. If total holding exceeds 25 cents, fee is levied on the entire plot extent, not just the excess."
                ),
                "anti_fragmentation_rule": (
                    "Exemption applies only to plots that did not exceed 25 cents as of 30 December 2017 (G.O.(P) No. 1166/2020/Rev). "
                    "Plots fragmented from larger holdings after 30-12-2017 are ineligible for 0% fee."
                ),
                "competent_authority": (
                    "Processed by Taluk-level Deputy Collectors across 71 taluks under Kerala Act 12 of 2024 (previously RDOs only)."
                ),
            }

    def search_precedents(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Full-text search across landmark Kerala judicial precedents."""
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Try FTS5 search first
            sanitized_query = "".join(c for c in query if c.isalnum() or c.isspace()).strip()
            fts_results = []
            if sanitized_query:
                try:
                    cursor.execute(
                        """
                        SELECT lp.*
                        FROM legal_precedents_fts fts
                        JOIN legal_precedents lp ON fts.rowid = lp.id
                        WHERE legal_precedents_fts MATCH ?
                        LIMIT ?
                        """,
                        (sanitized_query, limit),
                    )
                    fts_results = [dict(r) for r in cursor.fetchall()]
                except Exception:
                    fts_results = []

            if fts_results:
                return fts_results

            # Fallback to LIKE keyword search across categories and principles
            like_term = f"%{query}%"
            cursor.execute(
                """
                SELECT * FROM legal_precedents
                WHERE case_name LIKE ? OR category LIKE ? OR key_principle LIKE ? OR statute_reference LIKE ?
                LIMIT ?
                """,
                (like_term, like_term, like_term, like_term, limit),
            )
            return [dict(r) for r in cursor.fetchall()]

    def search_knowledge_corpus(self, query: str, limit: int = 2) -> list[dict[str, Any]]:
        """FTS search across statutory markdown articles."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            sanitized = "".join(c for c in query if c.isalnum() or c.isspace()).strip()
            if not sanitized:
                return []
            try:
                cursor.execute(
                    """
                    SELECT topic, title, snippet(knowledge_corpus_fts, 2, '<b>', '</b>', '...', 25) AS snippet, content
                    FROM knowledge_corpus_fts
                    WHERE knowledge_corpus_fts MATCH ?
                    LIMIT ?
                    """,
                    (sanitized, limit),
                )
                return [dict(r) for r in cursor.fetchall()]
            except Exception:
                return []

    def search_sro(self, query: str) -> list[dict[str, Any]]:
        """Searches administrative master data for SRO and village mappings."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            q = f"%{query}%"
            cursor.execute(
                """
                SELECT * FROM administrative_divisions
                WHERE village LIKE ? OR taluk LIKE ? OR district LIKE ? OR sro_name LIKE ?
                LIMIT 10
                """,
                (q, q, q, q),
            )
            return [dict(r) for r in cursor.fetchall()]

    def get_fair_value_benchmark(self, village: str, district: str | None = None) -> list[dict[str, Any]]:
        """Returns official notified Fair Value benchmarks per Are under Section 28A for a village."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            v_term = f"%{village.strip()}%"
            if district:
                d_term = f"%{district.strip()}%"
                cursor.execute(
                    """
                    SELECT * FROM fair_value_benchmarks
                    WHERE village LIKE ? AND district LIKE ?
                    ORDER BY fair_value_per_are_inr DESC
                    """,
                    (v_term, d_term),
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM fair_value_benchmarks
                    WHERE village LIKE ?
                    ORDER BY fair_value_per_are_inr DESC
                    """,
                    (v_term,),
                )
            rows = cursor.fetchall()
            if rows:
                return [dict(r) for r in rows]

            # Fallback: check taluk or district wide average
            cursor.execute(
                """
                SELECT * FROM fair_value_benchmarks
                WHERE district LIKE ? OR taluk LIKE ?
                ORDER BY fair_value_per_are_inr DESC
                LIMIT 3
                """,
                (v_term, v_term),
            )
            return [dict(r) for r in cursor.fetchall()]

    def check_digital_resurvey_status(self, village: str, district: str | None = None) -> dict[str, Any] | None:
        """Checks whether a village is notified under Kerala's Digital Resurvey ('Ente Bhoomi') program."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            v_term = f"%{village.strip()}%"
            if district:
                d_term = f"%{district.strip()}%"
                cursor.execute(
                    """
                    SELECT * FROM digital_resurvey_villages
                    WHERE village LIKE ? AND district LIKE ?
                    LIMIT 1
                    """,
                    (v_term, d_term),
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM digital_resurvey_villages
                    WHERE village LIKE ?
                    LIMIT 1
                    """,
                    (v_term,),
                )
            row = cursor.fetchone()
            return dict(row) if row else None


class AuditRepository:
    """Manages persistence and lookup of property title audits and single deed scans."""

    def save_audit(
        self,
        property_identifier: str,
        survey_no: str,
        deeds: list[dict[str, Any]],
        ec_records: list[dict[str, Any]],
        scorecard: dict[str, Any],
        session_id: str | None = None,
        village: str | None = None,
        taluk: str | None = None,
        district: str | None = None,
        sro_name: str | None = None,
    ) -> int:
        """Saves a complete title audit (property, deeds, EC records, report, risk flags)."""
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 1. Insert or get Property
            cursor.execute(
                "SELECT id FROM properties WHERE property_identifier = ?",
                (property_identifier,),
            )
            prop_row = cursor.fetchone()
            if prop_row:
                property_id = prop_row["id"]
            else:
                extent_cents = deeds[-1].get("extent_cents", 0.0) if deeds else 0.0
                cursor.execute(
                    """
                    INSERT INTO properties (property_identifier, survey_no, village, taluk, district, sro_name, extent_cents)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (property_identifier, survey_no, village, taluk, district, sro_name, extent_cents),
                )
                property_id = cursor.lastrowid

            # 2. Insert Deeds
            for d in deeds:
                cursor.execute(
                    """
                    INSERT INTO deed_records (
                        property_id, doc_number, year, sro_name, deed_type,
                        grantors_json, grantees_json, extent_cents, survey_no,
                        resurvey_no, consideration_inr, prior_doc_referenced,
                        is_minor_involved, minor_court_sanction_present,
                        unrepresented_heirs_json, easements_reserved_json, family_religion
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        property_id,
                        d.get("doc_number", ""),
                        d.get("year", 0),
                        d.get("sro_name", ""),
                        str(d.get("deed_type", "")),
                        json.dumps(d.get("grantors", [])),
                        json.dumps(d.get("grantees", [])),
                        d.get("extent_cents", 0.0),
                        d.get("survey_no", survey_no),
                        d.get("resurvey_no"),
                        d.get("consideration_inr", 0.0),
                        d.get("prior_doc_referenced"),
                        1 if d.get("is_minor_involved") else 0,
                        1 if d.get("minor_court_sanction_present") else 0,
                        json.dumps(d.get("unrepresented_heirs", [])),
                        json.dumps(d.get("easements_reserved", [])),
                        d.get("family_religion", "hindu"),
                    ),
                )

            # 3. Insert EC Records
            for ec in ec_records:
                cursor.execute(
                    """
                    INSERT INTO encumbrance_records (property_id, doc_number, year, sro_name, nature, parties_json)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        property_id,
                        ec.get("doc_number", ""),
                        ec.get("year", 0),
                        ec.get("sro_name", ""),
                        ec.get("nature", ""),
                        json.dumps(ec.get("parties", [])),
                    ),
                )

            # 4. Insert Audit Report
            cursor.execute(
                """
                INSERT INTO audit_reports (
                    property_id, session_id, overall_score, risk_level,
                    chain_of_custody_intact, lineage_path_json, advocate_recommendations_json,
                    whatsapp_malayalam_draft
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    property_id,
                    session_id,
                    scorecard.get("overall_score", 0),
                    scorecard.get("risk_level", "UNKNOWN"),
                    1 if scorecard.get("chain_of_custody_intact") else 0,
                    json.dumps(scorecard.get("lineage_path", [])),
                    json.dumps(scorecard.get("recommendations_for_advocate", [])),
                    scorecard.get("whatsapp_malayalam_draft", ""),
                ),
            )
            report_id = cursor.lastrowid

            # 5. Insert Risk Flags
            for rf in scorecard.get("risk_flags", []):
                cursor.execute(
                    """
                    INSERT INTO risk_flags (
                        audit_report_id, category, severity, title, description, legal_citation, remedial_action
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        report_id,
                        rf.get("category", ""),
                        rf.get("severity", ""),
                        rf.get("title", ""),
                        rf.get("description", ""),
                        rf.get("legal_citation", ""),
                        rf.get("remedial_action", ""),
                    ),
                )

            return report_id

    def get_property_audit_history(self, survey_no: str, village: str | None = None) -> list[dict[str, Any]]:
        """Retrieves prior audit reports and flags for a given survey number to detect recurring risks."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if village:
                cursor.execute(
                    """
                    SELECT p.property_identifier, p.survey_no, p.village, ar.id AS report_id,
                           ar.overall_score, ar.risk_level, ar.chain_of_custody_intact,
                           ar.created_at, ar.lineage_path_json, ar.advocate_recommendations_json
                    FROM properties p
                    JOIN audit_reports ar ON p.id = ar.property_id
                    WHERE p.survey_no = ? AND p.village = ?
                    ORDER BY ar.created_at DESC
                    """,
                    (survey_no, village),
                )
            else:
                cursor.execute(
                    """
                    SELECT p.property_identifier, p.survey_no, p.village, ar.id AS report_id,
                           ar.overall_score, ar.risk_level, ar.chain_of_custody_intact,
                           ar.created_at, ar.lineage_path_json, ar.advocate_recommendations_json
                    FROM properties p
                    JOIN audit_reports ar ON p.id = ar.property_id
                    WHERE p.survey_no = ?
                    ORDER BY ar.created_at DESC
                    """,
                    (survey_no,),
                )

            reports = []
            for row in cursor.fetchall():
                r = dict(row)
                report_id = r["report_id"]
                cursor.execute("SELECT * FROM risk_flags WHERE audit_report_id = ?", (report_id,))
                r["risk_flags"] = [dict(flag) for flag in cursor.fetchall()]
                r["lineage_path"] = json.loads(r.get("lineage_path_json") or "[]")
                r["advocate_recommendations"] = json.loads(r.get("advocate_recommendations_json") or "[]")
                reports.append(r)
            return reports

    def save_single_deed_scan(self, snippet: str, result_dict: dict[str, Any], session_id: str | None = None) -> int:
        """Persists a single-deed sanity scan."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO single_deed_scans (
                    session_id, deed_snippet, sanity_score, verdict,
                    findings_json, whatsapp_inquiry_malayalam, unverified_physical_aspects_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    snippet[:2000],  # truncate if extremely large
                    result_dict.get("sanity_score", 0),
                    result_dict.get("verdict", ""),
                    json.dumps(result_dict.get("findings", [])),
                    result_dict.get("whatsapp_inquiry_malayalam", ""),
                    json.dumps(result_dict.get("unverified_physical_aspects", [])),
                ),
            )
            return cursor.lastrowid
