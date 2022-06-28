""" add updated_at indices

Revision ID: a718fc89dd64
Revises: b426918c5ede
Create Date: 2022-06-08 22:55:34.446264

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "a718fc89dd64"
down_revision = "b426918c5ede"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(
        op.f("ix_invoice_updated_at"), "invoice", ["updated_at"], unique=False
    )
    op.create_index(op.f("ix_sku_updated_at"), "sku", ["updated_at"], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_sku_updated_at"), table_name="sku")
    op.drop_index(op.f("ix_invoice_updated_at"), table_name="invoice")
    # ### end Alembic commands ###
