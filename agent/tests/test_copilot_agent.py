from agents.copilot_agent import answer_question
from app.schemas import CopilotAnswerRequest, CopilotContext, WorkspaceContext


def test_mock_answer_grounds_on_context() -> None:
    request = CopilotAnswerRequest(
        question="なぜ価格関連の発言が増えた？",
        context=CopilotContext(
            facts=["高齢者から競合の待ち時間が短いという比較発言があった。"],
            hypotheses=["競合の利便性訴求が不満を強めている可能性がある。"],
            evidence=["駅前ドラッグのほうが待ち時間が短いと言われた。"],
            workspace=WorkspaceContext(competitors=["駅前ドラッグ"]),
        ),
    )

    result = answer_question(request)

    assert result.answer_method == "mock"
    assert result.answer
    # Observed facts and hypotheses are kept separate (R16).
    assert result.observed_facts == request.context.facts
    assert result.hypotheses == request.context.hypotheses
    assert len(result.recommended_observations) >= 1


def test_mock_answer_handles_empty_context() -> None:
    result = answer_question(CopilotAnswerRequest(question="状況は？"))

    assert result.answer_method == "mock"
    assert result.answer
    assert result.observed_facts == []
