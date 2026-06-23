from pydantic import BaseModel


class WikiUploadRequest(BaseModel):
    company_name: str
    wiki_markdown: str
    wiki_json: dict
    schema_sql: str


class WikiUploadResponse(BaseModel):
    company_id: str
    results: dict
