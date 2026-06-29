from __future__ import annotations

import json


def render_company_profile_markdown(company_profile: dict) -> str:
    issues = company_profile.get("current_issues") or ["TBD"]
    issue_lines = "\n".join(f"- {issue}" for issue in issues)
    source_refs = company_profile.get("source_refs") or []
    source_lines = "\n".join(f"- `{source}`" for source in source_refs) or "- TBD"
    return f"""# Company Profile

## Business Summary

{company_profile.get("business_summary", "TBD")}

## Customer Summary

{company_profile.get("customer_summary", "TBD")}

## Product / Service Summary

{company_profile.get("product_service_summary", "TBD")}

## Competition Summary

{company_profile.get("competition_summary", "TBD")}

## Operation Summary

{company_profile.get("operation_summary", "TBD")}

## Current Issues

{issue_lines}

## Confidence

{company_profile.get("confidence", 0.0)}

## Source References

{source_lines}

## Notes

- confirmed: 原回答に明記された事項
- inferred: AI推論を含む事項
- proposed: 人間承認前の仮説/候補
"""


def render_kpi_definitions_yaml(kpi_candidates: list[dict]) -> str:
    lines = ["kpis:"]
    if not kpi_candidates:
        lines.append("  []")
        return "\n".join(lines) + "\n"
    for item in kpi_candidates:
        source_refs = item.get("source_refs") or item.get("source_gcs_uris") or []
        lines.extend(
            [
                f"  - kpi_id: {item.get('kpi_candidate_id')}",
                f"    name: {item.get('kpi_name')}",
                f"    domain: {item.get('kpi_domain') or 'unknown'}",
                f"    type: {item.get('kpi_type') or 'unknown'}",
                "    unit: null",
                f"    description: {json.dumps(item.get('description', ''), ensure_ascii=False)}",
                f"    calculation_formula: {json.dumps(item.get('calculation_hint'), ensure_ascii=False)}",
                f"    measurement_frequency: {item.get('measurement_frequency') or 'unknown'}",
                f"    data_source: {json.dumps(item.get('data_source_hint'), ensure_ascii=False)}",
                f"    status: {item.get('approval_status', 'proposed')}",
                f"    confidence: {item.get('confidence', 0.0)}",
                "    source_refs:",
            ]
        )
        lines.extend(f"      - {json.dumps(ref, ensure_ascii=False)}" for ref in source_refs)
    return "\n".join(lines) + "\n"


def render_focus_metrics_yaml(focus_metric_candidates: list[dict]) -> str:
    lines = ["focus_metrics:"]
    if not focus_metric_candidates:
        lines.append("  []")
        return "\n".join(lines) + "\n"
    for item in focus_metric_candidates:
        source_refs = item.get("source_refs") or item.get("source_gcs_uris") or []
        related_kpis = item.get("related_kpi_candidate_ids") or item.get("related_kpi_candidates") or []
        lines.extend(
            [
                f"  - focus_metric_id: {item.get('focus_metric_candidate_id')}",
                f"    name: {item.get('metric_name')}",
                f"    category: {item.get('metric_category') or 'unknown'}",
                f"    description: {json.dumps(item.get('description', ''), ensure_ascii=False)}",
                "    related_kpis:",
            ]
        )
        lines.extend(f"      - {json.dumps(kpi, ensure_ascii=False)}" for kpi in related_kpis)
        lines.append("    observation_signals:")
        lines.extend(
            f"      - {json.dumps(signal, ensure_ascii=False)}"
            for signal in item.get("observation_signal_types", [])
        )
        lines.extend(
            [
                f"    trigger_condition: {json.dumps(item.get('trigger_condition'), ensure_ascii=False)}",
                f"    followup_policy: {json.dumps(item.get('followup_policy'), ensure_ascii=False)}",
                f"    measurement_frequency: {item.get('measurement_frequency') or 'unknown'}",
                f"    status: {item.get('approval_status', 'proposed')}",
                f"    confidence: {item.get('confidence', 0.0)}",
                "    source_refs:",
            ]
        )
        lines.extend(f"      - {json.dumps(ref, ensure_ascii=False)}" for ref in source_refs)
    return "\n".join(lines) + "\n"


def render_research_policy_yaml(company_id: str, research_plan: list[dict]) -> str:
    lines = [
        "research_policy:",
        f"  company_id: {company_id}",
        "  max_questions_per_run: 3",
        "  active_research_tasks:",
    ]
    if not research_plan:
        lines.append("    []")
        return "\n".join(lines) + "\n"
    for item in research_plan:
        lines.extend(
            [
                f"    - task_id: {item.get('research_task_id')}",
                f"      target_role: {json.dumps(item.get('target_role'), ensure_ascii=False)}",
                f"      frequency: {item.get('frequency', 'ad_hoc')}",
                f"      purpose: {json.dumps(item.get('question_intent'), ensure_ascii=False)}",
                "      related_kpis:",
            ]
        )
        lines.extend(
            f"        - {json.dumps(kpi, ensure_ascii=False)}"
            for kpi in item.get("related_kpi_candidates", [])
        )
        lines.append("      related_focus_metrics:")
        lines.extend(
            f"        - {json.dumps(metric, ensure_ascii=False)}"
            for metric in item.get("related_focus_metric_candidates", [])
        )
        lines.append("      base_questions:")
        lines.extend(
            f"        - {json.dumps(question, ensure_ascii=False)}"
            for question in item.get("base_questions", [])
        )
        lines.append(f"      followup_policy: {json.dumps(item.get('followup_policy'), ensure_ascii=False)}")
    return "\n".join(lines) + "\n"


def render_wiki_files(
    company_id: str,
    company_profile: dict,
    kpi_candidates: list[dict],
    focus_metric_candidates: list[dict],
    research_plan: list[dict],
) -> dict[str, str]:
    return {
        "company_profile.md": render_company_profile_markdown(company_profile),
        "kpi_definitions.yaml": render_kpi_definitions_yaml(kpi_candidates),
        "focus_metrics.yaml": render_focus_metrics_yaml(focus_metric_candidates),
        "research_policy.yaml": render_research_policy_yaml(company_id, research_plan),
        "manifest.json": json.dumps(
            {
                "company_id": company_id,
                "files": [
                    "company_profile.md",
                    "kpi_definitions.yaml",
                    "focus_metrics.yaml",
                    "research_policy.yaml",
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
    }


def render_wiki_markdown(
    company_id: str,
    company_name: str,
    nodes: list[dict],
    edges: list[dict],
    recommended_questions: list[dict],
    custom_tables: list[dict] | None = None,
) -> str:
    """Backward-compatible graph-oriented wiki renderer."""
    custom_tables = custom_tables or []
    node_lines = "\n".join(
        f"- `{n.get('node_id')}` [{n.get('node_type')}]: {n.get('label')} - {n.get('description', '')}"
        for n in nodes
    ) or "- まだ抽出されたノードはありません。"
    edge_lines = "\n".join(
        f"- `{e.get('source_node_id')}` -[{e.get('edge_type')}]-> `{e.get('target_node_id')}`: {e.get('description', '')}"
        for e in edges
    ) or "- まだ抽出された関係性はありません。"
    question_lines = "\n".join(
        f"- [{q.get('frequency')}] {q.get('question_text')} / 対象: {q.get('target_role')} / 型: {q.get('answer_type')}"
        for q in recommended_questions
    ) or "- まだ推奨質問はありません。"
    table_lines = "\n".join(
        f"- `{t.get('table_id')}`: {t.get('purpose')}" for t in custom_tables
    ) or "- 任意テーブルはまだありません。"
    return f"""# LLM Wiki: {company_name}

## Company ID

`{company_id}`

## Knowledge Nodes

{node_lines}

## Knowledge Edges

{edge_lines}

## Recommended Questions

{question_lines}

## Custom Tables

{table_lines}
"""


def render_wiki_json(
    company_id: str,
    company_name: str,
    nodes: list[dict],
    edges: list[dict],
    recommended_questions: list[dict],
    custom_tables: list[dict] | None = None,
) -> dict:
    return {
        "company_id": company_id,
        "company_name": company_name,
        "purpose": "Continuous Discovery Agent knowledge map",
        "nodes": nodes,
        "edges": edges,
        "recommended_questions": recommended_questions,
        "custom_tables": custom_tables or [],
    }


def build_custom_table_wiki_update(table_proposal: dict) -> str:
    return f"""
## Custom Table Proposal: `{table_proposal['table_id']}`

### Purpose

{table_proposal['purpose']}

### BigQuery DDL

```sql
{table_proposal['ddl']}
```

### Operation

This table proposal requires human review before execution.
""".strip()


def to_pretty_json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)
