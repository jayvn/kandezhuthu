# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Attach A2A (Agent2Agent) endpoints to the FastAPI app.

func:`attach_a2a_routes` registers the dynamic
agent-card endpoint and the JSON-RPC endpoint so the same app serves A2A
alongside the adk_api routes, reachable by A2A clients and Gemini Enterprise A2A
registration.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from typing import TYPE_CHECKING

from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    add_a2a_routes_to_fastapi,
    create_agent_card_routes,
)
from a2a.server.routes.common import DefaultServerCallContextBuilder
from a2a.server.routes.jsonrpc_dispatcher import JsonRpcDispatcher
from a2a.server.tasks import TaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentExtension, AgentInterface
from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH
from google.adk.a2a.executor.a2a_agent_executor import A2aAgentExecutor
from google.adk.a2a.utils.agent_card_builder import AgentCardBuilder
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

logger = logging.getLogger(__name__)


class _A2AServerCallContextBuilder(DefaultServerCallContextBuilder):
    """Context builder that ensures A2A-Version defaults correctly when missing.

    Proxy infrastructure (e.g. Google Cloud API Gateways) can strip custom HTTP headers
    like 'A2A-Version'. This builder attempts to infer A2A-version from the method name
    when the header is missing.
    """

    def build(self, request):
        context = super().build(request)
        headers = context.state.setdefault("headers", {})
        existing_version = (
            headers.get("A2A-Version")
            or headers.get("a2a-version")
            or headers.get("x-a2a-version")
            or headers.get("X-A2A-Version")
        )
        if existing_version:
            headers["A2A-Version"] = existing_version
            return context

        # 0.3 uses method names that include a '/' like "message/send" or "tasks/send"
        # 1.0 uses PascalCase like "SendMessage"
        json_body = getattr(request, "_json", {}) or {}
        method = json_body.get("method") if isinstance(json_body, dict) else None

        if method and "/" in str(method):
            headers["A2A-Version"] = "0.3"
        else:
            headers["A2A-Version"] = "1.0"

        return context


if TYPE_CHECKING:
    from fastapi import FastAPI
    from google.adk.agents import BaseAgent
    from google.adk.runners import Runner

# URI advertised on the agent card describing the executor extension shipped
# by ADK. Kept as a module-level constant so callers can override or extend
# the capabilities list when needed.
_ADK_AGENT_EXECUTOR_EXTENSION_URI = (
    "https://google.github.io/adk-docs/a2a/a2a-extension/"
)


async def _add_v0_3_compat_interface(card: AgentCard) -> AgentCard:
    """Advertise a v0.3 JSON-RPC interface so the served card stays consumable by
    v0.3 A2A clients — notably Gemini Enterprise registration, whose validator
    still requires the 0.3 card shape (top-level ``url``/``protocolVersion``)."""
    if card.supported_interfaces:
        has_0_3 = any(
            getattr(i, "protocol_version", "") == "0.3"
            for i in card.supported_interfaces
        )
        if not has_0_3:
            card.supported_interfaces.append(
                AgentInterface(
                    protocol_binding="JSONRPC",
                    protocol_version="0.3",
                    url=card.supported_interfaces[0].url,
                )
            )
    return card


def _default_capabilities() -> AgentCapabilities:
    """Returns the default A2A capabilities used by scaffolded projects."""
    return AgentCapabilities(
        streaming=True,
        extensions=[
            AgentExtension(
                uri=_ADK_AGENT_EXECUTOR_EXTENSION_URI,
                description=("Ability to use the new agent executor implementation"),
            ),
        ],
    )


async def attach_a2a_routes(
    app: FastAPI,
    *,
    agent: BaseAgent,
    runner: Runner,
    task_store: TaskStore,
    rpc_path: str,
    capabilities: AgentCapabilities | None = None,
    agent_version: str | None = None,
    app_url: str | None = None,
) -> None:
    """Register A2A routes (JSON-RPC + agent-card endpoints) under ``rpc_path``.

    Builds a dynamic agent card from ``agent`` and mounts the routes on ``app``.
    The ``runner`` should share the session/artifact/memory services with the
    standard ADK path. ``capabilities``, ``agent_version``, and ``app_url``
    override their defaults (streaming + ADK extension, ``AGENT_VERSION``,
    ``APP_URL``). Call once per app — typically in a FastAPI ``lifespan``, since
    the card is built asynchronously; repeated calls register duplicate routes.
    """
    resolved_app_url = app_url or os.getenv("APP_URL", "http://0.0.0.0:8000")
    resolved_agent_version = agent_version or os.getenv("AGENT_VERSION", "0.1.0")
    resolved_capabilities = capabilities or _default_capabilities()

    agent_card = await AgentCardBuilder(
        agent=agent,
        capabilities=resolved_capabilities,
        rpc_url=f"{resolved_app_url}{rpc_path}",
        agent_version=resolved_agent_version,
    ).build()

    request_handler = DefaultRequestHandler(
        agent_executor=A2aAgentExecutor(runner=runner),
        task_store=task_store,
        agent_card=agent_card,
    )

    dispatcher = JsonRpcDispatcher(
        request_handler=request_handler,
        context_builder=_A2AServerCallContextBuilder(),
        enable_v0_3_compat=True,
    )

    async def normalized_jsonrpc_endpoint(request: Request) -> Response:
        """Pre-processes incoming JSON-RPC calls, normalizing method aliases like
        'tasks/send' -> 'message/send' and 'tasks/status' -> 'tasks/get' for remote
        gateway & Gemini Enterprise multi-turn interactions.
        """
        try:
            body = await request.json()
            if isinstance(body, dict):
                method = body.get("method")
                params = body.get("params") or {}

                # Normalize tasks/send -> message/send
                if method == "tasks/send":
                    body["method"] = "message/send"
                    if isinstance(params, dict):
                        if "message" not in params:
                            user_text = params.pop("text", None) or params.pop("input", "")
                            params["message"] = {
                                "message_id": f"msg-{uuid.uuid4()}",
                                "role": "user",
                                "parts": [{"text": str(user_text)}],
                            }
                        else:
                            msg = params["message"]
                            if isinstance(msg, dict):
                                if "message_id" not in msg and "messageId" not in msg:
                                    msg["message_id"] = f"msg-{uuid.uuid4()}"
                                if "role" not in msg:
                                    msg["role"] = "user"
                        if "task_id" in params and "contextId" not in params:
                            if isinstance(params.get("message"), dict):
                                params["message"]["context_id"] = params["task_id"]
                            params["contextId"] = params["task_id"]
                    body["params"] = params

                # Normalize tasks/status -> tasks/get
                elif method == "tasks/status":
                    body["method"] = "tasks/get"
                    if isinstance(params, dict) and "task_id" in params:
                        params["id"] = params.pop("task_id")
                    body["params"] = params

                # Normalize tasks/get if task_id provided instead of id
                elif method == "tasks/get":
                    if isinstance(params, dict) and "task_id" in params:
                        params["id"] = params.pop("task_id")
                    body["params"] = params

                # Normalize SendMessage / GetTask if PascalCase used with task_id
                elif method == "SendMessage" and isinstance(params, dict):
                    if "task_id" in params and "contextId" not in params:
                        params["contextId"] = params["task_id"]

                request._json = body
                request._body = json.dumps(body).encode("utf-8")
        except Exception as e:
            logger.debug("Failed to normalize JSON-RPC request body: %s", e)

        return await dispatcher.handle_requests(request)

    # Agent card routes: rpc_path subpath, root .well-known, and GET rpc_path
    agent_card_routes = list(
        create_agent_card_routes(
            agent_card,
            card_modifier=_add_v0_3_compat_interface,
            card_url=f"{rpc_path}{AGENT_CARD_WELL_KNOWN_PATH}",
        )
    )
    agent_card_routes.extend(
        create_agent_card_routes(
            agent_card,
            card_modifier=_add_v0_3_compat_interface,
            card_url=AGENT_CARD_WELL_KNOWN_PATH,
        )
    )
    agent_card_routes.extend(
        create_agent_card_routes(
            agent_card,
            card_modifier=_add_v0_3_compat_interface,
            card_url=rpc_path,
        )
    )

    jsonrpc_routes = [
        Route(
            path=rpc_path,
            endpoint=normalized_jsonrpc_endpoint,
            methods=["POST"],
        )
    ]

    add_a2a_routes_to_fastapi(
        app,
        agent_card_routes=agent_card_routes,
        jsonrpc_routes=jsonrpc_routes,
    )
