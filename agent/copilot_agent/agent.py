"""Consult Copilot の会話専用エージェント（design §6.4 / §23.6）。

Orchestrator（agents/agent.py）とは別の ADK アプリとして提供する。
読み取り専用の会話役であり、tools・sub_agents を意図的に持たない
（書き込み系 tool call の漏れやサブエージェント transfer を構造的に排除する）。
back の copilot 経路（POST /{company}/report/copilot）はこのアプリに転送される。
"""
from google.adk.agents import Agent

from agents.config import settings
from prompts.prompts import COPILOT_AGENT_INSTRUCTION

root_agent = Agent(
    name="copilot_agent",
    model=settings.model_id,
    description="コンサルタントの質問に、蓄積ナレッジを根拠に事実と仮説を分けて答える会話エージェント。",
    instruction=COPILOT_AGENT_INSTRUCTION,
)
