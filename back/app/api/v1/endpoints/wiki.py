from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.wiki import WikiUploadRequest, WikiUploadResponse
from app.services.wiki_service import wiki_service

router = APIRouter()


@router.post('/{company_id}/wiki/upload', response_model=WikiUploadResponse)
def upload_wiki(company_id: str, data: WikiUploadRequest):
    results = wiki_service.upload_company_wiki(company_id, data.wiki_markdown, data.wiki_json, data.schema_sql)
    return WikiUploadResponse(company_id=company_id, results=results)


@router.get('/{company_id}/wiki/files')
def list_wiki_files(company_id: str):
    return {
        'company_id': company_id,
        'items': wiki_service.list_current_files(company_id),
    }


@router.get('/{company_id}/wiki/versions')
def list_wiki_versions(company_id: str):
    return {
        'company_id': company_id,
        'versions': wiki_service.list_versions(company_id),
    }


@router.get('/{company_id}/wiki/versions/{version}/files')
def list_wiki_version_files(company_id: str, version: str):
    return {
        'company_id': company_id,
        'version': version,
        'items': wiki_service.list_version_files(company_id, version),
    }


@router.get('/{company_id}/wiki/files/content')
def read_wiki_file(
    company_id: str,
    path: str = Query(..., description='Relative path under wiki/current/, e.g. company_profile.md'),
    version: str | None = Query(default=None, description='Snapshot version. Omit for the current file.'),
):
    try:
        if version:
            text = wiki_service.read_version_file(company_id, version, path)
        else:
            text = wiki_service.read_current_file(company_id, path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f'wiki file not found: {path}')
    return {'company_id': company_id, 'path': path, 'version': version, 'content': text}
