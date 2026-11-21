from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime, timedelta

from app.core.errors import ConflictError, ServiceUnavailableError
from app.domain.transaction import LEVEL_BY_ACTION, Assessment, decide
from app.repositories.protocols import FraudRepository, PersistedDecision
from app.schemas.api import (
    AnalyzeRequest,
    AnalyzeResponse,
    CardContext,
    ShapContribution,
    TopDriver,
)
from app.services.case_service import new_case
from app.services.inference_service import InferenceService

# Autor registrado cuando el sistema abre un caso por su cuenta.
SYSTEM_ACTOR = "sentinelai"


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
        card=(
            CardContext(
                previous_purchases=assessment.card.previous_purchases,
                seconds_since_previous=assessment.card.seconds_since_previous,
                average_amount=assessment.card.average_amount,
                purchases_1h=assessment.card.purchases_1h,
                amount_1h=assessment.card.amount_1h,
                purchases_24h=assessment.card.purchases_24h,
                amount_24h=assessment.card.amount_24h,
                customer_age=assessment.card.customer_age,
                customer_gender=assessment.card.customer_gender,
                city=assessment.card.city,
                state=assessment.card.state,
            )
            if assessment.card is not None
            else None
        ),
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
                stored = dict(existing.response_payload)
                # Respuestas guardadas antes de este cambio no traen la acción tomada.
                if "decision" not in stored:
                    stored["decision"] = "block" if stored.get("blocked") else "approve"
                    stored["level"] = LEVEL_BY_ACTION[stored["decision"]]
                replayed = AnalyzeResponse.model_validate(stored)
                replayed.idempotent_replay = True
                return replayed

        # Sin umbral explícito se usa el calibrado del modelo.
        if request.decision_threshold is None:
            request = request.model_copy(update={"decision_threshold": self._calibrated_threshold})
        decision_threshold = float(request.decision_threshold or 0.0)
        assessment = self._inference.analyze(request)
        response = _response_from_assessment(assessment)
        response.calibrated_threshold = self._calibrated_threshold

        # El nivel mostrado siempre coincide con la acción tomada.
        block_threshold = (
            request.block_threshold if request.block_threshold is not None else decision_threshold
        )
        action = decide(assessment.probability, decision_threshold, block_threshold)
        response.decision = action
        response.level = LEVEL_BY_ACTION[action]
        response.review_threshold = decision_threshold
        response.block_threshold = block_threshold

        # Toda transacción que no se aprueba abre un caso para que un analista la vea.
        case = new_case(assessment.decision_id) if action != "approve" else None
        if case is not None:
            response.case_id = case.id
            response.case_number = case.case_number

        stored = response.model_dump(by_alias=True, mode="json")

        decision = PersistedDecision(
            id=str(uuid.uuid4()),
            decision_id=assessment.decision_id,
            probability=assessment.probability,
            score=assessment.score,
            level=response.level,
            blocked=assessment.blocked,
            transaction_amount=request.amount,
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
        if case is not None:
            self._repository.create_case(case, SYSTEM_ACTOR)
        return response
