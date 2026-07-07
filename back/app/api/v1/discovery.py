from fastapi import APIRouter, HTTPException, Query

from app.schemas.discovery import (
    CopilotAnswer,
    CopilotAsk,
    Dashboard,
    FollowupRequest,
    FollowupResponse,
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
from app.services import graph_views
from app.services.discovery_mock import discovery_repository

router = APIRouter(tags=["continuous-discovery"])


@router.get("/workspaces", response_model=list[Workspace])
def list_workspaces() -> list[Workspace]:
    return discovery_repository.list_workspaces()


@router.post("/workspaces", response_model=Workspace)
def create_workspace(payload: WorkspaceCreate) -> Workspace:
    return discovery_repository.create_workspace(payload)


@router.get("/workspaces/{workspace_id}/dashboard")
def get_dashboard(workspace_id: str) -> Dashboard:
    return discovery_repository.dashboard(workspace_id)


@router.post("/report-forms", response_model=ReportForm)
def create_report_form(payload: ReportFormCreate) -> ReportForm:
    return discovery_repository.create_report_form(payload)


@router.get("/report-forms/{form_id}", response_model=ReportForm)
def get_report_form(form_id: str) -> ReportForm:
    form = discovery_repository.get_report_form(form_id)
    if form is None:
        raise HTTPException(status_code=404, detail="report form not found")
    return form


@router.post("/report-submissions", response_model=Source)
def submit_report(payload: ReportSubmissionCreate) -> Source:
    return discovery_repository.submit_report(payload)


@router.post("/voice-intakes", response_model=Source)
def submit_voice(payload: VoiceIntakeCreate) -> Source:
    return discovery_repository.submit_voice(payload)


@router.post("/intake/followups", response_model=FollowupResponse)
def intake_followups(payload: FollowupRequest) -> FollowupResponse:
    questions = discovery_repository.generate_followups(payload.workspace_id, payload.answers)
    return FollowupResponse(questions=questions)


@router.get("/search/evidence")
def search_evidence(
    workspace_id: str,
    q: str = Query(default=""),
) -> dict[str, object]:
    return {"results": discovery_repository.search_evidence(workspace_id, q)}


@router.get("/graph/slice", response_model=GraphSlice)
def graph_slice(
    workspace_id: str,
    view: str = Query(default=graph_views.DEFAULT_VIEW),
) -> GraphSlice:
    # Unknown view values fall back to the default inside the builder.
    return discovery_repository.graph_slice(workspace_id, view)


@router.get("/reports/weekly", response_model=WeeklyReport)
def weekly_report(workspace_id: str) -> WeeklyReport:
    return discovery_repository.weekly_report(workspace_id)


@router.post("/reports/weekly/generate", response_model=WeeklyReport)
def generate_weekly_report(workspace_id: str) -> WeeklyReport:
    # Explicit regeneration entry point (§13.4). Reports are generated
    # on-demand in the in-memory MVP, so this shares the GET implementation.
    return discovery_repository.weekly_report(workspace_id)


@router.post("/copilot/ask", response_model=CopilotAnswer)
def ask_copilot(payload: CopilotAsk) -> CopilotAnswer:
    return discovery_repository.ask_copilot(payload.workspace_id, payload.question)
