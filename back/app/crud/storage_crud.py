from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from google.api_core.exceptions import NotFound as GcpNotFound
from google.cloud.storage.exceptions import InvalidResponse as GcsInvalidResponse

from app.core.config import settings
from app.db.storage import get_storage_client


class StorageCrud:
    def _use_local_emulator(self) -> bool:
        # Mirrors app/db/bigquery.py's client selection: APP_ENV=local alone
        # isn't a signal to fall back to a filesystem emulator — it only
        # matters when there's actually no real bucket configured to fall
        # back *from*. Without this, a real WIKI_BUCKET is silently ignored
        # whenever APP_ENV=local (true for any devcontainer), even when
        # pointed at real production credentials.
        return settings.dry_run or not settings.wiki_bucket

    def _local_path(self, path: str) -> Path:
        safe_path = path.replace('\\', '/').strip('/').replace('..', '_')
        bucket = settings.wiki_bucket or 'local-cd-agent-knowledge'
        return Path(settings.storage_emulator_root) / bucket / safe_path

    def upload_text(self, path: str, content: str, content_type: str) -> dict:
        if self._use_local_emulator():
            target = self._local_path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding='utf-8')
            return {
                'dry_run': settings.dry_run,
                'emulated': True,
                'bucket': settings.wiki_bucket or 'local-cd-agent-knowledge',
                'path': path,
                'content_type': content_type,
                'local_path': str(target),
                'gs_uri': f'gs://{settings.wiki_bucket or "local-cd-agent-knowledge"}/{path}',
            }
        if not settings.wiki_bucket:
            raise ValueError('WIKI_BUCKET is required')
        client = get_storage_client()
        bucket = client.bucket(settings.wiki_bucket)
        blob = bucket.blob(path)
        blob.upload_from_string(content, content_type=content_type)
        return {
            'dry_run': False,
            'emulated': False,
            'bucket': settings.wiki_bucket,
            'path': path,
            'gs_uri': f'gs://{settings.wiki_bucket}/{path}',
            'generation': blob.generation,
        }

    def read_text(self, path: str) -> str:
        if self._use_local_emulator():
            target = self._local_path(path)
            if not target.exists():
                raise FileNotFoundError(str(target))
            return target.read_text(encoding='utf-8')
        if not settings.wiki_bucket:
            raise ValueError('WIKI_BUCKET is required')
        client = get_storage_client()
        bucket = client.bucket(settings.wiki_bucket)
        blob = bucket.blob(path)
        try:
            return blob.download_as_text(encoding='utf-8')
        except GcpNotFound as exc:
            raise FileNotFoundError(f'gs://{settings.wiki_bucket}/{path}') from exc
        except GcsInvalidResponse as exc:
            # GCS media download raises InvalidResponse (not NotFound) for 404,
            # so callers can't distinguish "missing" from other transport errors
            # unless we normalize here. Match the emulator branch above.
            response = getattr(exc, 'response', None)
            if getattr(response, 'status_code', None) == 404:
                raise FileNotFoundError(f'gs://{settings.wiki_bucket}/{path}') from exc
            raise

    def exists(self, path: str) -> bool:
        if self._use_local_emulator():
            return self._local_path(path).exists()
        if not settings.wiki_bucket:
            raise ValueError('WIKI_BUCKET is required')
        client = get_storage_client()
        bucket = client.bucket(settings.wiki_bucket)
        return bucket.blob(path).exists()

    def upload_json(self, path: str, content: dict[str, Any]) -> dict:
        return self.upload_text(
            path,
            json.dumps(content, ensure_ascii=False, indent=2),
            'application/json; charset=utf-8',
        )

    def read_json(self, path: str) -> dict[str, Any]:
        return json.loads(self.read_text(path))

    def list_prefix(self, prefix: str) -> list[dict[str, Any]]:
        safe_prefix = prefix.replace('\\', '/').strip('/').replace('..', '_')
        if self._use_local_emulator():
            root = self._local_path(safe_prefix)
            if not root.exists():
                return []
            results: list[dict[str, Any]] = []
            for path in sorted(root.rglob('*')):
                if not path.is_file():
                    continue
                rel = path.relative_to(self._local_path(''))
                results.append(
                    {
                        'bucket': settings.wiki_bucket or 'local-cd-agent-knowledge',
                        'path': str(rel).replace('\\', '/'),
                        'size': path.stat().st_size,
                        'updated': path.stat().st_mtime,
                        'generation': None,
                    }
                )
            return results
        if not settings.wiki_bucket:
            raise ValueError('WIKI_BUCKET is required')
        client = get_storage_client()
        bucket = client.bucket(settings.wiki_bucket)
        items: list[dict[str, Any]] = []
        for blob in client.list_blobs(bucket, prefix=safe_prefix):
            items.append(
                {
                    'bucket': settings.wiki_bucket,
                    'path': blob.name,
                    'size': blob.size,
                    'updated': blob.updated.isoformat() if blob.updated else None,
                    'generation': blob.generation,
                }
            )
        return items


storage_crud = StorageCrud()
