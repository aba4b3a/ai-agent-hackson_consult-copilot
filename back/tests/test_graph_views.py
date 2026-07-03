from app.schemas.discovery import Hypothesis, Observation, Workspace
from app.services.graph_views import build_graph_slice


def _workspace() -> Workspace:
    return Workspace(
        workspace_id="ws_test",
        workspace_name="テスト薬局",
        customer_segments=["高齢者"],
        competitors=["駅前ドラッグ"],
        known_issues=["待ち時間"],
        kpis=["再来店率"],
    )


def _observation(obs_id: str, entities: list[str]) -> Observation:
    return Observation(
        observation_id=obs_id,
        workspace_id="ws_test",
        source_id="src_test",
        source_type="daily_report",
        observed_at="2026-07-02T10:00:00+00:00",
        summary="テスト観察",
        quote="テスト",
        confidence=0.8,
        related_entities=entities,
        evidence_uri="gs://test",
    )


def test_customer_issue_view_builds_cooccurrence_edges() -> None:
    observations = [
        _observation("o1", ["高齢者", "待ち時間"]),
        _observation("o2", ["高齢者", "待ち時間", "駅前ドラッグ"]),
    ]

    slice_ = build_graph_slice(
        "customer-issue", _workspace(), {}, [], observations, []
    )

    node_types = {n.id: n.type for n in slice_.nodes}
    assert node_types["高齢者"] == "CustomerSegment"
    assert node_types["待ち時間"] == "Issue"
    # Competitor is out of view.
    assert "駅前ドラッグ" not in node_types
    edge = next(e for e in slice_.edges if {e.source, e.target} == {"高齢者", "待ち時間"})
    assert edge.evidence_count == 2
    assert edge.fact_or_hypothesis == "fact"


def test_hypothesis_view_produces_hypothesis_edges() -> None:
    observations = [_observation("o1", ["待ち時間", "駅前ドラッグ"])]
    hypotheses = [
        Hypothesis(
            hypothesis_id="hyp_001",
            workspace_id="ws_test",
            statement="競合の利便性が不満を強めている可能性がある。",
            status="observing",
            confidence=0.6,
            supporting_observation_ids=["o1"],
            recommended_observations=[],
        )
    ]

    slice_ = build_graph_slice("hypothesis", _workspace(), {}, [], observations, hypotheses)

    assert any(n.type == "Hypothesis" for n in slice_.nodes)
    assert slice_.edges
    assert all(e.fact_or_hypothesis == "hypothesis" for e in slice_.edges)


def test_unknown_view_falls_back_to_default() -> None:
    slice_ = build_graph_slice("nope", _workspace(), {}, [], [], [])

    # Default customer-issue view shows in-view context entities even with no
    # observations, so the demo never renders an empty pane for seed data.
    types = {n.type for n in slice_.nodes}
    assert types <= {"CustomerSegment", "Issue"}
    assert slice_.summary


def test_node_and_edge_caps_are_applied() -> None:
    observations = [
        _observation(f"o{i}", [f"顧客層{i}", f"課題{i}"]) for i in range(20)
    ]
    workspace = _workspace().model_copy(
        update={
            "customer_segments": [f"顧客層{i}" for i in range(20)],
            "known_issues": [f"課題{i}" for i in range(20)],
        }
    )

    slice_ = build_graph_slice("customer-issue", workspace, {}, [], observations, [])

    assert len(slice_.nodes) <= 12
    assert len(slice_.edges) <= 20
