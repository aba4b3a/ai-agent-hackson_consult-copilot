from __future__ import annotations

import json
from google.cloud import storage
from agents.config import settings


def _client() -> storage.Client:
    return storage.Client(project=settings.project_id)


def upload_text_to_gcs(path: str, content: str, content_type: str = "text/plain") -> dict:
    if not settings.wiki_bucket:
        if settings.dry_run:
            return {"dry_run": True, "bucket": "WIKI_BUCKET_NOT_SET", "path": path, "content_type": content_type, "preview": content[:1000]}
        raise ValueError("WIKI_BUCKET is not configured.")
    if settings.dry_run:
        return {"dry_run": True, "bucket": settings.wiki_bucket, "path": path, "content_type": content_type, "preview": content[:1000]}
    client = _client()
    bucket = client.bucket(settings.wiki_bucket)
    blob = bucket.blob(path)
    blob.upload_from_string(content, content_type=content_type)
    return {"dry_run": False, "bucket": settings.wiki_bucket, "path": path, "gs_uri": f"gs://{settings.wiki_bucket}/{path}"}


def upload_company_wiki(company_id: str, wiki_markdown: str, wiki_json: dict, schema_sql: str) -> dict:
    base = f"companies/{company_id}"
    md_result = upload_text_to_gcs(f"{base}/wiki.md", wiki_markdown, content_type="text/markdown; charset=utf-8")
    json_result = upload_text_to_gcs(f"{base}/wiki.json", json.dumps(wiki_json, ensure_ascii=False, indent=2), content_type="application/json; charset=utf-8")
    sql_result = upload_text_to_gcs(f"{base}/schema.sql", schema_sql, content_type="text/plain; charset=utf-8")
    return {"company_id": company_id, "wiki_md": md_result, "wiki_json": json_result, "schema_sql": sql_result}
