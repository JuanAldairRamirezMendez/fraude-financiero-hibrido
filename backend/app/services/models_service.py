from __future__ import annotations

from datetime import UTC, datetime

from app.domain.assessment import Alert
from app.repositories.protocols import FraudRepository
from app.schemas.api import ModelAlert, ModelHealth, ModelsResponse
from app.services.snapshot_service import SnapshotService


class ModelsService:
    def __init__(
        self,
        repository: FraudRepository,
        snapshot: SnapshotService,
        started_at: datetime,
    ) -> None:
        self._repository = repository
        self._snapshot = snapshot
        self._started_at = started_at

    def get(self) -> ModelsResponse:
        drift = self._snapshot.drift
        alerts = self._repository.list_alerts()
        if not alerts:
            alerts = [
                Alert(
                    id=str(item["id"]),
                    occurred_at=str(item["occurredAt"]),
                    model_id=str(item["modelId"]),
                    alert_type=str(item["alertType"]),
                    detail=str(item["detail"]),
                    status=str(item["status"]),
                )
                for item in self._snapshot.alerts
            ]
        critical = sum(1 for alert in alerts if alert.status == "UNACKNOWLEDGED")
        psi = drift.get("psi", 0.0)
        threshold = drift.get("psiThreshold", 0.2)
        uptime_seconds = max(0.0, (datetime.now(UTC) - self._started_at).total_seconds())
        uptime_pct = 99.99 if uptime_seconds > 0 else 100.0
        status = "degraded" if critical > 0 or psi > threshold else "stable"

        return ModelsResponse(
            health=ModelHealth(
                status=status,
                uptime_pct=uptime_pct,
                avg_latency_ms=self._repository.average_latency_ms(),
                critical_issues=critical,
                psi=psi,
                drift_shift_pct=drift.get("driftShiftPct", 0.0),
                psi_threshold=threshold,
                window_label=self._snapshot.window_label,
            ),
            alerts=[
                ModelAlert(
                    id=alert.id,
                    occurred_at=alert.occurred_at,
                    model_id=alert.model_id,
                    alert_type=alert.alert_type,
                    detail=alert.detail,
                    status=alert.status,  # type: ignore[arg-type]
                )
                for alert in alerts
            ],
            updated_at=self._snapshot.generated_at,
        )
