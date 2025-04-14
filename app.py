from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB
import mysql.connector
from functools import wraps
# --- Flask App Setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_super_secret_key_replace_this'  # Secure this key in production

# --- MySQL Database Connection ---
def get_db():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB
    )

# --- Routes ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Decorator for admin requirement ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # First, ensure user is logged in
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        # Then, check if the user is an admin
        if session.get('user_type') != 'Admin':
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('dashboard')) # Or wherever non-admins should go
        return f(*args, **kwargs)
    return decorated_function

# --- Add Product Route ---
@app.route('/add_product', methods=['GET', 'POST'])
@login_required # Make sure they are logged in
@admin_required # Make sure they are an admin
def add_product():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price_str = request.form.get('price')
        stock_quantity_str = request.form.get('stock_quantity')
        image_url = request.form.get('image_url', '') # Optional
        error = None

        # --- Input Validation ---
        if not name or not price_str or not stock_quantity_str:
            error = 'Product name, price, and stock quantity are required.'
        else:
            try:
                price = float(price_str)
                stock_quantity = int(stock_quantity_str)
                if price < 0 or stock_quantity < 0:
                    error = 'Price and stock quantity cannot be negative.'
            except ValueError:
                error = 'Price and stock quantity must be valid numbers.'

        if error is None:
            # --- Database Interaction ---
            try:
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO Products (name, description, price, stock_quantity, image_url)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (name, description, price, stock_quantity, image_url)
                )
                conn.commit()
                flash(f'Product "{name}" added successfully!', 'success')
                return redirect(url_for('add_product')) # Redirect back to the add form or to a product list
            except mysql.connector.Error as e:
                error = f"Database error adding product: {e}"
                conn.rollback() # Rollback changes on error
            finally:
                if conn:
                    conn.close()
        # If there was an error (validation or DB)
        if error:
            flash(error, 'error')
            # Optionally, pass back the entered data to repopulate the form
            return render_template('add_product.html',
                                   name=name,
                                   description=description,
                                   price=price_str,
                                   stock_quantity=stock_quantity_str,
                                   image_url=image_url)
    # --- Handle GET request ---
    return render_template('add_product.html') # Just show the empty form

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

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

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters.'
        elif not email:
            error = 'Email is required.'
        elif not user_type:
            error = 'User type selection is required.'
        else:
            try:
                conn = get_db()
                cursor = conn.cursor(dictionary=True)
                cursor.execute('SELECT id FROM Users WHERE username = %s', (username,))
                if cursor.fetchone():
                    error = f"Username '{username}' is already taken."
                else:
                    cursor.execute('SELECT id FROM Users WHERE email = %s', (email,))
                    if cursor.fetchone():
                        error = f"Email '{email}' is already registered."
            except mysql.connector.Error as e:
                error = f"Database error during validation: {e}"
            finally:
                if conn:
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
                flash('Account created successfully! Please log in.', 'success')
                return redirect(url_for('login'))
            except mysql.connector.Error as e:
                error = f"Database error during registration: {e}"
            finally:
                if conn:
                    conn.close()
        if error:
            flash(error, 'error')

    return render_template(
        'register.html',
        username=request.form.get('username', ''),
        email=request.form.get('email', ''),
        contact_info=request.form.get('contact_info', ''),
        user_type=request.form.get('user_type', 'Customer')
    )

# --- Login ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        error = None

        if not username or not password:
            error = 'Please enter both username and password.'
        else:
            try:
                conn = get_db()
                cursor = conn.cursor(dictionary=True)
                cursor.execute('SELECT * FROM Users WHERE username = %s', (username,))
                user = cursor.fetchone()

                if user is None or not check_password_hash(user['password_hash'], password):
                    error = 'Invalid credentials. Please try again.'
                else:
                    session.clear()
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    session['user_type'] = user['user_type']
                    flash(f'Welcome back, {user["username"]}!', 'success')
                    return redirect(url_for('dashboard'))

            except mysql.connector.Error as e:
                error = f"Database error during login: {e}"
            finally:
                if conn:
                    conn.close()

        if error:
            flash(error, 'error')

    return render_template('login.html')

# --- Dashboard (Protected) ---
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))

    username = session.get('username', 'User')
    return render_template('dashboard.html', username=username)

# --- Logout ---
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been successfully logged out.', 'info')
    return redirect(url_for('login'))

# --- Run the App ---
if __name__ == '__main__':
    app.run(debug=True)
