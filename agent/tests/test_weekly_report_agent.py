from agents.weekly_report_agent import generate_report
from app.schemas import WeeklyReportContext, WeeklyReportRequest, WorkspaceContext


def test_mock_report_grounds_on_context() -> None:
    request = WeeklyReportRequest(
        period="2026-06-29 – 2026-07-05",
        context=WeeklyReportContext(
            signals=["weekly_increase: 待ち時間の言及が 1 → 2"],
            facts=["待ち時間について高齢の顧客から指摘があった。"],
            hypotheses=["競合の利便性訴求が不満を強めている可能性がある。"],
            evidence=["今日も待ち時間が長いと言われた。"],
            workspace=WorkspaceContext(observation_topics=["待ち時間"]),
        ),
    )

    result = generate_report(request)

    assert result.report_method == "mock"
    assert "待ち時間" in result.summary
    # Facts and hypotheses stay separate (R6/R13).
    assert result.observed_facts == request.context.facts
    assert result.hypotheses == request.context.hypotheses
    assert len(result.recommended_observations) >= 1
    assert len(result.limitations) >= 1


def test_mock_report_handles_empty_context() -> None:
    result = generate_report(WeeklyReportRequest())

    assert result.report_method == "mock"
    assert result.summary
    assert result.limitations
