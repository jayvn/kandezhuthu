"""Data API for Kandezhuthu AI.

Organizes Kerala land law knowledge, administrative divisions, and property audit records.
Maintains:
1. Structured local copies under `data/organized/` with cryptographic manifest.
2. Cloud Storage copies in Google Cloud Storage (`gs://<bucket>/kandezhuthu-data/`).
3. Native Firestore document collections for real-time cloud data querying.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from app import fixtures
from app.db.database import get_db_connection, init_db
from app.db.seed_data import seed_all

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
ORGANIZED_DIR = DATA_DIR / "organized"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"
SAMPLE_DEEDS_DIR = DATA_DIR / "sample_deeds"


def _compute_sha256(file_path: Path) -> str:
    """Computes SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class DataAPI:
    """Unified Data API for Kandezhuthu data organization, query, and cloud sync."""

    def __init__(self, organized_dir: Path | None = None) -> None:
        self.organized_dir = organized_dir or ORGANIZED_DIR
        self.manifest_path = self.organized_dir / "manifest.json"

    def get_gcp_project_id(self) -> str:
        """Resolves GCP project ID from environment or gcloud config."""
        if project := os.environ.get("GOOGLE_CLOUD_PROJECT"):
            return project
        try:
            import subprocess

            out = subprocess.check_output(
                ["gcloud", "config", "get-value", "project"], text=True
            ).strip()
            if out and "error" not in out.lower():
                return out
        except Exception:
            pass
        return "qwiklabs-gcp-03-690fd21cfd7e"

    def get_gcs_bucket_name(self) -> str:
        """Resolves Google Cloud Storage bucket name."""
        if bucket := os.environ.get("GCS_BUCKET_NAME") or os.environ.get("LOGS_BUCKET_NAME"):
            return bucket.replace("gs://", "").strip("/")
        project = self.get_gcp_project_id()
        candidate = f"bwg3-{project}"
        # Verify via client or fallback
        try:
            from google.cloud import storage

            client = storage.Client(project=project)
            for b in client.list_buckets():
                if b.name.startswith("bwg3-") or project in b.name:
                    return b.name
        except Exception:
            pass
        return candidate

    # -------------------------------------------------------------------------
    # 1. LOCAL DATA EXTRACTION & ORGANIZATION
    # -------------------------------------------------------------------------

    def extract_database_records(self) -> dict[str, list[dict[str, Any]]]:
        """Extracts and normalizes all structured records from SQLite."""
        seed_all()  # Ensure database is seeded with latest master data
        datasets: dict[str, list[dict[str, Any]]] = {}

        tables = [
            "building_rules",
            "paddy_land_fee_slabs",
            "legal_precedents",
            "administrative_divisions",
            "properties",
            "deed_records",
            "encumbrance_records",
            "audit_reports",
            "risk_flags",
            "single_deed_scans",
        ]

        with get_db_connection() as conn:
            cursor = conn.cursor()
            for tbl in tables:
                try:
                    cursor.execute(f"SELECT * FROM {tbl}")
                    rows = [dict(r) for r in cursor.fetchall()]
                    # Parse JSON-encoded text fields for clean object trees
                    for row in rows:
                        for k, v in list(row.items()):
                            if isinstance(v, str) and (
                                k.endswith("_json") or (v.startswith(("[", "{")) and v.endswith(("]", "}")))
                            ):
                                try:
                                    row[k] = json.loads(v)
                                except Exception:
                                    pass
                    datasets[tbl] = rows
                except Exception as e:
                    print(f"Warning: could not extract table {tbl}: {e}")
                    datasets[tbl] = []

        return datasets

    def extract_knowledge_corpus(self) -> list[dict[str, Any]]:
        """Extracts and indexes markdown knowledge articles."""
        articles = []
        if not KNOWLEDGE_DIR.exists():
            return articles

        for md_file in sorted(KNOWLEDGE_DIR.glob("*.md")):
            content = md_file.read_text(encoding="utf-8")
            topic = md_file.stem
            lines = content.strip().splitlines()
            title = lines[0].lstrip("# ").strip() if lines else topic
            articles.append(
                {
                    "topic": topic,
                    "filename": md_file.name,
                    "title": title,
                    "size_bytes": len(content.encode("utf-8")),
                    "word_count": len(content.split()),
                    "content": content,
                }
            )
        return articles

    def extract_sample_documents(self) -> list[dict[str, Any]]:
        """Extracts and indexes sample deeds and encumbrance certificates."""
        documents = []
        if not SAMPLE_DEEDS_DIR.exists():
            return documents

        for doc in sorted(SAMPLE_DEEDS_DIR.glob("*.*")):
            if doc.name.startswith("."):
                continue
            documents.append(
                {
                    "filename": doc.name,
                    "format": doc.suffix.lstrip(".").lower(),
                    "size_bytes": doc.stat().st_size,
                    "sha256": _compute_sha256(doc),
                    "relative_path": f"sample_deeds/{doc.name}",
                }
            )
        return documents

    def organize_local(self) -> dict[str, Any]:
        """Organizes all data and writes clean structured local copies to data/organized/."""
        # Create directory hierarchy
        knowledge_dir = self.organized_dir / "knowledge"
        knowledge_md_dir = knowledge_dir / "markdown"
        admin_dir = self.organized_dir / "administrative"
        audits_dir = self.organized_dir / "audits"
        documents_dir = self.organized_dir / "documents"
        docs_samples_dir = documents_dir / "sample_deeds"

        for d in [knowledge_md_dir, admin_dir, audits_dir, docs_samples_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # 1. Extract data
        db_records = self.extract_database_records()
        knowledge_articles = self.extract_knowledge_corpus()
        sample_documents = self.extract_sample_documents()

        manifest_collections: dict[str, dict[str, Any]] = {}

        # 2. Save Knowledge Data
        knowledge_files = {
            "building_rules": db_records.get("building_rules", []),
            "paddy_land_fee_slabs": db_records.get("paddy_land_fee_slabs", []),
            "legal_precedents": db_records.get("legal_precedents", []),
            "knowledge_corpus": knowledge_articles,
        }
        for name, data in knowledge_files.items():
            file_path = knowledge_dir / f"{name}.json"
            file_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            manifest_collections[name] = {
                "category": "knowledge",
                "file": str(file_path.relative_to(self.organized_dir)),
                "records_count": len(data),
                "size_bytes": file_path.stat().st_size,
                "sha256": _compute_sha256(file_path),
            }

        # Copy raw markdown guides
        if KNOWLEDGE_DIR.exists():
            for md_file in KNOWLEDGE_DIR.glob("*.md"):
                shutil.copy2(md_file, knowledge_md_dir / md_file.name)

        # 3. Save Administrative Data
        admin_data = db_records.get("administrative_divisions", [])
        admin_file = admin_dir / "administrative_divisions.json"
        admin_file.write_text(json.dumps(admin_data, indent=2, ensure_ascii=False), encoding="utf-8")
        manifest_collections["administrative_divisions"] = {
            "category": "administrative",
            "file": str(admin_file.relative_to(self.organized_dir)),
            "records_count": len(admin_data),
            "size_bytes": admin_file.stat().st_size,
            "sha256": _compute_sha256(admin_file),
        }

        # 4. Save Audit Data
        audit_files = {
            "properties": db_records.get("properties", []),
            "deed_records": db_records.get("deed_records", []),
            "encumbrance_records": db_records.get("encumbrance_records", []),
            "audit_reports": db_records.get("audit_reports", []),
            "risk_flags": db_records.get("risk_flags", []),
            "single_deed_scans": db_records.get("single_deed_scans", []),
        }
        for name, data in audit_files.items():
            file_path = audits_dir / f"{name}.json"
            file_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            manifest_collections[name] = {
                "category": "audits",
                "file": str(file_path.relative_to(self.organized_dir)),
                "records_count": len(data),
                "size_bytes": file_path.stat().st_size,
                "sha256": _compute_sha256(file_path),
            }

        # 5. Save Documents metadata and copy samples
        docs_file = documents_dir / "documents_index.json"
        docs_file.write_text(json.dumps(sample_documents, indent=2, ensure_ascii=False), encoding="utf-8")
        manifest_collections["sample_documents"] = {
            "category": "documents",
            "file": str(docs_file.relative_to(self.organized_dir)),
            "records_count": len(sample_documents),
            "size_bytes": docs_file.stat().st_size,
            "sha256": _compute_sha256(docs_file),
        }

        if SAMPLE_DEEDS_DIR.exists():
            for doc in SAMPLE_DEEDS_DIR.glob("*.*"):
                if not doc.name.startswith("."):
                    shutil.copy2(doc, docs_samples_dir / doc.name)

        # 6. Build Manifest
        total_records = sum(c["records_count"] for c in manifest_collections.values())
        now_iso = datetime.now(timezone.utc).isoformat()

        manifest = {
            "manifest_version": "1.0.0",
            "project_name": "kandezhuthu",
            "title": "Kandezhuthu AI Legal Title Data Catalog",
            "generated_at": now_iso,
            "local_directory": str(self.organized_dir),
            "total_collections": len(manifest_collections),
            "total_records": total_records,
            "collections": manifest_collections,
            "cloud_sync": {
                "gcs": {"synced": False, "bucket": None, "last_synced_at": None},
                "firestore": {"synced": False, "database": "(default)", "last_synced_at": None},
            },
        }

        # Preserve previous cloud sync metadata if it existed
        if self.manifest_path.exists():
            try:
                old_manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
                if "cloud_sync" in old_manifest:
                    manifest["cloud_sync"] = old_manifest["cloud_sync"]
            except Exception:
                pass

        self.manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

        return {
            "status": "success",
            "message": f"Successfully organized {total_records} records across {len(manifest_collections)} collections locally.",
            "organized_dir": str(self.organized_dir),
            "manifest_path": str(self.manifest_path),
            "total_collections": len(manifest_collections),
            "total_records": total_records,
            "collections": list(manifest_collections.keys()),
        }

    # -------------------------------------------------------------------------
    # 2. GOOGLE CLOUD STORAGE (GCS) SYNC
    # -------------------------------------------------------------------------

    def sync_to_gcs(self, bucket_name: str | None = None) -> dict[str, Any]:
        """Synchronizes local organized data to Google Cloud Storage bucket."""
        from google.cloud import storage

        if not self.manifest_path.exists():
            self.organize_local()

        project_id = self.get_gcp_project_id()
        target_bucket = bucket_name or self.get_gcs_bucket_name()

        client = storage.Client(project=project_id)
        bucket = client.bucket(target_bucket)

        prefix = "kandezhuthu-data"
        uploaded_files: list[str] = []

        # Recursively upload all organized files
        for root, _, files in os.walk(self.organized_dir):
            for f in files:
                local_file = Path(root) / f
                rel_path = local_file.relative_to(self.organized_dir)
                gcs_blob_name = f"{prefix}/{rel_path}"

                blob = bucket.blob(gcs_blob_name)
                # Set content type
                content_type = "application/json"
                if f.endswith(".md"):
                    content_type = "text/markdown; charset=utf-8"
                elif f.endswith(".pdf"):
                    content_type = "application/pdf"
                elif f.endswith(".parquet"):
                    content_type = "application/vnd.apache.parquet"
                elif f.endswith(".jsonl"):
                    content_type = "application/x-ndjson"
                elif f.endswith(".geojson"):
                    content_type = "application/geo+json"

                blob.upload_from_filename(str(local_file), content_type=content_type)
                uploaded_files.append(f"gs://{target_bucket}/{gcs_blob_name}")

        now_iso = datetime.now(timezone.utc).isoformat()

        # Update local manifest with GCS sync info
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        manifest["cloud_sync"]["gcs"] = {
            "synced": True,
            "bucket": target_bucket,
            "gcs_uri_prefix": f"gs://{target_bucket}/{prefix}/",
            "uploaded_files_count": len(uploaded_files),
            "last_synced_at": now_iso,
        }
        self.manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        # Also upload the updated manifest itself to GCS root of prefix
        manifest_blob = bucket.blob(f"{prefix}/manifest.json")
        manifest_blob.upload_from_filename(str(self.manifest_path), content_type="application/json")

        return {
            "status": "success",
            "cloud_tool": "Google Cloud Storage",
            "bucket": target_bucket,
            "gcs_prefix": f"gs://{target_bucket}/{prefix}/",
            "uploaded_files_count": len(uploaded_files),
            "synced_at": now_iso,
            "files": uploaded_files,
        }

    # -------------------------------------------------------------------------
    # 3. GOOGLE CLOUD FIRESTORE SYNC
    # -------------------------------------------------------------------------

    def sync_to_firestore(self, project_id: str | None = None) -> dict[str, Any]:
        """Synchronizes structured collections into Google Cloud Firestore."""
        from google.cloud import firestore

        if not self.manifest_path.exists():
            self.organize_local()

        project = project_id or self.get_gcp_project_id()
        db = firestore.Client(project=project)

        synced_collections: dict[str, int] = {}
        now_iso = datetime.now(timezone.utc).isoformat()

        # Define mapping of local JSON files to Firestore collection names
        collections_to_sync = [
            ("knowledge/building_rules.json", "kandezhuthu_building_rules", "rule_id"),
            ("knowledge/paddy_land_fee_slabs.json", "kandezhuthu_paddy_fee_slabs", "slab_id"),
            ("knowledge/legal_precedents.json", "kandezhuthu_legal_precedents", "precedent_id"),
            ("administrative/administrative_divisions.json", "kandezhuthu_administrative_divisions", "div_id"),
            ("audits/properties.json", "kandezhuthu_properties", "prop_id"),
            ("audits/deed_records.json", "kandezhuthu_deed_records", "deed_id"),
            ("audits/encumbrance_records.json", "kandezhuthu_encumbrance_records", "ec_id"),
            ("audits/audit_reports.json", "kandezhuthu_audit_reports", "report_id"),
            ("audits/risk_flags.json", "kandezhuthu_risk_flags", "flag_id"),
            ("audits/single_deed_scans.json", "kandezhuthu_single_deed_scans", "scan_id"),
        ]

        batch = db.batch()
        batch_count = 0
        total_docs = 0

        for rel_file, collection_name, id_prefix in collections_to_sync:
            file_path = self.organized_dir / rel_file
            if not file_path.exists():
                continue

            records: list[dict[str, Any]] = json.loads(file_path.read_text(encoding="utf-8"))
            count = 0

            for idx, item in enumerate(records):
                # Clean row id
                doc_id = str(item.get("id") or f"{id_prefix}_{idx + 1}")
                doc_ref = db.collection(collection_name).document(doc_id)

                # Add sync timestamp and metadata
                doc_data = dict(item)
                doc_data["_synced_at"] = now_iso
                doc_data["_source"] = "kandezhuthu_data_api"

                batch.set(doc_ref, doc_data)
                batch_count += 1
                count += 1
                total_docs += 1

                # Firestore batch limit is 500 operations
                if batch_count >= 400:
                    batch.commit()
                    batch = db.batch()
                    batch_count = 0

            synced_collections[collection_name] = count

        if batch_count > 0:
            batch.commit()

        # Record top-level sync metadata in Firestore
        db.collection("kandezhuthu_sync_metadata").document("latest_sync").set(
            {
                "last_synced_at": now_iso,
                "project": project,
                "database": "(default)",
                "total_documents": total_docs,
                "collections": synced_collections,
                "client": "Kandezhuthu DataAPI 1.0",
            }
        )

        # Update local manifest
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        manifest["cloud_sync"]["firestore"] = {
            "synced": True,
            "database": "(default)",
            "project": project,
            "total_documents": total_docs,
            "collections": synced_collections,
            "last_synced_at": now_iso,
        }
        self.manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        return {
            "status": "success",
            "cloud_tool": "Google Cloud Firestore",
            "project": project,
            "database": "(default)",
            "total_documents_synced": total_docs,
            "collections_synced": synced_collections,
            "synced_at": now_iso,
        }

    # -------------------------------------------------------------------------
    # 4. UNIFIED ALL-IN-ONE ORGANIZER & SYNC
    # -------------------------------------------------------------------------

    def organize_and_sync_all(self) -> dict[str, Any]:
        """Organizes data locally and synchronizes to both Cloud Storage & Firestore."""
        local_result = self.organize_local()
        gcs_result = self.sync_to_gcs()
        firestore_result = self.sync_to_firestore()

        return {
            "status": "success",
            "local_copy": local_result,
            "google_cloud_storage": gcs_result,
            "google_cloud_firestore": firestore_result,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # -------------------------------------------------------------------------
    # 5. STATUS & QUERY API
    # -------------------------------------------------------------------------

    def get_status(self) -> dict[str, Any]:
        """Returns comprehensive status of local copy, GCS, and Firestore."""
        if not self.manifest_path.exists():
            return {
                "organized": False,
                "message": "Data has not been organized yet. Run organize_local() or POST /api/data/organize.",
            }

        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        return {
            "organized": True,
            "manifest_version": manifest.get("manifest_version"),
            "generated_at": manifest.get("generated_at"),
            "local_directory": str(self.organized_dir),
            "total_collections": manifest.get("total_collections"),
            "total_records": manifest.get("total_records"),
            "collections": manifest.get("collections", {}),
            "cloud_sync": manifest.get("cloud_sync", {}),
        }

    def query_collection(
        self, collection_name: str, limit: int = 50, filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Queries an organized collection from local JSON storage."""
        if not self.manifest_path.exists():
            self.organize_local()

        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        collections = manifest.get("collections", {})

        if collection_name not in collections:
            raise ValueError(
                f"Collection '{collection_name}' not found. Available collections: {list(collections.keys())}"
            )

        file_path = self.organized_dir / collections[collection_name]["file"]
        if not file_path.exists():
            return []

        records: list[dict[str, Any]] = json.loads(file_path.read_text(encoding="utf-8"))

        if filters:
            filtered = []
            for r in records:
                match = True
                for k, v in filters.items():
                    if str(r.get(k, "")).lower() != str(v).lower():
                        match = False
                        break
                if match:
                    filtered.append(r)
            return filtered[:limit]

        return records[:limit]

    # -------------------------------------------------------------------------
    # 6. SCALABLE FORMATS ENGINE (Parquet, JSONL, GeoJSON, RAG Chunks)
    # -------------------------------------------------------------------------

    def export_scalable_formats(self) -> dict[str, Any]:
        """Exports all structured and semi-structured collections into high-performance scalable formats:
        1. Apache Parquet (.parquet): Columnar storage with Snappy compression for BigQuery/DuckDB/Polars.
        2. JSON Lines (.jsonl): Line-delimited streaming format for LLM batch prediction & BigQuery streams.
        3. RAG Chunked JSONL: Semantic chunked markdown guides for Vertex AI RAG / Vector Search.
        4. GeoJSON (.geojson): Standard geospatial features for cadastral parcels & FMB boundaries.
        5. Storage & Scalability Benchmark: Comparative metrics across formats.
        """
        import pyarrow as pa
        import pyarrow.parquet as pq

        if not self.manifest_path.exists():
            self.organize_local()

        scalable_dir = self.organized_dir / "scalable"
        parquet_dir = scalable_dir / "parquet"
        jsonl_dir = scalable_dir / "jsonl"
        rag_dir = scalable_dir / "rag"
        geojson_dir = scalable_dir / "geojson"

        for d in [parquet_dir, jsonl_dir, rag_dir, geojson_dir]:
            d.mkdir(parents=True, exist_ok=True)

        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        collections = manifest.get("collections", {})

        benchmark_entries = []
        scalable_files = {}

        # 1. Export Tabular Collections to Parquet and JSONL
        for name, meta in collections.items():
            if meta.get("category") == "documents" or name == "knowledge_corpus":
                continue

            src_file = self.organized_dir / meta["file"]
            if not src_file.exists():
                continue

            records: list[dict[str, Any]] = json.loads(src_file.read_text(encoding="utf-8"))
            if not records:
                continue

            # --- JSON Lines (.jsonl) ---
            jsonl_file = jsonl_dir / f"{name}.jsonl"
            with open(jsonl_file, "w", encoding="utf-8") as jf:
                for r in records:
                    jf.write(json.dumps(r, ensure_ascii=False) + "\n")

            jsonl_size = jsonl_file.stat().st_size
            jsonl_sha = _compute_sha256(jsonl_file)

            # --- Apache Parquet (.parquet) ---
            normalized = []
            for r in records:
                clean_row = {}
                for k, v in r.items():
                    if isinstance(v, (dict, list)):
                        clean_row[k] = json.dumps(v, ensure_ascii=False)
                    else:
                        clean_row[k] = v
                normalized.append(clean_row)

            table = pa.Table.from_pylist(normalized)
            parquet_file = parquet_dir / f"{name}.parquet"
            pq.write_table(table, parquet_file, compression="snappy")

            parquet_size = parquet_file.stat().st_size
            parquet_sha = _compute_sha256(parquet_file)
            json_size = src_file.stat().st_size

            compression_ratio = round((1.0 - (parquet_size / json_size)) * 100, 2) if json_size > 0 else 0.0

            benchmark_entries.append(
                {
                    "collection": name,
                    "record_count": len(records),
                    "json_size_bytes": json_size,
                    "jsonl_size_bytes": jsonl_size,
                    "parquet_size_bytes": parquet_size,
                    "parquet_savings_percent": compression_ratio,
                }
            )

            scalable_files[f"parquet/{name}"] = {
                "format": "parquet",
                "file": str(parquet_file.relative_to(self.organized_dir)),
                "records": len(records),
                "size_bytes": parquet_size,
                "sha256": parquet_sha,
            }
            scalable_files[f"jsonl/{name}"] = {
                "format": "jsonl",
                "file": str(jsonl_file.relative_to(self.organized_dir)),
                "records": len(records),
                "size_bytes": jsonl_size,
                "sha256": jsonl_sha,
            }

        # 2. Export RAG Chunked JSONL for Vertex AI RAG / Vector Search
        rag_file = rag_dir / "knowledge_rag_chunks.jsonl"
        chunks = []
        if KNOWLEDGE_DIR.exists():
            for md_file in sorted(KNOWLEDGE_DIR.glob("*.md")):
                text = md_file.read_text(encoding="utf-8")
                sections = text.split("\n## ")
                doc_title = sections[0].split("\n")[0].lstrip("# ").strip()
                for i, sec in enumerate(sections[1:], start=1):
                    sec_lines = sec.split("\n")
                    heading = sec_lines[0].strip()
                    body = "\n".join(sec_lines[1:]).strip()
                    if not body:
                        continue
                    chunk_id = f"{md_file.stem}_chunk_{i}"
                    chunks.append(
                        {
                            "chunk_id": chunk_id,
                            "source_document": md_file.name,
                            "document_title": doc_title,
                            "section_heading": heading,
                            "text_content": f"# {doc_title} - {heading}\n\n{body}",
                            "estimated_tokens": len(body.split()) * 4 // 3,
                        }
                    )

        with open(rag_file, "w", encoding="utf-8") as rf:
            for ch in chunks:
                rf.write(json.dumps(ch, ensure_ascii=False) + "\n")

        scalable_files["rag/knowledge_rag_chunks"] = {
            "format": "jsonl-rag",
            "file": str(rag_file.relative_to(self.organized_dir)),
            "records": len(chunks),
            "size_bytes": rag_file.stat().st_size,
            "sha256": _compute_sha256(rag_file),
        }

        # 3. Export GeoJSON for Cadastral Parcels & Map Boundaries
        geojson_file = geojson_dir / "cadastral_parcels.geojson"
        # Parcel geometry is demo data (tests/fixtures/cadastral_parcels.json); empty otherwise.
        geojson_data = {"type": "FeatureCollection", "features": fixtures.load("cadastral_parcels", [])}
        geojson_file.write_text(json.dumps(geojson_data, indent=2, ensure_ascii=False), encoding="utf-8")
        scalable_files["geojson/cadastral_parcels"] = {
            "format": "geojson",
            "file": str(geojson_file.relative_to(self.organized_dir)),
            "records": len(geojson_data["features"]),
            "size_bytes": geojson_file.stat().st_size,
            "sha256": _compute_sha256(geojson_file),
        }

        # 4. Generate Storage & Query Scalability Benchmark Report
        total_json_size = sum(b["json_size_bytes"] for b in benchmark_entries)
        total_parquet_size = sum(b["parquet_size_bytes"] for b in benchmark_entries)
        total_jsonl_size = sum(b["jsonl_size_bytes"] for b in benchmark_entries)
        overall_parquet_savings = (
            round((1.0 - (total_parquet_size / total_json_size)) * 100, 2) if total_json_size > 0 else 0.0
        )

        benchmark_report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_collections_benchmarked": len(benchmark_entries),
                "total_json_bytes": total_json_size,
                "total_jsonl_bytes": total_jsonl_size,
                "total_parquet_bytes": total_parquet_size,
                "overall_parquet_compression_savings_percent": overall_parquet_savings,
            },
            "format_suitability_matrix": {
                "Apache Parquet (.parquet)": {
                    "paradigm": "Columnar, compressed binary",
                    "best_use_case": "High-volume analytical queries, BigQuery external tables, Polars/DuckDB joins",
                    "cloud_tool": "Google Cloud BigQuery & Vertex AI Batch Predictions",
                    "advantages": "Column pruning, predicate pushdown, 60-80% smaller storage footprint, strict schema typing",
                },
                "JSON Lines (.jsonl)": {
                    "paradigm": "Line-delimited streaming text",
                    "best_use_case": "Large batch ingestion, BigQuery streaming inserts, Gemini fine-tuning, RAG document chunks",
                    "cloud_tool": "BigQuery & Vertex AI Search / RAG Engine",
                    "advantages": "Memory-efficient O(1) stream parsing, appendable without rewriting entire array",
                },
                "GeoJSON (.geojson)": {
                    "paradigm": "Standard spatial vectors",
                    "best_use_case": "Cadastral boundary inspection, survey plot rendering, BhuNaksha GIS mapping",
                    "cloud_tool": "BigQuery GIS, Google Maps JavaScript API, Leaflet",
                    "advantages": "Universal standard across all mapping and cadastral libraries",
                },
                "Native Firestore": {
                    "paradigm": "NoSQL document database",
                    "best_use_case": "Real-time client synchronization, point lookups by deed ID/survey number",
                    "cloud_tool": "Google Cloud Firestore Native",
                    "advantages": "Sub-millisecond latency point lookups, ACID transactions, offline persistence",
                },
                "SQLite (WAL Mode)": {
                    "paradigm": "Embedded relational + Full-Text Search (FTS5)",
                    "best_use_case": "Zero-dependency local legal diligence, statutory BM25 search, instant local unit tests",
                    "cloud_tool": "Local runtime / Cloud Run container",
                    "advantages": "Self-contained single file, zero cloud cost, atomic transactions",
                },
            },
            "collections_breakdown": benchmark_entries,
        }

        bench_file = scalable_dir / "format_benchmark.json"
        bench_file.write_text(json.dumps(benchmark_report, indent=2), encoding="utf-8")

        # 5. Update Manifest
        manifest["scalable_formats"] = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "formats": ["parquet", "jsonl", "geojson", "rag-jsonl"],
            "total_files": len(scalable_files) + 1,
            "overall_parquet_savings_percent": overall_parquet_savings,
            "files": scalable_files,
        }
        self.manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        return {
            "status": "success",
            "message": f"Successfully generated scalable formats with {overall_parquet_savings}% Parquet storage savings.",
            "benchmark": benchmark_report["summary"],
            "scalable_dir": str(scalable_dir),
            "files_count": len(scalable_files) + 1,
        }


# -------------------------------------------------------------------------
# CLI ENTRYPOINT
# -------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kandezhuthu Data API CLI")
    parser.add_argument("--local", action="store_true", help="Organize and store local copy")
    parser.add_argument("--scalable", action="store_true", help="Export high-performance scalable formats (Parquet, JSONL, GeoJSON)")
    parser.add_argument("--cloud", action="store_true", help="Sync to Google Cloud tools (GCS + Firestore)")
    parser.add_argument("--all", action="store_true", help="Organize locally, generate scalable formats, and sync to Google Cloud tools")
    parser.add_argument("--status", action="store_true", help="Show data organization and cloud sync status")

    args = parser.parse_args()
    api = DataAPI()

    if args.status:
        print(json.dumps(api.get_status(), indent=2))
    elif args.scalable:
        res = api.export_scalable_formats()
        print(f"✅ Scalable formats export complete: {res['message']}")
        print(f"📊 Parquet savings: {res['benchmark']['overall_parquet_compression_savings_percent']}%")
    elif args.local:
        res = api.organize_local()
        print(f"✅ Local organization complete: {res['message']}")
    elif args.cloud:
        gcs = api.sync_to_gcs()
        print(f"✅ GCS sync complete: {gcs['gcs_prefix']} ({gcs['uploaded_files_count']} files)")
        fs = api.sync_to_firestore()
        print(f"✅ Firestore sync complete: {fs['total_documents_synced']} documents in {len(fs['collections_synced'])} collections")
    else:
        # Default to --all if no args or --all explicitly passed
        res = api.organize_and_sync_all()
        sc = api.export_scalable_formats()
        gcs = api.sync_to_gcs()
        print("🚀 Kandezhuthu Data API: Organization, Scalable Formats & Cloud Sync Complete!")
        print(f"📁 Local copy: {res['local_copy']['message']}")
        print(f"⚡ Scalable formats: {sc['message']}")
        print(f"☁️ Google Cloud Storage: {gcs['gcs_prefix']} ({gcs['uploaded_files_count']} files)")
        print(f"🔥 Google Cloud Firestore: {res['google_cloud_firestore']['total_documents_synced']} documents synced")
        print(f"☁️ Google Cloud Storage: {res['google_cloud_storage']['gcs_prefix']}")
        print(f"🔥 Google Cloud Firestore: {res['google_cloud_firestore']['total_documents_synced']} documents synced")
