from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.core.config import settings
from app.crud.storage_crud import storage_crud
from app.schemas.survey import InitialSurveyStatus, SurveyAnswerRead, SurveyQuestion, SurveyTemplate
from app.services.sample_company_data import sample_company_data


SEED_TEMPLATE_PATH = (
    Path(__file__).resolve().parents[1]
    / 'storage_seed'
    / 'survey_templates'
    / 'common_initial_v1.json'
)


class SurveyService:
    def _template_storage_path(self, survey_type: str = 'common_initial_survey', version: str = 'v1') -> str:
        return f'survey_templates/{survey_type}/{version}/template.json'

    def ensure_initial_template(self, version: str = 'v1') -> dict:
        path = self._template_storage_path(version=version)
        if storage_crud.exists(path):
            return {'created': False, 'path': path}
        seed = json.loads(SEED_TEMPLATE_PATH.read_text(encoding='utf-8'))
        storage_crud.upload_json(path, seed)
        return {'created': True, 'path': path}

    def get_initial_survey_template(self, company_id: str, version: str = 'v1') -> SurveyTemplate:
        seed_result = self.ensure_initial_template(version)
        raw_template = storage_crud.read_json(seed_result['path'])
        questions = [
            SurveyQuestion(
                **{
                    **question,
                    'company_id': company_id,
                    'version': raw_template.get('version', version),
                    'options': [choice['label'] for choice in question.get('choices', [])],
                }
            )
            for question in raw_template['questions']
        ]
        return SurveyTemplate(
            template_id=raw_template['template_id'],
            company_id=company_id,
            survey_type=raw_template['survey_type'],
            version=raw_template['version'],
            title=raw_template['title'],
            description=raw_template['description'],
            storage_path=seed_result['path'],
            questions=questions,
        )

    def generate_common_initial_survey(self, company_id: str) -> dict:
        return self.get_initial_survey_template(company_id).model_dump()

    def _query_responses(self, company_id: str, question_ids: list[str]) -> list[dict]:
        if settings.dry_run or not question_ids:
            return []
        try:
            from app.db.bigquery import get_bigquery_client
            survey_responses = settings.qualified_table(company_id, 'survey_responses')
            ids_sql = ', '.join(f"'{qid}'" for qid in question_ids)
            sql = f"""
                SELECT question_id, question_text, answer_type, respondent_role,
                       raw_answer, numeric_value, answer_json, collected_at
                FROM `{survey_responses}`
                WHERE question_id IN ({ids_sql})
                ORDER BY collected_at DESC
            """
            client = get_bigquery_client()
            return [dict(row) for row in client.query(sql).result()]
        except Exception:
            return []

    def get_initial_survey_status(self, company_id: str) -> InitialSurveyStatus:
        template = self.get_initial_survey_template(company_id)
        question_ids = [question.question_id for question in template.questions]

        rows = self._query_responses(company_id, question_ids)
        if not rows:
            sample = sample_company_data.structured(company_id)
            if sample:
                rows = [
                    row for row in sample.get('survey_responses', [])
                    if row.get('question_id') in question_ids
                ]

        latest_by_question: dict[str, SurveyAnswerRead] = {}
        for row in rows:
            # BigQuery returns TIMESTAMP columns as datetime objects, but the
            # sample-data fallback path supplies plain ISO strings; normalize
            # both to a string since SurveyAnswerRead.collected_at is str.
            collected_at = row.get('collected_at', '')
            if isinstance(collected_at, datetime):
                collected_at = collected_at.isoformat()
            answer = SurveyAnswerRead(
                question_id=row['question_id'],
                question_text=row.get('question_text', ''),
                answer_type=row.get('answer_type', 'text'),
                respondent_role=row.get('respondent_role', ''),
                raw_answer=row.get('raw_answer', ''),
                numeric_value=row.get('numeric_value'),
                answer_json=row.get('answer_json') or {},
                collected_at=collected_at or '',
            )
            existing = latest_by_question.get(answer.question_id)
            if not existing or answer.collected_at >= existing.collected_at:
                latest_by_question[answer.question_id] = answer

        answers = sorted(
            latest_by_question.values(),
            key=lambda answer: question_ids.index(answer.question_id) if answer.question_id in question_ids else len(question_ids),
        )
        return InitialSurveyStatus(
            company_id=company_id,
            answered=len(answers) > 0,
            answered_count=len(answers),
            total_count=len(question_ids),
            answers=answers,
        )


survey_service = SurveyService()
