from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import PurePosixPath

from google.cloud import storage  # type: ignore[attr-defined]

from agents.config import settings


def _client() -> storage.Client:
    return storage.Client(project=settings.project_id)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _safe_path_part(value: str) -> str:
    return value.replace("\\", "/").strip("/").replace("..", "_")


def _tenant_prefix(company_id: str) -> str:
    return f"tenants/{_safe_path_part(company_id)}"


def _upload_text_to_gcs(path: str, content: str, content_type: str = "text/plain") -> dict:
    if not settings.wiki_bucket:
        if settings.dry_run:
            return {
                "dry_run": True,
                "bucket": "WIKI_BUCKET_NOT_SET",
                "path": path,
                "content_type": content_type,
                "preview": content[:1000],
            }
        raise ValueError("WIKI_BUCKET is not configured.")
    if settings.dry_run:
        return {
            "dry_run": True,
            "bucket": settings.wiki_bucket,
            "path": path,
            "content_type": content_type,
            "preview": content[:1000],
            "gs_uri": f"gs://{settings.wiki_bucket}/{path}",
        }
    client = _client()
    bucket = client.bucket(settings.wiki_bucket)
    blob = bucket.blob(path)
    blob.upload_from_string(content, content_type=content_type)
    return {
        "dry_run": False,
        "bucket": settings.wiki_bucket,
        "path": path,
        "generation": blob.generation,
        "gs_uri": f"gs://{settings.wiki_bucket}/{path}",
    }


def upload_text_to_gcs(path: str, content: str, content_type: str = "text/plain") -> dict:
    """Backward-compatible low-level upload helper."""
    return _upload_text_to_gcs(_safe_path_part(path), content, content_type)


def _read_json_from_gcs(path: str) -> dict | None:
    if settings.dry_run or not settings.wiki_bucket:
        return None
    blob = _client().bucket(settings.wiki_bucket).blob(path)
    if not blob.exists():
        return None
    result: dict = json.loads(blob.download_as_text(encoding="utf-8"))
    return result


def register_research_schedule_item(
    company_id: str,
    table_name: str,
    purpose: str,
    frequency: str,
    target_role: str,
    question_text: str,
    value_type: str = "text",
    target_candidate_table: str | None = None,
    target_candidate_id: str | None = None,
    target_candidate_name: str | None = None,
) -> dict:
    """Upsert one entry into tenants/{company_id}/research/schedule.json, the
    GCS-stored definition Research reads at page-view time to decide what's
    due for collection. Call after create_research_collection_table with the
    same table_name so Research knows where submitted answers should land.
    """
    safe_table = _safe_path_part(table_name)
    path = str(PurePosixPath(_tenant_prefix(company_id), "research", "schedule.json"))
    schedule_item_id = f"sched_{safe_table}"
    item = {
        "schedule_item_id": schedule_item_id,
        "table_name": safe_table,
        "purpose": purpose,
        "frequency": frequency,
        "target_role": target_role,
        "question_text": question_text,
        "value_type": value_type if value_type in ("text", "number") else "text",
        "target_candidate_table": target_candidate_table,
        "target_candidate_id": target_candidate_id,
        "target_candidate_name": target_candidate_name,
        "updated_at": _now().isoformat(),
    }
    existing = _read_json_from_gcs(path) or {"company_id": company_id, "items": []}
    items = [i for i in existing.get("items", []) if i.get("schedule_item_id") != schedule_item_id]
    items.append(item)
    payload = {"company_id": company_id, "items": items}
    upload_result = _upload_text_to_gcs(
        path, json.dumps(payload, ensure_ascii=False, indent=2), "application/json; charset=utf-8"
    )
    return {
        "company_id": company_id,
        "schedule_item_id": schedule_item_id,
        "path": path,
        "items_count": len(items),
        "upload": upload_result,
    }


def write_wiki_file(
    company_id: str,
    relative_path: str,
    content: str,
    content_type: str = "text/markdown; charset=utf-8",
    create_version_snapshot: bool = True,
) -> dict:
    """Write one LLM Wiki file under tenants/{company_id}/wiki/current."""
    safe_relative_path = _safe_path_part(relative_path)
    current_path = str(PurePosixPath(_tenant_prefix(company_id), "wiki", "current", safe_relative_path))
    current_result = _upload_text_to_gcs(current_path, content, content_type)
    version_result = None
    if create_version_snapshot:
        stamp = _now().strftime("%Y%m%dT%H%M%SZ")
        version_path = str(
            PurePosixPath(_tenant_prefix(company_id), "wiki", "versions", stamp, safe_relative_path)
        )
        version_result = _upload_text_to_gcs(version_path, content, content_type)
    return {
        "company_id": company_id,
        "current": current_result,
        "version_snapshot": version_result,
    }


def write_wiki_files(
    company_id: str,
    files: dict[str, str],
    create_version_snapshot: bool = True,
) -> dict:
    """Write multiple LLM Wiki files under tenants/{company_id}/wiki/current."""
    results = []
    for relative_path, content in files.items():
        content_type = (
            "application/yaml; charset=utf-8"
            if relative_path.endswith((".yaml", ".yml"))
            else "application/json; charset=utf-8"
            if relative_path.endswith(".json")
            else "text/markdown; charset=utf-8"
        )
        results.append(
            write_wiki_file(
                company_id,
                relative_path,
                content,
                content_type=content_type,
                create_version_snapshot=create_version_snapshot,
            )
        )
    return {"company_id": company_id, "files_written": len(results), "results": results}


def write_raw_answer(company_id: str, fiscal_year: int, filename: str, content: str) -> dict:
    """Write immutable raw answer content and return its GCS URI metadata."""
    safe_filename = _safe_path_part(filename)
    path = str(
        PurePosixPath(
            _tenant_prefix(company_id),
            "raw",
            f"fiscal_year={fiscal_year}",
            "answers",
            safe_filename,
        )
    )
    return _upload_text_to_gcs(path, content, "application/jsonl; charset=utf-8")


def write_derived_json(company_id: str, fiscal_year: int, filename: str, content: str | dict) -> dict:
    """Write derived canonical JSON/YAML and return its GCS URI metadata."""
    safe_filename = _safe_path_part(filename)
    body = json.dumps(content, ensure_ascii=False, indent=2) if isinstance(content, dict) else content
    path = str(
        PurePosixPath(
            _tenant_prefix(company_id),
            "derived",
            f"fiscal_year={fiscal_year}",
            safe_filename,
        )
    )
    content_type = (
        "application/yaml; charset=utf-8"
        if safe_filename.endswith((".yaml", ".yml"))
        else "application/json; charset=utf-8"
    )
    return _upload_text_to_gcs(path, body, content_type)


def upload_company_wiki(
    company_id: str,
    wiki_markdown: str,
    wiki_json: dict,
    schema_sql: str = "",
) -> dict:
    """Backward-compatible wiki upload used by the existing ADK agent."""
    files = {
        "company_profile.md": wiki_markdown,
        "manifest.json": json.dumps(wiki_json, ensure_ascii=False, indent=2),
    }
    if schema_sql:
        files["schema.sql"] = schema_sql
    return write_wiki_files(company_id, files)
