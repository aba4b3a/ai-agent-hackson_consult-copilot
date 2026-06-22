from agents.knowledge_agent import _normalize_entities, extract_knowledge
from app.schemas import ExtractedEntity, ExtractionRequest, WorkspaceContext


def test_mock_extracts_observed_fact() -> None:
    request = ExtractionRequest(
        source_type="daily_report",
        body="駅前ドラッグのほうが待ち時間が短いと言われた。",
        workspace=WorkspaceContext(competitors=["駅前ドラッグ"], known_issues=["待ち時間"]),
    )

    result = extract_knowledge(request)

    assert result.extraction_method == "mock"
    assert len(result.observations) >= 1
    assert all(obs.fact_or_hypothesis == "fact" for obs in result.observations)
    assert "待ち時間" in result.observations[0].related_entities


def test_mock_extracts_typed_entities_and_relationships() -> None:
    request = ExtractionRequest(
        source_type="daily_report",
        body="高齢者から、駅前ドラッグのほうが待ち時間が短いと言われた。",
        workspace=WorkspaceContext(
            competitors=["駅前ドラッグ"],
            known_issues=["待ち時間"],
            customer_segments=["高齢者"],
        ),
    )

    result = extract_knowledge(request)

    types = {entity.name: entity.entity_type for entity in result.entities}
    assert types["駅前ドラッグ"] == "Competitor"
    assert types["高齢者"] == "CustomerSegment"
    assert types["待ち時間"] == "Issue"

    edges = {(rel.from_entity, rel.to_entity, rel.relationship_type) for rel in result.relationships}
    assert ("高齢者", "待ち時間", "MENTIONS") in edges
    assert ("待ち時間", "駅前ドラッグ", "RELATES_TO") in edges


def test_normalize_entities_merges_duplicates_and_aliases() -> None:
    entities = [
        ExtractedEntity(name="待ち時間", entity_type="Issue", aliases=["wait"]),
        ExtractedEntity(name="待ち時間", entity_type="Issue", aliases=["待機時間"]),
        ExtractedEntity(name="  ", entity_type="Issue"),
    ]

    normalized = _normalize_entities(entities)

    assert len(normalized) == 1
    assert normalized[0].aliases == ["wait", "待機時間"]


def test_mock_creates_hypothesis_on_competitor_mention() -> None:
    request = ExtractionRequest(
        source_type="voice_transcript",
        body="子育て世帯からオンライン服薬指導の相談が増えました。",
    )

    result = extract_knowledge(request)

    assert len(result.hypotheses) >= 1
    assert "可能性" in result.hypotheses[0].statement


def test_mock_handles_unmatched_text() -> None:
    request = ExtractionRequest(source_type="consultant_note", body="特記事項なし。")

    result = extract_knowledge(request)

    assert len(result.observations) == 1
    assert result.observations[0].related_entities == ["顧客変化"]
    assert result.hypotheses == []
