"""create analyses table

Revision ID: 0001
Revises:
Create Date: 2026-11-11 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "analyses",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("resume_filename", sa.String(255), nullable=False),
        sa.Column("job_title", sa.String(200), nullable=True),
        sa.Column("compatibility_score", sa.Float(), nullable=False),
        sa.Column("semantic_score", sa.Float(), nullable=False),
        sa.Column("required_skills_score", sa.Float(), nullable=False),
        sa.Column("experience_score", sa.Float(), nullable=False),
        sa.Column("preferred_skills_score", sa.Float(), nullable=False),
        sa.Column("matched_skills", sa.JSON(), nullable=False),
        sa.Column("missing_skills", sa.JSON(), nullable=False),
        sa.Column("partial_skills", sa.JSON(), nullable=False),
        sa.Column("strengths", sa.JSON(), nullable=False),
        sa.Column("weaknesses", sa.JSON(), nullable=False),
        sa.Column("suggestions", sa.JSON(), nullable=False),
        sa.Column("overall_assessment", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

def downgrade() -> None:
    op.drop_table("analyses")
