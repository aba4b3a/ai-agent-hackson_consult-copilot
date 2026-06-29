from __future__ import annotations

import json
from pathlib import Path

from app.crud.storage_crud import storage_crud
from app.schemas.survey import SurveyQuestion, SurveyTemplate


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


survey_service = SurveyService()
