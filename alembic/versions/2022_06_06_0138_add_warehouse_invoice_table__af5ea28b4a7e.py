"""add warehouse_invoice table

Revision ID: af5ea28b4a7e
Revises: e0b8061d03b8
Create Date: 2022-06-06 01:38:18.373159

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = 'af5ea28b4a7e'
down_revision = 'e0b8061d03b8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('warehouse_invoice',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('parent_invoice_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('warehouse_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('warehouse_inventories', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False),
    sa.Column('sku_variants', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False),
    sa.Column('skus', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False),
    sa.Column('quantities', postgresql.ARRAY(sa.Integer()), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['parent_invoice_id'], ['invoice.id'], ),
    sa.ForeignKeyConstraint(['warehouse_id'], ['warehouse.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_orderedby_created_date_warehouse_invoice', 'warehouse_invoice', ['created_at'], unique=False, postgresql_using='btree')
    op.create_index(op.f('ix_warehouse_invoice_id'), 'warehouse_invoice', ['id'], unique=False)
    op.create_index(op.f('ix_warehouse_invoice_parent_invoice_id'), 'warehouse_invoice', ['parent_invoice_id'], unique=False)
    op.create_index(op.f('ix_warehouse_invoice_warehouse_id'), 'warehouse_invoice', ['warehouse_id'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_warehouse_invoice_warehouse_id'), table_name='warehouse_invoice')
    op.drop_index(op.f('ix_warehouse_invoice_parent_invoice_id'), table_name='warehouse_invoice')
    op.drop_index(op.f('ix_warehouse_invoice_id'), table_name='warehouse_invoice')
    op.drop_index('idx_orderedby_created_date_warehouse_invoice', table_name='warehouse_invoice', postgresql_using='btree')
    op.drop_table('warehouse_invoice')
    # ### end Alembic commands ###
