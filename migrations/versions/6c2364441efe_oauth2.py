"""oauth2

Revision ID: 6c2364441efe
Revises: 
Create Date: 2024-09-05 08:25:56.590990

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6c2364441efe'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('last_updated', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('jobs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('playlist_id', sa.String(), nullable=False),
    sa.Column('playlist_name', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('scheduled_time', sa.Integer(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('ban_skits', sa.Boolean(), nullable=True),
    sa.Column('last_track_ids', sa.String(), nullable=True),
    sa.Column('banned_artist_ids', sa.String(), nullable=True),
    sa.Column('banned_track_ids', sa.String(), nullable=True),
    sa.Column('banned_genres', sa.String(), nullable=True),
    sa.Column('exceptions_to_banned_genres', sa.String(), nullable=True),
    sa.Column('min_popularity', sa.Integer(), nullable=True),
    sa.Column('max_popularity', sa.Integer(), nullable=True),
    sa.Column('min_duration', sa.Integer(), nullable=True),
    sa.Column('max_duration', sa.Integer(), nullable=True),
    sa.Column('min_danceability', sa.Integer(), nullable=True),
    sa.Column('max_danceability', sa.Integer(), nullable=True),
    sa.Column('min_energy', sa.Integer(), nullable=True),
    sa.Column('max_energy', sa.Integer(), nullable=True),
    sa.Column('min_acousticness', sa.Integer(), nullable=True),
    sa.Column('max_acousticness', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('tokens',
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('token_info', sa.JSON(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('user_id')
    )
    op.create_table('ingredients',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('job_id', sa.UUID(), nullable=False),
    sa.Column('playlist_id', sa.String(), nullable=False),
    sa.Column('playlist_name', sa.String(), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('ingredients')
    op.drop_table('tokens')
    op.drop_table('jobs')
    op.drop_table('users')
    # ### end Alembic commands ###
