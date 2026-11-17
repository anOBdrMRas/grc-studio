"""Controls (ICS), KPI with measurements, risk/opportunity/control/KPI links of process steps (stage 2b, reviewed).

Revision ID: 0003
Revises: 0002
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('controls',
    sa.Column('id', sa.String(length=40), nullable=False),
    sa.Column('code', sa.String(length=40), nullable=False),
    sa.Column('title', sa.Text(), server_default='', nullable=False),
    sa.Column('description', sa.Text(), server_default='', nullable=False),
    sa.Column('objective', sa.Text(), server_default='', nullable=False),
    sa.Column('key_control', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('control_type', sa.Text(), server_default='', nullable=False),
    sa.Column('automation', sa.Text(), server_default='', nullable=False),
    sa.Column('frequency', sa.Text(), server_default='', nullable=False),
    sa.Column('owner_role_id', sa.String(length=40), nullable=True),
    sa.Column('executor_role_id', sa.String(length=40), nullable=True),
    sa.Column('evidence', sa.Text(), server_default='', nullable=False),
    sa.Column('mitigates_risk_ids', postgresql.ARRAY(sa.String()), server_default='{}', nullable=False),
    sa.Column('annex_a', postgresql.ARRAY(sa.String()), server_default='{}', nullable=False),
    sa.Column('soa_applicable', sa.Text(), server_default='', nullable=False),
    sa.Column('implementation', sa.Text(), server_default='', nullable=False),
    sa.Column('soa_justification', sa.Text(), server_default='', nullable=False),
    sa.Column('test_method', sa.Text(), server_default='', nullable=False),
    sa.Column('design_effectiveness', sa.Text(), server_default='', nullable=False),
    sa.Column('operating_effectiveness', sa.Text(), server_default='', nullable=False),
    sa.Column('last_test', sa.Date(), nullable=True),
    sa.Column('next_test', sa.Date(), nullable=True),
    sa.Column('test_result', sa.Text(), server_default='', nullable=False),
    sa.Column('iso_refs', postgresql.ARRAY(sa.String()), server_default='{}', nullable=False),
    sa.Column('version', sa.Integer(), server_default='1', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_table('kpis',
    sa.Column('id', sa.String(length=40), nullable=False),
    sa.Column('code', sa.String(length=40), nullable=False),
    sa.Column('title', sa.Text(), server_default='', nullable=False),
    sa.Column('description', sa.Text(), server_default='', nullable=False),
    sa.Column('objective', sa.Text(), server_default='', nullable=False),
    sa.Column('formula', sa.Text(), server_default='', nullable=False),
    sa.Column('unit', sa.Text(), server_default='', nullable=False),
    sa.Column('direction', sa.String(length=10), server_default='higher', nullable=False),
    sa.Column('target', sa.Float(), server_default='0', nullable=False),
    sa.Column('warning', sa.Float(), server_default='0', nullable=False),
    sa.Column('critical', sa.Float(), server_default='0', nullable=False),
    sa.Column('frequency', sa.Text(), server_default='', nullable=False),
    sa.Column('data_source', sa.Text(), server_default='', nullable=False),
    sa.Column('owner_role_id', sa.String(length=40), nullable=True),
    sa.Column('evaluator_role_id', sa.String(length=40), nullable=True),
    sa.Column('iso_refs', postgresql.ARRAY(sa.String()), server_default='{}', nullable=False),
    sa.Column('version', sa.Integer(), server_default='1', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_table('kpi_measurements',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('kpi_id', sa.String(length=40), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('value', sa.Float(), nullable=False),
    sa.Column('by_user_id', sa.String(length=40), nullable=True),
    sa.ForeignKeyConstraint(['kpi_id'], ['kpis.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('kpi_id', 'date', name='uq_kpi_date')
    )
    op.create_index(op.f('ix_kpi_measurements_kpi_id'), 'kpi_measurements', ['kpi_id'], unique=False)
    op.create_table('step_links',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('process_id', sa.String(length=40), nullable=False),
    sa.Column('element_id', sa.String(length=120), nullable=False),
    sa.Column('kind', sa.String(length=20), nullable=False),
    sa.Column('target_id', sa.String(length=40), nullable=False),
    sa.ForeignKeyConstraint(['process_id'], ['processes.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('process_id', 'element_id', 'kind', 'target_id', name='uq_step_link')
    )
    op.create_index(op.f('ix_step_links_process_id'), 'step_links', ['process_id'], unique=False)
    op.create_index(op.f('ix_step_links_target_id'), 'step_links', ['target_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_step_links_target_id'), table_name='step_links')
    op.drop_index(op.f('ix_step_links_process_id'), table_name='step_links')
    op.drop_table('step_links')
    op.drop_index(op.f('ix_kpi_measurements_kpi_id'), table_name='kpi_measurements')
    op.drop_table('kpi_measurements')
    op.drop_table('kpis')
    op.drop_table('controls')
