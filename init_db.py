import logging
from app import app, db, User, Category, Subcategory, Product, Gift, Order, Discount, OrderItem  # Add OrderItem
from werkzeug.security import generate_password_hash
from datetime import datetime
from slugify import slugify

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def init_db():
    with app.app_context():
        try:
            logger.debug("Starting database initialization")
            # Create all tables
            logger.debug("Dropping all tables")
            db.drop_all()
            logger.debug("Creating all tables")
            db.create_all()

            # Initialize Users
            logger.debug("Checking for existing admin user")
            if not User.query.filter_by(username='admin').first():
                logger.debug("Creating admin and john_doe users")
                admin = User(
                    username='admin',
                    name='Admin',
                    email='admin@zira.com',
                    phone_number='1234567890',
                    password=generate_password_hash('admin'),
                    role='admin'
                )
                user = User(
                    username='john_doe',
                    name='John Doe',
                    email='john.doe@example.com',
                    phone_number='+1234567890',
                    password=generate_password_hash('password123'),
                    role='buyer',
                    address={
                        'street': '00100 Northern Bypass Road, Intersection',
                        'city': 'Nairobi',
                        'country': 'Kenya',
                        'postal_code': '00100'
                    }
                )
                db.session.add_all([admin, user])
                db.session.commit()
                logger.debug("Users created successfully")
            else:
                logger.debug("Admin user already exists, skipping user creation")

            # Initialize Categories
            logger.debug("Checking for existing categories")
            if not Category.query.first():
                logger.debug("Creating categories")
                categories = [
                    Category(name='Home', slug=slugify('Home')),
                    Category(name='Kitchen', slug=slugify('Kitchen')),
                    Category(name='Decor', slug=slugify('Decor')),
                    Category(name='Easter', slug=slugify('Easter'))
                ]
                db.session.bulk_save_objects(categories)
                db.session.commit()
                logger.debug("Categories created successfully")

            # Initialize Subcategories
            logger.debug("Checking for existing subcategories")
            if not Subcategory.query.first():
                logger.debug("Creating subcategories")
                subcategories = [
                    Subcategory(name='Bathroom', slug=slugify('Bathroom'), category_id=1),
                    Subcategory(name='Utensils', slug=slugify('Utensils'), category_id=2),
                    Subcategory(name='Candles', slug=slugify('Candles'), category_id=3),
                    Subcategory(name='Seasonal', slug=slugify('Seasonal'), category_id=4)
                ]
                db.session.bulk_save_objects(subcategories)
                db.session.commit()
                logger.debug("Subcategories created successfully")

            # Initialize Products
            logger.debug("Checking for existing products")
            if not Product.query.first():
                logger.debug("Creating products")
                products = [
                    Product(title='Soap Dish', category_id=1, subcategory_id=1, price=1500.00, image='soap_dish.jpg', created_at=datetime(2025, 5, 1)),
                    Product(title='Mortar & Pestle', category_id=2, subcategory_id=2, price=2841.99, image='mortar_pestle.jpg', created_at=datetime(2025, 5, 2)),
                    Product(title='Yin Yang Candleholder', category_id=3, subcategory_id=3, price=2453.99, image='candleholder.jpg', created_at=datetime(2025, 5, 3)),
                    Product(title='Pillar Candlesticks', category_id=3, subcategory_id=3, price=2583.99, image='candlesticks.jpg', created_at=datetime(2025, 5, 4)),
                    Product(title='Cup Set', category_id=2, subcategory_id=2, price=1299.99, image='cup_set.jpg', created_at=datetime(2025, 4, 30)),
                    Product(title='Marble Tray', category_id=3, subcategory_id=None, price=2099.00, image='marble_tray.jpg', created_at=datetime(2025, 4, 29)),
                    Product(title='Mini Vases', category_id=3, subcategory_id=None, price=799.00, image='mini_vases.jpg', created_at=datetime(2025, 4, 28)),
                    Product(title='Hex Coasters', category_id=1, subcategory_id=None, price=1100.00, image='hex_coasters.jpg', created_at=datetime(2025, 4, 27)),
                    Product(title='Bunny Candle', category_id=4, subcategory_id=4, price=1050.00, image='bunny_candle.jpg', created_at=datetime(2025, 4, 26)),
                    Product(title='Egg Holder', category_id=4, subcategory_id=4, price=1200.00, image='egg_holder.jpg', created_at=datetime(2025, 4, 25)),
                    Product(title='Spring Vase', category_id=4, subcategory_id=4, price=1700.00, image='spring_vase.jpg', created_at=datetime(2025, 4, 24)),
                    Product(title='Pastel Tray', category_id=4, subcategory_id=4, price=1600.00, image='pastel_tray.jpg', created_at=datetime(2025, 4, 23)),
                ]
                db.session.bulk_save_objects(products)
                db.session.commit()
                logger.debug("Products created successfully")

            # Initialize Discounts
            logger.debug("Checking for existing discounts")
            if not Discount.query.first():
                logger.debug("Creating discounts")
                discounts = [
                    Discount(percent=20, start_date=datetime(2025, 5, 1).date(), end_date=datetime(2025, 5, 31).date()),
                    Discount(percent=18, start_date=datetime(2025, 5, 1).date(), end_date=datetime(2025, 5, 31).date()),
                    Discount(percent=26, start_date=datetime(2025, 5, 1).date(), end_date=datetime(2025, 5, 31).date()),
                    Discount(percent=30, start_date=datetime(2025, 5, 1).date(), end_date=datetime(2025, 5, 31).date()),
                    Discount(percent=23, start_date=datetime(2025, 5, 1).date(), end_date=datetime(2025, 5, 31).date()),
                    Discount(percent=26, start_date=datetime(2025, 5, 1).date(), end_date=datetime(2025, 5, 31).date()),
                    Discount(percent=19, start_date=datetime(2025, 5, 1).date(), end_date=datetime(2025, 5, 31).date()),
                    Discount(percent=23, start_date=datetime(2025, 5, 1).date(), end_date=datetime(2025, 5, 31).date()),
                    Discount(percent=24, start_date=datetime(2025, 5, 1).date(), end_date=datetime(2025, 5, 31).date()),
                    Discount(percent=21, start_date=datetime(2025, 5, 1).date(), end_date=datetime(2025, 5, 31).date()),
                    Discount(percent=18, start_date=datetime(2025, 5, 1).date(), end_date=datetime(2025, 5, 31).date()),
                    Discount(percent=25, start_date=datetime(2025, 5, 1).date(), end_date=datetime(2025, 5, 31).date()),
                ]
                db.session.bulk_save_objects(discounts)
                db.session.commit()
                logger.debug("Discounts created successfully")

                # Assign discounts to products
                logger.debug("Assigning discounts to products")
                product_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
                for idx, product_id in enumerate(product_ids):
                    product = db.session.get(Product, product_id)  # Update to session.get
                    if product:
                        product.discount_id = discounts[idx].id
                db.session.commit()
                logger.debug("Discounts assigned successfully")

            # Initialize Orders
            logger.debug("Checking for existing orders")
            if not Order.query.first():
                user = User.query.filter_by(email='john.doe@example.com').first()
                if user:
                    logger.debug("Creating orders")
                    orders = [
                        Order(
                            user_id=user.id,
                            total=3600.00,
                            status='Pending',
                            customer_status='Active',
                            payment_method='immediate',
                            created_at=datetime(2025, 5, 1)
                        ),
                        Order(
                            user_id=user.id,
                            total=1500.00,
                            status='Delivered',
                            customer_status='Active',
                            payment_method='delivery',
                            created_at=datetime(2025, 5, 2)
                        ),
                    ]
                    db.session.bulk_save_objects(orders)
                    db.session.commit()
                    logger.debug("Orders created successfully")
                else:
                    logger.warning("No user found for john.doe@example.com, skipping order creation")

            # Initialize Order Items
            logger.debug("Checking for existing order items")
            if not OrderItem.query.first():
                logger.debug("Creating order items")
                order_items = [
                    OrderItem(order_id=1, product_id=1, quantity=2),
                    OrderItem(order_id=2, product_id=2, quantity=1),
                ]
                db.session.bulk_save_objects(order_items)
                db.session.commit()
                logger.debug("Order items created successfully")

            # Update Orders
            logger.debug("Updating orders with null customer_status")
            Order.query.filter_by(customer_status=None).update({'customer_status': 'Active'})
            db.session.commit()
            logger.debug("Orders updated successfully")

            logger.info("Database initialized successfully!")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during database initialization: {str(e)}")
            raise

if __name__ == '__main__':
    init_db()