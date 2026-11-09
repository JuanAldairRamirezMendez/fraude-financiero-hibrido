from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime, timedelta

from app.core.errors import ConflictError, ServiceUnavailableError
from app.domain.transaction import Assessment
from app.repositories.protocols import FraudRepository, PersistedDecision
from app.schemas.api import AnalyzeRequest, AnalyzeResponse, ShapContribution, TopDriver
from app.services.inference_service import InferenceService


def _response_from_assessment(assessment: Assessment) -> AnalyzeResponse:
    return AnalyzeResponse(
        decision_id=assessment.decision_id,
        probability=assessment.probability,
        score=assessment.score,
        level=assessment.level,
        blocked=assessment.blocked,
        signals_triggered=assessment.signals_triggered,
        latency_ms=assessment.latency_ms,
        shap=[
            ShapContribution(
                feature=item.feature,
                impact=item.impact,
                direction=item.direction,
            )
            for item in assessment.shap
        ],
        top_driver=TopDriver(
            feature=assessment.top_driver_feature,
            impact_pct=assessment.top_driver_impact_pct,
        ),
        model_version=assessment.model_version,
        calibrated_threshold=0.0,
        idempotent_replay=False,
    )


class AnalyzeService:
    def __init__(
        self,
        inference: InferenceService,
        repository: FraudRepository,
        *,
        calibrated_threshold: float,
        idempotency_ttl_hours: int = 24,
    ) -> None:
        self._inference = inference
        self._repository = repository
        self._calibrated_threshold = calibrated_threshold
        self._ttl = timedelta(hours=idempotency_ttl_hours)

    def analyze(
        self,
        request: AnalyzeRequest,
        *,
        request_id: str,
        idempotency_key: str | None = None,
    ) -> AnalyzeResponse:
        if not self._inference.ready:
            raise ServiceUnavailableError("El modelo no está cargado.")

        payload = request.model_dump(by_alias=True, mode="json")
        request_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        if idempotency_key:
            existing = self._repository.get_idempotency(idempotency_key)
            if existing is not None:
                if existing.request_hash != request_hash:
                    raise ConflictError(
                        "La Idempotency-Key ya fue utilizada con otra carga útil.",
                        {"idempotencyKey": idempotency_key},
                    )
                replayed = AnalyzeResponse.model_validate(existing.response_payload)
                replayed.idempotent_replay = True
                return replayed

        assessment = self._inference.analyze(request)
        response = _response_from_assessment(assessment)
        response.calibrated_threshold = self._calibrated_threshold
        stored = response.model_dump(by_alias=True, mode="json")

        decision = PersistedDecision(
            id=str(uuid.uuid4()),
            decision_id=assessment.decision_id,
            probability=assessment.probability,
            score=assessment.score,
            level=assessment.level,
            blocked=assessment.blocked,
            transaction_amount=request.transaction_amount,
            model_version=assessment.model_version,
            request_payload=payload,
            response_payload=stored,
            request_id=request_id,
        )

        if idempotency_key:
            self._repository.save_decision_with_idempotency(
                decision,
                idempotency_key,
                request_hash,
                stored,
                datetime.now(UTC) + self._ttl,
            )
        else:
            self._repository.save_decision(decision)
        return response
