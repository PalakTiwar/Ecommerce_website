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
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        contact_info = request.form.get('contact_info', '')
        user_type = request.form.get('user_type')
        error = None
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

        if error is None:
            try:
                password_hash = generate_password_hash(password)
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO users (username, password_hash, email, contact_info, user_type) VALUES (?, ?, ?, ?, ?)',
                    (username, password_hash, email, contact_info, user_type)
                )
                conn.commit()
                flash('Account created successfully! Please log in.', 'success')
                return redirect(url_for('login')) # Redirect to login after successful registration
            except sqlite3.Error as e: error = f"Database error during registration: {e}"
            finally:
                if conn: conn.close()
        if error: flash(error, 'error')

    # For GET requests or if POST had errors, render the registration form
    return render_template(
        'register.html',
        username=request.form.get('username', ''),
        email=request.form.get('email', ''),
        contact_info=request.form.get('contact_info', ''),
        user_type=request.form.get('user_type', 'Customer')
    )


# --- NEW: Login Route ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect them to the dashboard
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        error = None
        conn = None

        if not username or not password:
            error = 'Please enter both username and password.'
        else:
            try:
                conn = get_db()
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
            finally:
                if conn:
                    conn.close()

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
if __name__ == '__main__':
    init_db()
    app.run(debug=True) # Keep debug=True for development