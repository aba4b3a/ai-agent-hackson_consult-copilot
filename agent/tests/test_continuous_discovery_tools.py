import pytest

from tools.bigquery_tools import (
    insert_kpi_candidates,
    insert_research_followup_question_events,
    upsert_current_kpi_definition,
)
from tools.storage_tools import write_wiki_files
from tools.survey_tools import generate_common_initial_survey
from tools.wiki_tools import render_wiki_files


def test_generate_common_initial_survey_points_to_backend_storage() -> None:
    survey = generate_common_initial_survey("company_001")

    assert survey["source_of_truth"] == "cloud_storage"
    assert survey["backend_endpoint"] == "/api/v1/companies/company_001/survey/initial"
    assert survey["storage_path"] == "survey_templates/common_initial_survey/v1/template.json"


def test_insert_kpi_candidates_is_dry_run_safe() -> None:
    result = insert_kpi_candidates(
        "company_001",
        [
            {
                "kpi_candidate_id": "kpic_001",
                "kpi_name": "ランチ売上",
                "kpi_domain": "sales",
                "source_refs": ["answer_event_id:ans_001", "gs://bucket/raw.jsonl"],
                "confidence": 0.8,
            }
        ],
    )

    assert result["dry_run"] is True
    assert result["table"].endswith(".cd_tenant_company_001.kpi_candidates")
    assert result["rows"][0]["approval_status"] == "proposed"
    assert result["rows"][0]["source_answer_event_ids"] == ["ans_001"]
    assert result["rows"][0]["source_gcs_uris"] == ["gs://bucket/raw.jsonl"]


def test_insert_research_followup_question_events_is_dry_run_safe() -> None:
    result = insert_research_followup_question_events(
        "company_001",
        [
            {
                "followup_question_id": "fq_001",
                "question_text": "今週、顧客から価格について聞かれたことはありましたか？",
                "target_role": "接客担当",
            }
        ],
    )

    assert result["dry_run"] is True
    assert result["rows"][0]["status"] == "proposed"
    assert result["rows"][0]["priority_score"] == 0.0


def test_current_kpi_definition_requires_approval() -> None:
    with pytest.raises(PermissionError):
        upsert_current_kpi_definition(
            "company_001",
            {"kpi_id": "kpi_001", "kpi_name": "ランチ売上"},
            approved=False,
        )


def test_render_and_write_wiki_files_dry_run() -> None:
    files = render_wiki_files(
        "company_001",
        {
            "company_id": "company_001",
            "business_summary": "駅前立地の定食店",
            "source_refs": ["answer_event_id:ans_001"],
        },
        [],
        [],
        [],
    )
    result = write_wiki_files("company_001", files, create_version_snapshot=False)

    assert "company_profile.md" in files
    assert "駅前立地の定食店" in files["company_profile.md"]
    assert result["files_written"] == 5
    assert result["results"][0]["current"]["dry_run"] is True
