from __future__ import annotations

import json
from pathlib import Path

from openapi_spec_validator import validate_spec


def test_openapi_spec_is_valid(client):  # type: ignore[no-untyped-def]
    spec = client.get("/api/v1/openapi.json").json()
    validate_spec(spec)
    paths = spec["paths"]
    for path in ["/api/v1/health", "/api/v1/metadata", "/api/v1/analyze", "/api/v1/overview", "/api/v1/models"]:
        assert path in paths


def test_openapi_has_error_envelope(client):  # type: ignore[no-untyped-def]
    spec = client.get("/api/v1/openapi.json").json()
    schemas = spec["components"]["schemas"]
    assert "AnalyzeRequest" in schemas
    assert "AnalyzeResponse" in schemas
    assert "OverviewResponse" in schemas
    assert "ErrorResponse" in schemas
    assert "Idempotency-Key" in json.dumps(spec)


def test_frozen_openapi_matches_application(client):  # type: ignore[no-untyped-def]
    frozen_path = Path(__file__).resolve().parents[2] / "openapi.json"
    if not frozen_path.exists():
        return
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    current = client.get("/api/v1/openapi.json").json()
    assert frozen["paths"].keys() == current["paths"].keys()
    assert frozen["components"]["schemas"].keys() == current["components"]["schemas"].keys()
