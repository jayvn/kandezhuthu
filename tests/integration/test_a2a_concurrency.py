"""Concurrency Stress Test for A2A and SQLite WAL Mode.

Simulates 10+ simultaneous user / A2A sessions executing mixed reads and
high-frequency transactional writes on the SQLite database to verify WAL mode
concurrency without table or database locking errors.
"""

import asyncio
import concurrent.futures
import time
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.db.database import get_db_connection, init_db
from app.db.repository import AuditRepository, KnowledgeRepository
from app.fast_api_app import app


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Ensure database schema and initial tables are ready."""
    init_db()


def test_sqlite_wal_mode_enabled():
    """Verify that SQLite database is operating in WAL (Write-Ahead Logging) mode."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode;")
        row = cursor.fetchone()
        journal_mode = row[0].lower() if row else ""
        assert journal_mode == "wal", f"Expected WAL mode, got: {journal_mode}"

        cursor.execute("PRAGMA busy_timeout;")
        busy_timeout = cursor.fetchone()[0]
        assert busy_timeout >= 5000, f"Expected busy_timeout >= 5000ms, got: {busy_timeout}"


def _session_db_worker(session_idx: int) -> dict:
    """Simulates a single user/agent session performing concurrent reads and writes."""
    kr = KnowledgeRepository()
    ar = AuditRepository()
    worker_id = f"session-{session_idx}-{uuid.uuid4().hex[:6]}"

    # 1. Concurrent Read: Building rules
    rule = kr.get_building_rule(plot_cents=4.5)
    assert rule is not None, "Building rule lookup failed"

    # 2. Concurrent Read: Paddy conversion fee calculation
    fee_calc = kr.calculate_paddy_conversion_fee(plot_cents=7.5, fair_value_per_are=150000.0)
    assert "statutory_conversion_fee_inr" in fee_calc

    # 3. Concurrent Read: Judicial precedents
    precedents = kr.search_precedents(query="unregistered agreement")
    assert isinstance(precedents, list)

    # 4. Concurrent Write: Complete Title Audit record
    property_id = f"KL-EKM-ALV-{session_idx}-{int(time.time() * 1000)}"
    audit_id = ar.save_audit(
        property_identifier=property_id,
        survey_no=f"{100 + session_idx}/1A",
        deeds=[
            {
                "doc_number": f"{2000 + session_idx}/1998",
                "year": 1998,
                "sro": "Aluva",
                "deed_type": "THEERU (Sale Deed)",
                "seller": f"Seller {session_idx}",
                "buyer": f"Buyer {session_idx}",
                "extent_cents": 4.5,
                "boundaries": {"north": "Road", "south": "Plot 2", "east": "Plot 3", "west": "Canal"},
                "prior_doc_ref": "1100/1985",
            }
        ],
        ec_records=[
            {
                "doc_number": f"{2000 + session_idx}/1998",
                "year": 1998,
                "nature": "Theeru",
                "parties": f"Seller {session_idx} -> Buyer {session_idx}",
                "status": "MATCHED",
            }
        ],
        scorecard={
            "overall_score": 88,
            "risk_level": "LOW",
            "fatal_flaws_count": 0,
            "advisory_points": ["Verify latest land tax thandapper"],
        },
    )
    assert audit_id > 0, f"Failed to insert audit for {worker_id}"

    # 5. Concurrent Read: Verify newly saved audit
    history = ar.get_property_audit_history(survey_no=f"{100 + session_idx}/1A")
    assert isinstance(history, list)
    assert len(history) > 0
    assert history[0]["property_identifier"] == property_id

    # 6. Concurrent Write: Single Deed Scan record
    scan_id = ar.save_single_deed_scan(
        snippet=f"Jenmam theeru deed snippet {session_idx} Survey 10{session_idx}/1 Aluva",
        result_dict={
            "doc_number": f"{5000 + session_idx}/2021",
            "seller": f"Owner {session_idx}",
            "buyer": f"Purchaser {session_idx}",
            "extent_cents": 4.5,
            "fatal_flaws": [],
            "risk_level": "LOW",
        },
        session_id=worker_id,
    )
    assert scan_id > 0, f"Failed to insert single deed scan for {worker_id}"

    return {
        "session_idx": session_idx,
        "worker_id": worker_id,
        "audit_id": audit_id,
        "scan_id": scan_id,
    }


def test_concurrent_sessions_sqlite_wal():
    """Spawns 15 simultaneous threads executing mixed reads and writes."""
    num_sessions = 15
    start_time = time.perf_counter()

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_sessions) as executor:
        futures = [executor.submit(_session_db_worker, i) for i in range(num_sessions)]
        results = [f.result() for f in futures]

    duration = time.perf_counter() - start_time
    assert len(results) == num_sessions, f"Expected {num_sessions} results, got {len(results)}"

    # Verify all audits were persisted and distinct
    audit_ids = {r["audit_id"] for r in results}
    assert len(audit_ids) == num_sessions, "Duplicate or missing audit IDs detected"

    # Verify all deed scans were persisted and distinct
    scan_ids = {r["scan_id"] for r in results}
    assert len(scan_ids) == num_sessions, "Duplicate or missing scan IDs detected"

    msg = f"{num_sessions} concurrent sessions completed in {duration:.3f}s. Zero database locks!"
    print(msg)


@pytest.mark.asyncio
async def test_a2a_agent_card_concurrency():
    """Simulates 12 simultaneous remote clients querying the A2A Agent Card concurrently."""
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:

            async def fetch_card(endpoint: str):
                resp = await client.get(endpoint)
                assert resp.status_code == 200
                data = resp.json()
                assert "skills" in data
                assert "name" in data
                return data["name"]

            endpoints = [
                "/a2a/kandezhuthu/.well-known/agent-card.json",
                "/.well-known/agent-card.json",
                "/a2a/kandezhuthu",
            ]

            tasks = [fetch_card(endpoints[i % len(endpoints)]) for i in range(12)]
            results = await asyncio.gather(*tasks)

            assert len(results) == 12
            assert all(name == "kandezhuthu_agent" for name in results)


@pytest.mark.asyncio
async def test_a2a_jsonrpc_task_status_concurrency():
    """Simulates 10 concurrent clients querying JSON-RPC methods (tasks/status, tasks/get)."""
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:

            async def query_status(idx: int):
                payload = {
                    "jsonrpc": "2.0",
                    "id": f"req-concur-{idx}",
                    "method": "tasks/status",
                    "params": {"task_id": f"task-mock-{idx}"},
                }
                resp = await client.post("/a2a/kandezhuthu", json=payload)
                assert resp.status_code == 200
                return resp.json()

            tasks = [query_status(i) for i in range(10)]
            results = await asyncio.gather(*tasks)
            assert len(results) == 10
            for r in results:
                assert r.get("jsonrpc") == "2.0"
