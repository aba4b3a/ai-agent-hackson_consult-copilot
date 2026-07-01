from agents.followup_agent import generate_followups
from app.schemas import FollowupRequest, WorkspaceContext


def test_mock_followups_are_bounded_and_nonempty() -> None:
    request = FollowupRequest(
        workspace=WorkspaceContext(observation_topics=["価格比較", "待ち時間"]),
        answers=["今日は忙しかった"],
    )

    result = generate_followups(request)

    assert result.generation_method == "mock"
    assert 1 <= len(result.questions) <= 3
    assert all(q.strip() for q in result.questions)


def test_mock_followups_surface_uncovered_observation_topic() -> None:
    request = FollowupRequest(
        workspace=WorkspaceContext(observation_topics=["オンライン服薬指導"]),
        answers=["競合の話が出た"],
    )

    result = generate_followups(request)

    assert any("オンライン服薬指導" in q for q in result.questions)
