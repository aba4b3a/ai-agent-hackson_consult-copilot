"""Company master registry.

Lives in the ``companies`` table in the shared BigQuery dataset (same schema
the Knowledge Agent's ``generate_common_tables_ddl`` defines), unprefixed
since it's the one global registry of all companies rather than any single
company's own data. Both back and the agent read/write the same source of
truth. "Deleting" a company here is a logical delete only: ``active_status``
flips to ``inactive`` and the row (plus all of that company's own BigQuery
tables) is left intact for audit purposes.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from app.core.config import settings
from app.crud.bigquery_crud import bigquery_crud
from app.utils.bigquery_sql import sql_literal
from app.utils.time import utc_now_iso

TABLE = "companies"

_TIMESTAMP_FIELDS = ("created_at", "updated_at")

_ensured = False


def _table() -> str:
    return settings.qualified_common_table(TABLE)


def _ensure_table() -> None:
    global _ensured
    if _ensured or settings.dry_run:
        _ensured = True
        return
    ddl = f"""
CREATE SCHEMA IF NOT EXISTS `{settings.project_id}.{settings.dataset_id()}`;

CREATE TABLE IF NOT EXISTS `{_table()}` (
  company_id STRING NOT NULL,
  company_name STRING NOT NULL,
  legal_name STRING,
  industry_code STRING,
  industry_name STRING,
  sub_industry_code STRING,
  sub_industry_name STRING,
  business_type STRING,
  company_size_segment STRING,
  employee_count INT64,
  annual_revenue_range STRING,
  region_country STRING,
  region_prefecture STRING,
  region_city STRING,
  primary_sales_channels ARRAY<STRING>,
  primary_customer_types ARRAY<STRING>,
  primary_revenue_models ARRAY<STRING>,
  onboarding_status STRING,
  active_status STRING,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP
);
""".strip()
    bigquery_crud.execute_sql(ddl)
    _ensured = True


def _insert_row(row: dict) -> None:
    if settings.dry_run:
        return
    columns = list(row.keys())
    values_sql = ", ".join(sql_literal(row[column]) for column in columns)
    sql = f"INSERT INTO `{_table()}` ({', '.join(columns)}) VALUES ({values_sql})"
    bigquery_crud.execute_sql(sql)


def _row_to_dict(row: dict) -> dict:
    normalized = dict(row)
    for field in _TIMESTAMP_FIELDS:
        value = normalized.get(field)
        if isinstance(value, datetime):
            normalized[field] = value.isoformat()
    return normalized


class CompanyService:
    def create(
        self,
        company_id: str,
        company_name: str,
        industry_hint: str | None = None,
        size_hint: str | None = None,
    ) -> dict:
        _ensure_table()
        now = utc_now_iso()
        row: dict[str, Any] = {
            "company_id": company_id,
            "company_name": company_name,
            "legal_name": None,
            "industry_code": None,
            "industry_name": industry_hint,
            "sub_industry_code": None,
            "sub_industry_name": None,
            "business_type": None,
            "company_size_segment": size_hint,
            "employee_count": None,
            "annual_revenue_range": None,
            "region_country": None,
            "region_prefecture": None,
            "region_city": None,
            "primary_sales_channels": [],
            "primary_customer_types": [],
            "primary_revenue_models": [],
            "onboarding_status": "pending",
            "active_status": "active",
            "created_at": now,
            "updated_at": now,
        }
        _insert_row(row)
        return row

    def get(self, company_id: str) -> dict | None:
        _ensure_table()
        sql = (
            f"SELECT * FROM `{_table()}` "
            f"WHERE company_id = {sql_literal(company_id)} LIMIT 1"
        )
        rows = bigquery_crud.query_rows(sql)
        return _row_to_dict(rows[0]) if rows else None

    def deactivate(self, company_id: str) -> dict:
        """Logical delete: flips active_status to 'inactive'. Does not touch
        any of the company's actual data (core/tenant BigQuery datasets)."""
        _ensure_table()
        existing = self.get(company_id)
        if existing is None:
            raise KeyError(company_id)
        sql = f"""
UPDATE `{_table()}`
SET active_status = 'inactive', updated_at = {sql_literal(utc_now_iso())}
WHERE company_id = {sql_literal(company_id)}
""".strip()
        bigquery_crud.execute_sql(sql)
        updated = self.get(company_id)
        assert updated is not None
        return updated


company_service = CompanyService()
