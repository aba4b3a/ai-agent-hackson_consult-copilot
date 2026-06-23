from app.core.config import settings

COMMAND_AGENT_INSTRUCTION = 'あなたは Continuous Discovery Agent の司令塔 Agent です。Research Agent と Knowledge Agent を使い分けます。'
RESEARCH_AGENT_INSTRUCTION = 'あなたは Research Agent です。アンケート形式で、定量・定性の両方を収集します。'
KNOWLEDGE_AGENT_INSTRUCTION = 'あなたは Knowledge Agent です。回答から暗黙知を抽出し、BigQuery Graph用ノード・エッジ、LLM Wiki、DDLを設計します。'


def build_adk_agents():
    try:
        from google.adk.agents import Agent
    except Exception as exc:  # pragma: no cover
        raise RuntimeError('google-adk is not installed or importable') from exc
    research_agent = Agent(name='research_agent', model=settings.model_id, description='調査エージェント', instruction=RESEARCH_AGENT_INSTRUCTION)
    knowledge_agent = Agent(name='knowledge_agent', model=settings.model_id, description='ナレッジエージェント', instruction=KNOWLEDGE_AGENT_INSTRUCTION)
    command_agent = Agent(name='command_agent', model=settings.model_id, description='司令塔エージェント', instruction=COMMAND_AGENT_INSTRUCTION, sub_agents=[research_agent, knowledge_agent])
    return command_agent
