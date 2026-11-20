"""Work instructions and the description of process steps (stage 7).

Revision ID: 0008
Revises: 0007
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'work_instructions',
        sa.Column('id', sa.String(length=40), nullable=False),
        sa.Column('code', sa.String(length=40), nullable=False),
        sa.Column('title', sa.Text(), server_default='', nullable=False),
        sa.Column('description', sa.Text(), server_default='', nullable=False),
        sa.Column('owner_user_id', sa.String(length=40), nullable=True),
        sa.Column('content', sa.Text(), server_default='', nullable=False),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('custom', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='draft', nullable=False),
        sa.Column('doc_version', sa.String(length=20), server_default='0.1', nullable=False),
        sa.Column('next_review', sa.Date(), nullable=True),
        sa.Column('released', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
    )
    op.add_column('processes', sa.Column('step_notes', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False))


def downgrade() -> None:
    op.drop_column('processes', 'step_notes')
    op.drop_table('work_instructions')
