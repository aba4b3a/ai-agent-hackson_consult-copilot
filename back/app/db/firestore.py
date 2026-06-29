"""Firestore client + local fallback.

In production we use google-cloud-firestore. In local/dry_run mode we fall back
to a JSON file under ``settings.storage_emulator_root`` so the API and the
front-end can be exercised end-to-end without a live Firestore.

The fallback is intentionally simple — single-process, no transactions, no
querying beyond equality filters — and is only meant for local development.
"""
from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Iterable

from app.core.config import settings


_lock = threading.Lock()


def _use_local_fallback() -> bool:
    return settings.app_env == "local" or settings.dry_run


def _local_root() -> Path:
    return Path(settings.storage_emulator_root) / "firestore"


def _local_collection_path(collection: str) -> Path:
    safe = collection.replace("/", "__")
    return _local_root() / f"{safe}.json"


def _read_local(collection: str) -> dict[str, dict[str, Any]]:
    path = _local_collection_path(collection)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_local(collection: str, data: dict[str, dict[str, Any]]) -> None:
    path = _local_collection_path(collection)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _get_firestore_client():
    from google.cloud import firestore
    return firestore.Client(project=settings.project_id)


class FirestoreRepo:
    """Minimal Firestore-style repository with a local-file fallback."""

    def set(self, collection: str, doc_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        if _use_local_fallback():
            with _lock:
                data = _read_local(collection)
                data[doc_id] = payload
                _write_local(collection, data)
            return payload
        client = _get_firestore_client()
        client.collection(collection).document(doc_id).set(payload)
        return payload

    def update(self, collection: str, doc_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        if _use_local_fallback():
            with _lock:
                data = _read_local(collection)
                existing = data.get(doc_id)
                if existing is None:
                    raise KeyError(doc_id)
                existing.update(patch)
                data[doc_id] = existing
                _write_local(collection, data)
                return existing
        client = _get_firestore_client()
        ref = client.collection(collection).document(doc_id)
        ref.update(patch)
        snap = ref.get()
        if not snap.exists:
            raise KeyError(doc_id)
        return snap.to_dict() or {}

    def get(self, collection: str, doc_id: str) -> dict[str, Any] | None:
        if _use_local_fallback():
            data = _read_local(collection)
            return data.get(doc_id)
        client = _get_firestore_client()
        snap = client.collection(collection).document(doc_id).get()
        if not snap.exists:
            return None
        return snap.to_dict() or {}

    def delete(self, collection: str, doc_id: str) -> bool:
        if _use_local_fallback():
            with _lock:
                data = _read_local(collection)
                if doc_id not in data:
                    return False
                del data[doc_id]
                _write_local(collection, data)
                return True
        client = _get_firestore_client()
        client.collection(collection).document(doc_id).delete()
        return True

    def query(
        self,
        collection: str,
        filters: dict[str, Any] | None = None,
        order_by: str | None = None,
        descending: bool = True,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        if _use_local_fallback():
            data = _read_local(collection).values()
            rows: Iterable[dict[str, Any]] = data
            if filters:
                rows = [row for row in rows if all(row.get(k) == v for k, v in filters.items())]
            else:
                rows = list(rows)
            rows = list(rows)
            if order_by:
                rows.sort(key=lambda row: row.get(order_by) or "", reverse=descending)
            if limit is not None:
                rows = rows[:limit]
            return rows
        client = _get_firestore_client()
        query = client.collection(collection)
        if filters:
            for key, value in filters.items():
                query = query.where(key, "==", value)
        if order_by:
            from google.cloud.firestore_v1.base_query import BaseQuery
            direction = BaseQuery.DESCENDING if descending else BaseQuery.ASCENDING
            query = query.order_by(order_by, direction=direction)
        if limit is not None:
            query = query.limit(limit)
        return [doc.to_dict() or {} for doc in query.stream()]


firestore_repo = FirestoreRepo()
