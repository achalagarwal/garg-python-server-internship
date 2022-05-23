"""add weight fields to sku

Revision ID: 82714127ef1d
Revises: eb804936ee4a
Create Date: 2022-05-23 13:17:04.083725

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '82714127ef1d'
down_revision = 'eb804936ee4a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('sku', sa.Column('weight', sa.String(), nullable=True))
    op.add_column('sku', sa.Column('weight_unit', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('sku', 'weight_unit')
    op.drop_column('sku', 'weight')
    # ### end Alembic commands ###
