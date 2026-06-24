"""Report Copilot: back経由でagentのADK api_serverにリクエストを転送する。"""
from __future__ import annotations
import os
import httpx


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
                reply = _extract_reply(resp.json())
        except Exception as e:
            reply = f"[Agent unavailable: {e}]"

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


copilot_service = CopilotService()
