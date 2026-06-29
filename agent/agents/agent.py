from google.adk.agents import Agent

from agents.config import settings
from prompts.prompts import (
    COMMAND_AGENT_INSTRUCTION,
    KNOWLEDGE_AGENT_INSTRUCTION,
    RESEARCH_AGENT_INSTRUCTION,
)
from tools.bigquery_tools import (
    create_company_dataset,
    create_common_tables,
    create_core_tables,
    create_tenant_tables,
    generate_core_tables_ddl,
    generate_common_tables_ddl,
    generate_tenant_tables_ddl,
    insert_focus_metric_candidates,
    insert_kpi_candidates,
    insert_onboarding_answer_events,
    insert_research_followup_question_events,
    insert_survey_response,
    insert_wiki_revision_log,
    propose_custom_table_ddl,
    sample_graph_query,
    upsert_current_focus_metric_definition,
    upsert_current_kpi_definition,
    upsert_knowledge_edges,
    upsert_knowledge_nodes,
)
from tools.storage_tools import (
    upload_company_wiki,
    write_derived_json,
    write_raw_answer,
    write_wiki_file,
    write_wiki_files,
)
from tools.survey_tools import generate_common_initial_survey
from tools.wiki_tools import (
    build_custom_table_wiki_update,
    render_focus_metrics_yaml,
    render_kpi_definitions_yaml,
    render_research_policy_yaml,
    render_wiki_files,
    render_wiki_json,
    render_wiki_markdown,
)

research_agent = Agent(
    name="research_agent",
    model=settings.model_id,
    description="追加調査計画に基づいて、対象者別に最大3問の短い質問を生成・整理するエージェント。",
    instruction=RESEARCH_AGENT_INSTRUCTION,
    tools=[
        generate_common_initial_survey,
        insert_survey_response,
        insert_research_followup_question_events,
    ],
)

knowledge_agent = Agent(
    name="knowledge_agent",
    model=settings.model_id,
    description="初期回答と追加回答から企業モデル、KPI候補、重点管理指標候補、Wiki更新案、BigQuery書き込み計画を作るエージェント。",
    instruction=KNOWLEDGE_AGENT_INSTRUCTION,
    tools=[
        generate_core_tables_ddl,
        generate_tenant_tables_ddl,
        insert_onboarding_answer_events,
        insert_kpi_candidates,
        insert_focus_metric_candidates,
        insert_research_followup_question_events,
        insert_wiki_revision_log,
        upsert_current_kpi_definition,
        upsert_current_focus_metric_definition,
        upsert_knowledge_nodes,
        upsert_knowledge_edges,
        propose_custom_table_ddl,
        render_wiki_files,
        render_kpi_definitions_yaml,
        render_focus_metrics_yaml,
        render_research_policy_yaml,
        render_wiki_markdown,
        render_wiki_json,
        build_custom_table_wiki_update,
        write_wiki_file,
        write_wiki_files,
        write_derived_json,
        upload_company_wiki,
        sample_graph_query,
    ],
)

root_agent = Agent(
    name="orchestrator_agent",
    model=settings.model_id,
    description="Continuous Discovery Agent の進行管理、人間承認、Research Agent と Knowledge Agent の実行順序制御を担うエージェント。",
    instruction=COMMAND_AGENT_INSTRUCTION,
    tools=[
        create_company_dataset,
        create_common_tables,
        create_core_tables,
        create_tenant_tables,
        generate_common_tables_ddl,
        generate_core_tables_ddl,
        generate_tenant_tables_ddl,
        generate_common_initial_survey,
        write_raw_answer,
        write_wiki_files,
        insert_kpi_candidates,
        insert_focus_metric_candidates,
        insert_research_followup_question_events,
        upsert_current_kpi_definition,
        upsert_current_focus_metric_definition,
        propose_custom_table_ddl,
        sample_graph_query,
    ],
    sub_agents=[research_agent, knowledge_agent],
)
