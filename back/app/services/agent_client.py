"""Low-level HTTP client for invoking the ADK agent's api_server (/run).

Shared entry point for any back-end flow that needs the real agent (with its
BigQuery/Storage tools) to run a task, as opposed to copilot_service's chat
turn which has its own Ollama-specific retry/fallback tuning layered on top.
"""
from __future__ import annotations

import os

import httpx


def agent_url() -> str:
    return os.getenv('AGENT_BASE_URL', 'http://localhost:8080')


_BAD_FINISH_REASONS = {
    'MALFORMED_FUNCTION_CALL',
    'MAX_TOKENS',
    'SAFETY',
    'RECITATION',
    'OTHER',
}


def _extract_reply(events: list | dict) -> str:
    """Return the model's final text reply, or '' if the run crashed before
    producing one.

    A multi-agent run can hand off mid-task (e.g. orchestrator ->
    knowledge_agent) and leave a "handing off now" text behind in an earlier
    event before the sub-agent crashes — walking events in plain reverse
    order for the first text part would mistake that in-progress message for
    a completion. So: only the true last event counts as the reply, and only
    if it actually finished cleanly (no finishReason, or STOP); any other
    terminal finishReason (MALFORMED_FUNCTION_CALL, SAFETY, ...) means the
    run crashed and there is no real reply, regardless of what earlier
    events said.
    """
    if isinstance(events, dict):
        events = [events]
    if not events:
        return ''
    last = events[-1]
    finish_reason = last.get('finishReason')
    if finish_reason is not None and finish_reason in _BAD_FINISH_REASONS:
        return ''
    content = last.get('content') or {}
    for part in content.get('parts') or []:
        if isinstance(part, dict) and part.get('text'):
            return part['text']
    return ''


async def run_agent_turn(
    user_id: str, session_id: str, message: str, timeout_seconds: float = 600.0
) -> str:
    """Create the ADK session (idempotent, 409 on existing is fine) and run
    one turn, returning the final text reply. Raises on transport/HTTP errors
    — callers decide how to handle a failed run (retry, mark as failed, ...).
    """
    url = agent_url()
    timeout = httpx.Timeout(timeout_seconds, connect=10.0)
    payload = {
        'app_name': 'agents',
        'user_id': user_id,
        'session_id': session_id,
        'new_message': {'role': 'user', 'parts': [{'text': message}]},
        'streaming': False,
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(f'{url}/apps/agents/users/{user_id}/sessions/{session_id}', json={})
        if r.status_code not in (200, 409):
            r.raise_for_status()

        resp = await client.post(f'{url}/run', json=payload)
        resp.raise_for_status()
        return _extract_reply(resp.json())
