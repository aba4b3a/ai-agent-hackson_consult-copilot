from fastapi import APIRouter
from app.schemas.wiki import WikiUploadRequest, WikiUploadResponse
from app.services.wiki_service import wiki_service

router = APIRouter()


@router.post('/{company_id}/wiki/upload', response_model=WikiUploadResponse)
def upload_wiki(company_id: str, data: WikiUploadRequest):
    results = wiki_service.upload_company_wiki(company_id, data.wiki_markdown, data.wiki_json, data.schema_sql)
    return WikiUploadResponse(company_id=company_id, results=results)
