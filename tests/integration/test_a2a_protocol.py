"""A2A Protocol, Agent Card, and Multi-turn Gateway Integration Tests.

Validates:
1. Agent Card accessibility at subpath, root .well-known, and GET rpc_path.
2. Complete Agent Card schema (skills, dual 0.3/1.0 supportedInterfaces).
3. JSON-RPC method normalization for remote gateways ('tasks/send', 'tasks/status').
4. Multi-turn session context preservation across consecutive JSON-RPC requests.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.db.database import init_db
from app.fast_api_app import app


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    init_db()


@pytest.mark.asyncio
async def test_agent_card_multi_endpoint_and_schema():
    """Verify Agent Card is discoverable across all standard routes and valid."""
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            routes = [
                "/a2a/kandezhuthu/.well-known/agent-card.json",
                "/.well-known/agent-card.json",
                "/a2a/kandezhuthu",
            ]
            for route in routes:
                resp = await client.get(route)
                assert resp.status_code == 200, f"Failed to fetch card from {route}"
                card = resp.json()
                assert card.get("name") == "kandezhuthu_agent"
                assert "skills" in card
                assert len(card["skills"]) >= 5

                # Check supported interfaces includes both 0.3 and 1.0
                interfaces = card.get("supportedInterfaces", [])
                versions = {i.get("protocolVersion") for i in interfaces}
                assert "0.3" in versions, f"Missing 0.3 compatibility interface: {versions}"
                assert "1.0" in versions, f"Missing 1.0 protocol interface: {versions}"


@pytest.mark.asyncio
async def test_jsonrpc_task_send_and_status_simulation():
    """Simulates remote gateway/Gemini Enterprise calling tasks/send and tasks/status."""
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            # 1. Turn 1: Send query via tasks/send
            send_payload = {
                "jsonrpc": "2.0",
                "id": "gw-msg-101",
                "method": "tasks/send",
                "params": {
                    "text": "What is the minimum access road width required under KPBR 2019 for residential plots?"
                },
            }
            res_send = await client.post("/a2a/kandezhuthu", json=send_payload)
            assert res_send.status_code == 200
            data_send = res_send.json()
            assert "error" not in data_send, f"tasks/send error: {data_send}"
            assert data_send.get("jsonrpc") == "2.0"
            assert data_send.get("id") == "gw-msg-101"

            result = data_send.get("result", {})
            task_id = result.get("id")
            context_id = result.get("contextId")
            assert task_id is not None
            assert context_id is not None

            # 2. Check task status via tasks/status
            status_payload = {
                "jsonrpc": "2.0",
                "id": "gw-stat-101",
                "method": "tasks/status",
                "params": {"task_id": task_id},
            }
            res_status = await client.post("/a2a/kandezhuthu", json=status_payload)
            assert res_status.status_code == 200
            data_status = res_status.json()
            assert "error" not in data_status
            state = data_status.get("result", {}).get("status", {}).get("state")
            assert state in ("completed", "working", "submitted")

            # 3. Turn 2: Follow-up question using the established context/task
            turn2_payload = {
                "jsonrpc": "2.0",
                "id": "gw-msg-102",
                "method": "tasks/send",
                "params": {
                    "task_id": task_id,
                    "text": "Does this apply to small plots below 3 Ares?"
                },
            }
            res_turn2 = await client.post("/a2a/kandezhuthu", json=turn2_payload)
            assert res_turn2.status_code == 200
            data_turn2 = res_turn2.json()
            assert "error" not in data_turn2
            result2 = data_turn2.get("result", {})
            assert result2.get("contextId") in (context_id, task_id)
            assert result2.get("status", {}).get("state") in ("completed", "working")
