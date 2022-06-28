"""create sku variants index and rename parent_sku

Revision ID: 37b5dac4cbc4
Revises: e7d90cecc73d
Create Date: 2022-05-27 13:23:33.258921

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = '37b5dac4cbc4'
down_revision = 'e7d90cecc73d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('sku_variant', sa.Column('parent_sku_id', postgresql.UUID(), nullable=False))
    op.drop_index('ix_sku_variant_parent_sku', table_name='sku_variant')
    op.create_index(op.f('ix_sku_variant_parent_sku_id'), 'sku_variant', ['parent_sku_id'], unique=False)
    op.drop_constraint('sku_variant_parent_sku_fkey', 'sku_variant', type_='foreignkey')
    op.create_foreign_key(None, 'sku_variant', 'sku', ['parent_sku_id'], ['id'])
    op.drop_column('sku_variant', 'parent_sku')
    op.create_index('idx_sku_variants', 'warehouse_inventory', ['sku_variants'], unique=False, postgresql_using='gin')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('idx_sku_variants', table_name='warehouse_inventory', postgresql_using='gin')
    op.add_column('sku_variant', sa.Column('parent_sku', postgresql.UUID(), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'sku_variant', type_='foreignkey')
    op.create_foreign_key('sku_variant_parent_sku_fkey', 'sku_variant', 'sku', ['parent_sku'], ['id'])
    op.drop_index(op.f('ix_sku_variant_parent_sku_id'), table_name='sku_variant')
    op.create_index('ix_sku_variant_parent_sku', 'sku_variant', ['parent_sku'], unique=False)
    op.drop_column('sku_variant', 'parent_sku_id')
    # ### end Alembic commands ###
