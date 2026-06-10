from pydantic import BaseModel


class Approval(BaseModel):
    quality_run_id: str
    approved_by: str | None = None
    status: str
