import mysql.connector
import csv
from datetime import datetime, timedelta
import logging
import traceback

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DATABASES = ["offbeat_db1", "offbeat_db2"]
CONVERSION_RATE = 0.013  # Conversion rate from INR to USD

def get_mysql_connection(database_name):
    """Returns a MySQL connection to the specified database."""
    return mysql.connector.connect(
        host="localhost",
        user="offbeat_traveler",
        passwd="12345678",
        database=database_name,
        autocommit=False
    )

def create_database_if_not_exists(db_name):
    """Creates a database if it does not exist."""
    with mysql.connector.connect(
        host="localhost",
        user="offbeat_traveler",
        passwd="12345678",
        autocommit=False
    ) as db:
        with db.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
            db.commit()

def create_tables(db_name):
    """Creates necessary tables in the specified database."""
    with get_mysql_connection(db_name) as db:
        with db.cursor() as cursor:
            tables_queries = [
                "CREATE TABLE IF NOT EXISTS place (id INT AUTO_INCREMENT PRIMARY KEY, city VARCHAR(64), airport VARCHAR(64), code VARCHAR(3) UNIQUE, country VARCHAR(64))",
                "CREATE TABLE IF NOT EXISTS user (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(500) UNIQUE NOT NULL, password TEXT NOT NULL, db_id VARCHAR(50) NOT NULL DEFAULT 'offbeat_db1')",
                "CREATE TABLE IF NOT EXISTS flight (id INT AUTO_INCREMENT PRIMARY KEY, origin_id INT, destination_id INT, depart_time TIME, duration TIME, arrival_time TIME, flight_no VARCHAR(24), airline VARCHAR(64), economy_fare FLOAT, business_fare FLOAT NULL, first_fare FLOAT NULL, departure_date DATE, FOREIGN KEY (origin_id) REFERENCES place(id), FOREIGN KEY (destination_id) REFERENCES place(id))",
                "CREATE TABLE IF NOT EXISTS user_booking (booking_id INT AUTO_INCREMENT PRIMARY KEY, user_id INT, flight_id INT, passenger_name VARCHAR(100), family_name VARCHAR(100), gender ENUM('male', 'female', 'other'), dob DATE, status ENUM('booked', 'canceled'), FOREIGN KEY (user_id) REFERENCES user(id), FOREIGN KEY (flight_id) REFERENCES flight(id))"
            ]
            for query in tables_queries:
                cursor.execute(query)
            db.commit()

def initialize_databases():
    """Initializes both databases by creating necessary tables."""
    for db_name in DATABASES:
        create_database_if_not_exists(db_name)
        create_tables(db_name)

def populate_places_from_csv(file_path):
    """Populates the 'place' table in both databases from a CSV file."""
    with open(file_path, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            for db_name in DATABASES:
                with get_mysql_connection(db_name) as db:
                    with db.cursor() as cursor:
                        try:
                            cursor.execute(
                                "INSERT INTO place (city, airport, code, country) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE city=%s, airport=%s, country=%s",
                                (row['city'], row['airport'], row['code'], row['country'], row['city'], row['airport'], row['country']))
                            db.commit()
                        except mysql.connector.Error as e:
                            logging.error(f"Error occurred in {db_name}: {e}")

def populate_flights_from_csv(file_path):
    """Populates the 'flight' table in both databases from a CSV file."""
    with open(file_path, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        total_flights = 0
        successful_inserts = 0
        failed_flights = 0

        for row in reader:
            total_flights += 1
            for db_name in DATABASES:
                with get_mysql_connection(db_name) as db:
                    with db.cursor() as cursor:
                        try:
                            economy_fare = float(row['economy_fare']) * CONVERSION_RATE if row['economy_fare'] else None
                            business_fare = float(row['business_fare']) * CONVERSION_RATE if row.get('business_fare') else None
                            first_fare = float(row['first_fare']) * CONVERSION_RATE if row.get('first_fare') else None
                            departure_date = datetime.today().date() + timedelta(days=int(row['depart_weekday']))

                            cursor.execute("SELECT id FROM place WHERE code = %s", (row['origin'],))
                            origin_id = cursor.fetchone()
                            cursor.execute("SELECT id FROM place WHERE code = %s", (row['destination'],))
                            destination_id = cursor.fetchone()

                            if not origin_id or not destination_id:
                                raise ValueError("Missing place code.")

                            cursor.execute(
                                "INSERT INTO flight (origin_id, destination_id, depart_time, duration, arrival_time, flight_no, airline, economy_fare, business_fare, first_fare, departure_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                                (origin_id[0], destination_id[0], row['depart_time'], row['duration'], row['arrival_time'], row['flight_no'], row['airline'], economy_fare, business_fare, first_fare, departure_date)
                            )
                            db.commit()
                            successful_inserts += 1
                        except Exception as e:
                            failed_flights += 1

def main():
    initialize_databases()
    populate_places_from_csv('airports.csv')
    populate_flights_from_csv('international_flights.csv')
    logging.info("Database populated with place and flight data.")

if __name__ == "__main__":
    main()