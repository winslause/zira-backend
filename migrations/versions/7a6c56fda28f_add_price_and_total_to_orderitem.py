"""Add price and total to OrderItem

Revision ID: 7a6c56fda28f
Revises: fb21b8491c39
Create Date: 2025-05-31 01:03:54.124051

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a6c56fda28f'
down_revision = 'fb21b8491c39'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('order_item', schema=None) as batch_op:
        batch_op.add_column(sa.Column('price', sa.Float(), nullable=False))
        batch_op.add_column(sa.Column('total', sa.Float(), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('order_item', schema=None) as batch_op:
        batch_op.drop_column('total')
        batch_op.drop_column('price')

    # ### end Alembic commands ###
