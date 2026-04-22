"""
Slack Bot — AI Resolver
Commands:
  /list-open-incidents         → lists all TODO Jira incidents
  /resolve-incident IN-XXX     → triggers the full fix pipeline for one incident

Run:  python -m slack_bot.app
"""

import asyncio
import re

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

import config
from slack_bot import mcp_client

app = App(token=config.SLACK_BOT_TOKEN, signing_secret=config.SLACK_SIGNING_SECRET)


@app.command("/list-open-incidents")
def handle_list_incidents(ack, respond):
    ack()
    respond("Fetching open incidents from Jira…")
    try:
        result = asyncio.run(mcp_client.list_open_incidents())
        respond(result)
    except Exception as exc:
        respond(f"Error: {exc}")


@app.command("/resolve-incident")
def handle_resolve_incident(ack, respond, command):
    ack()
    text = (command.get("text") or "").strip()
    if not re.fullmatch(r"[A-Z]+-\d+", text, re.IGNORECASE):
        respond("Usage: `/resolve-incident IN-123`")
        return

    incident_id = text.upper()
    respond(f"Starting resolution of *{incident_id}*… I'll notify you when PRs are ready.")

    def _run():
        try:
            result = asyncio.run(mcp_client.process_incident(incident_id))
            respond(f"*{incident_id}* resolved :white_check_mark:\n\n{result}")
        except Exception as exc:
            respond(f"*{incident_id}* failed :x:\n{exc}")

    import threading
    threading.Thread(target=_run, daemon=True).start()


if __name__ == "__main__":
    handler = SocketModeHandler(app, config.SLACK_BOT_TOKEN)
    handler.start()
