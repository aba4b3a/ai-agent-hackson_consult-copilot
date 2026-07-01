"""Shared google-genai client construction.

Centralizes the Developer API vs Vertex AI backend choice so every agent uses
the same configuration. Imported lazily by callers so mock mode and tests do
not require the SDK to be installed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.config import settings

if TYPE_CHECKING:
    from google.genai import Client


def build_client() -> Client:
    from google import genai

    if settings.use_vertexai:
        # Vertex AI backend (aiplatform.googleapis.com), express mode with an
        # API key. Standard project/location + ADC setups can override here.
        return genai.Client(vertexai=True, api_key=settings.gemini_api_key)
    return genai.Client(api_key=settings.gemini_api_key)
