"""sku variant and inventory

Revision ID: e7d90cecc73d
Revises: 038b1bf8edc7
Create Date: 2022-05-24 11:55:43.723807

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = 'e7d90cecc73d'
down_revision = '038b1bf8edc7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('warehouse',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('display_name', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_warehouse_id'), 'warehouse', ['id'], unique=False)
    op.create_table('warehouse_inventory',
    sa.Column('id', postgresql.UUID(), nullable=False),
    sa.Column('row', sa.Integer(), nullable=False),
    sa.Column('column', sa.Integer(), nullable=False),
    sa.Column('warehouse_id', postgresql.UUID(), nullable=False),
    sa.Column('sku_variants', sa.ARRAY(postgresql.UUID()), nullable=False),
    sa.Column('quantities', sa.ARRAY(sa.Integer()), nullable=False),
    sa.ForeignKeyConstraint(['warehouse_id'], ['warehouse.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_row_column', 'warehouse_inventory', ['row', 'column'], unique=False)
    op.create_index(op.f('ix_warehouse_inventory_warehouse_id'), 'warehouse_inventory', ['warehouse_id'], unique=False)
    op.create_table('sku_variant',
    sa.Column('id', postgresql.UUID(), nullable=False),
    sa.Column('parent_sku', postgresql.UUID(), nullable=False),
    sa.Column('manufactured_date', sa.Date(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['parent_sku'], ['sku.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sku_variant_id'), 'sku_variant', ['id'], unique=False)
    op.create_index(op.f('ix_sku_variant_parent_sku'), 'sku_variant', ['parent_sku'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_sku_variant_parent_sku'), table_name='sku_variant')
    op.drop_index(op.f('ix_sku_variant_id'), table_name='sku_variant')
    op.drop_table('sku_variant')
    op.drop_index(op.f('ix_warehouse_inventory_warehouse_id'), table_name='warehouse_inventory')
    op.drop_index('idx_row_column', table_name='warehouse_inventory')
    op.drop_table('warehouse_inventory')
    op.drop_index(op.f('ix_warehouse_id'), table_name='warehouse')
    op.drop_table('warehouse')
    # ### end Alembic commands ###
