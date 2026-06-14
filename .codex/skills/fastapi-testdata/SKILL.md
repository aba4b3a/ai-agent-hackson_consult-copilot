<!-- Generated from .ai-common. Do not edit directly. -->

---
name: fastapi-testdata
description: Generate focused pytest fixtures and example payloads for FastAPI endpoints. Deterministic by default. No secrets, no real PII.
allowed-tools: Read Grep Bash
---

# FastAPI Test Data

Generates test data for FastAPI endpoints. Anchored to the OpenAPI spec and Pydantic models.

## Inputs

- Target endpoint(s) under `back/`.
- Pydantic models or OpenAPI spec for those endpoints.
- Existing fixtures (so generated data matches project conventions).

## Procedure

1. Read endpoint schemas and validation rules.
2. Cover the standard categories from `examples.md`:
   - Minimal valid payload.
   - Fully populated valid payload.
   - Missing required field.
   - Invalid type.
   - Boundary length / numeric value.
   - Unauthorized / forbidden request.
   - Duplicate / conflict case.
   - Idempotency retry case.
3. Match existing fixture patterns (factory style, parametrize, fixture composition).
4. Emit deterministic data; use randomness only when the test specifically exercises non-determinism.
5. Sanitize — no secrets, no production PII, no real customer identifiers.

## Output

- Fixture additions or new fixture files.
- Example request / response payloads.
- Coverage gaps the existing suite does not address.

## Guardrails

- No secrets, tokens, or real PII in fixtures.
- No network calls during fixture creation.
- Match existing pytest conventions; do not introduce a new style.
