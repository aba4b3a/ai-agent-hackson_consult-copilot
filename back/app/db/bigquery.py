import os
from app.core.config import settings


def get_bigquery_client():
    if not settings.project_id:
        raise ValueError('PROJECT_ID is required')
    from google.cloud import bigquery
    
    # Configure BigQuery emulator for local development
    if settings.app_env == 'local' and settings.bigquery_emulator_host:
        os.environ['BIGQUERY_EMULATOR_HOST'] = settings.bigquery_emulator_host
        return bigquery.Client(project=settings.project_id, location=settings.location)
    else:
        # Use Google Cloud BigQuery for production
        return bigquery.Client(project=settings.project_id)
