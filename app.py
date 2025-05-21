from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy.orm import sessionmaker, joinedload
from sqlalchemy import desc  # Import desc for ordering
import requests
import os
import string
import secrets
import random
import string
import uuid
# from models import Story
from datetime import datetime, timedelta
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
import logging
from flask_mail import Mail, Message
from flask_migrate import Migrate  # Add Flask-Migrate


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
logging.basicConfig(level=logging.INFO)
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        return filename
    return None

def validate_reset_token(token):
    user = User.query.filter_by(reset_token=token).first()
    if user and user.reset_token_expiry > datetime.utcnow():
        return user
    return None


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'zira_collection')  # Use env var
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Allow redirects
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JS access
app.config['SESSION_COOKIE_SECURE'] = False  # HTTP
app.config['SESSION_COOKIE_NAME'] = 'session'  # Explicit name


# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'vickiebmochama@gmail.com'
app.config['MAIL_PASSWORD'] = 'yugj xofc egbp whyn'
app.config['MAIL_DEFAULT_SENDER'] = 'vickiebmochama@gmail.com'

API_URL = 'https://api.apilayer.com/exchangerates_data/latest'
API_KEY = 'pgAxSoHnw8N0b2AEeap3wfuEd7wsSP2D'
SUPPORTED_CURRENCIES = ['EUR', 'GBP', 'KES', 'USD']
CACHE_DURATION = timedelta(days=1)  # Changed to 1 day for daily fetching

def get_next_mid_month():
    today = datetime.utcnow()
    if today.day >= 15:
        # Next month
        next_month = today.replace(day=1) + timedelta(days=32)
        next_month = next_month.replace(day=15)
    else:
        # Current month
        next_month = today.replace(day=15)
    return next_month

db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Initialize Flask-Migrate
mail = Mail(app)
# logger.debug("Flask-Mail initialized with mail object: %s", mail)

# Generate random password
def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

# Token generation and validation helpers
def generate_reset_token():
    return secrets.token_urlsafe(32)

def store_reset_token(user, token):
    user.reset_token = token
    user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)  # 1-hour expiry
    db.session.commit()

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
    reset_token = db.Column(db.String(255))  # New column for reset token
    reset_token_expiry = db.Column(db.DateTime)  # New column for token expiry
    
    
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
    customer_status = db.Column(db.String(20), default='Active')
    payment_method = db.Column(db.String(20), nullable=False)
    message_code = db.Column(db.String(50), nullable=True)
    customer_name = db.Column(db.String(100), nullable=True)  # New field
    customer_number = db.Column(db.String(15), nullable=True)  # New field
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
    
class ExchangeRate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    eur = db.Column(db.Float, nullable=False)  # 1 KES = X EUR
    gbp = db.Column(db.Float, nullable=False)  # 1 KES = X GBP
    kes = db.Column(db.Float, nullable=False, default=1.0)  # 1 KES = 1 KES
    usd = db.Column(db.Float, nullable=False)  # 1 KES = X USD
    depletion_timestamp = db.Column(db.DateTime, nullable=True)  # When to retry API after depletion

# Database Initialization
# Database Initialization
# Database Initialization
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
            role='buyer',
            address={
                'street': '00100 Northern Bypass Road, Intersection',
                'city': 'Nairobi',
                'country': 'Kenya',
                'postal_code': '00100'
            }
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
        if user:  # Only proceed if user exists
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

    # Ensure existing orders have customer_status
    Order.query.filter_by(customer_status=None).update({'customer_status': 'Active'})
    db.session.commit()
    
    
@app.route('/')
def index():
    # Get currency from session, default to KES (or USD if preferred)
    current_currency = session.get('currency', 'KES')  # Changed default to KES for consistency with your site’s Kenyan focus

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
        current_currency=current_currency,  # Pass the session currency
        stories=stories
    )

@app.route('/set_currency', methods=['POST'])
def set_currency():
    currency = request.json.get('currency')
    if currency in ['USD', 'EUR', 'GBP', 'KES']:
        session['currency'] = currency
        return jsonify({'status': 'success', 'currency': currency})
    return jsonify({'status': 'error', 'message': 'Invalid currency'}), 400


@app.route('/admin')
def admin():
    if 'admin' not in session:
        app.logger.debug("No admin session, redirecting to login")
        return redirect(url_for('login'))
    app.logger.debug("Rendering admin.html")
    return render_template('admin.html')

@app.route('/debug_session')
def debug_session():
    app.logger.debug("Checking session")
    return jsonify({
        'admin_in_session': 'admin' in session,
        'admin_id': session.get('admin')
    })

# Admin Forgot Password Route
@app.route('/api/admin_forgot_password', methods=['POST'])
def admin_forgot_password():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({'error': 'Email is required'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or user.role != 'admin':
        return jsonify({'error': 'No admin account found with this email'}), 404

    # Generate random password and reset token
    random_password = generate_random_password()
    reset_token = generate_reset_token()
    token_expiry = datetime.utcnow() + timedelta(hours=1)

    # Update user with temporary password and reset token
    user.password = generate_password_hash(random_password)
    user.reset_token = reset_token
    user.reset_token_expiry = token_expiry
    db.session.commit()

    # Create styled HTML email
    html_body = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Zira Collections Admin Password Reset</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
                color: #333;
            }}
            .container {{
                max-width: 600px;
                margin: 20px auto;
                background-color: #ffffff;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                overflow: hidden;
            }}
            .header {{
                background-color: #2c3e50;
                padding: 20px;
                text-align: center;
                color: #ffffff;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
            }}
            .content {{
                padding: 20px;
                line-height: 1.6;
            }}
            .content h2 {{
                color: #2c3e50;
                font-size: 20px;
            }}
            .content p {{
                margin: 10px 0;
            }}
            .temporary-password {{
                background-color: #e8f0fe;
                padding: 15px;
                border-radius: 5px;
                font-size: 18px;
                font-weight: bold;
                color: #1a73e8;
                text-align: center;
                margin: 20px 0;
            }}
            .cta-button {{
                display: inline-block;
                padding: 12px 24px;
                background-color: #1a73e8;
                color: #ffffff;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
                margin: 20px 0;
            }}
            .footer {{
                background-color: #f4f4f4;
                padding: 15px;
                text-align: center;
                font-size: 12px;
                color: #666;
            }}
            .footer a {{
                color: #1a73e8;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Zira Collections</h1>
            </div>
            <div class="content">
                <h2>Admin Password Reset</h2>
                <p>Hello,</p>
                <p>We received a request to reset your password for your Zira Collections admin account. Below is your temporary password, which is valid for 1 hour:</p>
                <div class="temporary-password">{random_password}</div>
                <p>Please use this temporary password to log in and reset your password immediately. For security reasons, this password will expire after 1 hour.</p>
                <a href="https://your-domain.com/login" class="cta-button">Log In Now</a>
                <p>If you did not request a password reset, please contact our support team immediately at <a href="mailto:support@ziracollections.com">support@ziracollections.com</a>.</p>
                <p>Thank you,<br>The Zira Collections Team</p>
            </div>
            <div class="footer">
                <p>&copy; {datetime.utcnow().year} Zira Collections. All rights reserved.</p>
                <p><a href="https://your-domain.com">Visit our website</a> | <a href="mailto:support@ziracollections.com">Contact Support</a></p>
            </div>
        </div>
    </body>
    </html>
    """

    # Send email with styled HTML
    try:
        msg = Message(
            subject='Zira Collections Admin Password Reset',
            recipients=[email],
            body=f'Your temporary password is: {random_password}\n\nThis password is valid for 1 hour. Please log in and reset your password immediately.',
            html=html_body  # Include the HTML version
        )
        mail.send(msg)
        return jsonify({'message': 'A temporary password has been sent to your email.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to send email. Please try again later.'}), 500
    

# Admin Reset Password Route
@app.route('/api/admin_reset_password', methods=['POST'])
def admin_reset_password():
    data = request.get_json()
    username = data.get('username')
    current_password = data.get('current_password')
    new_password = data.get('new_password')

    if not username or not current_password or not new_password:
        return jsonify({'error': 'Username, current password, and new password are required'}), 400

    user = User.query.filter_by(username=username).first()
    if not user or user.role != 'admin':
        return jsonify({'error': 'Admin user not found'}), 404

    # Verify current password
    if not check_password_hash(user.password, current_password):
        return jsonify({'error': 'Current password is incorrect'}), 400

    #fellVerify reset token and expiry
    if not user.reset_token or not user.reset_token_expiry or user.reset_token_expiry < datetime.utcnow():
        return jsonify({'error': 'Invalid or expired reset token'}), 400

    # Update password and clear reset token
    user.password = generate_password_hash(new_password)
    user.reset_token = None
    user.reset_token_expiry = None
    db.session.commit()

    return jsonify({'message': 'Password updated successfully'})


# Routes (unchanged except for redirect in /login)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        app.logger.debug(f"Login attempt for username: {username}")

        if not username or not password:
            app.logger.debug("Missing username or password")
            return jsonify({'error': 'Username and password are required'}), 400

        user = User.query.filter_by(username=username).first()
        if not user:
            app.logger.debug(f"No user found for username: {username}")
            return jsonify({'error': 'Invalid username'}), 401

        if not check_password_hash(user.password, password):
            app.logger.debug("Password check failed")
            return jsonify({'error': 'Invalid password'}), 401

        if user.role != 'admin':
            app.logger.debug(f"User {username} is not an admin, role: {user.role}")
            return jsonify({'error': 'Access denied: Admin role required'}), 403

        if user.reset_token and user.reset_token_expiry and user.reset_token_expiry > datetime.utcnow():
            app.logger.debug(f"Reset token active for user: {username}")
            return jsonify({
                'message': 'Password reset required',
                'reset_required': True,
                'username': user.username
            }), 200

        session['admin'] = user.id
        app.logger.debug(f"Login successful for user: {username}, redirecting to admin")
        return redirect(url_for('admin'))  # Server-side redirect

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

@app.route('/api/orders', methods=['GET'])
def get_orders():
    # Check for admin or user session
    if 'admin' not in session and 'user' not in session:
        app.logger.debug("No admin or user in session")
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Fetch orders based on session
        if 'admin' in session:
            orders = db.session.query(Order).all()
            app.logger.debug("Fetching all orders for admin")
        else:  # user in session
            user = User.query.filter_by(email=session['user']).first()
            if not user:
                app.logger.error(f"User not found for email: {session['user']}")
                return jsonify({'error': 'User not found'}), 404
            user_id = user.id
            orders = db.session.query(Order).filter_by(user_id=user_id).all()
            app.logger.debug(f"Fetching orders for user_id: {user_id}")

        orders_data = []
        for order in orders:
            # Fetch user details
            user = User.query.get(order.user_id)
            customer_name = order.customer_name or (user.name if user else 'Unknown')
            customer_number = order.customer_number or (user.phone_number if user and user.phone_number else 'N/A')
            location = user.address if user and hasattr(user, 'address') and isinstance(user.address, dict) else {}

            # Fetch order items with joined Product data
            order_items = db.session.query(OrderItem).filter_by(order_id=order.id).join(Product, isouter=True).all()
            items_data = []
            for item in order_items:
                product = item.product
                items_data.append({
                    'product_id': item.product_id,
                    'product_name': product.name if product else 'Deleted Product',
                    'quantity': item.quantity,
                    'image': product.image if product and product.image else 'default.jpg'
                })

            orders_data.append({
                'id': order.id,
                'customer': customer_name,
                'customer_number': customer_number,
                'location': {
                    'street': location.get('street', ''),
                    'city': location.get('city', ''),
                    'country': location.get('country', ''),
                    'postal_code': location.get('postal_code', '')
                },
                'total': float(order.total),
                'customer_status': order.customer_status,
                'status': order.status,
                'payment_method': order.payment_method,
                'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S') if order.created_at else '',
                'items': items_data
            })

        app.logger.debug(f"Returning {len(orders_data)} orders with items: {[order['items'] for order in orders_data]}")
        return jsonify(orders_data)

    except SQLAlchemyError as e:
        app.logger.error(f"Database error fetching orders: {str(e)}")
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        app.logger.error(f"Unexpected error fetching orders: {str(e)}")
        return jsonify({'error': 'Failed to fetch orders'}), 500



@app.route('/api/orders/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def handle_order(id):
    if 'admin' not in session:
        app.logger.debug('No admin in session')
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        order = Order.query.get_or_404(id)
        if request.method == 'GET':
            user = User.query.get(order.user_id)
            # Use customer_name and customer_number if available, else fall back to user details
            customer_name = order.customer_name or (user.name if user else 'Unknown')
            customer_number = order.customer_number or (user.phone_number if user and user.phone_number else 'N/A')
            # Use user.address as location, default to empty dict if missing
            location = user.address if user and hasattr(user, 'address') and isinstance(user.address, dict) else {}
            order_items = OrderItem.query.filter_by(order_id=order.id).all()
            items_data = [
                {
                    'product_id': item.product_id,
                    'product_name': Product.query.get(item.product_id).name if Product.query.get(item.product_id) else 'Deleted Product',
                    'quantity': item.quantity
                } for item in order_items
            ]
            return jsonify({
                'id': order.id,
                'customer': customer_name,
                'customer_number': customer_number,
                'location': {
                    'street': location.get('street', ''),
                    'city': location.get('city', ''),
                    'country': location.get('country', ''),
                    'postal_code': location.get('postal_code', '')
                },
                'total': float(order.total),
                'status': order.status,
                'customer_status': order.customer_status,
                'payment_method': order.payment_method,
                'items': items_data
            }), 200
        if request.method == 'PUT':
            data = request.get_json()
            order.status = data.get('status', order.status)
            db.session.commit()
            app.logger.debug(f'Order {id} status updated to {order.status}')
            return jsonify({'message': 'Order updated successfully'}), 200
        if request.method == 'DELETE':
            OrderItem.query.filter_by(order_id=id).delete()
            db.session.delete(order)
            db.session.commit()
            app.logger.debug(f'Order {id} deleted')
            return jsonify({'message': 'Order deleted successfully'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        app.logger.error(f"Database error in /api/orders/{id}: {str(e)}")
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Unexpected error in /api/orders/{id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
    
@app.route('/api/manual_orders', methods=['POST'])
def create_manual_order():
    if 'admin' not in session:
        logging.debug('Unauthorized: No admin in session')
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        logging.debug(f"Received manual order data: {data}")

        # Required fields for manual order
        required_fields = ['customer_name', 'customer_number', 'payment_method', 'products']
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        if missing_fields:
            logging.error(f"Missing required fields: {missing_fields}")
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400

        customer_name = data['customer_name']
        customer_number = data['customer_number']
        payment_method = data['payment_method']
        message_code = data.get('message_code')
        products = data['products']  # List of {product_id, quantity}

        # Validate payment method
        if payment_method not in ['immediate', 'delivery']:
            logging.error(f"Invalid payment method: {payment_method}")
            return jsonify({'error': 'Invalid payment method'}), 400
        if payment_method == 'immediate' and not message_code:
            logging.error("Message code required for immediate payment")
            return jsonify({'error': 'Message code required for immediate payment'}), 400

        # Validate customer details
        if len(customer_name) > 100:
            logging.error("Customer name too long")
            return jsonify({'error': 'Customer name must be 100 characters or less'}), 400
        if customer_number and len(customer_number) > 15:
            logging.error("Customer number too long")
            return jsonify({'error': 'Customer number must be 15 characters or less'}), 400

        # Validate products
        if not isinstance(products, list) or not products:
            logging.error("Products must be a non-empty list")
            return jsonify({'error': 'Products must be a non-empty list'}), 400

        total = 0
        order_items_data = []
        for item in products:
            product_id = item.get('product_id')
            quantity = item.get('quantity')
            if not product_id or not isinstance(quantity, int) or quantity < 1:
                logging.error(f"Invalid product data: product_id={product_id}, quantity={quantity}")
                return jsonify({'error': 'Each product must have a valid product_id and positive quantity'}), 400

            product = Product.query.get(product_id)
            if not product:
                logging.error(f"Product not found: product_id={product_id}")
                return jsonify({'error': f'Product ID {product_id} not found'}), 404

            # Calculate price with discount if applicable
            price = product.price
            if product.discount and product.discount.start_date <= datetime.utcnow().date() <= product.discount.end_date:
                price = price * (1 - product.discount.percent / 100)
                logging.debug(f"Applied discount for product {product_id}: {product.discount.percent}%")

            total += price * quantity
            order_items_data.append({'product_id': product_id, 'quantity': quantity})
            logging.debug(f"Processed product: product_id={product_id}, price={price}, quantity={quantity}, subtotal={price * quantity}")

        # Find or create a user for manual orders
        # We'll use a default user for manual orders or create a guest user
        user_email = f"manual_{customer_number.replace('+', '')}@zira.com"
        user = User.query.filter_by(email=user_email).first()
        if not user:
            username = f"manual_{customer_number.replace('+', '')}_{datetime.now().timestamp()}"
            user = User(
                username=username,
                name=customer_name,
                email=user_email,
                phone_number=customer_number,
                password=generate_password_hash('manual_order_default'),
                role='buyer'
            )
            db.session.add(user)
            db.session.flush()
            logging.debug(f"Created new user for manual order: email={user_email}")

        # Create the order
        order = Order(
            user_id=user.id,
            total=total,
            status='Pending',
            customer_status='Active',
            payment_method=payment_method,
            message_code=message_code,
            customer_name=customer_name,
            customer_number=customer_number,
            created_at=datetime.utcnow()
        )
        db.session.add(order)
        db.session.flush()
        logging.debug(f"Created order: order_id={order.id}, total={total}")

        # Create order items
        for item in order_items_data:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item['product_id'],
                quantity=item['quantity']
            )
            db.session.add(order_item)
            logging.debug(f"Added order item: product_id={item['product_id']}, quantity={item['quantity']}")

        db.session.commit()
        logging.info(f"Manual order created successfully: order_id={order.id}, customer={customer_name}")

        return jsonify({
            'message': 'Manual order created successfully',
            'order_id': order.id,
            'total': float(total)
        }), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error in POST /api/manual_orders: {str(e)}")
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        db.session.rollback()
        logging.error(f"Unexpected error in POST /api/manual_orders: {str(e)}")
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
    if 'admin' not in session:  # Changed from 'user' to 'admin'
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


# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

@app.route('/api/dashboard_stats', methods=['GET'])
def dashboard_stats():
    logger.debug('Entering /api/dashboard_stats')
    
    # Check session
    if 'admin' not in session:
        logger.debug('No admin in session')
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Define date range: last 30 days
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=30)
        logger.debug(f'Date range: {start_date} to {end_date}')

        # Sales data: Aggregate total sales by day
        try:
            sales_query = db.session.query(
                func.date(Order.created_at).label('date'),
                func.sum(Order.total).label('total')
            ).filter(
                Order.created_at >= start_date,
                Order.status != 'Canceled'
            ).group_by(
                func.date(Order.created_at)
            ).order_by(
                func.date(Order.created_at)
            ).all()
            logger.debug(f'Sales query result: {len(sales_query)} rows')
        except Exception as e:
            logger.error(f'Sales query failed: {str(e)}')
            sales_query = []

        sales_data = [
            {'date': str(row.date), 'total': float(row.total or 0.0)}
            for row in sales_query
        ]

        # Fill missing days with zero sales
        all_dates = [(start_date + timedelta(days=x)).strftime('%Y-%m-%d') for x in range(31)]
        sales_data_dict = {item['date']: item['total'] for item in sales_data}
        sales_data = [
            {'date': date, 'total': sales_data_dict.get(date, 0.0)}
            for date in all_dates
        ]
        logger.debug(f'Sales data length: {len(sales_data)}')

        # Users data: Aggregate new users by day
        try:
            users_query = db.session.query(
                func.date(User.created_at).label('date'),
                func.count(User.id).label('count')
            ).filter(
                User.created_at >= start_date
            ).group_by(
                func.date(User.created_at)
            ).order_by(
                func.date(User.created_at)
            ).all()
            logger.debug(f'Users query result: {len(users_query)} rows')
        except Exception as e:
            logger.error(f'Users query failed: {str(e)}')
            users_query = []

        users_data = [
            {'date': str(row.date), 'count': int(row.count or 0)}
            for row in users_query
        ]

        # Fill missing days with zero users
        users_data_dict = {item['date']: item['count'] for item in users_data}
        users_data = [
            {'date': date, 'count': users_data_dict.get(date, 0)}
            for date in all_dates
        ]
        logger.debug(f'Users data length: {len(users_data)}')

        # Total sales (all time, only Delivered orders)
        try:
            total_sales = db.session.query(func.sum(Order.total)).filter(Order.status == 'Delivered').scalar() or 0.0
            logger.debug(f'Total sales: {total_sales}')
        except Exception as e:
            logger.error(f'Total sales query failed: {str(e)}')
            total_sales = 0.0

        # New users (last 30 days)
        try:
            new_users = db.session.query(func.count(User.id)).filter(User.created_at >= start_date).scalar() or 0
            logger.debug(f'New users: {new_users}')
        except Exception as e:
            logger.error(f'New users query failed: {str(e)}')
            new_users = 0

        # Pending orders
        try:
            pending_orders = db.session.query(func.count(Order.id)).filter(Order.status == 'Pending').scalar() or 0
            logger.debug(f'Pending orders: {pending_orders}')
        except Exception as e:
            logger.error(f'Pending orders query failed: {str(e)}')
            pending_orders = 0

        # Top product (by total quantity in completed orders in last 30 days)
        try:
            top_product_query = db.session.query(
                Product.name,
                func.sum(OrderItem.quantity).label('total_quantity')
            ).join(OrderItem, Product.id == OrderItem.product_id).join(
                Order, OrderItem.order_id == Order.id
            ).filter(
                Order.created_at >= start_date,
                Order.status == 'Delivered'
            ).group_by(
                Product.name
            ).order_by(
                func.sum(OrderItem.quantity).desc()
            ).first()
            top_product = top_product_query.name if top_product_query else 'None'
            logger.debug(f'Top product: {top_product} (Total quantity: {top_product_query.total_quantity if top_product_query else 0})')
        except Exception as e:
            logger.error(f'Top product query failed: {str(e)}')
            top_product = 'None'

        response = {
            'total_sales': float(total_sales),
            'new_users': new_users,
            'pending_orders': pending_orders,
            'top_product': top_product,
            'sales_data': sales_data,
            'users_data': users_data
        }
        logger.debug('Dashboard stats response prepared')
        return jsonify(response), 200

    except Exception as e:
        logger.error(f'Unexpected error in dashboard_stats: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500
    
    
@app.route('/api/orders/<int:id>/cancel', methods=['POST'])
def cancel_order(id):
    try:
        logging.debug(f"Session contents: {dict(session)}, Cookies: {request.cookies}")
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
        order.customer_status = 'Canceled'
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
    
    # Fetch cart items with products and discounts
    cart_items = Cart.query.filter_by(user_id=user_id).options(
        joinedload(Cart.product).joinedload(Product.discount)
    ).all()
    if not cart_items:
        return jsonify({'error': 'Cart is empty'}), 400
    
    total = 0
    for item in cart_items:
        product = item.product
        if not product:
            return jsonify({'error': f'Product ID {item.product_id} not found'}), 404
        # Calculate discounted price in KES
        if product.discount and product.discount.percent > 0:
            price = product.price * (1 - product.discount.percent / 100)
        else:
            price = product.price
        total += price * item.quantity
        logging.debug(f"Cart item: product_id={item.product_id}, original_price={product.price}, discounted_price={price}, quantity={item.quantity}")
    
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
        product = item.product
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity
        )
        db.session.add(order_item)
    
    # Clear cart
    Cart.query.filter_by(user_id=user_id).delete()
    
    # Update user details
    user.address = data['address']
    user.name = data['name']
    user.phone_number = data['phone_number']
    
    db.session.commit()
    logging.debug(f"Order created: order_id={order.id}, user_id={user_id}, total={total}, payment_method={data['payment_method']}")
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

# Add /reset_password
@app.route('/reset_password', methods=['POST'])
def reset_password():
    logging.info('Received password reset submission')
    try:
        data = request.get_json()
        token = data.get('token')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        if not all([token, new_password, confirm_password]):
            logging.error('Missing reset fields')
            return jsonify({'error': 'Token, new password, and confirmation are required'}), 400
        if new_password != confirm_password:
            logging.error('Passwords do not match')
            return jsonify({'error': 'Passwords do not match'}), 400
        if len(new_password) < 6:
            logging.error('Password too short')
            return jsonify({'error': 'Password must be at least 6 characters'}), 400

        user = validate_reset_token(token)
        if not user:
            logging.warning('Invalid or expired token')
            return jsonify({'error': 'Invalid or expired token'}), 400

        user.password = generate_password_hash(new_password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        logging.info(f'Password reset successful for {user.email}')
        return jsonify({'message': 'Password changed successfully'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f'Database error in reset_password: {str(e)}')
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        logging.error(f'Reset password error: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500
    
    
@app.route('/api/check_session', methods=['GET'])
def check_session():
    # Check for admin session
    if 'admin' in session:
        user = User.query.get(session['admin'])
        if user and user.role == 'admin':
            return jsonify({
                'message': 'Session valid',
                'username': user.username,
                'role': user.role
            }), 200
    # Check for normal user session
    elif 'user' in session:
        user = User.query.get(session['user'])
        if user:
            return jsonify({
                'message': 'Session valid',
                'username': user.username,
                'role': user.role
            }), 200
    # No valid session
    return jsonify({'error': 'Unauthorized'}), 401

@app.route('/account')
def account():
    if 'user' not in session:
        return redirect(url_for('user_login'))
    
    # Handle case where session['user'] is a dictionary (for backward compatibility)
    user_email = session['user']
    if isinstance(user_email, dict) and 'email' in user_email:
        user_email = user_email['email']
        session['user'] = user_email  # Update session to store email string
    
    user = User.query.filter_by(email=user_email).first()
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
    all_products = Product.query.order_by(Product.created_at.desc()).all()
    products = [
        p for p in all_products
        if not p.discount or p.discount.percent == 0
    ]

    # Validate and log product data
    for p in products:
        p.name = p.name.strip() if p.name else "Unnamed Product"
        p.category = p.category.strip() if p.category else "Uncategorized"
        p.price = float(p.price) if p.price is not None else 0.0
        p.description = p.description if p.description else "No description available."
        p.image = p.image if p.image else "default.jpg"
        print(f"Product: id={p.id}, name={p.name}, category={p.category}, price={p.price}, description={p.description}, image={p.image}")

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
 #   if 'user' not in session:
    #    return redirect(url_for('user_login'))
    
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

# API endpoint to send email
@app.route('/api/send-email', methods=['POST'])
def send_email():
    logger.debug("Received request to /api/send-email")
    
    # Check session
    if 'user' not in session:
        logger.error("No user in session")
        return jsonify({'error': 'User not logged in'}), 401

    try:
        # Log session user
        user_email = session['user']
        logger.debug(f"Session user email: {user_email}")

        # Get form data
        data = request.get_json()
        if not data:
            logger.error("No JSON data received")
            return jsonify({'error': 'No data provided'}), 400

        subject = data.get('subject')
        message = data.get('message')
        logger.debug(f"Form data - subject: {subject}, message: {message}")

        if not subject or not message:
            logger.error("Missing subject or message")
            return jsonify({'error': 'Subject and message are required'}), 400

        # Query user
        user = User.query.filter_by(email=user_email).first()
        if not user:
            logger.error(f"User not found for email: {user_email}")
            return jsonify({'error': 'User not found'}), 404

        logger.debug(f"User found - name: {user.name}, email: {user.email}")

        # Replace newlines in message for HTML
        formatted_message = message.replace('\n', '<br>')

        # Prepare HTML email without logo
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4;">
                <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <tr>
                        <td style="background-color: #d97706; padding: 20px; text-align: center; border-top-left-radius: 8px; border-top-right-radius: 8px;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 24px;">Zira Collection</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 20px;">
                            <h2 style="color: #333333; margin-top: 0;">New Message from Zira Collection</h2>
                            <p style="color: #555555; line-height: 1.6;">You have received a new message from a Zira Collection user:</p>
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin: 20px 0;">
                                <tr>
                                    <td style="padding: 10px; background-color: #f9f9f9; border: 1px solid #e0e0e0; border-radius: 4px;">
                                        <strong style="color: #333333;">From:</strong> {user.name} <{user.email}>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px; background-color: #f9f9f9; border: 1px solid #e0e0e0; border-radius: 4px; margin-top: 10px;">
                                        <strong style="color: #333333;">Subject:</strong> {subject}
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px; background-color: #f9f9f9; border: 1px solid #e0e0e0; border-radius: 4px; font-size: 24px; margin-top: 10px;">
                                        <strong style="color: #333333;"></strong><br>{formatted_message}
                                    </td>
                                </tr>
                            </table>
                            <p style="color: #555555; line-height: 1.6;">Thank you for being part of Zira Collection!</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="background-color: #d97706; padding: 10px; text-align: center; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px;">
                            <p style="color: #ffffff; margin: 0; font-size: 12px;">© 2025 Zira Collection. All rights reserved.</p>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """

        # Prepare email
        msg = Message(
            subject=f"Zira Collection: {subject}",
            recipients=['vickiebmochama@gmail.com'],  # Recipient is vickiebmochama@gmail.com
            html=html_body,
            sender=(user.name, user.email)  # Sender is the logged-in user (name, email)
        )

        # Send email
        mail.send(msg)
        logger.info("Email sent successfully")

        return jsonify({'message': 'Email sent successfully'}), 200

    except Exception as e:
        logger.exception(f"Error sending email: {str(e)}")
        return jsonify({'error': f'Failed to send email: {str(e)}'}), 500
    

# Update /request_reset
@app.route('/request_reset', methods=['POST'])
def request_reset():
    try:
        data = request.get_json()
        email = data.get('email')
        if not email:
            logging.debug('Invalid reset request: Missing email')
            return jsonify({'error': 'Email is required'}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            logging.debug(f'Password reset failed: Email {email} not found')
            return jsonify({'error': 'Email not found'}), 404

        # Generate and store reset token
        token = generate_reset_token()
        store_reset_token(user, token)

        # Send email with reset token
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4;">
                <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <tr>
                        <td style="background-color: #d97706; padding: 20px; text-align: center; border-top-left-radius: 8px; border-top-right-radius: 8px;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 24px;">Zira Artifacts</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 20px;">
                            <h2 style="color: #333333; margin-top: 0;">Password Reset</h2>
                            <p style="color: #555555; line-height: 1.6;">Dear {user.name},</p>
                            <p style="color: #555555; line-height: 1.6;">You have requested to reset your password. Please use the following token to set a new password:</p>
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin: 20px 0;">
                                <tr>
                                    <td style="padding: 10px; background-color: #f9f9f9; border: 1px solid #e0e0e0; border-radius: 4px; text-align: center;">
                                        <strong style="color: #333333; font-size: 18px;">{token}</strong>
                                    </td>
                                </tr>
                            </table>
                            <p style="color: #555555; line-height: 1.6;">This token expires in 1 hour. Enter it in the password reset form to set your new password.</p>
                            <p style="color: #555555; line-height: 1.6;">If you did not request this reset, please contact support immediately.</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="background-color: #d97706; padding: 10px; text-align: center; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px;">
                            <p style="color: #ffffff; margin: 0; font-size: 12px;">© 2025 Zira Artifacts. All rights reserved.</p>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """

        msg = Message(
            subject="Zira Artifacts: Password Reset",
            recipients=[email],
            html=html_body,
            sender=('Zira Artifacts', 'vickiebmochama@gmail.com')
        )

        mail.send(msg)
        logging.info(f"Password reset email sent to {email}")

        return jsonify({'message': 'A reset token has been sent to your email'}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error in POST /request_reset: {str(e)}")
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        db.session.rollback()
        logging.error(f"Unexpected error in POST /request_reset: {str(e)}")
        return jsonify({'error': 'Failed to send email'}), 500
    
    
@app.route('/api/change_password', methods=['POST'])
def change_password():
    logging.info('Received request to /api/change_password')
    try:
        if 'user' not in session:
            logging.warning('Unauthorized access to /api/change_password')
            return jsonify({'error': 'Unauthorized'}), 401

        data = request.get_json()
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        # Validate input
        if not old_password or not new_password or not confirm_password:
            logging.error('Missing old_password, new_password, or confirm_password')
            return jsonify({'error': 'All password fields are required'}), 400
        if new_password != confirm_password:
            logging.error('New passwords do not match')
            return jsonify({'error': 'New passwords do not match'}), 400
        if len(new_password) < 8:
            logging.error('New password too short')
            return jsonify({'error': 'New password must be at least 8 characters long'}), 400

        # Find user
        user = User.query.filter_by(email=session['user']).first()
        if not user:
            logging.error(f'User not found for email: {session["user"]}')
            return jsonify({'error': 'User not found'}), 404

        # Verify old password
        if not check_password_hash(user.password, old_password):
            logging.error('Incorrect old password provided')
            return jsonify({'error': 'Incorrect old password'}), 400

        # Update password
        user.password = generate_password_hash(new_password)
        db.session.commit()

        logging.info(f"Password changed successfully for user {user.email}")
        return jsonify({'message': 'Password changed successfully'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error in POST /api/change_password: {str(e)}")
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        logging.error(f"Unexpected error in POST /api/change_password: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
    
@app.route('/api/exchange_rates', methods=['GET'])
def get_exchange_rates():
    # Check for latest valid rates in database
    latest_rate = ExchangeRate.query.order_by(desc(ExchangeRate.timestamp)).first()
    now = datetime.utcnow()

    if latest_rate:
        is_cache_valid = (now - latest_rate.timestamp) < CACHE_DURATION
        is_depleted = latest_rate.depletion_timestamp and now < latest_rate.depletion_timestamp

        if is_cache_valid and not is_depleted:
            rates = {
                'EUR': latest_rate.eur,
                'GBP': latest_rate.gbp,
                'KES': latest_rate.kes,
                'USD': latest_rate.usd
            }
            return jsonify(rates), 200

        if is_depleted:
            rates = {
                'EUR': latest_rate.eur,
                'GBP': latest_rate.gbp,
                'KES': latest_rate.kes,
                'USD': latest_rate.usd
            }
            return jsonify(rates), 200

    # Fetch new rates from API
    try:
        response = requests.get(
            f'{API_URL}?base=KES&symbols={",".join(SUPPORTED_CURRENCIES)}',
            headers={'apikey': API_KEY}
        )

        if response.status_code == 429:
            if latest_rate:
                rates = {
                    'EUR': latest_rate.eur,
                    'GBP': latest_rate.gbp,
                    'KES': latest_rate.kes,
                    'USD': latest_rate.usd
                }
                # Update depletion timestamp
                latest_rate.depletion_timestamp = get_next_mid_month()
                db.session.commit()
                return jsonify(rates), 200
            else:
                # Fallback to static rates
                rates = {
                    'EUR': 0.0073,
                    'GBP': 0.0061,
                    'KES': 1.0,
                    'USD': 0.0077
                }
                return jsonify(rates), 200

        response.raise_for_status()
        data = response.json()
        if not data.get('success') or not data.get('rates'):
            return jsonify({'error': 'Invalid API response'}), 500

        # Store new rates
        new_rate = ExchangeRate(
            eur=data['rates']['EUR'],
            gbp=data['rates']['GBP'],
            kes=data['rates']['KES'],
            usd=data['rates']['USD'],
            timestamp=now,
            depletion_timestamp=None
        )
        db.session.add(new_rate)
        db.session.commit()

        rates = {
            'EUR': new_rate.eur,
            'GBP': new_rate.gbp,
            'KES': new_rate.kes,
            'USD': new_rate.usd
        }
        return jsonify(rates), 200

    except requests.RequestException as e:
        if latest_rate:
            rates = {
                'EUR': latest_rate.eur,
                'GBP': latest_rate.gbp,
                'KES': latest_rate.kes,
                'USD': latest_rate.usd
            }
            return jsonify(rates), 200
        # Fallback to static rates
        rates = {
            'EUR': 0.0073,
            'GBP': 0.0061,
            'KES': 1.0,
            'USD': 0.0077
        }
        return jsonify(rates), 200
    
    
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