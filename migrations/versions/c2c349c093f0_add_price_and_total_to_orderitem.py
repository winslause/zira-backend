"""Add price and total to OrderItem

Revision ID: c2c349c093f0
Revises: 7a6c56fda28f
Create Date: <timestamp>

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c2c349c093f0'
down_revision = '7a6c56fda28f'
branch_labels = None
depends_on = None

def upgrade():
    # Check if columns exist before adding
    inspector = sa.inspect(op.get_bind())
    columns = [col['name'] for col in inspector.get_columns('order_item')]

    with op.batch_alter_table('order_item', schema=None) as batch_op:
        if 'price' not in columns:
            batch_op.add_column(sa.Column('price', sa.Float(), nullable=False))
        if 'total' not in columns:
            batch_op.add_column(sa.Column('total', sa.Float(), nullable=False))

def downgrade():
    # Remove columns only if they exist
    inspector = sa.inspect(op.get_bind())
    columns = [col['name'] for col in inspector.get_columns('order_item')]

    with op.batch_alter_table('order_item', schema=None) as batch_op:
        if 'total' in columns:
            batch_op.drop_column('total')
        if 'price' in columns:
            batch_op.drop_column('price')