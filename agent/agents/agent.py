from google.adk.agents import Agent

from agents.config import settings
from prompts.prompts import COMMAND_AGENT_INSTRUCTION, RESEARCH_AGENT_INSTRUCTION, KNOWLEDGE_AGENT_INSTRUCTION
from tools.bigquery_tools import (
    create_company_dataset,
    generate_core_tables_ddl,
    create_core_tables,
    insert_survey_response,
    upsert_knowledge_nodes,
    upsert_knowledge_edges,
    propose_custom_table_ddl,
    sample_graph_query,
)
from tools.storage_tools import upload_company_wiki
from tools.survey_tools import generate_common_initial_survey
from tools.wiki_tools import render_wiki_markdown, render_wiki_json, build_custom_table_wiki_update

research_agent = Agent(
    name="research_agent",
    model=settings.model_id,
    description="アンケート形式で中小企業の定量・定性情報を収集する調査エージェント",
    instruction=RESEARCH_AGENT_INSTRUCTION,
    tools=[generate_common_initial_survey, insert_survey_response],
)

knowledge_agent = Agent(
    name="knowledge_agent",
    model=settings.model_id,
    description="暗黙知を分析・構造化し、BigQuery GraphとLLM Wikiを設計するナレッジエージェント",
    instruction=KNOWLEDGE_AGENT_INSTRUCTION,
    tools=[
        generate_core_tables_ddl,
        upsert_knowledge_nodes,
        upsert_knowledge_edges,
        propose_custom_table_ddl,
        render_wiki_markdown,
        render_wiki_json,
        build_custom_table_wiki_update,
        upload_company_wiki,
        sample_graph_query,
    ],
)

root_agent = Agent(
    name="command_agent",
    model=settings.model_id,
    description="Continuous Discovery Agent の司令塔。Research Agent と Knowledge Agent を統括する。",
    instruction=COMMAND_AGENT_INSTRUCTION,
    tools=[
        create_company_dataset,
        create_core_tables,
        generate_core_tables_ddl,
        generate_common_initial_survey,
        propose_custom_table_ddl,
        upload_company_wiki,
        sample_graph_query,
    ],
    sub_agents=[research_agent, knowledge_agent],
)
