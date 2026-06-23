from pydantic import BaseModel


class DdlResponse(BaseModel):
    company_id: str
    dataset_id: str
    graph_name: str
    ddl: str
    human_review_required: bool = True


class ExecuteDdlResponse(BaseModel):
    dry_run: bool
    dataset_id: str
    execution: dict


class GraphQueryResponse(BaseModel):
    company_id: str
    graph_query: str
    note: str
