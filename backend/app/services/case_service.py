from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.core.errors import ConflictError, NotFoundError
from app.repositories.protocols import FraudRepository, PersistedCase
from app.schemas.api import CaseCreateRequest, CaseResponse, CaseUpdateRequest


def _response(case: PersistedCase) -> CaseResponse:
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

        now = datetime.now(UTC)
        case = PersistedCase(
            id=str(uuid4()),
            case_number=f"CASE-{uuid4().hex[:12].upper()}",
            decision_id=payload.decision_id,
            status="new",
            assigned_to=payload.assigned_to,
            verdict=None,
            feedback_comment=None,
            created_at=now,
            updated_at=now,
            resolved_at=None,
            notes=(),
        )
        self._repository.create_case(case, actor)
        return _response(case)

    def list(self, status: str | None, assigned_to: str | None) -> list[CaseResponse]:
        return [_response(case) for case in self._repository.list_cases(status=status, assigned_to=assigned_to)]

    def get(self, case_id: str) -> CaseResponse:
        case = self._repository.get_case(case_id)
        if case is None:
            raise NotFoundError("El caso no existe.", {"caseId": case_id})
        return _response(case)

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