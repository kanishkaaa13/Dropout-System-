"""add counselor and teacher roles

Revision ID: add_counselor_teacher_roles
Revises: a6d2a4515b12
Create Date: 2026-05-28

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_counselor_teacher_roles'
down_revision = 'a6d2a4515b12'
branch_labels = None
depends_on = None


def upgrade():
    # Update the role column to include counselor and teacher as valid values
    # Since it's a String column without an ENUM constraint, we just need to ensure
    # existing data is compatible and document the new valid values
    pass


def downgrade():
    # No changes needed to downgrade since we didn't modify the schema
    pass
