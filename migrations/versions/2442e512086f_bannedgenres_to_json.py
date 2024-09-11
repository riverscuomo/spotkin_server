from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2442e512086f'
down_revision = '899c7561de33'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the 'banned_genres' column
    with op.batch_alter_table('jobs', schema=None) as batch_op:
        batch_op.drop_column('banned_genres')

    # Re-add the 'banned_genres' column as JSON
    with op.batch_alter_table('jobs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('banned_genres', sa.JSON, nullable=True))


def downgrade():
    # Reverse the changes, drop the 'banned_genres' JSON column and re-add it as String (if needed)
    with op.batch_alter_table('jobs', schema=None) as batch_op:
        batch_op.drop_column('banned_genres')
        batch_op.add_column(
            sa.Column('banned_genres', sa.String(), nullable=True))
