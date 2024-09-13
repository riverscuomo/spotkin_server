"""jobastupdated

Revision ID: 31a890d73e36
Revises: 7cf34caf4ac7
Create Date: 2024-09-10 09:15:44.668791

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '31a890d73e36'
down_revision = '7cf34caf4ac7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('jobs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_updated', sa.Integer(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('jobs', schema=None) as batch_op:
        batch_op.drop_column('last_updated')

    # ### end Alembic commands ###