from fastapi import APIRouter, Query

from app.schemas.discovery import (
    CopilotAnswer,
    CopilotAsk,
    GraphSlice,
    ReportForm,
    ReportFormCreate,
    ReportSubmissionCreate,
    Source,
    VoiceIntakeCreate,
    WeeklyReport,
    Workspace,
    WorkspaceCreate,
)
from app.services.discovery_mock import discovery_repository

router = APIRouter(tags=["continuous-discovery"])


@router.get("/workspaces", response_model=list[Workspace])
def list_workspaces() -> list[Workspace]:
    return discovery_repository.list_workspaces()


@router.post("/workspaces", response_model=Workspace)
def create_workspace(payload: WorkspaceCreate) -> Workspace:
    return discovery_repository.create_workspace(payload)


@router.get("/workspaces/{workspace_id}/dashboard")
def get_dashboard(workspace_id: str) -> dict[str, object]:
    return discovery_repository.dashboard(workspace_id)


@router.post("/report-forms", response_model=ReportForm)
def create_report_form(payload: ReportFormCreate) -> ReportForm:
    return discovery_repository.create_report_form(payload)


@router.post("/report-submissions", response_model=Source)
def submit_report(payload: ReportSubmissionCreate) -> Source:
    return discovery_repository.submit_report(payload)


@router.post("/voice-intakes", response_model=Source)
def submit_voice(payload: VoiceIntakeCreate) -> Source:
    return discovery_repository.submit_voice(payload)


@router.get("/search/evidence")
def search_evidence(
    workspace_id: str,
    q: str = Query(default=""),
) -> dict[str, object]:
    return {"results": discovery_repository.search_evidence(workspace_id, q)}


@router.get("/graph/slice", response_model=GraphSlice)
def graph_slice(workspace_id: str) -> GraphSlice:
    return discovery_repository.graph_slice(workspace_id)


@router.get("/reports/weekly", response_model=WeeklyReport)
def weekly_report(workspace_id: str) -> WeeklyReport:
    return discovery_repository.weekly_report(workspace_id)


@router.post("/copilot/ask", response_model=CopilotAnswer)
def ask_copilot(payload: CopilotAsk) -> CopilotAnswer:
    return discovery_repository.ask_copilot(payload.workspace_id, payload.question)
