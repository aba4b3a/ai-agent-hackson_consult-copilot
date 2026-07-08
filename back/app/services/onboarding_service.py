from __future__ import annotations

import asyncio
import json

from app.core.config import settings
from app.crud.storage_crud import storage_crud
from app.schemas.company import CompanyOnboardingPrepareRequest, CompanyOnboardingPrepareResponse
from app.schemas.survey import SurveyAnswerCreate
from app.services import agent_client
from app.services.bigquery_service import bigquery_service
from app.services.company_service import company_service
from app.services.survey_service import survey_service
from app.services.wiki_service import wiki_service


def _wiki_written(company_id: str) -> bool:
    """The agent's self-reported completion text is not trustworthy on its
    own: observed directly against real Vertex AI Gemini, it can (a) report
    ONBOARDING_FAILED over one transient hiccup (e.g. a BigQuery
    streaming-insert 404 on a table created moments earlier) even though it
    went on to finish everything else, and worse, (b) report success while
    having only *described* a plausible-looking write_wiki_files result in
    prose without actually calling the tool. Wiki files actually existing in
    storage is the pipeline's last step and the one directly verifiable side
    effect, so it — not the model's text — is the authority on completion."""
    return bool(storage_crud.list_prefix(f'tenants/{company_id}/wiki/current/'))


def _build_onboarding_message(company_id: str, company_name: str, answers: list[SurveyAnswerCreate]) -> str:
    answers_payload = [
        {
            "question_id": a.question_id,
            "question_text": a.question_text,
            "respondent_role": a.respondent_role,
            "raw_answer": a.raw_answer,
            "numeric_value": a.numeric_value,
        }
        for a in answers
    ]
    return f"""企業ID: {company_id}
企業名: {company_name}

以下は初期アンケート(18問)の回答です。この内容をもとに、この企業のオンボーディング処理を最初から最後まで実行してください。

{json.dumps(answers_payload, ensure_ascii=False, indent=2)}

実行してほしい手順:
1. ensure_shared_dataset と create_core_tables(company_id="{company_id}") で、この企業用のBigQuery基本テーブル(survey_responses/knowledge_nodes/knowledge_edges)とプロパティグラフを作成する。
2. create_tenant_tables(company_id="{company_id}") で、KPI候補・重点管理指標候補などのテナント用テーブルを作成する。
3. insert_onboarding_answer_events は、上記の回答すべてを1つの records 配列にまとめて1回だけ呼び出す(回答1件ごとに個別に呼び出さないこと)。
4. 上記の回答内容を分析し、KPI候補・重点管理指標候補を抽出して insert_kpi_candidates / insert_focus_metric_candidates で登録する。
5. 継続的な収集が必要な指標があれば、create_research_collection_table と register_research_schedule_item で収集用テーブルと収集スケジュールを用意する。
6. 上記の内容をもとに render_wiki_files で初期Wikiの各ファイルを生成し、write_wiki_files で保存する。

途中のツール呼び出しが失敗しても構わないので、必ず最後まで進めてください。write_wiki_files は
実際に呼び出して結果を確認すること — ツールを呼ばずに成功したかのような結果を文章で捏造しては
いけません。最後の返信の1行目は、全ての手順が完了した場合は必ず「ONBOARDING_COMPLETE」、途中で
続行できない手順がある場合は「ONBOARDING_FAILED: <理由>」のどちらか一方だけを出力し、その後に
実行結果の要約を続けてください。"""


# The multi-step tool chain this triggers (table DDL -> tenant tables ->
# KPI/focus-metric extraction -> wiki generation) occasionally makes the model
# emit a malformed function call partway through and crash the run (observed
# directly, repeatedly, against real Vertex AI Gemini — most often right as
# knowledge_agent takes over after the orchestrator's handoff). This is a
# real model-reliability limitation with this many tools/complex schemas, not
# something back-end retry logic can fully paper over; 3 attempts trades a
# meaningfully better success rate for proportionally higher LLM cost. A
# retry uses a fresh session so the model starts the chain over; the
# table-creation/write tools it re-runs are idempotent (CREATE TABLE IF NOT
# EXISTS, MERGE-based upserts), except onboarding_answer_events, which may
# get a harmless duplicate append row on retry.
_MAX_ATTEMPTS = 3


class OnboardingService:
    def prepare(self, company_id: str, data: CompanyOnboardingPrepareRequest) -> CompanyOnboardingPrepareResponse:
        initial_survey = survey_service.generate_common_initial_survey(company_id)
        ddl = bigquery_service.generate_core_tables_ddl(company_id)
        wiki_markdown, wiki_json = wiki_service.render_initial_wiki(company_id, data.company_name, initial_survey)
        if data.industry_hint:
            wiki_json['industry_hint'] = data.industry_hint
        if data.size_hint:
            wiki_json['size_hint'] = data.size_hint
        return CompanyOnboardingPrepareResponse(company_id=company_id, company_name=data.company_name, dataset_id=settings.dataset_id(), core_tables_ddl=ddl.ddl, initial_survey=initial_survey, wiki_markdown=wiki_markdown, wiki_json=wiki_json)

    async def run_agent_onboarding(self, company_id: str, answers: list[SurveyAnswerCreate]) -> None:
        """Kick off the real ADK agent (BigQuery table creation, KPI/focus
        metric extraction, wiki generation) once a company finishes its
        initial intake. Invoked as a FastAPI background task from
        survey.create_initial_survey_submission — the agent run itself can
        take minutes, so this must never block the HTTP response.
        """
        company = company_service.get(company_id)
        if company is not None and company.get('onboarding_status') == 'processing':
            return
        company_name = company['company_name'] if company else company_id
        company_service.update_onboarding_status(company_id, 'processing')
        message = _build_onboarding_message(company_id, company_name, answers)

        last_error: Exception | None = None
        for attempt in range(_MAX_ATTEMPTS):
            reply = ''
            try:
                reply = await agent_client.run_agent_turn(
                    user_id=company_id, session_id=f'onboarding_{company_id}_{attempt}', message=message
                )
                last_error = None
            except Exception as exc:
                last_error = exc
            # Wiki files existing is the sole pass/fail authority (see
            # _wiki_written) — checked unconditionally, whether or not the
            # HTTP call above raised, since the tools can have run for real
            # server-side even if the response itself failed to parse.
            if _wiki_written(company_id):
                company_service.update_onboarding_status(company_id, 'completed')
                return
            if last_error is None:
                last_error = RuntimeError(f'agent run finished without writing wiki files: {reply[:500]}')
            if attempt < _MAX_ATTEMPTS - 1:
                await asyncio.sleep(1.0)

        company_service.update_onboarding_status(company_id, 'failed', str(last_error)[:1000])


onboarding_service = OnboardingService()
