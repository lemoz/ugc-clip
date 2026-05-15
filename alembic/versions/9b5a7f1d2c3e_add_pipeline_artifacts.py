"""add pipeline artifacts

Revision ID: 9b5a7f1d2c3e
Revises: 644ccf36e0f4
Create Date: 2026-05-15 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "9b5a7f1d2c3e"
down_revision: str | None = "644ccf36e0f4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pipeline_artifacts",
        sa.Column("id", sa.TEXT(), nullable=False),
        sa.Column("project_id", sa.TEXT(), nullable=False),
        sa.Column("user_id", sa.TEXT(), nullable=False),
        sa.Column("stage_number", sa.Integer(), nullable=False),
        sa.Column("artifact_type", sa.String(length=100), nullable=False),
        sa.Column("content_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_pipeline_artifacts_project_id"), "pipeline_artifacts", ["project_id"])
    op.create_index(op.f("ix_pipeline_artifacts_user_id"), "pipeline_artifacts", ["user_id"])
    op.create_index(
        op.f("ix_pipeline_artifacts_stage_number"), "pipeline_artifacts", ["stage_number"]
    )
    op.create_index(
        op.f("ix_pipeline_artifacts_artifact_type"), "pipeline_artifacts", ["artifact_type"]
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_pipeline_artifacts_artifact_type"), table_name="pipeline_artifacts")
    op.drop_index(op.f("ix_pipeline_artifacts_stage_number"), table_name="pipeline_artifacts")
    op.drop_index(op.f("ix_pipeline_artifacts_user_id"), table_name="pipeline_artifacts")
    op.drop_index(op.f("ix_pipeline_artifacts_project_id"), table_name="pipeline_artifacts")
    op.drop_table("pipeline_artifacts")
