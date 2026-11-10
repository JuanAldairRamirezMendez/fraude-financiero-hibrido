from app.db.database import Database
from app.repositories.protocols import PersistedDecision
from app.repositories.sql_repository import SqlFraudRepository


def test_decision_is_written_to_outbox_and_can_be_published(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = Database(f"sqlite:///{tmp_path / 'outbox.db'}")
    database.create_all()
    repository = SqlFraudRepository(database)
    decision = PersistedDecision(
        id="decision-row-1",
        decision_id="DEC-OUTBOX-0001",
        probability=0.91,
        score=91,
        level="high",
        blocked=True,
        transaction_amount=9000.0,
        model_version="model-1",
        request_payload={"transactionAmount": 9000.0},
        response_payload={"decisionId": "DEC-OUTBOX-0001", "score": 91},
        request_id="request-1",
    )

    repository.save_decision(decision)

    pending = repository.list_pending_events()
    assert len(pending) == 1
    assert pending[0].event_type == "decision.created"
    assert pending[0].aggregate_id == decision.decision_id
    assert pending[0].payload["score"] == decision.score

    repository.mark_event_published(pending[0].id)

    assert repository.list_pending_events() == []
    database.dispose()