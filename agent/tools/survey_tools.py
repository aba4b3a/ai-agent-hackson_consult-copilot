from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4


def generate_common_initial_survey(company_id: str, version: str = "v1") -> dict:
    """Return the backend/Storage lookup contract for the initial survey.

    The fixed question set is intentionally not embedded in the agent package.
    Backend owns the template at:
    survey_templates/common_initial_survey/{version}/template.json
    """
    return {
        "company_id": company_id,
        "survey_type": "common_initial_survey",
        "version": version,
        "source_of_truth": "cloud_storage",
        "backend_endpoint": f"/api/v1/companies/{company_id}/survey/initial",
        "storage_path": f"survey_templates/common_initial_survey/{version}/template.json",
        "note": "Fetch the typed question template from backend/Cloud Storage. Do not generate fixed questions inside the agent.",
    }


def generate_response_id() -> str:
    return f"resp_{uuid4().hex}"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
