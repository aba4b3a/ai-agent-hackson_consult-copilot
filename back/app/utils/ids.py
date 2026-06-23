import hashlib
from uuid import uuid4


def new_id(prefix: str) -> str:
    return f'{prefix}_{uuid4().hex}'


def stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha1('|'.join(parts).encode('utf-8')).hexdigest()[:16]
    return f'{prefix}_{digest}'
