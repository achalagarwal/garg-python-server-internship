"""remove table image

Revision ID: 506f308229b7
Revises: 37b5dac4cbc4
Create Date: 2022-06-02 13:41:46.440078

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = '506f308229b7'
down_revision = '37b5dac4cbc4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_image_id', table_name='image')
    op.drop_constraint('sku_image_id_fkey', 'sku', type_='foreignkey')
    op.drop_table('image')
    op.drop_column('sku', 'image_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('sku', sa.Column('image_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_table('image',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('title', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('base64', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('user_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='image_user_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='image_pkey')
    )
    op.create_foreign_key('sku_image_id_fkey', 'sku', 'image', ['image_id'], ['id'])
    op.create_index('ix_image_id', 'image', ['id'], unique=False)
    # ### end Alembic commands ###
