"""Lightweight JSON Schema validator for Knowledge/Research agent outputs.

We intentionally do not pull in the ``jsonschema`` library: this is
single-purpose and the schemas use only a small subset of JSON Schema
(``type``, ``required``, ``properties``, ``items``, ``enum``, ``minLength``,
``minimum``, ``maximum``). If we later need full draft-2020-12 support,
swap this for ``jsonschema.validate``.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schemas"

KNOWLEDGE_AGENT_OUTPUT_SCHEMA = "knowledge_agent_output.schema.json"
RESEARCH_AGENT_OUTPUT_SCHEMA = "research_agent_output.schema.json"


class SchemaValidationError(ValueError):
    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


def load_schema(name: str) -> dict[str, Any]:
    path = SCHEMA_DIR / name
    schema: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return schema


def _type_matches(value: Any, expected: str | list[str]) -> bool:
    expected_types = expected if isinstance(expected, list) else [expected]
    for type_name in expected_types:
        if type_name == "string" and isinstance(value, str):
            return True
        if type_name == "number" and isinstance(value, (int, float)) and not isinstance(value, bool):
            return True
        if type_name == "integer" and isinstance(value, int) and not isinstance(value, bool):
            return True
        if type_name == "boolean" and isinstance(value, bool):
            return True
        if type_name == "object" and isinstance(value, dict):
            return True
        if type_name == "array" and isinstance(value, list):
            return True
        if type_name == "null" and value is None:
            return True
    return False


def _validate_against(value: Any, schema: dict[str, Any], path: str, errors: list[str]) -> None:
    if "type" in schema and not _type_matches(value, schema["type"]):
        errors.append(f"{path}: expected type {schema['type']}, got {type(value).__name__}")
        return

    if isinstance(value, dict):
        for required in schema.get("required", []):
            if required not in value:
                errors.append(f"{path}.{required}: required property missing")
        for key, sub_schema in (schema.get("properties") or {}).items():
            if key in value:
                _validate_against(value[key], sub_schema, f"{path}.{key}", errors)

    if isinstance(value, list) and "items" in schema:
        for idx, item in enumerate(value):
            _validate_against(item, schema["items"], f"{path}[{idx}]", errors)

    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path}: shorter than minLength={schema['minLength']}")
        if "enum" in schema and value not in schema["enum"]:
            errors.append(f"{path}: '{value}' not in enum {schema['enum']}")
    if value is None and "enum" in schema and None not in schema["enum"]:
        errors.append(f"{path}: null not in enum {schema['enum']}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: {value} < minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: {value} > maximum {schema['maximum']}")


def validate(payload: dict[str, Any], schema_name: str) -> None:
    schema = load_schema(schema_name)
    errors: list[str] = []
    _validate_against(payload, schema, "$", errors)
    if errors:
        raise SchemaValidationError(errors)


def validate_knowledge_agent_output(payload: dict[str, Any]) -> None:
    validate(payload, KNOWLEDGE_AGENT_OUTPUT_SCHEMA)


def validate_research_agent_output(payload: dict[str, Any]) -> None:
    validate(payload, RESEARCH_AGENT_OUTPUT_SCHEMA)
