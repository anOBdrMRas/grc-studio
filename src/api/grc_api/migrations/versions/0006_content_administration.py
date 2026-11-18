"""Content administration: settings and values of custom fields (stage 3c, reviewed).

Revision ID: 0006
Revises: 0005
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('settings',
    sa.Column('key', sa.String(length=40), nullable=False),
    sa.Column('value', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
    sa.Column('version', sa.Integer(), server_default='1', nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('key')
    )
    op.add_column('audit_findings', sa.Column('custom', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False))
    op.add_column('audits', sa.Column('custom', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False))
    op.add_column('controls', sa.Column('custom', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False))
    op.add_column('kpis', sa.Column('custom', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False))
    op.add_column('mandates', sa.Column('custom', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False))
    op.add_column('opportunities', sa.Column('custom', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False))
    op.add_column('positions', sa.Column('custom', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False))
    op.add_column('processes', sa.Column('custom', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False))
    op.add_column('risks', sa.Column('custom', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False))
    op.add_column('roles', sa.Column('custom', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False))
    op.add_column('users', sa.Column('custom', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False))


def downgrade() -> None:
    op.drop_column('users', 'custom')
    op.drop_column('roles', 'custom')
    op.drop_column('risks', 'custom')
    op.drop_column('processes', 'custom')
    op.drop_column('positions', 'custom')
    op.drop_column('opportunities', 'custom')
    op.drop_column('mandates', 'custom')
    op.drop_column('kpis', 'custom')
    op.drop_column('controls', 'custom')
    op.drop_column('audits', 'custom')
    op.drop_column('audit_findings', 'custom')
    op.drop_table('settings')
