# app.py
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy.orm import sessionmaker, joinedload
from sqlalchemy import desc
from datetime import datetime, timedelta
from slugify import slugify
import os
import secrets
import random
import string
import base64
import logging
from sqlalchemy.sql import func
from sqlalchemy.exc import SQLAlchemyError  

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'zira_collection')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_NAME'] = 'session'

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'vickiebmochama@gmail.com'
app.config['MAIL_PASSWORD'] = 'yugj xofc egbp whyn'
app.config['MAIL_DEFAULT_SENDER'] = 'vickiebmochama@gmail.com'

# Ensure upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)

# Utility functions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        return filename
    return None

def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

def generate_reset_token():
    return secrets.token_urlsafe(32)

def store_reset_token(user, token):
    user.reset_token = token
    user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
    db.session.commit()

def validate_reset_token(token):
    user = User.query.filter_by(reset_token=token).first()
    if user and user.reset_token_expiry > datetime.utcnow():
        return user
    return None

def get_next_mid_month():
    today = datetime.utcnow()
    if today.day >= 15:
        next_month = today.replace(day=1) + timedelta(days=32)
        next_month = next_month.replace(day=15)
    else:
        next_month = today.replace(day=15)
    return next_month

# Models
class User(db.Model):
    __tablename__ = 'user'
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
    reset_token = db.Column(db.String(255))
    reset_token_expiry = db.Column(db.DateTime)

class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(255), nullable=True)
    price = db.Column(db.Float, nullable=False)
    discount_id = db.Column(db.Integer, db.ForeignKey('discount.id'), nullable=True)  # Add foreign key
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    subcategory_id = db.Column(db.Integer, db.ForeignKey('subcategory.id'), nullable=True)
    category = db.relationship('Category', back_populates='products')
    subcategory = db.relationship('Subcategory', back_populates='products')
    discount = db.relationship('Discount', back_populates='product', uselist=False)  # Add relationship

class Order(db.Model):
    __tablename__ = 'order'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    customer_status = db.Column(db.String(20), default='Active')
    payment_method = db.Column(db.String(20), nullable=False)
    message_code = db.Column(db.String(50), nullable=True)
    customer_name = db.Column(db.String(100), nullable=True)
    customer_number = db.Column(db.String(15), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    order_items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    __tablename__ = 'order_item'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    product = db.relationship('Product', backref='order_items', lazy=True)

class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)  # Already present
    image = db.Column(db.String(255), nullable=True)  # Add image field
    products = db.relationship('Product', back_populates='category')
    subcategories = db.relationship('Subcategory', back_populates='category')
    gifts = db.relationship('Gift', back_populates='category')

class Subcategory(db.Model):
    __tablename__ = 'subcategory'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    slug = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    category = db.relationship('Category', back_populates='subcategories')
    products = db.relationship('Product', back_populates='subcategory')
    gifts = db.relationship('Gift', back_populates='subcategory')

class Discount(db.Model):
    __tablename__ = 'discount'
    id = db.Column(db.Integer, primary_key=True)
    percent = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    product = db.relationship('Product', back_populates='discount', uselist=False)  # One-to-one relationship

class Artisan(db.Model):
    __tablename__ = 'artisan'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone_number = db.Column(db.String(15))
    status = db.Column(db.String(20), default='Pending')

class Story(db.Model):
    __tablename__ = 'story'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(200))

class Review(db.Model):
    __tablename__ = 'review'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    status = db.Column(db.String(20), default='Pending')

class Wishlist(db.Model):
    __tablename__ = 'wishlist'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product = db.relationship('Product', backref='wishlist_items', lazy=True)

class Cart(db.Model):
    __tablename__ = 'cart'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    product = db.relationship('Product', backref='cart_items', lazy=True)

class ExchangeRate(db.Model):
    __tablename__ = 'exchange_rate'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    eur = db.Column(db.Float, nullable=False)
    gbp = db.Column(db.Float, nullable=False)
    kes = db.Column(db.Float, nullable=False, default=1.0)
    usd = db.Column(db.Float, nullable=False)
    depletion_timestamp = db.Column(db.DateTime, nullable=True)

class Gift(db.Model):
    __tablename__ = 'gift'
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    subcategory_id = db.Column(db.Integer, db.ForeignKey('subcategory.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    category = db.relationship('Category', back_populates='gifts')
    subcategory = db.relationship('Subcategory', back_populates='gifts')


    
    
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
@app.route('/api/discounted_artefacts', methods=['POST'])
def add_product():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        if not data:
            logger.error('No JSON data provided')
            return jsonify({'error': 'Invalid request: JSON data required'}), 415

        # Validate required fields
        required_fields = ['title', 'category_id', 'price']
        for field in required_fields:
            if field not in data or data[field] is None:
                logger.error(f'Missing required field: {field}')
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Verify category exists
        category = Category.query.get(data['category_id'])
        if not category:
            logger.error(f'Invalid category_id: {data["category_id"]}')
            return jsonify({'error': 'Invalid category'}), 400

        # Verify subcategory if provided
        subcategory = None
        if data.get('subcategory_id'):
            subcategory = Subcategory.query.get(data['subcategory_id'])
            if not subcategory or subcategory.category_id != data['category_id']:
                logger.error(f'Invalid subcategory_id: {data["subcategory_id"]}')
                return jsonify({'error': 'Invalid subcategory'}), 400

        # Validate discount if provided
        discount_id = None
        if data.get('discount'):
            try:
                discount_data = data['discount']
                percent = float(discount_data.get('percent'))
                start_date = datetime.strptime(discount_data.get('start_date'), '%Y-%m-%d').date()
                end_date = datetime.strptime(discount_data.get('end_date'), '%Y-%m-%d').date()
                if percent < 0 or percent > 100:
                    logger.error('Discount percent must be between 0 and 100')
                    return jsonify({'error': 'Discount percent must be between 0 and 100'}), 400
                if start_date > end_date:
                    logger.error('Discount start date cannot be after end date')
                    return jsonify({'error': 'Discount start date cannot be after end date'}), 400

                # Create Discount record
                discount = Discount(
                    percent=percent,
                    start_date=start_date,
                    end_date=end_date
                )
                db.session.add(discount)
                db.session.flush()  # Ensure discount ID is available
                discount_id = discount.id
            except (ValueError, TypeError) as e:
                logger.error(f'Invalid discount data: {str(e)}')
                return jsonify({'error': 'Invalid discount data'}), 400

        # Handle image if provided
        image_filename = None
        if data.get('image') and data.get('image_type'):
            try:
                image_data = base64.b64decode(data['image'])
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                image_filename = f"product_{timestamp}.{data['image_type']}"
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
                with open(image_path, 'wb') as f:
                    f.write(image_data)
                logger.debug(f'Image saved: {image_filename}')
            except Exception as e:
                logger.error(f'Failed to save image: {str(e)}')
                return jsonify({'error': 'Failed to process image'}), 400

        # Create new product
        product = Product(
            title=data['title'],
            category_id=data['category_id'],
            subcategory_id=data.get('subcategory_id'),
            price=float(data['price']),
            discount_id=discount_id,  # Set discount_id instead of discount
            description=data.get('description'),
            image=image_filename
        )
        db.session.add(product)
        db.session.commit()

        logger.info(f'Product added successfully: {product.id}')
        return jsonify({'id': product.id, 'message': 'Product added successfully'}), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error adding product: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/discounted_artefacts', methods=['GET'])
def get_products():
    try:
        products = db.session.query(Product).options(
            joinedload(Product.category),
            joinedload(Product.subcategory),
            joinedload(Product.discount)
        ).all()
        return jsonify([{
            'id': p.id,
            'name': p.title,  # Map title to name
            'category_id': p.category_id,
            'subcategory_id': p.subcategory_id,
            'price': float(p.price),
            'discount': {
                'percent': float(p.discount.percent),
                'start_date': p.discount.start_date.isoformat(),
                'end_date': p.discount.end_date.isoformat()
            } if p.discount else None,
            'image': p.image,
            'description': p.description
        } for p in products])
    except SQLAlchemyError as e:
        logger.error(f'Error fetching products: {str(e)}')
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        logger.error(f'Error fetching products: {str(e)}')
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/discounted_artefacts/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def handle_product(id):
    # Fetch product or return 404 if not found
    product = Product.query.get_or_404(id)

    if request.method == 'GET':
        try:
            # Return product details
            return jsonify({
                'id': product.id,
                'title': product.title,
                'description': product.description,
                'price': product.price,
                'category_id': product.category_id,
                'subcategory_id': product.subcategory_id,
                'image': product.image,
                'discount': {
                    'percent': product.discount.percent,
                    'start_date': product.discount.start_date.isoformat(),
                    'end_date': product.discount.end_date.isoformat()
                } if product.discount else None
            })
        except Exception as e:
            logger.error(f"Error retrieving product {id}: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

    elif request.method == 'PUT':
        if 'admin' not in session:
            logger.error("Unauthorized access to update product")
            return jsonify({'error': 'Unauthorized'}), 401

        try:
            # Determine content type and extract data
            is_json = request.content_type and 'application/json' in request.content_type
            if is_json:
                data = request.get_json()
                if not data:
                    logger.error("No JSON data provided")
                    return jsonify({'error': 'Invalid JSON data'}), 400
                title = data.get('title', product.title)
                description = data.get('description', product.description)
                price = data.get('price', product.price)
                category_id = data.get('category_id', product.category_id)
                subcategory_id = data.get('subcategory_id', product.subcategory_id)
                discount_data = data.get('discount')
                image_data = data.get('image')  # Base64 string
                image_type = data.get('image_type')  # e.g., 'jpg'
            else:
                # Expect multipart/form-data
                title = request.form.get('title', product.title)
                description = request.form.get('description', product.description)
                price = request.form.get('price', product.price)
                category_id = request.form.get('category_id', product.category_id)
                subcategory_id = request.form.get('subcategory_id', product.subcategory_id)
                discount_data = request.form.get('discount')
                image_data = None
                image_type = None

            logger.debug(f"Received data: title={title}, price={price}, category_id={category_id}, subcategory_id={subcategory_id}, discount_data={discount_data}")

            # Validate required fields
            if not title or price is None or category_id is None:
                logger.error("Missing required fields: title, price, or category_id")
                return jsonify({'error': 'Title, price, and category_id are required'}), 400

            # Validate price
            try:
                price = float(price)
                if price < 0:
                    logger.error("Negative price provided")
                    return jsonify({'error': 'Price cannot be negative'}), 400
            except (ValueError, TypeError):
                logger.error("Invalid price value")
                return jsonify({'error': 'Invalid price value'}), 400

            # Validate category
            try:
                category_id = int(category_id)
            except (ValueError, TypeError):
                logger.error("Invalid category_id")
                return jsonify({'error': 'Invalid category_id'}), 400
            category = Category.query.get(category_id)
            if not category:
                logger.error(f"Category not found: {category_id}")
                return jsonify({'error': 'Category not found'}), 404

            # Validate subcategory
            subcategory_id = int(subcategory_id) if subcategory_id else None
            if subcategory_id:
                subcategory = Subcategory.query.get(subcategory_id)
                if not subcategory or subcategory.category_id != category_id:
                    logger.error(f"Invalid subcategory_id: {subcategory_id}")
                    return jsonify({'error': 'Invalid subcategory for selected category'}), 400

            # Handle discount
            if discount_data:
                try:
                    discount_dict = json.loads(discount_data) if isinstance(discount_data, str) else discount_data
                    percent = float(discount_dict.get('percent'))
                    start_date = datetime.strptime(discount_dict.get('start_date'), '%Y-%m-%d').date()
                    end_date = datetime.strptime(discount_dict.get('end_date'), '%Y-%m-%d').date()
                    if percent < 0 or percent > 100:
                        logger.error("Invalid discount percent")
                        return jsonify({'error': 'Discount percent must be between 0 and 100'}), 400
                    if start_date > end_date:
                        logger.error("Invalid discount dates")
                        return jsonify({'error': 'Discount start date cannot be after end date'}), 400

                    if product.discount:
                        product.discount.percent = percent
                        product.discount.start_date = start_date
                        product.discount.end_date = end_date
                    else:
                        discount = Discount(
                            percent=percent,
                            start_date=start_date,
                            end_date=end_date
                        )
                        db.session.add(discount)
                        db.session.flush()
                        product.discount_id = discount.id
                except (ValueError, TypeError, json.JSONDecodeError) as e:
                    logger.error(f"Invalid discount data: {str(e)}")
                    return jsonify({'error': 'Invalid discount data'}), 400
            else:
                if product.discount:
                    db.session.delete(product.discount)
                    product.discount_id = None

            # Update product fields
            product.title = title
            product.description = description
            product.price = price
            product.category_id = category_id
            product.subcategory_id = subcategory_id

            # Handle image upload
            if is_json and image_data and image_type:
                # Handle base64 image
                try:
                    image_bytes = base64.b64decode(image_data)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = secure_filename(f"product_{timestamp}.{image_type}")
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    with open(image_path, 'wb') as f:
                        f.write(image_bytes)
                    if product.image:
                        old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], product.image)
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
                    product.image = filename
                    logger.debug(f"Base64 image saved: {filename}")
                except Exception as e:
                    logger.error(f"Failed to process base64 image: {str(e)}")
                    return jsonify({'error': 'Failed to process image'}), 400
            elif not is_json and 'image' in request.files and request.files['image'].filename:
                # Handle file upload
                image = request.files['image']
                if not image.mimetype in ['image/jpeg', 'image/png']:
                    logger.error("Invalid image mimetype")
                    return jsonify({'error': 'Only JPG and PNG images are allowed'}), 400
                if image.content_length > 3 * 1024 * 1024:
                    logger.error("Image size exceeds 3MB")
                    return jsonify({'error': 'Image size exceeds 3MB'}), 400
                if product.image:
                    old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], product.image)
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                filename = secure_filename(f"product_{datetime.now().timestamp()}_{image.filename}")
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                product.image = filename
                logger.debug(f"File image saved: {filename}")

            db.session.commit()
            logger.info(f"Product {id} updated successfully")
            return jsonify({
                'message': 'Product updated successfully',
                'product': {
                    'id': product.id,
                    'title': product.title,
                    'description': product.description,
                    'price': product.price,
                    'category_id': product.category_id,
                    'subcategory_id': product.subcategory_id,
                    'image': product.image,
                    'discount': {
                        'percent': product.discount.percent,
                        'start_date': product.discount.start_date.isoformat(),
                        'end_date': product.discount.end_date.isoformat()
                    } if product.discount else None
                }
            })
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error updating product {id}: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        except Exception as e:
            db.session.rollback()
            logger.error(f"Unexpected error updating product {id}: {str(e)}")
            return jsonify({'error': f'Internal server error: {str(e)}'}), 500

    elif request.method == 'DELETE':
        if 'admin' not in session:
            logger.error("Unauthorized access to delete product")
            return jsonify({'error': 'Unauthorized'}), 401

        try:
            # Delete associated discount if exists
            if product.discount:
                db.session.delete(product.discount)

            # Delete product image file if exists
            if product.image:
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], product.image)
                if os.path.exists(image_path):
                    os.remove(image_path)

            # Delete product
            db.session.delete(product)
            db.session.commit()
            logger.info(f"Product {id} deleted successfully")
            return jsonify({'message': 'Product deleted successfully'})
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error deleting product {id}: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        except Exception as e:
            db.session.rollback()
            logger.error(f"Unexpected error deleting product {id}: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
        
@app.route('/api/gifts', methods=['GET'])
def get_gifts():
    if not session.get('admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    gifts = Gift.query.all()
    return jsonify([{
        'id': gift.id,
        'product_name': gift.product_name,
        'description': gift.description,
        'price': gift.price,
        'start_date': gift.start_date.isoformat(),
        'end_date': gift.end_date.isoformat(),
        'category_id': gift.category_id,
        'subcategory_id': gift.subcategory_id,
        'category': gift.category.name if gift.category else 'N/A',
        'subcategory': gift.subcategory.name if gift.subcategory else 'None',
        'image': gift.image,
        'created_at': gift.created_at.isoformat()
    } for gift in gifts])

@app.route('/api/gifts', methods=['POST'])
def create_gift():
    if not session.get('admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not request.form or not request.files:
        return jsonify({'error': 'Missing form data or file'}), 400
    
    product_name = request.form.get('product_name')
    description = request.form.get('description')
    price = request.form.get('price')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    category_id = request.form.get('category_id')
    subcategory_id = request.form.get('subcategory_id')
    image = request.files.get('image')
    
    if not all([product_name, description, price, start_date, end_date, category_id]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        price = float(price)
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        category_id = int(category_id)
        subcategory_id = int(subcategory_id) if subcategory_id else None
    except ValueError:
        return jsonify({'error': 'Invalid price, date, category_id, or subcategory_id format'}), 400
    
    if start_date > end_date:
        return jsonify({'error': 'End date must be after start date'}), 400
    
    category = Category.query.get(category_id)
    if not category:
        return jsonify({'error': 'Category not found'}), 404
    
    if subcategory_id:
        subcategory = Subcategory.query.get(subcategory_id)
        if not subcategory or subcategory.category_id != category_id:
            return jsonify({'error': 'Invalid subcategory for selected category'}), 400
    
    if not image or not image.filename:
        return jsonify({'error': 'Image is required'}), 400
    
    if not image.mimetype in ['image/jpeg', 'image/png']:
        return jsonify({'error': 'Only JPG and PNG images are allowed'}), 400
    if image.content_length > 3 * 1024 * 1024:
        return jsonify({'error': 'Image size must be less than 3MB'}), 400
    
    filename = secure_filename(f"gift_{datetime.now().timestamp()}_{image.filename}")
    image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    gift = Gift(
        product_name=product_name,
        description=description,
        price=price,
        start_date=start_date,
        end_date=end_date,
        category_id=category_id,
        subcategory_id=subcategory_id,
        image=filename
    )
    db.session.add(gift)
    db.session.commit()
    
    return jsonify({'message': 'Gift created successfully', 'id': gift.id}), 201

@app.route('/api/gifts/<int:id>', methods=['GET'])
def get_gift(id):
    if not session.get('admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    gift = Gift.query.get_or_404(id)
    return jsonify({
        'id': gift.id,
        'product_name': gift.product_name,
        'description': gift.description,
        'price': gift.price,
        'start_date': gift.start_date.isoformat(),
        'end_date': gift.end_date.isoformat(),
        'category_id': gift.category_id,
        'subcategory_id': gift.subcategory_id,
        'image': gift.image,
        'created_at': gift.created_at.isoformat()
    })

@app.route('/api/gifts/<int:id>', methods=['PUT'])
def update_gift(id):
    if not session.get('admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    gift = Gift.query.get_or_404(id)
    
    if not request.form:
        return jsonify({'error': 'Missing form data'}), 400
    
    product_name = request.form.get('product_name')
    description = request.form.get('description')
    price = request.form.get('price')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    category_id = request.form.get('category_id')
    subcategory_id = request.form.get('subcategory_id')
    image = request.files.get('image')
    
    if not all([product_name, description, price, start_date, end_date, category_id]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        price = float(price)
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        category_id = int(category_id)
        subcategory_id = int(subcategory_id) if subcategory_id else None
    except ValueError:
        return jsonify({'error': 'Invalid price, date, category_id, or subcategory_id format'}), 400
    
    if start_date > end_date:
        return jsonify({'error': 'End date must be after start date'}), 400
    
    category = Category.query.get(category_id)
    if not category:
        return jsonify({'error': 'Category not found'}), 404
    
    if subcategory_id:
        subcategory = Subcategory.query.get(subcategory_id)
        if not subcategory or subcategory.category_id != category_id:
            return jsonify({'error': 'Invalid subcategory for selected category'}), 400
    
    gift.product_name = product_name
    gift.description = description
    gift.price = price
    gift.start_date = start_date
    gift.end_date = end_date
    gift.category_id = category_id
    gift.subcategory_id = subcategory_id
    
    if image and image.filename:
        if not image.mimetype in ['image/jpeg', 'image/png']:
            return jsonify({'error': 'Only JPG and PNG images are allowed'}), 400
        if image.content_length > 3 * 1024 * 1024:
            return jsonify({'error': 'Image size must be less than 3MB'}), 400
        if gift.image:
            old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], gift.image)
            if os.path.exists(old_image_path):
                os.remove(old_image_path)
        filename = secure_filename(f"gift_{datetime.now().timestamp()}_{image.filename}")
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        gift.image = filename
    
    db.session.commit()
    return jsonify({'message': 'Gift updated successfully'})

@app.route('/api/gifts/<int:id>', methods=['DELETE'])
def delete_gift(id):
    if not session.get('admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    gift = Gift.query.get_or_404(id)
    if gift.image:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], gift.image)
        if os.path.exists(image_path):
            os.remove(image_path)
    db.session.delete(gift)
    db.session.commit()
    return jsonify({'message': 'Gift deleted successfully'})

@app.route('/api/subcategories', methods=['GET', 'POST'])
@app.route('/api/subcategories/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def handle_subcategories(id=None):
    if 'admin' not in session:
        app.logger.debug("No admin in session")
        return jsonify({'error': 'Unauthorized'}), 401

    if request.method == 'GET':
        try:
            if id:
                subcategory = db.session.get(Subcategory, id)
                if not subcategory:
                    app.logger.debug(f"Subcategory ID {id} not found")
                    return jsonify({'error': 'Subcategory not found'}), 404
                return jsonify({
                    'id': subcategory.id,
                    'name': subcategory.name,
                    'slug': subcategory.slug,
                    'description': subcategory.description,
                    'category_id': subcategory.category_id
                }), 200
            else:
                subcategories = Subcategory.query.all()
                app.logger.debug(f"Fetched {len(subcategories)} subcategories")
                return jsonify([{
                    'id': s.id,
                    'name': s.name,
                    'slug': s.slug,
                    'description': s.description,
                    'category_id': s.category_id
                } for s in subcategories]), 200
        except SQLAlchemyError as e:
            app.logger.error(f"Database error fetching subcategories: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        except Exception as e:
            app.logger.error(f"Unexpected error fetching subcategories: {str(e)}")
            return jsonify({'error': 'Failed to fetch subcategories'}), 500

    if request.method == 'POST':
        try:
            data = request.get_json()
            app.logger.debug(f"Received POST /api/subcategories data: {data}")
            required_fields = ['name', 'category_id']
            missing_fields = [field for field in required_fields if field not in data or not data[field]]
            if missing_fields:
                return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400

            category = db.session.get(Category, data['category_id'])
            if not category:
                return jsonify({'error': 'Category not found'}), 404

            subcategory = Subcategory(
                name=data['name'],
                slug=slugify(data['name']),
                description=data.get('description'),
                category_id=data['category_id']
            )
            db.session.add(subcategory)
            db.session.commit()
            app.logger.debug(f"Created subcategory: {subcategory.name}")
            return jsonify({'message': 'Subcategory created successfully', 'id': subcategory.id}), 201
        except SQLAlchemyError as e:
            db.session.rollback()
            app.logger.error(f"Database error creating subcategory: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Unexpected error creating subcategory: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

    if request.method == 'PUT':
        try:
            subcategory = db.session.get(Subcategory, id)
            if not subcategory:
                app.logger.debug(f"Subcategory ID {id} not found")
                return jsonify({'error': 'Subcategory not found'}), 404

            data = request.get_json()
            app.logger.debug(f"Received PUT /api/subcategories/{id} data: {data}")
            if 'name' in data:
                subcategory.name = data['name']
                subcategory.slug = slugify(data['name'])
            if 'description' in data:
                subcategory.description = data['description']
            if 'category_id' in data:
                category = db.session.get(Category, data['category_id'])
                if not category:
                    return jsonify({'error': 'Category not found'}), 404
                subcategory.category_id = data['category_id']

            db.session.commit()
            app.logger.debug(f"Updated subcategory ID {id}")
            return jsonify({'message': 'Subcategory updated successfully'}), 200
        except SQLAlchemyError as e:
            db.session.rollback()
            app.logger.error(f"Database error updating subcategory: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Unexpected error updating subcategory: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

    if request.method == 'DELETE':
        try:
            subcategory = db.session.get(Subcategory, id)
            if not subcategory:
                app.logger.debug(f"Subcategory ID {id} not found")
                return jsonify({'error': 'Subcategory not found'}), 404

            # Check for dependent products or gifts
            products = Product.query.filter_by(subcategory_id=id).count()
            gifts = Gift.query.filter_by(subcategory_id=id).count()
            if products > 0 or gifts > 0:
                app.logger.debug(f"Subcategory ID {id} has {products} products and {gifts} gifts")
                return jsonify({'error': 'Cannot delete subcategory with associated products or gifts'}), 400

            db.session.delete(subcategory)
            db.session.commit()
            app.logger.debug(f"Deleted subcategory ID {id}")
            return jsonify({'message': 'Subcategory deleted successfully'}), 200
        except SQLAlchemyError as e:
            db.session.rollback()
            app.logger.error(f"Database error deleting subcategory: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Unexpected error deleting subcategory: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/subcategories/<int:id>', methods=['PUT'])
def update_subcategory(id):
    if not session.get('admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    subcategory = Subcategory.query.get_or_404(id)
    data = request.get_json()
    if not data or not data.get('name') or not data.get('category_id'):
        return jsonify({'error': 'Missing name or category_id'}), 400
    
    if Subcategory.query.filter_by(name=data['name'], category_id=data['category_id']).filter(Subcategory.id != id).first():
        return jsonify({'error': 'Subcategory already exists in this category'}), 400
    
    category = Category.query.get(data['category_id'])
    if not category:
        return jsonify({'error': 'Category not found'}), 404
    
    subcategory.name = data['name']
    subcategory.slug = slugify(data['name'])
    subcategory.description = data.get('description')
    subcategory.category_id = data['category_id']
    db.session.commit()
    return jsonify({'message': 'Subcategory updated successfully'})

@app.route('/api/subcategories/<int:id>', methods=['DELETE'])
def delete_subcategory(id):
    if not session.get('admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    subcategory = Subcategory.query.get_or_404(id)
    if Product.query.filter_by(subcategory_id=id).first() or Gift.query.filter_by(subcategory_id=id).first():
        return jsonify({'error': 'Cannot delete subcategory with associated products or gifts'}), 400
    
    db.session.delete(subcategory)
    db.session.commit()
    return jsonify({'message': 'Subcategory deleted successfully'})

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
            user = db.session.get(User, order.user_id)  # Use session.get
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
                    'product_name': product.title if product else 'Deleted Product',  # Use title
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

@app.route('/api/discounts', methods=['GET', 'POST'])
def handle_discounts():
    if 'admin' not in session:
        logger.debug("No admin in session")
        return jsonify({'error': 'Unauthorized'}), 401

    if request.method == 'GET':
        try:
            discounts = db.session.query(Discount).options(joinedload(Discount.product)).all()
            logger.debug(f"Fetched {len(discounts)} discounts")
            discount_data = []
            for d in discounts:
                logger.debug(f"Discount ID: {d.id}, Product: {d.product.title if d.product else 'None'}")
                discount_data.append({
                    'id': d.id,
                    'productId': d.product.id if d.product else None,
                    'productName': d.product.title if d.product else 'N/A',
                    'percent': d.percent,
                    'startDate': d.start_date.isoformat() if d.start_date else None,
                    'endDate': d.end_date.isoformat() if d.end_date else None
                })
            return jsonify(discount_data), 200
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching discounts: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        except Exception as e:
            logger.error(f"Unexpected error fetching discounts: {str(e)}")
            return jsonify({'error': 'Failed to fetch discounts'}), 500

    if request.method == 'POST':
        try:
            data = request.get_json()
            logger.debug(f"Received POST /api/discounts data: {data}")
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

            product = db.session.get(Product, product_id)
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
            logger.error(f"Database error in POST /api/discounts: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        except Exception as e:
            db.session.rollback()
            logger.error(f"Unexpected error in POST /api/discounts: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
        
        
@app.route('/api/discounts/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def handle_discount(id):
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    discount = Discount.query.options(joinedload(Discount.product)).get_or_404(id)
    if request.method == 'GET':
        return jsonify({
            'id': discount.id,
            'productId': discount.product.id if discount.product else None,
            'productName': discount.product.title if discount.product else 'N/A',  # Use title
            'percent': discount.percent,
            'startDate': discount.start_date.isoformat(),
            'endDate': discount.end_date.isoformat()
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
    # Check for admin or user session
    if 'admin' not in session and 'user' not in session:
        logging.debug(f"Unauthorized access to user {id}: No admin or user in session")
        return jsonify({'error': 'Unauthorized'}), 401

    user = User.query.get_or_404(id)

    # For regular users, ensure they can only access their own profile
    if 'user' in session and 'admin' not in session:
        current_user = User.query.filter_by(email=session['user']).first()
        if not current_user or current_user.id != id:
            logging.debug(f"Unauthorized: User {session['user']} attempted to access user {id}")
            return jsonify({'error': 'Unauthorized'}), 403

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
            if not data:
                logging.error(f"No data provided for user {id} update")
                return jsonify({'error': 'No data provided'}), 400

            # Restrict fields for non-admin users
            if 'user' in session and 'admin' not in session:
                allowed_fields = ['name', 'phone_number']
                data = {k: v for k, v in data.items() if k in allowed_fields}
                logging.debug(f"Non-admin user updating allowed fields: {data}")
            else:
                # Validate uniqueness for admin updates
                if 'username' in data and data['username'] and User.query.filter_by(username=data['username']).filter(User.id != id).first():
                    logging.error(f"Username {data['username']} already exists")
                    return jsonify({'error': 'Username already exists'}), 400
                if 'email' in data and data['email'] and User.query.filter_by(email=data['email']).filter(User.id != id).first():
                    logging.error(f"Email {data['email']} already exists")
                    return jsonify({'error': 'Email already exists'}), 400

            # Update fields
            user.username = data.get('username', user.username) if 'admin' in session else user.username
            user.name = data.get('name', user.name)
            user.email = data.get('email', user.email) if 'admin' in session else user.email
            user.phone_number = data.get('phone_number', user.phone_number)
            user.role = data.get('role', user.role) if 'admin' in session else user.role

            # Validate phone number if provided
            if 'phone_number' in data and data['phone_number'] and len(data['phone_number']) > 15:
                logging.error("Phone number too long")
                return jsonify({'error': 'Phone number must be 15 characters or less'}), 400

            db.session.commit()
            logging.info(f"User {id} updated successfully")
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
        # Only admins can delete users
        if 'admin' not in session:
            logging.debug(f"Unauthorized: Non-admin attempted to delete user {id}")
            return jsonify({'error': 'Unauthorized'}), 401
        try:
            db.session.delete(user)
            db.session.commit()
            logging.info(f"User {id} deleted successfully")
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
        return jsonify([{
            'id': c.id,
            'name': c.name,
            'description': c.description,
            'image': c.image
        } for c in categories])
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    if request.method == 'POST':
        try:
            # Expect form data for name, description, and image
            if not request.form.get('name'):
                return jsonify({'error': 'Category name is required'}), 400
            if Category.query.filter_by(name=request.form['name']).first():
                return jsonify({'error': 'Category already exists'}), 400

            # Handle image upload
            image_filename = None
            if 'image' in request.files and request.files['image'].filename:
                image = request.files['image']
                if not allowed_file(image.filename):
                    return jsonify({'error': 'Invalid image format (use PNG, JPG, JPEG, GIF)'}), 400
                if image.content_length > 3 * 1024 * 1024:  # 3MB limit
                    return jsonify({'error': 'Image size exceeds 3MB'}), 400
                image_filename = save_file(image)

            category = Category(
                name=request.form['name'],
                slug=slugify(request.form['name']),
                description=request.form.get('description'),
                image=image_filename
            )
            db.session.add(category)
            db.session.commit()
            return jsonify({'message': 'Category created successfully', 'id': category.id}), 201
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
    if request.method == 'DELETE':
        try:
            # Check for associated subcategories
            subcategories = Subcategory.query.filter_by(category_id=id).count()
            if subcategories > 0:
                return jsonify({'error': 'Please remove its subcategories first.'}), 400
            # Check for associated products or gifts
            products = Product.query.filter_by(category_id=id).count()
            gifts = Gift.query.filter_by(category_id=id).count()
            if products > 0 or gifts > 0:
                return jsonify({'error': 'Cannot delete category with associated products or gifts'}), 400
            # Remove image file if exists
            if category.image:
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], category.image)
                if os.path.exists(image_path):
                    os.remove(image_path)
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
    
    if 'admin' not in session:
        logger.debug('No admin in session')
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=30)
        logger.debug(f'Date range: {start_date} to {end_date}')

        # Sales data
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

        sales_data = [
            {'date': str(row.date), 'total': float(row.total or 0.0)}
            for row in sales_query
        ]

        all_dates = [(start_date + timedelta(days=x)).strftime('%Y-%m-%d') for x in range(31)]
        sales_data_dict = {item['date']: item['total'] for item in sales_data}
        sales_data = [
            {'date': date, 'total': sales_data_dict.get(date, 0.0)}
            for date in all_dates
        ]

        # Users data
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

        users_data = [
            {'date': str(row.date), 'count': int(row.count or 0)}
            for row in users_query
        ]

        users_data_dict = {item['date']: item['count'] for item in users_data}
        users_data = [
            {'date': date, 'count': users_data_dict.get(date, 0)}
            for date in all_dates
        ]

        # Total sales
        total_sales = db.session.query(func.sum(Order.total)).filter(Order.status == 'Delivered').scalar() or 0.0
        logger.debug(f'Total sales: {total_sales}')

        # New users
        new_users = db.session.query(func.count(User.id)).filter(User.created_at >= start_date).scalar() or 0
        logger.debug(f'New users: {new_users}')

        # Pending orders
        pending_orders = db.session.query(func.count(Order.id)).filter(Order.status == 'Pending').scalar() or 0
        logger.debug(f'Pending orders: {pending_orders}')

        # Top product
        top_product_query = db.session.query(
            Product.title,
            func.sum(OrderItem.quantity).label('total_quantity')
        ).join(OrderItem, Product.id == OrderItem.product_id).join(
            Order, OrderItem.order_id == Order.id
        ).filter(
            Order.created_at >= start_date,
            Order.status == 'Delivered'
        ).group_by(
            Product.title
        ).order_by(
            func.sum(OrderItem.quantity).desc()
        ).first()
        top_product = top_product_query.title if top_product_query else 'None'
        logger.debug(f'Top product: {top_product}')

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
    
@app.route('/categories')
@app.route('/categories/<string:slug>')
def categories(slug=None):
    try:
        # Get current currency from session (default to KES)
        current_currency = session.get('currency', 'KES')

        # Fetch all categories for display (e.g., in a sidebar or dropdown)
        categories = Category.query.all()

        if slug:
            # If a category slug is provided, fetch products for that category
            category = Category.query.filter_by(slug=slug).first_or_404()
            products = Product.query.filter_by(category_id=category.id).order_by(Product.created_at.desc()).all()
            page_title = f"{category.name} - Zira Collections"
        else:
            # If no slug, show all categories or a general category overview
            products = Product.query.order_by(Product.created_at.desc()).limit(12).all()  # Limit for overview
            page_title = "Categories - Zira Collections"

        # Log the fetched data for debugging
        logging.debug(f"Rendering category.html: slug={slug}, categories={len(categories)}, products={len(products)}")

        return render_template(
            'category.html',
            categories=categories,
            products=products,
            selected_category=category if slug else None,
            today=datetime.utcnow().date(),
            current_currency=current_currency,
            page_title=page_title
        )

    except SQLAlchemyError as e:
        logging.error(f"Database error in /categories: {str(e)}")
        return render_template('500.html'), 500
    except Exception as e:
        logging.error(f"Unexpected error in /categories: {str(e)}")
        return render_template('500.html'), 500

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