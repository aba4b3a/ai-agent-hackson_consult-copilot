"""Report Copilot: back経由でagentのADK api_serverにリクエストを転送する。"""
from __future__ import annotations
import asyncio
import json
import os
import re
import uuid
import httpx
from app.schemas.approval import ApprovalCreate
from app.services.approval_service import approval_service
from app.services.sample_company_data import sample_company_data

# Local Ollama-backed agent runs occasionally crash mid-inference (e.g. the
# llama-server runner process dying under load) and auto-recover for the next
# request, so a single retry avoids masking a purely transient failure behind
# the sample-data fallback below.
_MAX_ATTEMPTS = 2
_RETRY_DELAY_SECONDS = 1.0

# The Ollama/Gemma runtime doesn't execute ADK function calls natively: instead
# of actually invoking the tool, it sometimes emits the call as plain-text JSON
# (`{"name": "insert_kpi_candidates", "parameters": {...}}`) inside the final
# reply. Rather than showing that raw blob to the user, we parse it here and
# queue the proposed records as pending approvals (writes still require human
# approval per AGENTS.md), replying with a human-readable summary instead.
_KPI_CANDIDATE_TOOL_NAME = "insert_kpi_candidates"


def _agent_url() -> str:
    return os.getenv('AGENT_BASE_URL', 'http://localhost:8080')


class CopilotService:
    async def chat(self, company_id: str, message: str, session_id: str | None = None) -> dict:
        agent_url = _agent_url()
        sid = session_id or f"session_{company_id}"

        payload = {
            "app_name": "agents",
            "user_id": company_id,
            "session_id": sid,
            "new_message": {"role": "user", "parts": [{"text": message}]},
            "streaming": False,
        }

        # タイムアウトを300秒に設定（LLM推論は時間がかかる）
        timeout = httpx.Timeout(300.0, connect=10.0)

        last_error: Exception | None = None
        reply: str | None = None
        for attempt in range(_MAX_ATTEMPTS):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    # セッション作成（409=既存は無視）
                    r = await client.post(
                        f"{agent_url}/apps/agents/users/{company_id}/sessions/{sid}",
                        json={},
                    )
                    if r.status_code not in (200, 409):
                        r.raise_for_status()

                    resp = await client.post(f"{agent_url}/run", json=payload)
                    resp.raise_for_status()
                    candidate = _extract_reply(resp.json())
                    if _looks_incomplete(candidate):
                        # A crashed/killed local model run still returns HTTP 200 with
                        # whatever partial text it managed to emit (e.g. `{"`), so this
                        # doesn't raise on its own — treat it as a failed attempt so the
                        # retry/sample-data fallback below still kicks in.
                        raise RuntimeError(f"agent returned an incomplete reply: {candidate!r}")
                    reply = candidate
                break
            except Exception as e:
                last_error = e
                if attempt < _MAX_ATTEMPTS - 1:
                    await asyncio.sleep(_RETRY_DELAY_SECONDS)

        if reply is None:
            reply = sample_company_data.copilot_answer(company_id, message) or f"[Agent unavailable: {last_error}]"
        else:
            reply = _handle_tool_call_reply(reply, company_id)

        return {"company_id": company_id, "session_id": sid, "reply": reply}


def _extract_reply(events: list | dict) -> str:
    if isinstance(events, dict):
        events = [events]
    for event in reversed(events):
        content = event.get("content") or {}
        for part in (content.get("parts") or []):
            if isinstance(part, dict) and part.get("text"):
                return part["text"]
    return "応答を取得できませんでした"


def _looks_incomplete(reply: str) -> bool:
    """Detect a truncated tool-call fragment (e.g. `{"`) left behind by a model
    run that crashed mid-generation. A real reply is either prose or a fully
    parseable JSON blob; anything starting with `{` that fails to parse is
    neither."""
    stripped = reply.strip()
    if not stripped:
        return True
    if stripped.startswith("{"):
        try:
            json.loads(stripped)
        except json.JSONDecodeError:
            return True
    return False


def _extract_tool_call_json(text: str) -> dict | None:
    """Pull a `{"name": ..., "parameters": {...}}` blob out of free-form text, if present."""
    candidate = text.strip()
    fence_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", candidate, re.DOTALL)
    if fence_match:
        candidate = fence_match.group(1)
    else:
        start, end = candidate.find("{"), candidate.rfind("}")
        if start == -1 or end == -1 or end < start:
            return None
        candidate = candidate[start : end + 1]

    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return None

    if isinstance(parsed, dict) and isinstance(parsed.get("parameters"), dict) and parsed.get("name"):
        return parsed
    return None


def _handle_tool_call_reply(reply: str, company_id: str) -> str:
    tool_call = _extract_tool_call_json(reply)
    if tool_call is None or tool_call.get("name") != _KPI_CANDIDATE_TOOL_NAME:
        return reply

    records = tool_call["parameters"].get("records") or []
    target_company_id = tool_call["parameters"].get("company_id") or company_id
    if not isinstance(records, list) or not records:
        return reply

    names = []
    for record in records:
        if not isinstance(record, dict):
            continue
        name = record.get("name") or record.get("kpi_id") or "KPI候補"
        names.append(name)
        approval_service.create(
            ApprovalCreate(
                company_id=target_company_id,
                target_type="kpi_candidate",
                target_id=record.get("kpi_id") or f"kpi_{uuid.uuid4().hex[:12]}",
                title=name,
                summary=record.get("description", ""),
                proposed_payload=record,
                confidence=record.get("confidence"),
                reason=record.get("calculation_formula"),
                created_by="agent:consult_copilot",
            )
        )

    if not names:
        return reply

    joined = "、".join(names)
    return f"KPI候補を{len(names)}件、承認待ちキューに登録しました: {joined}\n人間承認後、正式なKPI定義として反映されます。"


copilot_service = CopilotService()
