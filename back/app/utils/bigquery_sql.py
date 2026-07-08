import json


def _escape_string(value: str) -> str:
    # Order matters: backslash first, then the characters whose escape
    # sequences introduce backslashes. A raw '\n'/'\r' inside a single-quoted
    # (non-triple-quoted) BigQuery string literal is a syntax error, not a
    # literal newline — e.g. an agent's multi-line reply text or error
    # message stored via sql_literal() needs this or the DML statement breaks.
    return (
        value.replace("\\", "\\\\")
        .replace("'", "\\'")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
    )


def sql_literal(value: object) -> str:
    """Render a Python value as a BigQuery SQL literal for DML statements."""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict):
        escaped = _escape_string(json.dumps(value, ensure_ascii=False))
        return f"JSON '{escaped}'"
    if isinstance(value, list):
        if not value:
            return "[]"
        return "[" + ", ".join(sql_literal(v) for v in value) + "]"
    return f"'{_escape_string(str(value))}'"
