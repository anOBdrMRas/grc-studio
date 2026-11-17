"""Initial schema: organisation, processes, workflow, audit log, sessions (reviewed).

Revision ID: 0001
Revises: 
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('audit_log',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('actor_id', sa.String(length=80), nullable=False),
    sa.Column('action', sa.String(length=30), nullable=False),
    sa.Column('kind', sa.String(length=30), nullable=False),
    sa.Column('entity_id', sa.String(length=80), nullable=False),
    sa.Column('changes', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
    sa.Column('note', sa.Text(), server_default='', nullable=False),
    sa.Column('vars', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_target', 'audit_log', ['kind', 'entity_id'], unique=False)
    op.create_table('positions',
    sa.Column('id', sa.String(length=40), nullable=False),
    sa.Column('code', sa.String(length=40), nullable=False),
    sa.Column('title', sa.Text(), server_default='', nullable=False),
    sa.Column('description', sa.Text(), server_default='', nullable=False),
    sa.Column('org_unit', sa.Text(), server_default='', nullable=False),
    sa.Column('is_manager', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('headcount', sa.Integer(), server_default='1', nullable=False),
    sa.Column('location', sa.Text(), server_default='', nullable=False),
    sa.Column('purpose', sa.Text(), server_default='', nullable=False),
    sa.Column('tasks', sa.Text(), server_default='', nullable=False),
    sa.Column('authorities', sa.Text(), server_default='', nullable=False),
    sa.Column('signing_authority', sa.Text(), server_default='', nullable=False),
    sa.Column('approval_limit', sa.Integer(), server_default='0', nullable=False),
    sa.Column('qualification', sa.Text(), server_default='', nullable=False),
    sa.Column('experience', sa.Text(), server_default='', nullable=False),
    sa.Column('competencies', sa.Text(), server_default='', nullable=False),
    sa.Column('trainings', sa.Text(), server_default='', nullable=False),
    sa.Column('screening_required', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('nda_required', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('reports_to_disciplinary_id', sa.String(length=40), nullable=True),
    sa.Column('reports_to_functional_id', sa.String(length=40), nullable=True),
    sa.Column('deputy_position_id', sa.String(length=40), nullable=True),
    sa.Column('deputy_inducted', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('iso_refs', postgresql.ARRAY(sa.String()), server_default='{}', nullable=False),
    sa.Column('last_review', sa.Date(), nullable=True),
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
    op.create_table('processes',
    sa.Column('id', sa.String(length=40), nullable=False),
    sa.Column('code', sa.String(length=40), nullable=False),
    sa.Column('title', sa.Text(), server_default='', nullable=False),
    sa.Column('description', sa.Text(), server_default='', nullable=False),
    sa.Column('category', sa.Text(), server_default='', nullable=False),
    sa.Column('owner_role_id', sa.String(length=40), nullable=True),
    sa.Column('area', sa.Text(), server_default='', nullable=False),
    sa.Column('landscape_order', sa.Integer(), server_default='0', nullable=False),
    sa.Column('inputs', sa.Text(), server_default='', nullable=False),
    sa.Column('outputs', sa.Text(), server_default='', nullable=False),
    sa.Column('resources', sa.Text(), server_default='', nullable=False),
    sa.Column('standards', postgresql.ARRAY(sa.String()), server_default='{}', nullable=False),
    sa.Column('xml', sa.Text(), server_default='', nullable=False),
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
    op.create_table('roles',
    sa.Column('id', sa.String(length=40), nullable=False),
    sa.Column('code', sa.String(length=40), nullable=False),
    sa.Column('title', sa.Text(), server_default='', nullable=False),
    sa.Column('description', sa.Text(), server_default='', nullable=False),
    sa.Column('role_type', sa.Text(), server_default='', nullable=False),
    sa.Column('org_unit', sa.Text(), server_default='', nullable=False),
    sa.Column('mandatory', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('compliance_relevant', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('role_owner_user_id', sa.String(length=40), nullable=True),
    sa.Column('responsibilities', sa.Text(), server_default='', nullable=False),
    sa.Column('authorities', sa.Text(), server_default='', nullable=False),
    sa.Column('competencies', sa.Text(), server_default='', nullable=False),
    sa.Column('trainings', sa.Text(), server_default='', nullable=False),
    sa.Column('incompatible_role_ids', postgresql.ARRAY(sa.String()), server_default='{}', nullable=False),
    sa.Column('required_mandate', sa.Text(), server_default='', nullable=False),
    sa.Column('written_form', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('authority_notice', sa.Text(), server_default='', nullable=False),
    sa.Column('iso_refs', postgresql.ARRAY(sa.String()), server_default='{}', nullable=False),
    sa.Column('last_review', sa.Date(), nullable=True),
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
    op.create_table('users',
    sa.Column('id', sa.String(length=40), nullable=False),
    sa.Column('code', sa.String(length=40), nullable=False),
    sa.Column('last_name', sa.Text(), server_default='', nullable=False),
    sa.Column('first_name', sa.Text(), server_default='', nullable=False),
    sa.Column('display_name', sa.Text(), server_default='', nullable=False),
    sa.Column('division', sa.Text(), server_default='', nullable=False),
    sa.Column('department', sa.Text(), server_default='', nullable=False),
    sa.Column('position_id', sa.String(length=40), nullable=True),
    sa.Column('position_since', sa.Date(), nullable=True),
    sa.Column('description', sa.Text(), server_default='', nullable=False),
    sa.Column('system_roles', postgresql.ARRAY(sa.String()), server_default='{}', nullable=False),
    sa.Column('status', sa.String(length=20), server_default='active', nullable=False),
    sa.Column('email', sa.Text(), server_default='', nullable=False),
    sa.Column('username', sa.String(length=80), nullable=True),
    sa.Column('password_hash', sa.Text(), nullable=True),
    sa.Column('failed_logins', sa.Integer(), server_default='0', nullable=False),
    sa.Column('version', sa.Integer(), server_default='1', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code'),
    sa.UniqueConstraint('username')
    )
    op.create_table('workflow_entries',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('kind', sa.String(length=30), nullable=False),
    sa.Column('entity_id', sa.String(length=80), nullable=False),
    sa.Column('step', sa.String(length=20), nullable=False),
    sa.Column('by_user_id', sa.String(length=40), nullable=False),
    sa.Column('at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('comment', sa.Text(), server_default='', nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_workflow_target', 'workflow_entries', ['kind', 'entity_id'], unique=False)
    op.create_table('position_roles',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('position_id', sa.String(length=40), nullable=False),
    sa.Column('role_id', sa.String(length=40), nullable=False),
    sa.Column('comment', sa.Text(), server_default='', nullable=False),
    sa.Column('sort', sa.Integer(), server_default='0', nullable=False),
    sa.ForeignKeyConstraint(['position_id'], ['positions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_position_roles_position_id'), 'position_roles', ['position_id'], unique=False)
    op.create_index(op.f('ix_position_roles_role_id'), 'position_roles', ['role_id'], unique=False)
    op.create_table('sessions',
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('user_id', sa.String(length=40), nullable=False),
    sa.Column('csrf_token', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('token_hash')
    )
    op.create_index(op.f('ix_sessions_user_id'), 'sessions', ['user_id'], unique=False)
    op.create_table('step_assignments',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('process_id', sa.String(length=40), nullable=False),
    sa.Column('element_id', sa.String(length=120), nullable=False),
    sa.Column('role_id', sa.String(length=40), nullable=False),
    sa.Column('raci', sa.String(length=1), server_default='R', nullable=False),
    sa.ForeignKeyConstraint(['process_id'], ['processes.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('process_id', 'element_id', 'role_id', name='uq_step_role')
    )
    op.create_index(op.f('ix_step_assignments_process_id'), 'step_assignments', ['process_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_step_assignments_process_id'), table_name='step_assignments')
    op.drop_table('step_assignments')
    op.drop_index(op.f('ix_sessions_user_id'), table_name='sessions')
    op.drop_table('sessions')
    op.drop_index(op.f('ix_position_roles_role_id'), table_name='position_roles')
    op.drop_index(op.f('ix_position_roles_position_id'), table_name='position_roles')
    op.drop_table('position_roles')
    op.drop_index('ix_workflow_target', table_name='workflow_entries')
    op.drop_table('workflow_entries')
    op.drop_table('users')
    op.drop_table('roles')
    op.drop_table('processes')
    op.drop_table('positions')
    op.drop_index('ix_audit_target', table_name='audit_log')
    op.drop_table('audit_log')
