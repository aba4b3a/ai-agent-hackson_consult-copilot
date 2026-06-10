from google.auth.credentials import AnonymousCredentials
from google.cloud import bigquery

from app.core.config import settings


def get_bigquery_client() -> bigquery.Client:
    if settings.bigquery_emulator_host:
        return bigquery.Client(
            project=settings.gcp_project,
            credentials=AnonymousCredentials(),  # type: ignore[no-untyped-call]
            client_options={"api_endpoint": settings.bigquery_emulator_host},
        )

    return bigquery.Client(project=settings.gcp_project)
