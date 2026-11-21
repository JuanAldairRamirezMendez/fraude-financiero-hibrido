from __future__ import annotations

from app.domain.transaction import risk_level
from app.services.snapshot_service import OverviewFilters


def test_analyze_returns_contract(client, valid_payload):  # type: ignore[no-untyped-def]
    response = client.post("/api/v1/analyze", json=valid_payload)
    assert response.status_code == 200
    body = response.json()
    assert body["decisionId"].startswith("DEC-")
    assert body["score"] == 91
    assert body["level"] == "high"
    assert body["blocked"] is True
    assert len(body["shap"]) == 2
    assert body["topDriver"]["feature"] == "monto"
    assert body["modelVersion"] == "fake-xgboost-1.0.0"
    assert response.headers["X-Request-ID"]
    assert response.headers["Cache-Control"] == "no-store"


def test_analyze_idempotent_replay_and_conflict(client, valid_payload):  # type: ignore[no-untyped-def]
    headers = {"Idempotency-Key": "same-key"}
    first = client.post("/api/v1/analyze", json=valid_payload, headers=headers)
    second = client.post("/api/v1/analyze", json=valid_payload, headers=headers)
    assert first.status_code == second.status_code == 200
    assert second.json()["idempotentReplay"] is True
    assert second.json()["decisionId"] == first.json()["decisionId"]

    changed = {**valid_payload, "amount": 100}
    conflict = client.post("/api/v1/analyze", json=changed, headers=headers)
    assert conflict.status_code == 409
    assert conflict.json()["code"] == "conflict"


def test_case_lifecycle_and_human_feedback(client, valid_payload):  # type: ignore[no-untyped-def]
    # Una transacción aprobada no abre caso solo; aquí el analista lo abre a mano.
    approved = {**valid_payload, "amount": 100}
    analyzed = client.post("/api/v1/analyze", json=approved).json()
    decision_id = analyzed["decisionId"]

    created = client.post(
        "/api/v1/cases",
        json={"decisionId": decision_id, "assignedTo": "analyst@example.com"},
    )
    assert created.status_code == 201
    case = created.json()
    assert case["status"] == "new"
    assert case["decisionId"] == decision_id

    duplicate = client.post("/api/v1/cases", json={"decisionId": decision_id})
    assert duplicate.status_code == 409

    updated = client.patch(
        f"/api/v1/cases/{case['id']}",
        json={
            "status": "resolved",
            "verdict": "confirmed_fraud",
            "feedbackComment": "La revisión confirmó el patrón de riesgo.",
            "note": "Se validó con evidencia del comercio.",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "resolved"
    assert updated.json()["verdict"] == "confirmed_fraud"
    assert len(updated.json()["notes"]) == 1


def test_case_requires_verdict_to_resolve(client, valid_payload):  # type: ignore[no-untyped-def]
    approved = {**valid_payload, "amount": 100}
    decision_id = client.post("/api/v1/analyze", json=approved).json()["decisionId"]
    case = client.post("/api/v1/cases", json={"decisionId": decision_id}).json()
    response = client.patch(f"/api/v1/cases/{case['id']}", json={"status": "resolved"})
    assert response.status_code == 409
    assert response.json()["code"] == "conflict"


def test_analyze_rejects_extra_fields(client, valid_payload):  # type: ignore[no-untyped-def]
    response = client.post(
        "/api/v1/analyze", json={**valid_payload, "unexpected": "value"}
    )
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "validation_error"
    assert body["requestId"]
    assert any(item["field"] == "unexpected" for item in body["details"])


def test_analyze_rejects_out_of_range(client, valid_payload):  # type: ignore[no-untyped-def]
    response = client.post(
        "/api/v1/analyze", json={**valid_payload, "merchantDistanceKm": -1}
    )
    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_metadata_contract(client):  # type: ignore[no-untyped-def]
    response = client.get("/api/v1/metadata")
    assert response.status_code == 200
    body = response.json()
    assert body["model"]["featureCount"] == 46
    assert body["decisionThreshold"]["default"] == 0.5
    assert body["fields"]
    assert response.headers["ETag"].startswith('"')
    assert "max-age=60" in response.headers["Cache-Control"]


def test_overview_pagination_and_filters(client):  # type: ignore[no-untyped-def]
    response = client.get("/api/v1/overview?pageSize=2&page=1")
    assert response.status_code == 200
    body = response.json()
    assert body["transactions"]["total"] == 4
    assert body["transactions"]["totalPages"] == 2
    assert len(body["transactions"]["items"]) == 2
    assert body["transactions"]["items"][0]["score"] == 96

    filtered = client.get("/api/v1/overview?decision=Flagged&pageSize=10")
    assert filtered.json()["transactions"]["total"] == 2

    searched = client.get("/api/v1/overview?q=cust-3")
    assert searched.json()["transactions"]["total"] == 1
    assert searched.json()["transactions"]["items"][0]["customerId"] == "CUST-3"


def test_overview_rejects_invalid_page_size(client):  # type: ignore[no-untyped-def]
    response = client.get("/api/v1/overview?pageSize=500")
    assert response.status_code == 422


def test_models_health_and_alerts(client):  # type: ignore[no-untyped-def]
    response = client.get("/api/v1/models")
    assert response.status_code == 200
    body = response.json()
    assert body["health"]["status"] == "stable"
    assert body["health"]["avgLatencyMs"] == 12.0
    assert body["alerts"][0]["id"] == "ALT-TEST-1"


def test_health_reports_degraded_without_artifacts(client):  # type: ignore[no-untyped-def]
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["checks"]["modelLoaded"] is False
    assert body["status"] == "degraded"
    assert body["requestId"]

    liveness = client.get("/api/v1/health/live")
    assert liveness.status_code == 200

    readiness = client.get("/api/v1/health/ready")
    assert readiness.status_code == 503


def test_security_headers_and_request_id(client):  # type: ignore[no-untyped-def]
    response = client.get("/api/v1/metadata", headers={"X-Request-ID": "client-id-123"})
    assert response.headers["X-Request-ID"] == "client-id-123"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"


def test_unknown_api_route_returns_envelope(client):  # type: ignore[no-untyped-def]
    response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "not_found"
    assert body["requestId"]


def test_snapshot_filters_object() -> None:
    filters = OverviewFilters(q="abc", min_score=10, max_score=90)
    assert filters.q == "abc"
    assert filters.min_score == 10


def test_risk_level_matches_api_contract() -> None:
    assert risk_level(75) == "high"


def test_analyze_accepts_real_dataset_ranges(client, valid_payload):  # type: ignore[no-untyped-def]
    """El monto máximo del dataset Sparkov es 28 948.90; la hora puede venir con zona."""
    payload = {**valid_payload, "amount": 28_948.9, "transactionTime": "2020-10-15T22:23:52Z"}
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200


def test_analyze_rejects_invalid_transactions(client, valid_payload):  # type: ignore[no-untyped-def]
    for field, value in [
        ("amount", 50_001),
        ("amount", 0),
        ("category", "gambling"),
        ("cardId", "4532-1234"),
        ("transactionTime", "ayer"),
    ]:
        response = client.post("/api/v1/analyze", json={**valid_payload, field: value})
        assert response.status_code == 422, field


def test_analyze_uses_calibrated_threshold_by_default(client, valid_payload):  # type: ignore[no-untyped-def]
    payload = {key: value for key, value in valid_payload.items() if key != "decisionThreshold"}
    body = client.post("/api/v1/analyze", json=payload).json()
    assert body["reviewThreshold"] == 0.25
    assert body["decision"] == "block"


def test_policy_approves_or_blocks_and_opens_case(client, valid_payload):  # type: ignore[no-untyped-def]
    # La analítica falsa devuelve 0.91 para montos >= 3000 y 0.12 para el resto.
    approved = client.post("/api/v1/analyze", json={**valid_payload, "amount": 100}).json()
    assert approved["decision"] == "approve"
    assert approved["level"] == "low"
    assert approved["blocked"] is False
    assert approved["caseId"] is None

    blocked = client.post("/api/v1/analyze", json=valid_payload).json()
    assert blocked["decision"] == "block"
    assert blocked["level"] == "high"
    assert blocked["blocked"] is True
    assert blocked["reviewThreshold"] == blocked["blockThreshold"] == 0.5
    assert blocked["caseNumber"].startswith("CASE-")


def test_optional_block_threshold_enables_review_band(client, valid_payload):  # type: ignore[no-untyped-def]
    review = client.post(
        "/api/v1/analyze", json={**valid_payload, "blockThreshold": 0.95}
    ).json()
    assert review["decision"] == "review"
    assert review["level"] == "medium"
    assert review["blocked"] is True
    assert review["reviewThreshold"] == 0.5
    assert review["blockThreshold"] == 0.95
    assert review["caseNumber"].startswith("CASE-")


def test_blocked_decision_opens_case_with_model_context(client, valid_payload):  # type: ignore[no-untyped-def]
    review = client.post("/api/v1/analyze", json=valid_payload).json()

    case = client.get(f"/api/v1/cases/{review['caseId']}").json()
    assert case["status"] == "new"
    assert case["decisionId"] == review["decisionId"]
    assert case["decision"]["decision"] == "block"
    assert case["decision"]["score"] == 91
    assert case["decision"]["transaction"]["amount"] == 9000
    assert "decisionThreshold" not in case["decision"]["transaction"]
    assert case["decision"]["shap"][0]["feature"] == "monto"

    listed = client.get("/api/v1/cases").json()
    assert [item["id"] for item in listed["items"]] == [review["caseId"]]

    duplicate = client.post("/api/v1/cases", json={"decisionId": review["decisionId"]})
    assert duplicate.status_code == 409


def test_analyze_rejects_block_threshold_below_review(client, valid_payload):  # type: ignore[no-untyped-def]
    response = client.post(
        "/api/v1/analyze",
        json={**valid_payload, "decisionThreshold": 0.6, "blockThreshold": 0.4},
    )
    assert response.status_code == 422


def test_me_returns_local_user_when_auth_is_disabled(client):  # type: ignore[no-untyped-def]
    status = client.get("/api/v1/auth/me").json()
    assert status["authenticated"] is True
    assert status["user"]["username"] == "analista"
