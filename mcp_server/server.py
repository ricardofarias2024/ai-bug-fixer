"""
MCP Incident Processor Server — exposes tools over SSE so the Slack bot
can trigger incident resolution without direct HTTP coupling.

Run:  python -m mcp_server.server
"""

import asyncio

import uvicorn
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import TextContent, Tool
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Mount, Route

import config
from incident_processor.jira_client import JiraClient
from incident_processor.processor import IncidentProcessor

server = Server("incident-processor")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="list_open_incidents",
            description="List all Jira incidents in TODO status ready for resolution.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="process_incident",
            description=(
                "Fetch a Jira incident, use the LLM to analyse and fix the bug, "
                "then open PRs to master, stage, and integration."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "incident_id": {
                        "type": "string",
                        "description": "Jira incident ID, e.g. IN-42",
                    }
                },
                "required": ["incident_id"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "list_open_incidents":
        jira = JiraClient()
        incidents = jira.get_open_incidents()
        if not incidents:
            text = "No open incidents found."
        else:
            lines = [f"• {i['key']}: {i['summary']} [{i['priority']}]" for i in incidents]
            text = "\n".join(lines)
        return [TextContent(type="text", text=text)]

    if name == "process_incident":
        incident_id = arguments["incident_id"]
        processor = IncidentProcessor()
        result = await processor.process(incident_id)
        return [TextContent(type="text", text=result)]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


def build_starlette_app() -> Starlette:
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request):
        async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
            await server.run(
                streams[0],
                streams[1],
                server.create_initialization_options(),
            )

    return Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ]
    )


if __name__ == "__main__":
    app = build_starlette_app()
    uvicorn.run(app, host=config.MCP_SERVER_HOST, port=config.MCP_SERVER_PORT)
