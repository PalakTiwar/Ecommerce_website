<<<<<<< HEAD
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
=======
import sqlite3
# Import session from Flask!
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash # check_password_hash is crucial for login

# --- Configuration ---
DATABASE = 'users.db'
SECRET_KEY = 'your_super_secret_key_replace_this' # Keep this! Essential for sessions

# --- Flask App Setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY # Configure the secret key for session management

# --- Database Helper Functions (Keep these as they are) ---
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                contact_info TEXT,
                user_type TEXT NOT NULL
            )
        ''')
        conn.commit()
        print("Database table 'users' checked/initialized.")
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        if conn:
            conn.close()

# --- Routes ---

@app.route('/')
def index():
    # Redirect to dashboard if logged in, otherwise to login
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login')) # Default to login page now

# --- Registration Route (Keep as is) ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # ... (Keep all your existing registration logic here) ...
>>>>>>> cdbb0c8d369c522697bd8b8c4141dfe6f87e9839
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        contact_info = request.form.get('contact_info', '')
        user_type = request.form.get('user_type')
        error = None
<<<<<<< HEAD

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
=======
        conn = None # Initialize conn

        if not username: error = 'Username is required.'
        elif not password: error = 'Password is required.'
        elif len(password) < 6: error = 'Password must be at least 6 characters.'
        elif not email: error = 'Email is required.'
        elif not user_type: error = 'User type selection is required.'
        else:
            try:
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
                if cursor.fetchone() is not None: error = f"Username '{username}' is already taken."
                else:
                    cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
                    if cursor.fetchone() is not None: error = f"Email '{email}' is already registered."
            except sqlite3.Error as e: error = f"Database error during validation: {e}"
            finally:
                if conn: conn.close()
>>>>>>> cdbb0c8d369c522697bd8b8c4141dfe6f87e9839

        if error is None:
            try:
                password_hash = generate_password_hash(password)
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute(
<<<<<<< HEAD
                    'INSERT INTO Users (username, password_hash, email, contact_info, user_type) VALUES (%s, %s, %s, %s, %s)',
=======
                    'INSERT INTO users (username, password_hash, email, contact_info, user_type) VALUES (?, ?, ?, ?, ?)',
>>>>>>> cdbb0c8d369c522697bd8b8c4141dfe6f87e9839
                    (username, password_hash, email, contact_info, user_type)
                )
                conn.commit()
                flash('Account created successfully! Please log in.', 'success')
<<<<<<< HEAD
                return redirect(url_for('login'))
            except mysql.connector.Error as e:
                error = f"Database error during registration: {e}"
            finally:
                if conn:
                    conn.close()
        if error:
            flash(error, 'error')

=======
                return redirect(url_for('login')) # Redirect to login after successful registration
            except sqlite3.Error as e: error = f"Database error during registration: {e}"
            finally:
                if conn: conn.close()
        if error: flash(error, 'error')

    # For GET requests or if POST had errors, render the registration form
>>>>>>> cdbb0c8d369c522697bd8b8c4141dfe6f87e9839
    return render_template(
        'register.html',
        username=request.form.get('username', ''),
        email=request.form.get('email', ''),
        contact_info=request.form.get('contact_info', ''),
        user_type=request.form.get('user_type', 'Customer')
    )

<<<<<<< HEAD
# --- Login ---
@app.route('/login', methods=['GET', 'POST'])
def login():
=======

# --- NEW: Login Route ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect them to the dashboard
>>>>>>> cdbb0c8d369c522697bd8b8c4141dfe6f87e9839
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        error = None
<<<<<<< HEAD
=======
        conn = None
>>>>>>> cdbb0c8d369c522697bd8b8c4141dfe6f87e9839

        if not username or not password:
            error = 'Please enter both username and password.'
        else:
            try:
                conn = get_db()
<<<<<<< HEAD
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
=======
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
                user = cursor.fetchone() # Get the full user row (as a Row object)

                if user is None:
                    error = 'Invalid credentials. Please try again.' # Generic error
                # Check the hashed password
                elif not check_password_hash(user['password_hash'], password):
                    error = 'Invalid credentials. Please try again.' # Generic error
                else:
                    # --- Login Successful ---
                    session.clear() # Clear any old session data
                    # Store user info in the session
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    session['user_type'] = user['user_type'] # Store user type if needed
                    flash(f'Welcome back, {user["username"]}!', 'success')
                    return redirect(url_for('dashboard')) # Redirect to dashboard

            except sqlite3.Error as e:
                error = f"Database error during login: {e}"
                # Log this properly in a real app
>>>>>>> cdbb0c8d369c522697bd8b8c4141dfe6f87e9839
            finally:
                if conn:
                    conn.close()

<<<<<<< HEAD
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
=======
        # If login failed or database error occurred
        if error:
            flash(error, 'error')

    # Render the login template for GET requests or failed POST requests
    return render_template('login.html')


# --- NEW: Dashboard Route (Protected) ---
@app.route('/dashboard')
def dashboard():
    # Check if user is logged in (check if user_id is in session)
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))

    # User is logged in, display the dashboard
    # You can fetch more user-specific data here if needed
    username = session.get('username', 'User') # Get username from session
    return render_template('dashboard.html', username=username)


# --- NEW: Logout Route ---
@app.route('/logout')
def logout():
    session.clear() # Clear all data from the session
    flash('You have been successfully logged out.', 'info')
    return redirect(url_for('login')) # Redirect to login page


# --- Run the App (Keep as is) ---
>>>>>>> cdbb0c8d369c522697bd8b8c4141dfe6f87e9839
if __name__ == '__main__':
    init_db()
    app.run(debug=True) # Keep debug=True for development