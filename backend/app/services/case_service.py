from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.core.errors import ConflictError, NotFoundError
from app.domain.transaction import LEVEL_BY_ACTION
from app.repositories.protocols import FraudRepository, PersistedCase, PersistedDecision
from app.schemas.api import (
    CardContext,
    CaseCreateRequest,
    CaseDecision,
    CaseResponse,
    CaseUpdateRequest,
    ShapContribution,
)

THRESHOLD_FIELDS = ("decisionThreshold", "blockThreshold")


def new_case(decision_id: str, assigned_to: str | None = None) -> PersistedCase:
    now = datetime.now(UTC)
    return PersistedCase(
        id=str(uuid4()),
        case_number=f"CASE-{uuid4().hex[:12].upper()}",
        decision_id=decision_id,
        status="new",
        assigned_to=assigned_to,
        verdict=None,
        feedback_comment=None,
        created_at=now,
        updated_at=now,
        resolved_at=None,
        notes=(),
    )


def _decision_summary(decision: PersistedDecision | None) -> CaseDecision | None:
    if decision is None:
        return None
    stored = decision.response_payload or {}
    # Decisiones guardadas antes de este cambio no traen la acción: si se bloqueó, fue un bloqueo.
    action = stored.get("decision") or ("block" if decision.blocked else "approve")
    return CaseDecision(
        probability=decision.probability,
        score=decision.score,
        level=stored["level"] if stored.get("decision") else LEVEL_BY_ACTION[action],
        decision=action,
        model_version=decision.model_version,
        transaction={
            key: value
            for key, value in (decision.request_payload or {}).items()
            if key not in THRESHOLD_FIELDS
        },
        shap=[ShapContribution.model_validate(item) for item in stored.get("shap", [])],
        card=CardContext.model_validate(stored["card"]) if stored.get("card") else None,
    )


def _response(case: PersistedCase, decision: PersistedDecision | None = None) -> CaseResponse:
    return CaseResponse(
        id=case.id,
        case_number=case.case_number,
        decision_id=case.decision_id,
        status=case.status,  # type: ignore[arg-type]
        assigned_to=case.assigned_to,
        verdict=case.verdict,  # type: ignore[arg-type]
        feedback_comment=case.feedback_comment,
        created_at=case.created_at.isoformat(),
        updated_at=case.updated_at.isoformat(),
        resolved_at=case.resolved_at.isoformat() if case.resolved_at else None,
        notes=[
            {"author": note["author"], "content": note["content"], "createdAt": note["createdAt"]}
            for note in case.notes
        ],
        decision=_decision_summary(decision),
    )


class CaseService:
    def __init__(self, repository: FraudRepository) -> None:
        self._repository = repository

    def create(self, payload: CaseCreateRequest, actor: str) -> CaseResponse:
        decision = self._repository.get_decision(payload.decision_id)
        if decision is None:
            raise NotFoundError("La decisión indicada no existe.", {"decisionId": payload.decision_id})
        existing_case = next(
            (
                existing
                for existing in self._repository.list_cases()
                if existing.decision_id == payload.decision_id
            ),
            None,
        )
        if existing_case is not None:
            raise ConflictError(
                "Ya existe un caso para esta decisión.",
                {"caseId": existing_case.id},
            )

        case = new_case(payload.decision_id, payload.assigned_to)
        self._repository.create_case(case, actor)
        return _response(case, decision)

    def list(self, status: str | None, assigned_to: str | None) -> list[CaseResponse]:
        return [
            _response(case, self._repository.get_decision(case.decision_id))
            for case in self._repository.list_cases(status=status, assigned_to=assigned_to)
        ]

    def get(self, case_id: str) -> CaseResponse:
        case = self._repository.get_case(case_id)
        if case is None:
            raise NotFoundError("El caso no existe.", {"caseId": case_id})
        return _response(case, self._repository.get_decision(case.decision_id))

    def update(self, case_id: str, payload: CaseUpdateRequest, actor: str) -> CaseResponse:
        case = self._repository.get_case(case_id)
        if case is None:
            raise NotFoundError("El caso no existe.", {"caseId": case_id})

        status = payload.status or case.status
        verdict = payload.verdict if payload.verdict is not None else case.verdict
        if status == "resolved" and verdict is None:
            raise ConflictError("Un caso resuelto requiere un veredicto humano.")
        if verdict is not None and payload.status is None and case.status != "resolved":
            status = "resolved"
        now = datetime.now(UTC)
        updated = PersistedCase(
            id=case.id,
            case_number=case.case_number,
            decision_id=case.decision_id,
            status=status,
            assigned_to=payload.assigned_to if payload.assigned_to is not None else case.assigned_to,
            verdict=verdict,
            feedback_comment=(
                payload.feedback_comment
                if payload.feedback_comment is not None
                else case.feedback_comment
            ),
            created_at=case.created_at,
            updated_at=now,
            resolved_at=now if status == "resolved" else None,
            notes=case.notes,
        )
        self._repository.update_case(updated, actor)
        if payload.note:
            self._repository.add_case_note(case_id, actor, payload.note)
        return self.get(case_id)