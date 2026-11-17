"""Delegations and powers of attorney with their own grant/accept approval (stage 2c, reviewed).

Revision ID: 0004
Revises: 0003
"""

from alembic import op
import sqlalchemy as sa


revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('mandates',
    sa.Column('id', sa.String(length=40), nullable=False),
    sa.Column('code', sa.String(length=40), nullable=False),
    sa.Column('title', sa.Text(), server_default='', nullable=False),
    sa.Column('description', sa.Text(), server_default='', nullable=False),
    sa.Column('mandate_type', sa.Text(), server_default='', nullable=False),
    sa.Column('legal_basis', sa.Text(), server_default='', nullable=False),
    sa.Column('recipient_user_id', sa.String(length=40), nullable=True),
    sa.Column('granted_by_user_id', sa.String(length=40), nullable=True),
    sa.Column('granted_by_body', sa.Text(), server_default='', nullable=False),
    sa.Column('role_id', sa.String(length=40), nullable=True),
    sa.Column('position_id', sa.String(length=40), nullable=True),
    sa.Column('scope', sa.Text(), server_default='', nullable=False),
    sa.Column('powers', sa.Text(), server_default='', nullable=False),
    sa.Column('budget', sa.Text(), server_default='', nullable=False),
    sa.Column('amount_limit', sa.Integer(), server_default='0', nullable=False),
    sa.Column('representation', sa.Text(), server_default='', nullable=False),
    sa.Column('sub_delegation_allowed', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('status', sa.String(length=20), server_default='draft', nullable=False),
    sa.Column('valid_from', sa.Date(), nullable=True),
    sa.Column('valid_until', sa.Date(), nullable=True),
    sa.Column('revoked_at', sa.Date(), nullable=True),
    sa.Column('document', sa.Text(), server_default='', nullable=False),
    sa.Column('accepted_at', sa.Date(), nullable=True),
    sa.Column('register_entry', sa.Text(), server_default='', nullable=False),
    sa.Column('registered_at', sa.Date(), nullable=True),
    sa.Column('supervision', sa.Text(), server_default='', nullable=False),
    sa.Column('supervision_frequency', sa.Text(), server_default='', nullable=False),
    sa.Column('last_supervision', sa.Date(), nullable=True),
    sa.Column('next_supervision', sa.Date(), nullable=True),
    sa.Column('version', sa.Integer(), server_default='1', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_mandates_recipient_user_id'), 'mandates', ['recipient_user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_mandates_recipient_user_id'), table_name='mandates')
    op.drop_table('mandates')
