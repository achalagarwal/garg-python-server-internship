"""add timestamp fields and default id

Revision ID: b426918c5ede
Revises: af5ea28b4a7e
Create Date: 2022-06-08 20:49:12.015266

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = 'b426918c5ede'
down_revision = 'af5ea28b4a7e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('image', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.add_column('image', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.add_column('invoice', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.add_column('invoice', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.add_column('sku', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.add_column('sku', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.add_column('sku_variant', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.add_column('user', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.add_column('user', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.create_index(op.f('ix_user_id'), 'user', ['id'], unique=False)
    op.add_column('warehouse', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.add_column('warehouse', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.add_column('warehouse_inventory', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.add_column('warehouse_inventory', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.add_column('warehouse_invoice', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('warehouse_invoice', 'updated_at')
    op.drop_column('warehouse_inventory', 'updated_at')
    op.drop_column('warehouse_inventory', 'created_at')
    op.drop_column('warehouse', 'updated_at')
    op.drop_column('warehouse', 'created_at')
    op.drop_index(op.f('ix_user_id'), table_name='user')
    op.drop_column('user', 'updated_at')
    op.drop_column('user', 'created_at')
    op.drop_column('sku_variant', 'updated_at')
    op.drop_column('sku', 'updated_at')
    op.drop_column('sku', 'created_at')
    op.drop_column('invoice', 'updated_at')
    op.drop_column('invoice', 'created_at')
    op.drop_column('image', 'updated_at')
    op.drop_column('image', 'created_at')
    # ### end Alembic commands ###
