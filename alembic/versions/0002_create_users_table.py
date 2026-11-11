"""create users table and add user_id to analyses

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-12 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # 2. Add user_id column to analyses table
    op.add_column(
        "analyses",
        sa.Column("user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    )
    op.create_index("ix_analyses_user_id", "analyses", ["user_id"], unique=False)

def downgrade() -> None:
    op.drop_index("ix_analyses_user_id", table_name="analyses")
    op.drop_column("analyses", "user_id")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
