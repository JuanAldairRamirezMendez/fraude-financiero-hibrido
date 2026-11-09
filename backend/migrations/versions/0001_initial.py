"""Initial fraud API schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-11-09
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "decisions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("decision_id", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("probability", sa.Float(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("level", sa.String(length=12), nullable=False),
        sa.Column("blocked", sa.Boolean(), nullable=False),
        sa.Column("transaction_amount", sa.Float(), nullable=False),
        sa.Column("model_version", sa.String(length=80), nullable=False),
        sa.Column("request_payload", sa.JSON(), nullable=False),
        sa.Column("response_payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("decision_id"),
    )
    op.create_index("ix_decisions_created_at", "decisions", ["created_at"])
    op.create_index("ix_decisions_level", "decisions", ["level"])
    op.create_index("ix_decisions_blocked", "decisions", ["blocked"])

    op.create_table(
        "idempotency_keys",
        sa.Column("key", sa.String(length=120), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("response_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )
    op.create_index("ix_idempotency_expires_at", "idempotency_keys", ["expires_at"])

    op.create_table(
        "alerts",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("model_id", sa.String(length=80), nullable=False),
        sa.Column("alert_type", sa.String(length=40), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_alerts_occurred_at", "alerts", ["occurred_at"])
    op.create_index("ix_alerts_status", "alerts", ["status"])

    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_log_created_at", "audit_log", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_log_created_at", table_name="audit_log")
    op.drop_table("audit_log")
    op.drop_index("ix_alerts_status", table_name="alerts")
    op.drop_index("ix_alerts_occurred_at", table_name="alerts")
    op.drop_table("alerts")
    op.drop_index("ix_idempotency_expires_at", table_name="idempotency_keys")
    op.drop_table("idempotency_keys")
    op.drop_index("ix_decisions_blocked", table_name="decisions")
    op.drop_index("ix_decisions_level", table_name="decisions")
    op.drop_index("ix_decisions_created_at", table_name="decisions")
    op.drop_table("decisions")
