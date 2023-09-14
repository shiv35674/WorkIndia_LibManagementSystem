from flask import Flask, jsonify, request
import bcrypt
import jwt
from datetime import datetime, timedelta
import psycopg2

app = Flask(__name__)

app.config['SECRET_KEY'] = 'your_secret_key_here'

# Update the PostgreSQL database configuration
mydb = psycopg2.connect(
    host="localhost",
    user="postgres",
    password="shivam",
    database="libmanagementsystem"
)

cursor = mydb.cursor()

# Define your database tables (ADMIN, BOOKS, BOOKINGS) if not already defined
cursor.execute(
    'CREATE TABLE IF NOT EXISTS USERS (\
    user_id SERIAL PRIMARY KEY,\
    username VARCHAR(255) UNIQUE NOT NULL,\
    password VARCHAR(255) NOT NULL,\
    email VARCHAR(255) NOT NULL\
)'
)

cursor.execute(
    'CREATE TABLE IF NOT EXISTS BOOKS (\
    book_id SERIAL PRIMARY KEY,\
    title VARCHAR(255) NOT NULL,\
    author VARCHAR(255) NOT NULL,\
    isbn VARCHAR(13) NOT NULL\
);'
)

cursor.execute(
    'CREATE TABLE IF NOT EXISTS BOOKINGS (\
    booking_id SERIAL PRIMARY KEY,\
    book_id INT NOT NULL,\
    user_id INT NOT NULL,\
    issue_time timestamp NOT NULL,\
    return_time timestamp NOT NULL,\
    FOREIGN KEY (book_id) REFERENCES BOOKS(book_id),\
    FOREIGN KEY (user_id) REFERENCES USERS(user_id)\
);'
)

mydb.commit()
# ...

@app.route('/api/signup', methods=['POST'])
def signUp():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')

        if not username or not password or not email:
            return jsonify({"status": "Missing parameters", "status_code": 400}), 400

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Insert the user into the database
        cursor.execute("INSERT INTO USERS (username, password, email) VALUES (%s, %s, %s)", (username, hashed_password, email))
        mydb.commit()

        return jsonify({
            "status": "Account successfully created",
            "status_code": 200,
            "user_id": cursor.lastrowid
        }), 200

    except Exception as e:
        print(e)
        return jsonify({"status": "Internal server error", "status_code": 500}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({"status": "Missing parameters", "status_code": 400}), 400

        # Retrieve user from the database
        cursor.execute("SELECT user_id, password FROM USERS WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[1].encode('utf-8')):
            # Generate an access token
            access_token = jwt.encode({'user_id': user[0], 'exp': datetime.utcnow() + timedelta(hours=1)},
app.config['SECRET_KEY'], algorithm='HS256')

            return jsonify({
                "status": "Login successful",
                "status_code": 200,
                "user_id": user[0],
                "access_token": access_token
            }), 200
        else:
            return jsonify({"status": "Incorrect username/password provided. Please retry", "status_code": 401}), 401

    except Exception as e:
        print(e)
        return jsonify({"status": "Internal server error", "status_code": 500}), 500

# Implement other endpoints (e.g., book creation, searching, availability, borrowing) similarly

# ... (previous code)

@app.route('/api/books/create', methods=['POST'])
def createBook():
    try:
        data = request.json
        title = data.get('title')
        author = data.get('author')
        isbn = data.get('isbn')

        if not title or not author or not isbn:
            return jsonify({"status": "Missing parameters", "status_code": 400}), 400

        # Insert the book into the database (assuming you have a 'BOOKS' table)
        cursor.execute("INSERT INTO BOOKS (title, author, isbn) VALUES (%s, %s, %s)", (title, author, isbn))
        mydb.commit()

        return jsonify({
            "status": "Book added successfully",
            "status_code": 200,
            "book_id": cursor.lastrowid
        }), 200

    except Exception as e:
        print(e)
        return jsonify({"status": "Internal server error", "status_code": 500}), 500

@app.route('/api/books', methods=['GET'])
def searchBooksByTitle():
    try:
        search_query = request.args.get('title')

        if not search_query:
            return jsonify({"status": "Missing parameters", "status_code": 400}), 400

        # Search for books by title in the database
        cursor.execute("SELECT book_id, title, author, isbn FROM BOOKS WHERE title LIKE %s", ('%' + search_query + '%',))
        books = cursor.fetchall()

        return jsonify({
            "results": books
        }), 200

    except Exception as e:
        print(e)
        return jsonify({"status": "Internal server error", "status_code": 500}), 500

@app.route('/api/books/<book_id>/availability', methods=['GET'])
def getBookAvailability(book_id):
    try:
        # Check if the book is available for borrowing (assuming you have a 'BOOKINGS' table)
        cursor.execute("SELECT * FROM BOOKINGS WHERE book_id = %s", (book_id,))
        booking = cursor.fetchone()

        if not booking:
            return jsonify({
                "book_id": book_id,
                "title": "Book Title",  # Replace with actual book title
                "author": "Book Author",  # Replace with actual book author
                "available": True
            }), 200
        else:
            return jsonify({
                "book_id": book_id,
                "title": "Book Title",  # Replace with actual book title
                "author": "Book Author",  # Replace with actual book author
                "available": False,
                "next_available_at": booking['return_time']
            }), 200

    except Exception as e:
        print(e)
        return jsonify({"status": "Internal server error", "status_code": 500}), 500

@app.route('/api/books/borrow', methods=['POST'])
def borrowBook():
    try:
        data = request.json
        book_id = data.get('book_id')
        user_id = data.get('user_id')
        issue_time = data.get('issue_time')
        return_time = data.get('return_time')

        if not book_id or not user_id or not issue_time or not return_time:
            return jsonify({"status": "Missing parameters", "status_code": 400}), 400

        # Check if the book is already booked (assuming you have a 'BOOKINGS' table)
        cursor.execute("SELECT * FROM BOOKINGS WHERE book_id = %s", (book_id,))
        existing_booking = cursor.fetchone()

        if existing_booking:
            return jsonify({"status": "Book is not available at this moment", "status_code": 400}), 400

        # Insert the booking into the database (assuming you have a 'BOOKINGS' table)
        cursor.execute("INSERT INTO BOOKINGS (book_id, user_id, issue_time, return_time) VALUES (%s, %s, %s, %s)",
                       (book_id, user_id, issue_time, return_time))
        mydb.commit()

        return jsonify({
            "status": "Book booked successfully",
            "status_code": 200,
            "booking_id": cursor.lastrowid
        }), 200

    except Exception as e:
        print(e)
        return jsonify({"status": "Internal server error", "status_code": 500}), 500

# ... (other endpoints)

if __name__ == '__main__':
    app.run(debug=True)
