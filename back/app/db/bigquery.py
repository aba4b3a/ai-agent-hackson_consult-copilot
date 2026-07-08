import os
from functools import lru_cache
from app.core.config import settings


@lru_cache(maxsize=1)
def get_bigquery_client():
    # Every caller (dashboard_service, bigquery_crud, ...) used to call this
    # per query, and bigquery.Client() is never explicitly closed, so each
    # call leaked its underlying HTTP connection pool as a CLOSE_WAIT socket.
    # Caching a single client for the process lifetime keeps one pool alive
    # instead of one per query.
    if not settings.project_id:
        raise ValueError('PROJECT_ID is required')
    from google.cloud import bigquery
    
    # Configure BigQuery emulator for local development
    if settings.app_env == 'local' and settings.bigquery_emulator_host:
        from google.auth.credentials import AnonymousCredentials
        os.environ['BIGQUERY_EMULATOR_HOST'] = settings.bigquery_emulator_host
        # The emulator has no real auth; without explicit AnonymousCredentials,
        # google.cloud.client.Client still calls google.auth.default(), which
        # probes the GCE metadata server and can hang for a long time before
        # failing in environments without that server.
        return bigquery.Client(
            project=settings.project_id,
            location=settings.location,
            credentials=AnonymousCredentials(),
        )
    else:
        # Use Google Cloud BigQuery for production
        # location must be pinned explicitly: without it, jobs for
        # not-yet-existing datasets (e.g. CREATE SCHEMA IF NOT EXISTS) fall
        # back to BigQuery's US default instead of settings.location.
        return bigquery.Client(project=settings.project_id, location=settings.location)
