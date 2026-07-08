import json
from app.core.config import settings
from app.db.bigquery import get_bigquery_client


class BigQueryCrud:
    def create_dataset(self) -> dict:
        dataset_id = settings.dataset_id()
        full_dataset_id = f'{settings.project_id}.{dataset_id}'
        if settings.dry_run:
            return {'dry_run': True, 'dataset_id': dataset_id, 'full_dataset_id': full_dataset_id}
        from google.cloud import bigquery
        client = get_bigquery_client()
        dataset = bigquery.Dataset(full_dataset_id)
        dataset.location = settings.location
        client.create_dataset(dataset, exists_ok=True)
        return {'dry_run': False, 'dataset_id': dataset_id, 'full_dataset_id': full_dataset_id}

    def execute_sql(self, sql: str) -> dict:
        if settings.dry_run:
            return {'dry_run': True, 'sql': sql}
        client = get_bigquery_client()
        job = client.query(sql)
        job.result()
        return {'dry_run': False, 'job_id': job.job_id}

    def query_rows(self, sql: str) -> list[dict]:
        if settings.dry_run:
            return []
        client = get_bigquery_client()
        return [dict(row.items()) for row in client.query(sql).result()]

    def insert_json_rows(self, table_id: str, rows: list[dict]) -> dict:
        if settings.dry_run:
            return {'dry_run': True, 'table_id': table_id, 'rows': rows}
        client = get_bigquery_client()
        errors = client.insert_rows_json(table_id, rows)
        if errors:
            raise RuntimeError(json.dumps(errors, ensure_ascii=False))
        return {'dry_run': False, 'table_id': table_id, 'inserted': len(rows)}


bigquery_crud = BigQueryCrud()
