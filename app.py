from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB
import mysql.connector
import decimal
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_super_secret_key_replace_this'

# --- MySQL Database Connection ---
def get_db():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB
    )

# --- Auth Decorators ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        if session.get('user_type') != 'Admin':
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# --- Home Redirect ---
@app.route('/')
def index():
    return redirect(url_for('dashboard')) if 'user_id' in session else redirect(url_for('login'))

# --- Registration ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        contact_info = request.form.get('contact_info', '')
        user_type = request.form.get('user_type')
        error = None

        if not username or not password or not email or not user_type:
            error = 'All fields are required.'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters.'
        else:
            try:
                conn = get_db()
                cursor = conn.cursor(dictionary=True)
                cursor.execute('SELECT user_id FROM Users WHERE username = %s OR email = %s', (username, email))
                if cursor.fetchone():
                    error = 'Username or email already exists.'
            except mysql.connector.Error as e:
                error = f"Database error: {e}"
            finally:
                conn.close()

        if error is None:
            try:
                password_hash = generate_password_hash(password)
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO Users (username, password_hash, email, contact_info, user_type) VALUES (%s, %s, %s, %s, %s)',
                    (username, password_hash, email, contact_info, user_type)
                )
                conn.commit()
                flash('Registration successful. Please log in.', 'success')
                return redirect(url_for('login'))
            except mysql.connector.Error as e:
                flash(f"Database error during registration: {e}", 'error')
            finally:
                conn.close()
        else:
            flash(error, 'error')

    return render_template('register.html')

# --- Login ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        error = None

        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT * FROM Users WHERE username = %s', (username,))
            user = cursor.fetchone()
            if not user or not check_password_hash(user['password_hash'], password):
                error = 'Invalid credentials.'
            else:
                session.clear()
                session['user_id'] = user['user_id']
                session['username'] = user['username']
                session['user_type'] = user['user_type']
                flash(f"Welcome, {user['username']}!", 'success')
                return redirect(url_for('dashboard'))
        except mysql.connector.Error as e:
            error = f"Database error: {e}"
        finally:
            conn.close()

        if error:
            flash(error, 'error')

    return render_template('login.html')

# --- Logout ---
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

# --- Dashboard ---
@app.route('/dashboard')
@login_required
def dashboard():
    username = session.get('username', 'User')
    products = []
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM Products WHERE stock_quantity > 0 ORDER BY name ASC')
        products = cursor.fetchall()
    except mysql.connector.Error as e:
        flash(f"Error loading products: {e}", 'error')
    finally:
        conn.close()
    return render_template('dashboard.html', username=username, products=products)

# --- Admin: Add Product ---
@app.route('/add_product', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        stock = request.form.get('stock_quantity')
        image = request.form.get('image_url', '')
        error = None

        try:
            price = float(price)
            stock = int(stock)
            if price < 0 or stock < 0:
                error = "Price and stock must be non-negative."
        except:
            error = "Invalid price or stock."

        if not name or error:
            flash(error or "Product name is required.", 'error')
        else:
            try:
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO Products (name, description, price, stock_quantity, image_url) VALUES (%s, %s, %s, %s, %s)',
                    (name, description, price, stock, image)
                )
                conn.commit()
                flash('Product added successfully!', 'success')
                return redirect(url_for('add_product'))
            except mysql.connector.Error as e:
                flash(f"Error adding product: {e}", 'error')
            finally:
                conn.close()

    return render_template('add_product.html')

# --- Add to Cart ---
@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    if 'cart' not in session:
        session['cart'] = {}

    quantity = 1
    product_key = str(product_id)

    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT name, price, stock_quantity FROM Products WHERE product_id = %s', (product_id,))
        product = cursor.fetchone()
        conn.close()
    except mysql.connector.Error as e:
        flash(f"Error accessing product: {e}", 'error')
        return redirect(url_for('dashboard'))

    if not product:
        flash('Product not found.', 'error')
    elif product['stock_quantity'] < quantity:
        flash('Not enough stock.', 'error')
    else:
        cart = session['cart']
        if product_key in cart:
            if cart[product_key]['quantity'] + quantity > product['stock_quantity']:
                flash("Cannot exceed available stock.", 'error')
            else:
                cart[product_key]['quantity'] += quantity
        else:
            cart[product_key] = {
                'name': product['name'],
                'price': str(product['price']),
                'quantity': quantity
            }
        session['cart'] = cart
        session.modified = True
        flash(f"{product['name']} added to cart.", 'success')

    return redirect(url_for('dashboard'))

# --- View Cart ---
@app.route('/cart')
@login_required
def view_cart():
    cart = session.get('cart', {})
    cart_items = []
    grand_total = decimal.Decimal('0.00')

    for pid, item in cart.items():
        try:
            price = decimal.Decimal(item['price'])
            quantity = int(item['quantity'])
            subtotal = price * quantity
            cart_items.append({
                'id': pid,
                'name': item['name'],
                'price': price,
                'quantity': quantity,
                'subtotal': subtotal
            })
            grand_total += subtotal
        except:
            flash(f"Problem with cart item {pid}.", 'error')

    return render_template('cart.html', cart_items=cart_items, grand_total=grand_total)

# --- Run the App ---
if __name__ == '__main__':
    app.run(debug=True)
