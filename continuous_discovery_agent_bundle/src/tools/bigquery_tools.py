"""
BigQuery tool interface skeleton.

重要: エージェントに任意SQLを実行させない。
許可された操作だけを関数として公開する。
"""

from typing import Any, Dict, List


class BigQueryTools:
    def __init__(self, project_id: str):
        self.project_id = project_id

    def insert_kpi_candidates(self, tenant_dataset: str, records: List[Dict[str, Any]]) -> None:
        """Insert KPI candidate records."""
        raise NotImplementedError

    def insert_focus_metric_candidates(self, tenant_dataset: str, records: List[Dict[str, Any]]) -> None:
        """Insert focus metric candidate records."""
        raise NotImplementedError

    def insert_research_followup_questions(self, tenant_dataset: str, records: List[Dict[str, Any]]) -> None:
        """Insert research followup question records."""
        raise NotImplementedError

    def upsert_current_kpi_definition(self, tenant_dataset: str, record: Dict[str, Any], approved: bool) -> None:
        """Upsert current KPI definition. Must require approval."""
        if not approved:
            raise PermissionError("Human approval is required before updating current KPI definitions.")
        raise NotImplementedError

    def upsert_current_focus_metric_definition(self, tenant_dataset: str, record: Dict[str, Any], approved: bool) -> None:
        """Upsert current focus metric definition. Must require approval."""
        if not approved:
            raise PermissionError("Human approval is required before updating current focus metric definitions.")
        raise NotImplementedError
