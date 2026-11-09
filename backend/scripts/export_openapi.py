#!/usr/bin/env python3
"""Freeze the OpenAPI contract consumed by the frontend type generator."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.settings import Settings  # noqa: E402
from app.main import create_app  # noqa: E402

OUTPUT = Path(__file__).resolve().parents[1] / "openapi.json"


def main() -> None:
    app = create_app(
        Settings(
            environment="test",
            fail_fast=False,
            expose_prometheus=False,
            database_url="sqlite:///:memory:",
        )
    )
    spec = app.openapi()
    spec["info"]["description"] = (
        "Contrato congelado de la API de fraude. El frontend genera sus tipos "
        "TypeScript desde este archivo con `pnpm gen:api`."
    )
    OUTPUT.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"OpenAPI written to {OUTPUT}")
    print(f"Paths: {len(spec['paths'])} · Schemas: {len(spec['components']['schemas'])}")


if __name__ == "__main__":
    main()
