"""Add fraud cases, notes and analyst feedback.

Revision ID: 0003_fraud_cases
Revises: 0002_auth
Create Date: 2026-11-09
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_fraud_cases"
down_revision: str | None = "0002_auth"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "fraud_cases",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("case_number", sa.String(length=40), nullable=False),
        sa.Column("decision_id", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("assigned_to", sa.String(length=120), nullable=True),
        sa.Column("verdict", sa.String(length=24), nullable=True),
        sa.Column("feedback_comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["decision_id"], ["decisions.decision_id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_number"),
        sa.UniqueConstraint("decision_id"),
    )
    op.create_index("ix_fraud_cases_status", "fraud_cases", ["status"])
    op.create_index("ix_fraud_cases_assigned_to", "fraud_cases", ["assigned_to"])
    op.create_index("ix_fraud_cases_updated_at", "fraud_cases", ["updated_at"])
    op.create_table(
        "fraud_case_notes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("case_id", sa.String(length=36), nullable=False),
        sa.Column("author", sa.String(length=120), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["fraud_cases.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_fraud_case_notes_case_id", "fraud_case_notes", ["case_id"])


def downgrade() -> None:
    op.drop_index("ix_fraud_case_notes_case_id", table_name="fraud_case_notes")
    op.drop_table("fraud_case_notes")
    op.drop_index("ix_fraud_cases_updated_at", table_name="fraud_cases")
    op.drop_index("ix_fraud_cases_assigned_to", table_name="fraud_cases")
    op.drop_index("ix_fraud_cases_status", table_name="fraud_cases")
    op.drop_table("fraud_cases")