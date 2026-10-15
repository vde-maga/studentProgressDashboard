"""add password_hash to users

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-15

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Added with a temporary default so existing rows are backfilled, then the
    # default is dropped: the application must always supply a hash.
    op.add_column(
        "users",
        sa.Column(
            "password_hash",
            sa.String(length=255),
            nullable=False,
            server_default="",
        ),
    )
    op.alter_column("users", "password_hash", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "password_hash")
