from app.core.config import settings


def get_bigquery_client():
    if not settings.project_id:
        raise ValueError('PROJECT_ID is required')
    from google.cloud import bigquery
    return bigquery.Client(project=settings.project_id)
