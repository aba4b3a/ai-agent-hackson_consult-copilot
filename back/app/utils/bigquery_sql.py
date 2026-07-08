import json


def sql_literal(value: object) -> str:
    """Render a Python value as a BigQuery SQL literal for DML statements."""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict):
        escaped = json.dumps(value, ensure_ascii=False).replace("\\", "\\\\").replace("'", "\\'")
        return f"JSON '{escaped}'"
    if isinstance(value, list):
        if not value:
            return "[]"
        return "[" + ", ".join(sql_literal(v) for v in value) + "]"
    escaped = str(value).replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"
