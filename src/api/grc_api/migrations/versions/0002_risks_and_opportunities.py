"""Risks and opportunities with approval workflow (stage 2a, reviewed).

Revision ID: 0002
Revises: 0001
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('opportunities',
    sa.Column('id', sa.String(length=40), nullable=False),
    sa.Column('code', sa.String(length=40), nullable=False),
    sa.Column('title', sa.Text(), server_default='', nullable=False),
    sa.Column('description', sa.Text(), server_default='', nullable=False),
    sa.Column('category', sa.Text(), server_default='', nullable=False),
    sa.Column('benefit', sa.Text(), server_default='', nullable=False),
    sa.Column('likelihood', sa.Integer(), server_default='0', nullable=False),
    sa.Column('benefit_score', sa.Integer(), server_default='0', nullable=False),
    sa.Column('measures', sa.Text(), server_default='', nullable=False),
    sa.Column('owner_role_id', sa.String(length=40), nullable=True),
    sa.Column('progress_status', sa.Text(), server_default='', nullable=False),
    sa.Column('iso_refs', postgresql.ARRAY(sa.String()), server_default='{}', nullable=False),
    sa.Column('created_by_user_id', sa.String(length=40), nullable=True),
    sa.Column('version', sa.Integer(), server_default='1', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('status', sa.String(length=20), server_default='draft', nullable=False),
    sa.Column('doc_version', sa.String(length=20), server_default='0.1', nullable=False),
    sa.Column('next_review', sa.Date(), nullable=True),
    sa.Column('released', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_table('risks',
    sa.Column('id', sa.String(length=40), nullable=False),
    sa.Column('code', sa.String(length=40), nullable=False),
    sa.Column('title', sa.Text(), server_default='', nullable=False),
    sa.Column('description', sa.Text(), server_default='', nullable=False),
    sa.Column('department', sa.Text(), server_default='', nullable=False),
    sa.Column('category', sa.Text(), server_default='', nullable=False),
    sa.Column('activity', sa.Text(), server_default='', nullable=False),
    sa.Column('process_ids', postgresql.ARRAY(sa.String()), server_default='{}', nullable=False),
    sa.Column('compliance_obligation', sa.Text(), server_default='', nullable=False),
    sa.Column('cause', sa.Text(), server_default='', nullable=False),
    sa.Column('owner_user_id', sa.String(length=40), nullable=True),
    sa.Column('treatment_status', sa.Text(), server_default='', nullable=False),
    sa.Column('consequence_type', sa.Text(), server_default='', nullable=False),
    sa.Column('likelihood', sa.Integer(), server_default='0', nullable=False),
    sa.Column('likelihood_reason', sa.Text(), server_default='', nullable=False),
    sa.Column('impact', sa.Integer(), server_default='0', nullable=False),
    sa.Column('impact_reason', sa.Text(), server_default='', nullable=False),
    sa.Column('treatment', sa.Text(), server_default='', nullable=False),
    sa.Column('actions', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
    sa.Column('assessment_reason', sa.Text(), server_default='', nullable=False),
    sa.Column('last_assessment', sa.Date(), nullable=True),
    sa.Column('review_note', sa.Text(), server_default='', nullable=False),
    sa.Column('affected_assets', sa.Text(), server_default='', nullable=False),
    sa.Column('protection_goals', postgresql.ARRAY(sa.String()), server_default='{}', nullable=False),
    sa.Column('interested_parties', sa.Text(), server_default='', nullable=False),
    sa.Column('entity', sa.Text(), server_default='', nullable=False),
    sa.Column('source_ref', sa.Text(), server_default='', nullable=False),
    sa.Column('iso_refs', postgresql.ARRAY(sa.String()), server_default='{}', nullable=False),
    sa.Column('created_by_user_id', sa.String(length=40), nullable=True),
    sa.Column('version', sa.Integer(), server_default='1', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('status', sa.String(length=20), server_default='draft', nullable=False),
    sa.Column('doc_version', sa.String(length=20), server_default='0.1', nullable=False),
    sa.Column('next_review', sa.Date(), nullable=True),
    sa.Column('released', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )


def downgrade() -> None:
    op.drop_table('risks')
    op.drop_table('opportunities')
