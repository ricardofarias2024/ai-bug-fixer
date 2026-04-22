"""Thin async wrapper around the MCP SSE client."""

from contextlib import asynccontextmanager

from mcp import ClientSession
from mcp.client.sse import sse_client

import config


def _server_url() -> str:
    return f"http://{config.MCP_SERVER_HOST}:{config.MCP_SERVER_PORT}/sse"


@asynccontextmanager
async def _session():
    async with sse_client(_server_url()) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


async def list_open_incidents() -> str:
    async with _session() as session:
        result = await session.call_tool("list_open_incidents", {})
        return result.content[0].text if result.content else "No response."


async def process_incident(incident_id: str) -> str:
    async with _session() as session:
        result = await session.call_tool("process_incident", {"incident_id": incident_id})
        return result.content[0].text if result.content else "No response."
