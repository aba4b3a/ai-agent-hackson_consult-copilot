from __future__ import annotations

import functools
import traceback
from typing import Any, Callable, TypeVar

# Tool functions return either a structured dict (BigQuery/storage tools) or
# rendered text (wiki-rendering tools), so the bound has to cover both.
F = TypeVar("F", bound=Callable[..., "dict[str, Any] | str"])


def safe_tool(func: F) -> F:
    """Wrap an ADK tool function so malformed LLM tool-call arguments (missing
    keys, wrong types, etc.) return a structured error the agent can react to
    instead of raising, which otherwise crashes the entire agent turn."""

    @functools.wraps(func)
    def wrapper(*args: object, **kwargs: object) -> dict[str, Any] | str:
        try:
            return func(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 - must not crash the whole agent turn
            return {
                "error": f"{type(exc).__name__}: {exc}",
                "tool": func.__name__,
                "traceback": traceback.format_exc(limit=3),
            }

    return wrapper  # type: ignore[return-value]
