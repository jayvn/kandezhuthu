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
# CLI ENTRYPOINT
# -------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kandezhuthu Data API CLI")
    parser.add_argument("--local", action="store_true", help="Organize and store local copy")
    parser.add_argument("--cloud", action="store_true", help="Sync to Google Cloud tools (GCS + Firestore)")
    parser.add_argument("--all", action="store_true", help="Organize locally and sync to Google Cloud tools")
    parser.add_argument("--status", action="store_true", help="Show data organization and cloud sync status")

    args = parser.parse_args()
    api = DataAPI()

    if args.status:
        print(json.dumps(api.get_status(), indent=2))
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
        print("🚀 Kandezhuthu Data API: Organization & Cloud Sync Complete!")
        print(f"📁 Local copy: {res['local_copy']['message']}")
        print(f"☁️ Google Cloud Storage: {res['google_cloud_storage']['gcs_prefix']}")
        print(f"🔥 Google Cloud Firestore: {res['google_cloud_firestore']['total_documents_synced']} documents synced")
