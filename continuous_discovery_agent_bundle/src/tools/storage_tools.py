"""
Cloud Storage tool interface skeleton.
"""

from typing import Dict


class StorageTools:
    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name

    def write_wiki_files(self, company_id: str, files: Dict[str, str], create_version_snapshot: bool = True) -> None:
        """Write LLM Wiki files under tenants/{company_id}/wiki/current."""
        raise NotImplementedError

    def write_raw_answer(self, company_id: str, fiscal_year: int, filename: str, content: str) -> str:
        """Write immutable raw answer content. Return gs:// URI."""
        raise NotImplementedError

    def write_derived_json(self, company_id: str, fiscal_year: int, filename: str, content: str) -> str:
        """Write derived canonical JSON/YAML. Return gs:// URI."""
        raise NotImplementedError
