"""Call activities linked to the called process (stage 4b, reviewed).

Revision ID: 0007
Revises: 0006
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('processes', sa.Column('call_links', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False))


def downgrade() -> None:
    op.drop_column('processes', 'call_links')
