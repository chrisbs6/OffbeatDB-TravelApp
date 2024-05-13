from flask import Flask, render_template, request, redirect, url_for, flash, current_app
from flask_login import LoginManager, current_user, login_user, logout_user, login_required, UserMixin
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import mysql.connector
from pymongo import MongoClient
from flask_wtf.csrf import CSRFProtect
import csv

# Create the Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://offbeat_traveler:12345678@localhost/offbeat_db1"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
csrf = CSRFProtect(app)

# Initialize plugins
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Define the user loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(500), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    db_id = db.Column(db.String(50), nullable=False)

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')  
    submit = SubmitField('Log In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class UserBooking(db.Model):
    __tablename__ = 'user_booking'
    booking_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    flight_id = db.Column(db.Integer, db.ForeignKey('flight.id'), nullable=False)
    passenger_name = db.Column(db.String(100), nullable=False)
    family_name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.Enum('male', 'female', 'other'), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum('booked', 'canceled'), nullable=False)

    def __repr__(self):
        return f"<UserBooking(user_id='{self.user_id}', flight_id='{self.flight_id}')>"

def ensure_database_exists(database_name):
    conn = mysql.connector.connect(
        host="localhost",
        user="offbeat_traveler",
        passwd="12345678"
    )
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name}")
    cursor.close()
    conn.close()

ensure_database_exists('offbeat_db1')
ensure_database_exists('offbeat_db2')

def determine_database(data_type):
    """
    Determines the appropriate database (MySQL or MongoDB) based on the data type.
    """
    # Mapping of data types to databases
    use_sql = ['user', 'booking', 'transaction', 'flight']
    use_nosql = ['faq', 'log', 'document']

    if data_type in use_sql:
        return 'MySQL'
    elif data_type in use_nosql:
        return 'MongoDB'
    else:
        raise ValueError("No suitable database found for the provided data type.")

def manual_hash(input_string):
    """
    A simple hash function to map an input string to an integer.
    """
    # Base value for the hash
    hash_value = 0

    # Process each character in the input string
    for char in input_string:
        # Shift left by 5 (equivalent to multiplying by 32), then add the character code
        hash_value = (hash_value << 5) - hash_value + ord(char)

    # Return the hash value
    return hash_value

def get_mysql_connection(username):
    hash_value = manual_hash(username)
    database_index = abs(hash_value) % 2
    database_name = "offbeat_db1" if database_index == 0 else "offbeat_db2"
    return mysql.connector.connect(
        host="localhost",
        user="offbeat_traveler",
        passwd="12345678",
        database=database_name  # Make sure this parameter is correctly set
    )

def get_mongo_connection():
    client = MongoClient("mongodb://offbeat_traveler:12345678@localhost:27017")
    return client.travels

@app.route('/faq')
def faq():
    if determine_database('faq') == 'MongoDB':
        db = get_mongo_connection()
        collection = db['faq']
        faqs_raw = list(collection.find({}))
        faqs = {}
        for faq in faqs_raw:
            category = faq['category']
            if category not in faqs:
                faqs[category] = []
            faqs[category].append({'question': faq['question'], 'answer': faq['answer']})
        return render_template('faqs.html', faqs=faqs)
    else:
        return redirect(url_for('home'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # Use the hashed username to decide which database to connect to
        conn = get_mysql_connection(username)
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM user WHERE username = %s", (username,))
            user_data = cursor.fetchone()
            if user_data and check_password_hash(user_data['password'], password):
                user = User.query.get(user_data['id'])
                login_user(user, remember=form.remember.data)
                return redirect(request.args.get('next') or url_for('home'))
            else:
                flash('Invalid username or password', 'danger')
        except Exception as e:
            flash(f"Login error: {str(e)}", 'danger')
        finally:
            cursor.close()
            conn.close()

    return render_template('login.html', form=form)

def register_user(username, password, db_id):
    hashed_password = generate_password_hash(password)
    conn = get_mysql_connection(db_id)  # Assuming you choose the database based on some logic
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO user (username, password, db_id) VALUES (%s, %s, %s)", 
                (username, hashed_password, db_id)
            )
        conn.commit()
    except mysql.connector.Error as e:
        logging.error(f"Failed to register user: {e}")
    finally:
        conn.close()

def user_exists(user_id, db_name):
    conn = get_mysql_connection(db_name)
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM user WHERE id = %s", (user_id,))
            return cursor.fetchone() is not None
    finally:
        conn.close()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        conn = get_mysql_connection(username)
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT id FROM user WHERE username = %s", (username,))
            if cursor.fetchone():
                flash('Username already taken. Please choose a different one.', 'danger')
                return render_template('register.html', form=form)
            
            hashed_password = generate_password_hash(password)
            database_name = "offbeat_db1" if manual_hash(username) % 2 == 0 else "offbeat_db2"
            cursor.execute("INSERT INTO user (username, password, db_id) VALUES (%s, %s, %s)", 
                           (username, hashed_password, database_name))
            conn.commit()
            # Removed other flash messages related to successful registration
            return redirect(url_for('login'))
        except Exception as e:
            conn.rollback()
            # This flash could be commented out if you don't want any error messages
            # flash(f"An error occurred during registration: {str(e)}", 'danger')
        finally:
            cursor.close()
            conn.close()

    return render_template('register.html', form=form)
    
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/')
def home():
    with open('airports.csv', mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        codes = [row['code'] for row in reader]
    return render_template('home.html', airport_codes=codes)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Here, you'd collect data from a form submission and possibly store it in a database
        if determine_database('contact_messages') == 'MongoDB':
            db = get_mongo_connection()
            db.messages.insert_one(request.form.to_dict())
            return redirect(url_for('contact'))
        else:
            flash("Failed to process contact message.", "error")
    return render_template('contact.html')

@app.route('/search_results', methods=['GET'])
@login_required
def search_results():
    origin_code = request.args.get('from')
    destination_code = request.args.get('to')
    departure_date = request.args.get('departure_date')
    flight_class = request.args.get('class')

    if not (origin_code and destination_code and departure_date):
        return redirect(url_for('home'))

    # Assuming we are getting the user's database from current_user object
    username = current_user.username
    conn = get_mysql_connection(username)
    cursor = conn.cursor(dictionary=True)

    try:
        query = """
            SELECT flight.*, origin.code as origin_code, destination.code as destination_code, %s as source_db
            FROM flight
            JOIN place as origin ON flight.origin_id = origin.id
            JOIN place as destination ON flight.destination_id = destination.id
            WHERE origin.code = %s AND destination.code = %s AND DATE(departure_date) = DATE(%s)
        """
        cursor.execute(query, (conn.database, origin_code, destination_code, departure_date))
        flights = cursor.fetchall()
        if not flights:
            flash("We're sorry, there are no flights available for your search criteria at this time.", "info")
            return render_template('search_results.html', flights=None, flight_class=flight_class)

        return render_template('search_results.html', flights=flights, flight_class=flight_class)
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", 'danger')
    finally:
        cursor.close()
        conn.close()

@app.route('/booking_form/<int:flight_id>', methods=['GET', 'POST'])
@login_required
def booking_form(flight_id):
    # Assuming the username is used to determine the database
    username = current_user.username
    database_name = "offbeat_db1" if manual_hash(username) % 2 == 0 else "offbeat_db2"

    flight = get_flight_details(flight_id, database_name)

    if not flight:
        flash('Flight not found.', 'error')
        return redirect(url_for('search_results'))

    return render_template('booking_form.html', flight=flight)

def get_booking_details(booking_id):
    if determine_database('booking') == 'MySQL':
        conn = get_mysql_connection(booking_id)  # Assume booking_id can somewhat determine the database
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT user_booking.*, flight.flight_no, flight.airline,
        origin.city as origin_city, destination.city as destination_city
        FROM user_booking
        JOIN flight ON user_booking.flight_id = flight.id
        JOIN place as origin ON flight.origin_id = origin.id
        JOIN place as destination ON flight.destination_id = destination.id
        WHERE user_booking.booking_id = %s
        """
        cursor.execute(query, (booking_id,))
        booking_details = cursor.fetchone()

        cursor.close()
        conn.close()
        return booking_details
    else:
        return None  # Or handle the error accordingly

@app.route('/book_flight/<int:flight_id>', methods=['POST'])
@login_required
def book_flight(flight_id):
    passenger_name = request.form.get('passenger_name')
    family_name = request.form.get('family_name')
    gender = request.form.get('gender')
    dob = request.form.get('dob')

    if not all([passenger_name, family_name, gender, dob]):  # Ensure all fields are provided
        flash('All fields are required.', 'error')
        return redirect(url_for('booking_form', flight_id=flight_id))

    username = current_user.username  # Assuming current_user has the username
    database_name = "offbeat_db1" if manual_hash(username) % 2 == 0 else "offbeat_db2"
    conn = get_mysql_connection(username)  # Updated to use the hashed username
    cursor = conn.cursor()
    try:
        # Insert user_id from current_user to link the booking
        cursor.execute("""
            INSERT INTO user_booking (user_id, flight_id, passenger_name, family_name, gender, dob)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (current_user.id, flight_id, passenger_name, family_name, gender, dob))
        conn.commit()
    except Exception as e:
        conn.rollback()
        app.logger.error(f"Error booking flight: {e}")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('my_bookings'))


def get_user_bookings(user_id):
    username = current_user.username  # Assuming current_user has the username
    database_name = "offbeat_db1" if manual_hash(username) % 2 == 0 else "offbeat_db2"

    conn = get_mysql_connection(username)  # Using the username to determine database
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT user_booking.*, flight.flight_no, flight.airline,
    origin.city as origin_city, destination.city as destination_city
    FROM user_booking
    JOIN flight ON user_booking.flight_id = flight.id
    JOIN place as origin ON flight.origin_id = origin.id
    JOIN place as destination ON flight.destination_id = destination.id
    WHERE user_booking.user_id = %s
    """
    cursor.execute(query, (user_id,))
    user_bookings = cursor.fetchall()

    cursor.close()
    conn.close()

    return user_bookings

@app.route('/my_bookings')
@login_required
def my_bookings():
    # Retrieve bookings for the current user
    bookings = get_user_bookings(current_user.id)

    return render_template('my_bookings.html', bookings=bookings)

def get_flight_details(flight_id, source_db):
    conn = mysql.connector.connect(
        host="localhost",
        user="offbeat_traveler",
        passwd="12345678",
        database=source_db  # Use the database passed as parameter
    )
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * FROM flight WHERE id = %s
        """, (flight_id,))
        flight_details = cursor.fetchone()
        return flight_details
    except mysql.connector.Error as e:
        flash(f'Failed to retrieve flight details: {str(e)}', 'danger')
        return None
    finally:
        cursor.close()
        conn.close()

@app.route('/update_booking/<int:booking_id>', methods=['POST'])
@login_required
def update_booking(booking_id):
    # Make sure the method is POST
    if request.method == 'POST':
        # Extract the updated details from the form
        passenger_name = request.form.get('passenger_name')
        family_name = request.form.get('family_name')

        # Get the username to determine which database to use
        username = current_user.username
        database_name = "offbeat_db1" if manual_hash(username) % 2 == 0 else "offbeat_db2"

        # Connect to the appropriate database
        conn = get_mysql_connection(username)
        cursor = conn.cursor(dictionary=True)
        
        # Prepare the SQL update statement
        sql = """
            UPDATE user_booking
            SET passenger_name = %s, family_name = %s
            WHERE booking_id = %s AND user_id = %s
        """
        try:
            # Execute the update query
            cursor.execute(sql, (passenger_name, family_name, booking_id, current_user.id))
            conn.commit()

            # Check if the update was successful
            affected_rows = cursor.rowcount
        
        except mysql.connector.Error as e:
            conn.rollback()
            current_app.logger.error("SQL Error on update: %s", e)
        
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('my_bookings'))
@app.route('/update_booking_form/<int:booking_id>', methods=['GET'])
@login_required
def update_booking_form(booking_id):
    booking = UserBooking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        return redirect(url_for('my_bookings'))
    return render_template('update_booking_form.html', booking=booking)

@app.route('/cancel_booking/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    if request.method == 'POST':
        # Determine the database where the booking is stored
        username = current_user.username
        database_name = "offbeat_db1" if manual_hash(username) % 2 == 0 else "offbeat_db2"
        
        # Connect to the appropriate database
        conn = get_mysql_connection(username)
        cursor = conn.cursor(dictionary=True)
        try:
            # Execute the delete operation
            cursor.execute("""
                DELETE FROM user_booking
                WHERE booking_id = %s AND user_id = %s
            """, (booking_id, current_user.id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            app.logger.error(f"Error cancelling booking: {e}")
        finally:
            cursor.close()
            conn.close()
        
        return redirect(url_for('my_bookings'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', debug=True)