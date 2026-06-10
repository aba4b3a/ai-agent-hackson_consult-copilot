class StorageService:
    def build_report_path(self, quality_run_id: str) -> str:
        return f"reports/{quality_run_id}.json"
