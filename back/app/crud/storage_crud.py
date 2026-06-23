from app.core.config import settings
from app.db.storage import get_storage_client


class StorageCrud:
    def upload_text(self, path: str, content: str, content_type: str) -> dict:
        if not settings.wiki_bucket:
            raise ValueError('WIKI_BUCKET is required')
        if settings.dry_run:
            return {
                'dry_run': True,
                'bucket': settings.wiki_bucket,
                'path': path,
                'content_type': content_type,
                'preview': content[:1000],
            }
        client = get_storage_client()
        bucket = client.bucket(settings.wiki_bucket)
        blob = bucket.blob(path)
        blob.upload_from_string(content, content_type=content_type)
        return {'dry_run': False, 'bucket': settings.wiki_bucket, 'path': path, 'gs_uri': f'gs://{settings.wiki_bucket}/{path}'}


storage_crud = StorageCrud()
