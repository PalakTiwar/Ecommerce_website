from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import config

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY


# ---------------- DATABASE ----------------
def get_db():
    return mysql.connector.connect(
        host=config.MYSQL_HOST,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DB
    )


# ---------------- HOME ----------------
@app.route('/')
def index():
    return redirect(url_for('login'))


# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash("Please enter both username and password.", "error")
            return render_template('login.html')

        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Users WHERE username = %s", (username,))
            user = cursor.fetchone()

            if not user or not check_password_hash(user['password'], password):
                flash("Invalid credentials.", "error")
            else:
                session.clear()
                session['user_id'] = user['user_id']
                session['username'] = user['username']
                session['user_type'] = user['user_type']

                flash(f"Welcome back, {user['username']}!", "success")

                if user['user_type'] == 'Admin':
                    return redirect(url_for('admin_products'))
                return redirect(url_for('dashboard'))

        except mysql.connector.Error:
            flash("Database error during login.", "error")

        finally:
            if conn.is_connected():
                conn.close()

    return render_template('login.html')


# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        contact_info = request.form.get('contact_info', '')
        user_type = request.form.get('user_type', 'Customer')

        if not username or not password or not email:
            flash("All required fields must be filled.", "error")
            return render_template('register.html')

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template('register.html')

        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM Users WHERE username=%s OR email=%s", (username, email))
            if cursor.fetchone():
                flash("Username or Email already exists.", "error")
            else:
                hashed = generate_password_hash(password)
                cursor.execute("""
                    INSERT INTO Users (username, password, email, contact_info, user_type)
                    VALUES (%s, %s, %s, %s, %s)
                """, (username, hashed, email, contact_info, user_type))
                conn.commit()
                flash("Account created successfully!", "success")
                return redirect(url_for('login'))

        except mysql.connector.Error:
            conn.rollback()
            flash("Database error during registration.", "error")

        finally:
            if conn.is_connected():
                conn.close()

    return render_template('register.html')


# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    category = request.args.get('category')
    products, categories = [], []

    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT DISTINCT category FROM Products")
        categories = cursor.fetchall()

        if category:
            if category == 'All':
                cursor.execute("SELECT * FROM Products")
            else:
                cursor.execute("SELECT * FROM Products WHERE category=%s", (category,))
            products = cursor.fetchall()

    except mysql.connector.Error:
        flash("Error loading dashboard.", "error")

    finally:
        if conn.is_connected():
            conn.close()

    return render_template('dashboard.html',
                           products=products,
                           categories=categories,
                           selected_category=category)


# ---------------- ADMIN PRODUCTS ----------------
@app.route('/admin/products', methods=['GET', 'POST'])
def admin_products():
    if session.get('user_type') != 'Admin':
        return redirect(url_for('login'))

    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        if request.method == 'POST':
            action = request.form.get('action')

            if action == 'add':
                cursor.execute("""
                    INSERT INTO Products (name, price, stock_quantity, category)
                    VALUES (%s, %s, %s, %s)
                """, (
                    request.form['name'],
                    float(request.form['price']),
                    int(request.form['stock_quantity']),
                    request.form['category']
                ))
                conn.commit()
                flash("Product added.", "success")

            elif action == 'delete':
                cursor.execute("DELETE FROM Products WHERE product_id=%s",
                               (request.form['product_id'],))
                conn.commit()
                flash("Product deleted.", "success")

        cursor.execute("SELECT * FROM Products")
        products = cursor.fetchall()

    except mysql.connector.Error:
        flash("Database error.", "error")
        products = []

    finally:
        if conn.is_connected():
            conn.close()

    return render_template('admin_products.html', products=products)


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('login'))


# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True)
