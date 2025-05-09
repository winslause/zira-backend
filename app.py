from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
# from models import Story
from datetime import datetime, timedelta
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
import logging


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
db = SQLAlchemy(app)

# Ensure upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Logging setup
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

# Models (unchanged from your code)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone_number = db.Column(db.String(15))
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='buyer')
    profile_picture = db.Column(db.String(200))
    address = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(200))
    description = db.Column(db.Text)
    discount_id = db.Column(db.Integer, db.ForeignKey('discount.id'))
    discount = db.relationship('Discount', backref='product', uselist=False, foreign_keys=[discount_id])
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    payment_method = db.Column(db.String(20), nullable=False)
    message_code = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    order_items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    product = db.relationship('Product', backref='order_items', lazy=True)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class Discount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    percent = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

class Artisan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone_number = db.Column(db.String(15))
    status = db.Column(db.String(20), default='Pending')

class Story(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(200))

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    status = db.Column(db.String(20), default='Pending')

class Wishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product = db.relationship('Product', backref='wishlist_items', lazy=True)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    product = db.relationship('Product', backref='cart_items', lazy=True)

# Database Initialization (unchanged)
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            name='Admin',
            email='admin@zira.com',
            phone_number='1234567890',
            password=generate_password_hash('admin'),
            role='admin'
        )
        db.session.add(admin)
        user = User(
            username='john_doe',
            name='John Doe',
            email='john.doe@example.com',
            phone_number='+1234567890',
            password=generate_password_hash('password123'),
            role='buyer'
        )
        db.session.add(user)
        db.session.commit()

    if not Category.query.first():
        categories = [
            Category(name='Home'),
            Category(name='Kitchen'),
            Category(name='Decor'),
            Category(name='Easter')
        ]
        db.session.bulk_save_objects(categories)
        db.session.commit()

    if not Product.query.first():
        products = [
            Product(name='Soap Dish', category='Home', price=1500.00, image='soap_dish.jpg', created_at=datetime(2025, 5, 1)),
            Product(name='Mortar & Pestle', category='Kitchen', price=2841.99, image='mortar_pestle.jpg', created_at=datetime(2025, 5, 2)),
            Product(name='Yin Yang Candleholder', category='Decor', price=2453.99, image='candleholder.jpg', created_at=datetime(2025, 5, 3)),
            Product(name='Pillar Candlesticks', category='Decor', price=2583.99, image='candlesticks.jpg', created_at=datetime(2025, 5, 4)),
            Product(name='Cup Set', category='Kitchen', price=1299.99, image='cup_set.jpg', created_at=datetime(2025, 4, 30)),
            Product(name='Marble Tray', category='Decor', price=2099.00, image='marble_tray.jpg', created_at=datetime(2025, 4, 29)),
            Product(name='Mini Vases', category='Decor', price=799.00, image='mini_vases.jpg', created_at=datetime(2025, 4, 28)),
            Product(name='Hex Coasters', category='Home', price=1100.00, image='hex_coasters.jpg', created_at=datetime(2025, 4, 27)),
            Product(name='Bunny Candle', category='Easter', price=1050.00, image='bunny_candle.jpg', created_at=datetime(2025, 4, 26)),
            Product(name='Egg Holder', category='Easter', price=1200.00, image='egg_holder.jpg', created_at=datetime(2025, 4, 25)),
            Product(name='Spring Vase', category='Easter', price=1700.00, image='spring_vase.jpg', created_at=datetime(2025, 4, 24)),
            Product(name='Pastel Tray', category='Easter', price=1600.00, image='pastel_tray.jpg', created_at=datetime(2025, 4, 23)),
        ]
        db.session.bulk_save_objects(products)
        db.session.commit()

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

        product_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        for idx, product_id in enumerate(product_ids):
            product = Product.query.get(product_id)
            discount = Discount.query.get(idx + 1)
            if product and discount:
                product.discount_id = discount.id
        db.session.commit()

    if not Order.query.first():
        user = User.query.filter_by(email='john.doe@example.com').first()
        orders = [
            Order(
                user_id=user.id,
                total=3600.00,
                status='Pending',
                payment_method='immediate',
                created_at=datetime(2025, 5, 1)
            ),
            Order(
                user_id=user.id,
                total=1500.00,
                status='Delivered',
                payment_method='delivery',
                created_at=datetime(2025, 5, 2)
            ),
        ]
        db.session.bulk_save_objects(orders)
        db.session.commit()

# Helper Functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png'}

def save_file(file):
    if file and allowed_file(file.filename):
        filename = f"{datetime.now().timestamp()}_{file.filename}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return filename
    return None

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('user_login'))

    stories = Story.query.all()
    latest_products = Product.query.order_by(Product.created_at.desc()).limit(4).all()
    current_date = datetime.utcnow().date()
    discount_products = Product.query.join(Discount, Product.discount_id == Discount.id).filter(
        Discount.start_date <= current_date,
        Discount.end_date >= current_date
    ).order_by(Product.created_at.desc()).limit(4).all()
    popular_products = db.session.query(Product, func.count(OrderItem.id).label('order_count'))\
        .join(OrderItem, Product.id == OrderItem.product_id)\
        .group_by(Product.id)\
        .order_by(func.count(OrderItem.id).desc())\
        .limit(4).all()
    popular_products = [product for product, _ in popular_products]

    return render_template(
        'index.html',
        latest_products=latest_products,
        discount_products=discount_products,
        popular_products=popular_products,
        today=datetime.utcnow().date(),
        current_currency='USD',
        stories=stories  
    )


@app.route('/admin')
def admin():
    if 'admin' not in session:
        return redirect(url_for('login'))
    return render_template('admin.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password) and user.role == 'admin':
            session['admin'] = user.id
            return jsonify({'message': 'Login successful'})
        return jsonify({'error': 'Invalid credentials or not an admin'}), 401
    return render_template('admin-login.html')

@app.route('/logout')
def logout():
    if 'admin' in session:
        session.pop('admin', None)
        return jsonify({'message': 'Admin logged out successfully'})
    elif 'user' in session:
        session.pop('user', None)
        return jsonify({'message': 'User logged out successfully'})
    return jsonify({'message': 'No user logged in'})

@app.route('/logout1')
def user_logout():
    session.pop('user', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('user_login'))

# Product Routes
@app.route('/api/discounted_artefacts', methods=['GET', 'POST'])
def handle_products():
    if request.method == 'GET':
        products = Product.query.all()
        return jsonify([
            {
                'id': p.id,
                'name': p.name,
                'category': p.category,
                'price': p.price,
                'image': p.image,
                'description': p.description,
                'discount': p.discount.percent if p.discount else None
            } for p in products
        ])
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            category = request.form.get('category')
            price = request.form.get('price')
            description = request.form.get('description', '')
            image = request.files.get('image')

            if not all([name, category, price]):
                return jsonify({'error': 'Name, category, and price are required'}), 400
            if not image or not allowed_file(image.filename):
                return jsonify({'error': 'Valid image (JPG/PNG) is required'}), 400
            if image.content_length > 3 * 1024 * 1024:
                return jsonify({'error': 'Image size exceeds 3MB'}), 400

            filename = save_file(image)
            if not filename:
                return jsonify({'error': 'Failed to save image'}), 500

            product = Product(
                name=name,
                category=category,
                price=float(price),
                image=filename,
                description=description
            )
            db.session.add(product)
            db.session.commit()
            return jsonify({'message': 'Product created successfully', 'id': product.id}), 201
        except ValueError:
            return jsonify({'error': 'Invalid price format'}), 400
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Database error in POST /api/discounted_artefacts: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        except Exception as e:
            db.session.rollback()
            logging.error(f"Unexpected error in POST /api/discounted_artefacts: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/discounted_artefacts/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def handle_product(id):
    product = Product.query.get_or_404(id)
    if request.method == 'GET':
        return jsonify({
            'id': product.id,
            'name': product.name,
            'category': product.category,
            'price': product.price,
            'image': product.image,
            'description': product.description,
            'discount': product.discount.percent if product.discount else None
        })
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    if request.method == 'PUT':
        try:
            product.name = request.form.get('name', product.name)
            product.category = request.form.get('category', product.category)
            product.price = float(request.form.get('price', product.price))
            product.description = request.form.get('description', product.description)
            if 'image' in request.files and request.files['image'].filename:
                image = request.files['image']
                if not allowed_file(image.filename):
                    return jsonify({'error': 'Invalid image format'}), 400
                if image.content_length > 3 * 1024 * 1024:
                    return jsonify({'error': 'Image size exceeds 3MB'}), 400
                filename = save_file(image)
                if product.image and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], product.image)):
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], product.image))
                product.image = filename
            db.session.commit()
            return jsonify({'message': 'Product updated successfully'})
        except ValueError:
            return jsonify({'error': 'Invalid price format'}), 400
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Database error in PUT /api/discounted_artefacts/{id}: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        except Exception as e:
            db.session.rollback()
            logging.error(f"Unexpected error in PUT /api/discounted_artefacts/{id}: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    if request.method == 'DELETE':
        try:
            logging.debug(f"Deleting product ID {id}: {product.name}")

            # Delete related cart items
            cart_items = Cart.query.filter_by(product_id=id).all()
            if cart_items:
                logging.debug(f"Found {len(cart_items)} cart items for product ID {id}")
                Cart.query.filter_by(product_id=id).delete()

            # Delete related order items
            order_items = OrderItem.query.filter_by(product_id=id).all()
            if order_items:
                logging.debug(f"Found {len(order_items)} order items for product ID {id}")
                OrderItem.query.filter_by(product_id=id).delete()

            # Delete related wishlist items
            wishlist_items = Wishlist.query.filter_by(product_id=id).all()
            if wishlist_items:
                logging.debug(f"Found {len(wishlist_items)} wishlist items for product ID {id}")
                Wishlist.query.filter_by(product_id=id).delete()

            # Delete related reviews
            reviews = Review.query.filter_by(product_id=id).all()
            if reviews:
                logging.debug(f"Found {len(reviews)} reviews for product ID {id}")
                Review.query.filter_by(product_id=id).delete()

            # Delete related discount
            if product.discount_id:
                discount = Discount.query.get(product.discount_id)
                if discount:
                    logging.debug(f"Deleting discount ID {discount.id} for product ID {id}")
                    db.session.delete(discount)

            # Delete product image
            if product.image and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], product.image)):
                logging.debug(f"Deleting image: {product.image}")
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], product.image))

            # Delete the product
            db.session.delete(product)
            db.session.commit()
            logging.debug(f"Product ID {id} deleted successfully")

            return jsonify({'message': 'Product deleted successfully'})
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Database error in DELETE /api/discounted_artefacts/{id}: {str(e)}")
            return jsonify({'error': 'Cannot delete product due to database constraints'}), 500
        except Exception as e:
            db.session.rollback()
            logging.error(f"Unexpected error in DELETE /api/discounted_artefacts/{id}: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

# Order Routes
@app.route('/api/orders', methods=['GET'])
def handle_orders():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    orders = Order.query.all()
    return jsonify([
        {
            'id': o.id,
            'customer': User.query.get(o.user_id).name,
            'customer_number': User.query.get(o.user_id).phone_number or 'N/A',
            'location': User.query.get(o.user_id).address.get('location', 'N/A') if User.query.get(o.user_id).address else 'N/A',
            'total': o.total,
            'status': o.status,
            'payment_method': o.payment_method
        } for o in orders
    ])

@app.route('/api/orders/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def handle_order(id):
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    order = Order.query.get_or_404(id)
    if request.method == 'GET':
        return jsonify({
            'id': order.id,
            'customer': User.query.get(order.user_id).name,
            'customer_number': User.query.get(order.user_id).phone_number or 'N/A',
            'location': User.query.get(order.user_id).address.get('location', 'N/A') if User.query.get(order.user_id).address else 'N/A',
            'total': order.total,
            'status': order.status,
            'payment_method': order.payment_method
        })
    if request.method == 'PUT':
        try:
            data = request.get_json()
            order.status = data.get('status', order.status)
            db.session.commit()
            return jsonify({'message': 'Order updated successfully'})
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Database error in PUT /api/orders/{id}: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        except Exception as e:
            db.session.rollback()
            logging.error(f"Unexpected error in PUT /api/orders/{id}: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    if request.method == 'DELETE':
        try:
            OrderItem.query.filter_by(order_id=id).delete()
            db.session.delete(order)
            db.session.commit()
            return jsonify({'message': 'Order deleted successfully'})
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Database error in DELETE /api/orders/{id}: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        except Exception as e:
            db.session.rollback()
            logging.error(f"Unexpected error in DELETE /api/orders/{id}: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

# Discount Routes
@app.route('/api/discounts', methods=['GET', 'POST'])
def handle_discounts():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    if request.method == 'GET':
        try:
            discounts = Discount.query.all()
            return jsonify([
                {
                    'id': d.id,
                    'productId': p.id if (p := Product.query.filter_by(discount_id=d.id).first()) else None,
                    'productName': p.name if (p := Product.query.filter_by(discount_id=d.id).first()) else 'N/A',
                    'percent': d.percent,
                    'startDate': d.start_date.strftime('%Y-%m-%d'),
                    'endDate': d.end_date.strftime('%Y-%m-%d')
                } for d in discounts
            ])
        except SQLAlchemyError as e:
            logging.error(f"Database error in GET /api/discounts: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        except Exception as e:
            logging.error(f"Unexpected error in GET /api/discounts: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    if request.method == 'POST':
        try:
            data = request.get_json()
            logging.debug(f"Received POST /api/discounts data: {data}")
            required_fields = ['productId', 'percent', 'startDate', 'endDate']
            missing_fields = [field for field in required_fields if field not in data or not data[field]]
            if missing_fields:
                return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400

            product_id = data['productId']
            percent = data['percent']
            start_date = data['startDate']
            end_date = data['endDate']

            if not isinstance(percent, int) or percent < 0 or percent > 100:
                return jsonify({'error': 'Percent must be an integer between 0 and 100'}), 400

            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                if start_date > end_date:
                    return jsonify({'error': 'End date must be after start date'}), 400
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

            product = Product.query.get(product_id)
            if not product:
                return jsonify({'error': 'Product not found'}), 404
            if product.discount_id:
                return jsonify({'error': 'Product already has a discount'}), 400

            discount = Discount(
                percent=percent,
                start_date=start_date,
                end_date=end_date
            )
            db.session.add(discount)
            db.session.flush()
            product.discount_id = discount.id
            db.session.commit()

            return jsonify({
                'message': 'Discount created successfully',
                'id': discount.id
            }), 201
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Database error in POST /api/discounts: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        except Exception as e:
            db.session.rollback()
            logging.error(f"Unexpected error in POST /api/discounts: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/discounts/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def handle_discount(id):
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    discount = Discount.query.get_or_404(id)
    if request.method == 'GET':
        return jsonify({
            'id': discount.id,
            'productId': discount.product.id if discount.product else None,
            'productName': discount.product.name if discount.product else 'N/A',
            'percent': discount.percent,
            'startDate': discount.start_date.strftime('%Y-%m-%d'),
            'endDate': discount.end_date.strftime('%Y-%m-%d')
        })
    if request.method == 'PUT':
        try:
            data = request.get_json()
            required_fields = ['productId', 'percent', 'startDate', 'endDate']
            missing_fields = [field for field in required_fields if field not in data or not data[field]]
            if missing_fields:
                return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400

            product_id = data['productId']
            percent = data['percent']
            start_date = data['startDate']
            end_date = data['endDate']

            if not isinstance(percent, int) or percent < 0 or percent > 100:
                return jsonify({'error': 'Percent must be an integer between 0 and 100'}), 400

            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                if start_date > end_date:
                    return jsonify({'error': 'End date must be after start date'}), 400
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

            product = Product.query.get(product_id)
            if not product:
                return jsonify({'error': 'Product not found'}), 404
            if product.discount_id and product.discount_id != discount.id:
                return jsonify({'error': 'Product already has a different discount'}), 400

            old_product = Product.query.filter_by(discount_id=discount.id).first()
            if old_product and old_product.id != product_id:
                old_product.discount_id = None

            discount.percent = percent
            discount.start_date = start_date
            discount.end_date = end_date
            product.discount_id = discount.id

            db.session.commit()
            return jsonify({'message': 'Discount updated successfully'})
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Database error in PUT /api/discounts/{id}: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        except Exception as e:
            db.session.rollback()
            logging.error(f"Unexpected error in PUT /api/discounts/{id}: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    if request.method == 'DELETE':
        try:
            product = Product.query.filter_by(discount_id=id).first()
            if product:
                product.discount_id = None
            db.session.delete(discount)
            db.session.commit()
            return jsonify({'message': 'Discount deleted successfully'})
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Database error in DELETE /api/discounts/{id}: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        except Exception as e:
            db.session.rollback()
            logging.error(f"Unexpected error in DELETE /api/discounts/{id}: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

# Other routes (unchanged or minimally modified)
@app.route('/api/users', methods=['GET', 'POST'])
def handle_users():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    if request.method == 'GET':
        users = User.query.all()
        return jsonify([
            {
                'id': u.id,
                'username': u.username,
                'name': u.name,
                'email': u.email,
                'phone_number': u.phone_number or 'N/A',
                'role': u.role
            } for u in users
        ])
    if request.method == 'POST':
        try:
            data = request.get_json()
            required_fields = ['username', 'name', 'email', 'role']
            missing_fields = [field for field in required_fields if field not in data or not data[field]]
            if missing_fields:
                return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
            if User.query.filter_by(username=data['username']).first():
                return jsonify({'error': 'Username already exists'}), 400
            if User.query.filter_by(email=data['email']).first():
                return jsonify({'error': 'Email already exists'}), 400
            user = User(
                username=data['username'],
                name=data['name'],
                email=data['email'],
                phone_number=data.get('phone_number', ''),
                password=generate_password_hash('default123'),
                role=data['role']
            )
            db.session.add(user)
            db.session.commit()
            return jsonify({'message': 'User created successfully'}), 201
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Database error in POST /api/users: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        except Exception as e:
            db.session.rollback()
            logging.error(f"Unexpected error in POST /api/users: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/users/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def handle_user(id):
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    user = User.query.get_or_404(id)
    if request.method == 'GET':
        return jsonify({
            'id': user.id,
            'username': user.username,
            'name': user.name,
            'email': user.email,
            'phone_number': user.phone_number or 'N/A',
            'role': user.role
        })
    if request.method == 'PUT':
        try:
            data = request.get_json()
            if 'username' in data and data['username'] and User.query.filter_by(username=data['username']).filter(User.id != id).first():
                return jsonify({'error': 'Username already exists'}), 400
            if 'email' in data and data['email'] and User.query.filter_by(email=data['email']).filter(User.id != id).first():
                return jsonify({'error': 'Email already exists'}), 400
            user.username = data.get('username', user.username)
            user.name = data.get('name', user.name)
            user.email = data.get('email', user.email)
            user.phone_number = data.get('phone_number', user.phone_number)
            user.role = data.get('role', user.role)
            db.session.commit()
            return jsonify({'message': 'User updated successfully'})
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Database error in PUT /api/users/{id}: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        except Exception as e:
            db.session.rollback()
            logging.error(f"Unexpected error in PUT /api/users/{id}: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    if request.method == 'DELETE':
        try:
            db.session.delete(user)
            db.session.commit()
            return jsonify({'message': 'User deleted successfully'})
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Database error in DELETE /api/users/{id}: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        except Exception as e:
            db.session.rollback()
            logging.error(f"Unexpected error in DELETE /api/users/{id}: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/categories', methods=['GET', 'POST'])
def handle_categories():
    if request.method == 'GET':
        categories = Category.query.all()
        return jsonify([{'id': c.id, 'name': c.name} for c in categories])
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data.get('name'):
                return jsonify({'error': 'Category name is required'}), 400
            if Category.query.filter_by(name=data['name']).first():
                return jsonify({'error': 'Category already exists'}), 400
            category = Category(name=data['name'])
            db.session.add(category)
            db.session.commit()
            return jsonify({'message': 'Category created successfully'}), 201
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Database error in POST /api/categories: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        except Exception as e:
            db.session.rollback()
            logging.error(f"Unexpected error in POST /api/categories: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/categories/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def handle_category(id):
    category = Category.query.get_or_404(id)
    if request.method == 'GET':
        return jsonify({'id': category.id, 'name': category.name})
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    if request.method == 'PUT':
        try:
            data = request.get_json()
            if 'name' in data and data['name'] and Category.query.filter_by(name=data['name']).filter(Category.id != id).first():
                return jsonify({'error': 'Category already exists'}), 400
            category.name = data.get('name', category.name)
            db.session.commit()
            return jsonify({'message': 'Category updated successfully'})
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Database error in PUT /api/categories/{id}: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        except Exception as e:
            db.session.rollback()
            logging.error(f"Unexpected error in PUT /api/categories/{id}: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    if request.method == 'DELETE':
        try:
            db.session.delete(category)
            db.session.commit()
            return jsonify({'message': 'Category deleted successfully'})
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Database error in DELETE /api/categories/{id}: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        except Exception as e:
            db.session.rollback()
            logging.error(f"Unexpected error in DELETE /api/categories/{id}: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/artisans', methods=['GET', 'POST'])
def handle_artisans():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    if request.method == 'GET':
        artisans = Artisan.query.all()
        return jsonify([
            {
                'id': a.id,
                'name': a.name,
                'email': a.email,
                'phone_number': a.phone_number or 'N/A',
                'status': a.status
            } for a in artisans
        ])
    if request.method == 'POST':
        try:
            data = request.get_json()
            required_fields = ['name', 'email', 'status']
            missing_fields = [field for field in required_fields if field not in data or not data[field]]
            if missing_fields:
                return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
            if Artisan.query.filter_by(email=data['email']).first():
                return jsonify({'error': 'Email already exists'}), 400
            artisan = Artisan(
                name=data['name'],
                email=data['email'],
                phone_number=data.get('phone_number', ''),
                status=data['status']
            )
            db.session.add(artisan)
            db.session.commit()
            return jsonify({'message': 'Artisan created successfully'}), 201
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Database error in POST /api/artisans: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        except Exception as e:
            db.session.rollback()
            logging.error(f"Unexpected error in POST /api/artisans: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/artisans/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def handle_artisan(id):
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    artisan = Artisan.query.get_or_404(id)
    if request.method == 'GET':
        return jsonify({
            'id': artisan.id,
            'name': artisan.name,
            'email': artisan.email,
            'phone_number': artisan.phone_number or 'N/A',
            'status': artisan.status
        })
    if request.method == 'PUT':
        try:
            data = request.get_json()
            if 'email' in data and data['email'] and Artisan.query.filter_by(email=data['email']).filter(Artisan.id != id).first():
                return jsonify({'error': 'Email already exists'}), 400
            artisan.name = data.get('name', artisan.name)
            artisan.email = data.get('email', artisan.email)
            artisan.phone_number = data.get('phone_number', artisan.phone_number)
            artisan.status = data.get('status', artisan.status)
            db.session.commit()
            return jsonify({'message': 'Artisan updated successfully'})
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Database error in PUT /api/artisans/{id}: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        except Exception as e:
            db.session.rollback()
            logging.error(f"Unexpected error in PUT /api/artisans/{id}: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    if request.method == 'DELETE':
        try:
            db.session.delete(artisan)
            db.session.commit()
            return jsonify({'message': 'Artisan deleted successfully'})
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Database error in DELETE /api/artisans/{id}: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        except Exception as e:
            db.session.rollback()
            logging.error(f"Unexpected error in DELETE /api/artisans/{id}: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/stories', methods=['GET', 'POST'])
def handle_stories():
    if request.method == 'GET':
        stories = Story.query.all()
        return jsonify([
            {
                'id': s.id,
                'title': s.title,
                'content': s.content,
                'image': s.image
            } for s in stories
        ])
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    if request.method == 'POST':
        try:
            if 'image' not in request.files:
                return jsonify({'error': 'Image is required'}), 400
            image = request.files['image']
            if not allowed_file(image.filename):
                return jsonify({'error': 'Invalid image format'}), 400
            if image.content_length > 3 * 1024 * 1024:
                return jsonify({'error': 'Image size exceeds 3MB'}), 400
            filename = save_file(image)
            story = Story(
                title=request.form['title'],
                content=request.form['content'],
                image=filename
            )
            db.session.add(story)
            db.session.commit()
            return jsonify({'message': 'Story created successfully'}), 201
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Database error in POST /api/stories: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        except Exception as e:
            db.session.rollback()
            logging.error(f"Unexpected error in POST /api/stories: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/stories/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def handle_story(id):
    story = Story.query.get_or_404(id)
    if request.method == 'GET':
        return jsonify({
            'id': story.id,
            'title': story.title,
            'content': story.content,
            'image': story.image
        })
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    if request.method == 'PUT':
        try:
            story.title = request.form.get('title', story.title)
            story.content = request.form.get('content', story.content)
            if 'image' in request.files and request.files['image'].filename:
                image = request.files['image']
                if not allowed_file(image.filename):
                    return jsonify({'error': 'Invalid image format'}), 400
                if image.content_length > 3 * 1024 * 1024:
                    return jsonify({'error': 'Image size exceeds 3MB'}), 400
                filename = save_file(image)
                if story.image and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], story.image)):
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], story.image))
                story.image = filename
            db.session.commit()
            return jsonify({'message': 'Story updated successfully'})
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Database error in PUT /api/stories/{id}: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        except Exception as e:
            db.session.rollback()
            logging.error(f"Unexpected error in PUT /api/stories/{id}: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    if request.method == 'DELETE':
        try:
            if story.image and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], story.image)):
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], story.image))
            db.session.delete(story)
            db.session.commit()
            return jsonify({'message': 'Story deleted successfully'})
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Database error in DELETE /api/stories/{id}: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        except Exception as e:
            db.session.rollback()
            logging.error(f"Unexpected error in DELETE /api/stories/{id}: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
        
@app.route('/stories')
def stories():
    try:
        stories = Story.query.all()
        logging.debug(f"Stories fetched: {len(stories)}")
        for s in stories:
            logging.debug(f"Story: {s.id}, {s.title}, {s.image}")
        if not stories:
            logging.warning("No stories found in the database")
        return render_template('index.html', stories=stories)
    except Exception as e:
        logging.error(f"Error fetching stories: {str(e)}")
        return render_template('index.html', stories=[])
    
# Review Routes
@app.route('/api/reviews', methods=['GET'])
def handle_reviews():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    reviews = Review.query.all()
    return jsonify([
        {
            'id': r.id,
            'product': Product.query.get(r.product_id).name,
            'customer': User.query.get(r.user_id).name,
            'rating': r.rating,
            'comment': r.comment,
            'status': r.status
        } for r in reviews
    ])

@app.route('/api/reviews/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def handle_review(id):
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    review = Review.query.get_or_404(id)
    if request.method == 'GET':
        return jsonify({
            'id': review.id,
            'product': Product.query.get(review.product_id).name,
            'customer': User.query.get(review.user_id).name,
            'rating': review.rating,
            'comment': review.comment,
            'status': review.status
        })
    if request.method == 'PUT':
        try:
            data = request.get_json()
            review.status = data.get('status', review.status)
            db.session.commit()
            return jsonify({'message': 'Review updated successfully'})
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Database error in PUT /api/reviews/{id}: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        except Exception as e:
            db.session.rollback()
            logging.error(f"Unexpected error in PUT /api/reviews/{id}: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    if request.method == 'DELETE':
        try:
            db.session.delete(review)
            db.session.commit()
            return jsonify({'message': 'Review deleted successfully'})
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Database error in DELETE /api/reviews/{id}: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        except Exception as e:
            db.session.rollback()
            logging.error(f"Unexpected error in DELETE /api/reviews/{id}: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

# Other routes (unchanged)
@app.route('/api/change_admin_password', methods=['POST'])
def change_admin_password():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    if not current_password or not new_password:
        return jsonify({'error': 'Current and new password are required'}), 400
    admin = User.query.get(session['admin'])
    if not check_password_hash(admin.password, current_password):
        return jsonify({'error': 'Current password is incorrect'}), 400
    admin.password = generate_password_hash(new_password)
    db.session.commit()
    return jsonify({'message': 'Password updated successfully'})

@app.route('/api/dashboard_stats')
def dashboard_stats():
    total_sales = db.session.query(func.sum(Order.total)).filter(Order.status == 'Delivered').scalar() or 0
    new_users = User.query.filter(User.created_at >= datetime.utcnow() - timedelta(days=30)).count()
    pending_orders = Order.query.filter_by(status='Pending').count()
    top_product = db.session.query(Product.name)\
        .join(OrderItem, Product.id == OrderItem.product_id)\
        .group_by(Product.id)\
        .order_by(func.count(OrderItem.id).desc())\
        .first()
    top_product_name = top_product[0] if top_product else 'N/A'

    sales_data = [
        {'month': (datetime.utcnow() - timedelta(days=30*i)).strftime('%Y-%m'), 'total': 0}
        for i in range(6, -1, -1)
    ]
    sales_query = db.session.query(
        func.strftime('%Y-%m', Order.created_at).label('month'),
        func.sum(Order.total).label('total')
    ).filter(Order.status == 'Delivered').group_by('month').all()
    for sale in sales_query:
        for data in sales_data:
            if data['month'] == sale.month:
                data['total'] = float(sale.total)

    users_data = [
        {'month': (datetime.utcnow() - timedelta(days=30*i)).strftime('%Y-%m'), 'count': 0}
        for i in range(6, -1, -1)
    ]
    users_query = db.session.query(
        func.strftime('%Y-%m', User.created_at).label('month'),
        func.count(User.id).label('count')
    ).group_by('month').all()
    for user in users_query:
        for data in users_data:
            if data['month'] == user.month:
                data['count'] = user.count

    return jsonify({
        'total_sales': total_sales,
        'new_users': new_users,
        'pending_orders': pending_orders,
        'top_product': top_product_name,
        'sales_data': sales_data,
        'users_data': users_data
    })

@app.route('/api/orders/<int:id>/cancel', methods=['POST'])
def cancel_order(id):
    try:
        logging.debug(f"Session contents: {dict(session)}")
        if 'user' not in session:
            logging.debug('Unauthorized: No user in session')
            return jsonify({'error': 'Unauthorized'}), 401
        user_email = session['user']
        order = Order.query.get_or_404(id)
        user = User.query.filter_by(email=user_email).first()
        if not user or order.user_id != user.id:
            logging.debug(f'Unauthorized: User {user_email} does not own order {id}')
            return jsonify({'error': 'Unauthorized'}), 403
        if order.status != 'Pending':
            logging.debug(f'Order {id} cannot be canceled, status: {order.status}')
            return jsonify({'error': 'Only pending orders can be canceled'}), 400
        order.status = 'Canceled'
        db.session.commit()
        logging.debug(f'Order {id} canceled by user {user_email}')
        return jsonify({'message': 'Order canceled successfully'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error in POST /api/orders/{id}/cancel: {str(e)}")
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        db.session.rollback()
        logging.error(f"Unexpected error in POST /api/orders/{id}/cancel: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/orders', methods=['POST'])
def create_order():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    user = User.query.filter_by(email=session['user']).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    user_id = user.id
    data = request.get_json()
    
    required_fields = ['name', 'phone_number', 'address', 'payment_method']
    missing_fields = [field for field in required_fields if field not in data or not data[field]]
    if missing_fields:
        return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
    if data['payment_method'] not in ['immediate', 'delivery']:
        return jsonify({'error': 'Invalid payment method'}), 400
    if data['payment_method'] == 'immediate' and not data.get('message_code'):
        return jsonify({'error': 'Message code required for immediate payment'}), 400
    
    cart_items = Cart.query.filter_by(user_id=user_id).all()
    if not cart_items:
        return jsonify({'error': 'Cart is empty'}), 400
    
    total = 0
    for item in cart_items:
        product = Product.query.get(item.product_id)
        if not product:
            return jsonify({'error': f'Product ID {item.product_id} not found'}), 404
        total += product.price * item.quantity
    
    order = Order(
        user_id=user_id,
        total=total,
        status='Pending',
        payment_method=data['payment_method'],
        message_code=data.get('message_code')
    )
    db.session.add(order)
    db.session.flush()
    
    for item in cart_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity
        )
        db.session.add(order_item)
    
    Cart.query.filter_by(user_id=user_id).delete()
    
    user.address = data['address']
    user.name = data['name']
    user.phone_number = data['phone_number']
    
    db.session.commit()
    logging.debug(f"Order created: order_id={order.id}, user_id={user_id}, payment_method={data['payment_method']}")
    return jsonify({'message': 'Order placed successfully', 'order_id': order.id}), 201

@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        try:
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
            if not email or not password:
                logging.debug('Invalid login request: Missing email or password')
                return jsonify({'error': 'Email and password are required'}), 400
            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password, password) and user.role in ['buyer', 'artisan']:
                session['user'] = email
                session.permanent = True
                logging.debug(f'User {email} logged in, session: {dict(session)}')
                return jsonify({'message': 'Login successful', 'role': user.role}), 200
            logging.debug(f'Invalid login attempt for {email}')
            return jsonify({'error': 'Invalid credentials or not a user/artisan'}), 401
        except SQLAlchemyError as e:
            logging.error(f"Database error in POST /user_login: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        except Exception as e:
            logging.error(f"Unexpected error in POST /user_login: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    return render_template('user-login.html')

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        required_fields = ['name', 'email', 'password', 'role']
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
        if len(data['password']) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        if data['role'] not in ['buyer', 'artisan']:
            return jsonify({'error': 'Invalid role'}), 400
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400
        username = data['email'].split('@')[0]
        if User.query.filter_by(username=username).first():
            username = f"{username}_{datetime.now().timestamp()}"
        user = User(
            username=username,
            name=data['name'],
            email=data['email'],
            password=generate_password_hash(data['password']),
            role=data['role']
        )
        db.session.add(user)
        if data['role'] == 'artisan':
            artisan = Artisan(
                name=data['name'],
                email=data['email'],
                phone_number=data.get('phone_number', ''),
                status='Pending'
            )
            db.session.add(artisan)
        db.session.commit()
        return jsonify({'message': 'Registration successful'}), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error in POST /register: {str(e)}")
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        db.session.rollback()
        logging.error(f"Unexpected error in POST /register: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/reset_password', methods=['POST'])
def reset_password():
    try:
        data = request.get_json()
        email = data.get('email')
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': 'Email not found'}), 404
        return jsonify({'message': 'Password reset link sent (not implemented)'})
    except SQLAlchemyError as e:
        logging.error(f"Database error in POST /reset_password: {str(e)}")
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        logging.error(f"Unexpected error in POST /reset_password: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/check_session', methods=['GET'])
def check_session():
    if 'user' in session:
        return jsonify({'message': 'Session valid', 'email': session['user']}), 200
    return jsonify({'error': 'Unauthorized'}), 401

@app.route('/account')
def account():
    if 'user' not in session:
        return redirect(url_for('user_login'))
    user = User.query.filter_by(email=session['user']).first()
    if not user:
        session.pop('user', None)
        return redirect(url_for('user_login'))
    
    wishlist_items = Wishlist.query.filter_by(user_id=user.id).join(Product).all()
    cart_items = Cart.query.filter_by(user_id=user.id).join(Product).all()
    orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()
    
    return render_template('account.html',
                           user=user,
                           wishlist_items=wishlist_items,
                           cart_items=cart_items,
                           orders=orders,
                           address=user.address or {},
                           current_currency='USD')

@app.route('/our_products')
def our_products():
    if 'user' not in session:
        return redirect(url_for('user_login'))
    
    all_products = Product.query.order_by(Product.created_at.desc()).all()
    products = [
        p for p in all_products
        if not p.discount or p.discount.percent == 0
    ]
    
    categories = Category.query.all()
    
    return render_template(
        'artefacts.html',
        products=products,
        categories=categories,
        today=datetime.utcnow().date(),
        current_currency='USD'
    )

@app.route('/discounted_artefacts', endpoint='discounted_artefacts')
def products():
    if 'user' not in session:
        return redirect(url_for('user_login'))
    
    all_products = Product.query.order_by(Product.created_at.desc()).all()
    categories = Category.query.all()
    
    return render_template('products.html',
                           products=all_products,
                           categories=categories,
                           today=datetime.utcnow().date(),
                           current_currency='USD')

@app.route('/api/wishlist', methods=['GET', 'POST'])
def handle_wishlist():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    user = User.query.filter_by(email=session['user']).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    user_id = user.id
    if request.method == 'GET':
        wishlist_items = Wishlist.query.filter_by(user_id=user_id).join(Product).all()
        return jsonify([
            {
                'id': item.id,
                'product_id': item.product_id,
                'name': item.product.name,
                'price': item.product.price,
                'image': item.product.image
            } for item in wishlist_items
        ])
    if request.method == 'POST':
        try:
            data = request.get_json()
            product_id = data.get('product_id')
            if not product_id:
                return jsonify({'error': 'Product ID is required'}), 400
            product = Product.query.get(product_id)
            if not product:
                return jsonify({'error': 'Product not found'}), 404
            if Wishlist.query.filter_by(user_id=user_id, product_id=product_id).first():
                return jsonify({'message': 'Product already in wishlist'}), 200
            wishlist_item = Wishlist(user_id=user_id, product_id=product_id)
            db.session.add(wishlist_item)
            db.session.commit()
            return jsonify({'message': 'Product added to wishlist'}), 201
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Database error in POST /api/wishlist: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        except Exception as e:
            db.session.rollback()
            logging.error(f"Unexpected error in POST /api/wishlist: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/wishlist/<int:id>', methods=['DELETE'])
def delete_wishlist_item(id):
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    user = User.query.filter_by(email=session['user']).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    wishlist_item = Wishlist.query.get_or_404(id)
    if wishlist_item.user_id != user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    db.session.delete(wishlist_item)
    db.session.commit()
    return jsonify({'message': 'Product removed from wishlist'})

@app.route('/api/cart', methods=['GET', 'POST', 'PUT', 'DELETE'])
def handle_cart():
    # Check if user is logged in
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized', 'redirect': '/login'}), 401

    # Get user
    user = User.query.filter_by(email=session['user']).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    user_id = user.id

    if request.method == 'GET':
        # Retrieve cart items
        try:
            cart_items = Cart.query.filter_by(user_id=user_id).join(Product).all()
            return jsonify([
                {
                    'id': item.id,
                    'product_id': item.product_id,
                    'name': item.product.name,
                    'price': item.product.price,
                    'image': item.product.image,
                    'quantity': item.quantity,
                    'total_price': round(item.product.price * item.quantity, 2)
                } for item in cart_items
            ])
        except SQLAlchemyError as e:
            logging.error(f"Database error in GET /api/cart: {str(e)}")
            return jsonify({'error': 'Database error'}), 500

    elif request.method == 'POST':
        # Add or update product in cart
        try:
            data = request.get_json()
            product_id = data.get('product_id')
            quantity = data.get('quantity', 1)

            # Validate input
            if not product_id:
                return jsonify({'error': 'Product ID is required'}), 400
            if not isinstance(quantity, int) or quantity < 1:
                return jsonify({'error': 'Quantity must be a positive integer'}), 400

            product = Product.query.get(product_id)
            if not product:
                return jsonify({'error': 'Product not found'}), 404

            # Check stock availability (if applicable)
            if hasattr(product, 'stock') and product.stock < quantity:
                return jsonify({'error': f'Only {product.stock} items available in stock'}), 400

            cart_item = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()
            if cart_item:
                # Update existing cart item
                cart_item.quantity += quantity
            else:
                # Add new cart item
                cart_item = Cart(user_id=user_id, product_id=product_id, quantity=quantity)
                db.session.add(cart_item)

            db.session.commit()
            return jsonify({'message': 'Product added to cart', 'product_id': product_id, 'quantity': cart_item.quantity}), 201

        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Database error in POST /api/cart: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        except Exception as e:
            db.session.rollback()
            logging.error(f"Unexpected error in POST /api/cart: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

    elif request.method == 'PUT':
        # Update quantity of an existing cart item
        try:
            data = request.get_json()
            product_id = data.get('product_id')
            quantity = data.get('quantity')

            # Validate input
            if not product_id:
                return jsonify({'error': 'Product ID is required'}), 400
            if not isinstance(quantity, int) or quantity < 1:
                return jsonify({'error': 'Quantity must be a positive integer'}), 400

            cart_item = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()
            if not cart_item:
                return jsonify({'error': 'Cart item not found'}), 404

            product = Product.query.get(product_id)
            if not product:
                return jsonify({'error': 'Product not found'}), 404

            # Check stock availability (if applicable)
            if hasattr(product, 'stock') and product.stock < quantity:
                return jsonify({'error': f'Only {product.stock} items available in stock'}), 400

            cart_item.quantity = quantity
            db.session.commit()
            return jsonify({'message': 'Cart item updated', 'product_id': product_id, 'quantity': quantity}), 200

        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Database error in PUT /api/cart: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        except Exception as e:
            db.session.rollback()
            logging.error(f"Unexpected error in PUT /api/cart: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

    elif request.method == 'DELETE':
        # Remove product from cart
        try:
            data = request.get_json()
            product_id = data.get('product_id')

            if not product_id:
                return jsonify({'error': 'Product ID is required'}), 400

            cart_item = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()
            if not cart_item:
                return jsonify({'error': 'Cart item not found'}), 404

            db.session.delete(cart_item)
            db.session.commit()
            return jsonify({'message': 'Product removed from cart', 'product_id': product_id}), 200

        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Database error in DELETE /api/cart: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        except Exception as e:
            db.session.rollback()
            logging.error(f"Unexpected error in DELETE /api/cart: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/cart/<int:id>', methods=['DELETE'])
def delete_cart_item(id):
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    user = User.query.filter_by(email=session['user']).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    cart_item = Cart.query.get_or_404(id)
    if cart_item.user_id != user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    db.session.delete(cart_item)
    db.session.commit()
    return jsonify({'message': 'Product removed from cart'})

@app.route('/api/profile/picture', methods=['POST'])
def upload_profile_picture():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    if 'image' not in request.files:
        return jsonify({'error': 'Image is required'}), 400
    image = request.files['image']
    if not allowed_file(image.filename):
        return jsonify({'error': 'Invalid image format'}), 400
    filename = save_file(image)
    user = User.query.filter_by(email=session['user']).first()
    user.profile_picture = filename
    db.session.commit()
    return jsonify({'message': 'Profile picture updated', 'image_url': url_for('static', filename=f'uploads/{filename}')})

@app.route('/api/profile/address', methods=['POST'])
def add_address():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    user = User.query.filter_by(email=session['user']).first()
    user.address = data
    db.session.commit()
    return jsonify({'message': 'Address added successfully'})

@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Endpoint not found'}), 404
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)