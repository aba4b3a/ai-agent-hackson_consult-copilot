from app.core.config import settings


def get_storage_client():
    if not settings.project_id:
        raise ValueError('PROJECT_ID is required')
    from google.cloud import storage
    return storage.Client(project=settings.project_id)
