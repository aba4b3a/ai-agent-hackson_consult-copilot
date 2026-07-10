"""copilot_agent（会話専用エージェント、design §23.6）の構造テスト。"""
from copilot_agent.agent import root_agent


def test_copilot_agent_is_read_only_conversation_agent() -> None:
    assert root_agent.name == "copilot_agent"
    # 読み取り専用の会話役: tools と sub_agents を持たないことが安全性の前提
    assert list(root_agent.tools) == []
    assert list(root_agent.sub_agents) == []


def test_copilot_agent_instruction_separates_fact_and_hypothesis() -> None:
    instruction = root_agent.instruction
    # ADK の instruction は str | Callable の Union のため型を確定させる
    assert isinstance(instruction, str)
    assert "仮説" in instruction
    assert "事実" in instruction
    assert "Consult Copilot" in instruction
