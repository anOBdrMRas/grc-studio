"""Audits and audit findings with corrective actions (stage 3a, reviewed).

Revision ID: 0005
Revises: 0004
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('audits',
    sa.Column('id', sa.String(length=40), nullable=False),
    sa.Column('code', sa.String(length=40), nullable=False),
    sa.Column('title', sa.Text(), server_default='', nullable=False),
    sa.Column('description', sa.Text(), server_default='', nullable=False),
    sa.Column('audit_type', sa.Text(), server_default='', nullable=False),
    sa.Column('cert_stage', sa.Text(), server_default='', nullable=False),
    sa.Column('program_year', sa.Text(), server_default='', nullable=False),
    sa.Column('audit_status', sa.String(length=30), server_default='Planned', nullable=False),
    sa.Column('standards', postgresql.ARRAY(sa.String()), server_default='{}', nullable=False),
    sa.Column('objective', sa.Text(), server_default='', nullable=False),
    sa.Column('criteria', postgresql.ARRAY(sa.String()), server_default='{}', nullable=False),
    sa.Column('process_ids', postgresql.ARRAY(sa.String()), server_default='{}', nullable=False),
    sa.Column('audited_role_ids', postgresql.ARRAY(sa.String()), server_default='{}', nullable=False),
    sa.Column('sites', sa.Text(), server_default='', nullable=False),
    sa.Column('lead_auditor_user_id', sa.String(length=40), nullable=True),
    sa.Column('external_lead_auditor', sa.Text(), server_default='', nullable=False),
    sa.Column('team_user_ids', postgresql.ARRAY(sa.String()), server_default='{}', nullable=False),
    sa.Column('external_org', sa.Text(), server_default='', nullable=False),
    sa.Column('auditee_contact_user_id', sa.String(length=40), nullable=True),
    sa.Column('planned_date', sa.Date(), nullable=True),
    sa.Column('start_date', sa.Date(), nullable=True),
    sa.Column('end_date', sa.Date(), nullable=True),
    sa.Column('report_date', sa.Date(), nullable=True),
    sa.Column('report_document', sa.Text(), server_default='', nullable=False),
    sa.Column('certificate_valid_until', sa.Date(), nullable=True),
    sa.Column('next_audit_due', sa.Date(), nullable=True),
    sa.Column('verdict', sa.Text(), server_default='', nullable=False),
    sa.Column('summary', sa.Text(), server_default='', nullable=False),
    sa.Column('strengths', sa.Text(), server_default='', nullable=False),
    sa.Column('version', sa.Integer(), server_default='1', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_table('audit_findings',
    sa.Column('id', sa.String(length=40), nullable=False),
    sa.Column('code', sa.String(length=40), nullable=False),
    sa.Column('audit_id', sa.String(length=40), nullable=False),
    sa.Column('finding_type', sa.Text(), server_default='', nullable=False),
    sa.Column('clause', sa.Text(), server_default='', nullable=False),
    sa.Column('description', sa.Text(), server_default='', nullable=False),
    sa.Column('evidence', sa.Text(), server_default='', nullable=False),
    sa.Column('process_id', sa.String(length=40), nullable=True),
    sa.Column('element_id', sa.Text(), server_default='', nullable=False),
    sa.Column('risk_ids', postgresql.ARRAY(sa.String()), server_default='{}', nullable=False),
    sa.Column('control_ids', postgresql.ARRAY(sa.String()), server_default='{}', nullable=False),
    sa.Column('responsible_role_id', sa.String(length=40), nullable=True),
    sa.Column('responsible_user_id', sa.String(length=40), nullable=True),
    sa.Column('root_cause', sa.Text(), server_default='', nullable=False),
    sa.Column('corrective_action', sa.Text(), server_default='', nullable=False),
    sa.Column('due_date', sa.Date(), nullable=True),
    sa.Column('status', sa.String(length=30), server_default='Open', nullable=False),
    sa.Column('verified_at', sa.Date(), nullable=True),
    sa.Column('verified_by_user_id', sa.String(length=40), nullable=True),
    sa.Column('verification_result', sa.Text(), server_default='', nullable=False),
    sa.Column('version', sa.Integer(), server_default='1', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['audit_id'], ['audits.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_audit_findings_audit_id'), 'audit_findings', ['audit_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_audit_findings_audit_id'), table_name='audit_findings')
    op.drop_table('audit_findings')
    op.drop_table('audits')
