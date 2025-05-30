"""Added product_type to Wishlist and Cart

Revision ID: fb21b8491c39
Revises: bef970706b53
Create Date: 2025-05-30 12:56:39.440123
"""
from alembic import op
import sqlalchemy as sa

# Revision identifiers, used by Alembic.
revision = 'fb21b8491c39'
down_revision = 'bef970706b53'
branch_labels = None
depends_on = None

def upgrade():
    # Create temporary tables with the new schema
    op.create_table(
        'wishlist_temp',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('product_type', sa.String(length=20), nullable=False, default='product'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'cart_temp',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, default=1),
        sa.Column('added_at', sa.DateTime(), nullable=True),
        sa.Column('product_type', sa.String(length=20), nullable=False, default='product'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Copy data from old tables to temporary tables
    op.execute("""
        INSERT INTO wishlist_temp (id, user_id, product_id, product_type)
        SELECT id, user_id, product_id, 'product' FROM wishlist
    """)
    op.execute("""
        INSERT INTO cart_temp (id, user_id, product_id, quantity, added_at, product_type)
        SELECT id, user_id, product_id, quantity, added_at, 'product' FROM cart
    """)

    # Drop old tables
    op.drop_table('wishlist')
    op.drop_table('cart')

    # Rename temporary tables to original names
    op.rename_table('wishlist_temp', 'wishlist')
    op.rename_table('cart_temp', 'cart')

def downgrade():
    # Create temporary tables with the old schema
    op.create_table(
        'wishlist_temp',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['product.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'cart_temp',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, default=1),
        sa.Column('added_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['product.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Copy data from new tables to temporary tables (only for product_type='product')
    op.execute("""
        INSERT INTO wishlist_temp (id, user_id, product_id)
        SELECT id, user_id, product_id FROM wishlist WHERE product_type = 'product'
    """)
    op.execute("""
        INSERT INTO cart_temp (id, user_id, product_id, quantity, added_at)
        SELECT id, user_id, product_id, quantity, added_at FROM cart WHERE product_type = 'product'
    """)

    # Drop new tables
    op.drop_table('wishlist')
    op.drop_table('cart')

    # Rename temporary tables to original names
    op.rename_table('wishlist_temp', 'wishlist')
    op.rename_table('cart_temp', 'cart')