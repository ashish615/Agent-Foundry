"""Add models table

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-28
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "models",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("slug", sa.Text, nullable=False, unique=True),
        sa.Column("display_name", sa.Text, nullable=False),
        sa.Column("provider", sa.Text, nullable=False),
        sa.Column("endpoint_url", sa.Text, nullable=True),
        sa.Column("context_window", sa.Integer, nullable=True),
        sa.Column("max_output_tokens", sa.Integer, nullable=True),
        sa.Column("input_cost_per_1m", sa.Numeric(12, 6), nullable=True),
        sa.Column("output_cost_per_1m", sa.Numeric(12, 6), nullable=True),
        sa.Column("capabilities", postgresql.ARRAY(sa.Text), nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("meta_json", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_models_slug", "models", ["slug"])
    op.create_index("idx_models_provider", "models", ["provider"])


def downgrade() -> None:
    op.drop_table("models")
