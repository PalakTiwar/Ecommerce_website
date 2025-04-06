from flask import Flask, render_template, request, redirect
import mysql.connector
from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB

app = Flask(__name__)

# Connect to MySQL using your config
def get_db_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB
    )

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        contact_info = request.form['contact_info']
        user_type = request.form['user_type']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Users (username, password, email, contact_info, user_type)
            VALUES (%s, %s, %s, %s, %s)
        """, (username, password, email, contact_info, user_type))
        conn.commit()
        cursor.close()
        conn.close()

        return redirect('/')

    return render_template('register.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            if user['user_type'] == 'Admin':
                return redirect('/admin')
            else:
                return redirect('/customer')
        else:
            error = "Invalid username or password"

    return render_template('login.html', error=error)

@app.route('/admin')
def admin_dashboard():
    return "Welcome Admin!"

@app.route('/customer')
def customer_dashboard():
    return "Welcome Customer!"
@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        stock_quantity = request.form['stock_quantity']
        image_url = request.form['image_url']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Products (name, description, price, stock_quantity, image_url)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, description, price, stock_quantity, image_url))
        conn.commit()
        cursor.close()
        conn.close()

        return "Product added successfully!"

    return render_template('add_product.html')

if __name__ == '__main__':
    app.run(debug=True)
