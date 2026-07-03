from datetime import UTC, datetime, timedelta

from app.schemas.discovery import Observation, Workspace
from app.services.discovery_rules import detect_signals

NOW = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


def _workspace() -> Workspace:
    return Workspace(
        workspace_id="ws_test",
        workspace_name="テスト薬局",
        known_issues=["待ち時間"],
        competitors=["駅前ドラッグ"],
    )


def _observation(obs_id: str, observed_at: datetime, entities: list[str]) -> Observation:
    return Observation(
        observation_id=obs_id,
        workspace_id="ws_test",
        source_id="src_test",
        source_type="daily_report",
        observed_at=observed_at.isoformat(),
        summary="テスト観察",
        quote="テスト",
        confidence=0.8,
        related_entities=entities,
        evidence_uri="gs://test",
    )


def test_weekly_increase_fires_on_doubling() -> None:
    observations = [
        _observation("o1", NOW - timedelta(weeks=1), ["待ち時間"]),
        _observation("o2", NOW, ["待ち時間"]),
        _observation("o3", NOW, ["待ち時間"]),
    ]

    signals = detect_signals(observations, _workspace(), now=NOW)

    increases = [s for s in signals if s.signal_type == "weekly_increase"]
    assert len(increases) == 1
    assert increases[0].current_value == 2
    assert increases[0].baseline_value == 1
    assert increases[0].related_entities == ["待ち時間"]


def test_weekly_increase_respects_min_count() -> None:
    # 1 -> 1 stays below MIN_CURRENT_COUNT and the rate threshold.
    observations = [
        _observation("o1", NOW - timedelta(weeks=1), ["待ち時間"]),
        _observation("o2", NOW, ["待ち時間"]),
    ]

    signals = detect_signals(observations, _workspace(), now=NOW)

    assert not [s for s in signals if s.signal_type == "weekly_increase"]


def test_new_entity_detected_for_unknown_term_only() -> None:
    observations = [
        _observation("o1", NOW, ["ヘルスケア便"]),
        _observation("o2", NOW, ["駅前ドラッグ"]),  # known competitor -> not new
    ]

    signals = detect_signals(observations, _workspace(), now=NOW)

    new_entities = {s.related_entities[0] for s in signals if s.signal_type == "new_entity"}
    assert "ヘルスケア便" in new_entities
    assert "駅前ドラッグ" not in new_entities


def test_observations_without_timestamp_are_ignored() -> None:
    obs = _observation("o1", NOW, ["待ち時間"])
    obs = obs.model_copy(update={"observed_at": ""})

    assert detect_signals([obs], _workspace(), now=NOW) == []
