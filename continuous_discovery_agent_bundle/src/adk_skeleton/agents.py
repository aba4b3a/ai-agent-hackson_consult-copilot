"""
ADK / Agent SDK implementation skeleton.

実際のGoogle ADK APIに合わせて import とAgent定義は調整してください。
このファイルは責務分離とツール接続のイメージを示すための雛形です。
"""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class AgentResult:
    output: Dict[str, Any]
    requires_human_review: bool = False


class OrchestratorAgent:
    def __init__(self, knowledge_agent: "KnowledgeAgent", research_agent: "ResearchAgent"):
        self.knowledge_agent = knowledge_agent
        self.research_agent = research_agent

    def run_onboarding(self, payload: Dict[str, Any]) -> AgentResult:
        knowledge_result = self.knowledge_agent.analyze_initial_answers(payload)
        research_plan = knowledge_result.output.get("research_plan", [])
        return AgentResult(
            output={
                "knowledge_result": knowledge_result.output,
                "research_plan": research_plan,
            },
            requires_human_review=knowledge_result.requires_human_review,
        )

    def run_research_cycle(self, research_context: Dict[str, Any]) -> AgentResult:
        research_result = self.research_agent.collect_information(research_context)
        knowledge_update = self.knowledge_agent.update_from_research(research_result.output)
        return AgentResult(
            output={
                "research_result": research_result.output,
                "knowledge_update": knowledge_update.output,
            },
            requires_human_review=knowledge_update.requires_human_review,
        )


class KnowledgeAgent:
    def __init__(self, tools: Dict[str, Any]):
        self.tools = tools

    def analyze_initial_answers(self, payload: Dict[str, Any]) -> AgentResult:
        # 1. initial_answersを分析
        # 2. KPI候補、重点管理指標候補、research_plan、wiki_files、bigquery_write_planを生成
        # 3. 承認不要な候補はcandidate tablesへinsert
        # 4. wiki proposed filesをCloud Storageへwrite
        return AgentResult(output={"status": "stub", "research_plan": []}, requires_human_review=True)

    def update_from_research(self, payload: Dict[str, Any]) -> AgentResult:
        # Research Agentの観測結果を受け取り、候補やWikiを更新
        return AgentResult(output={"status": "stub_update"}, requires_human_review=True)


class ResearchAgent:
    def __init__(self, tools: Dict[str, Any]):
        self.tools = tools

    def collect_information(self, payload: Dict[str, Any]) -> AgentResult:
        # research_planに基づき質問を生成・送信・回答を構造化
        return AgentResult(output={"status": "stub_research"}, requires_human_review=False)
