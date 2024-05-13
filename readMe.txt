Readme for Offbeat Travels

Project Overview:
Offbeat Travels is a web-based application that manages travel bookings and inquiries. The application uses Flask for the web server, MySQL for relational data storage, and MongoDB for non-relational data like FAQs and logs.

File Structure:
- offbeat-env/: Contains the virtual environment setup for the project.
- static/: Holds all static content used by the web application, such as images, CSS, and JavaScript files.
- templates/: Contains HTML files which define the structure and layout of the web application's pages.
- airports.csv: A CSV file containing data about different airports, used to populate the MySQL database.
- international_flights.csv: A CSV file containing data about flights, used to populate the MySQL database.
- app.py: The main Flask application file that starts the web server.
- create_db.py: Python script that initializes the MySQL database with the required tables and schema.
- populate_faq.py: Python script used to populate the MongoDB database with frequently asked questions for the FAQ section of the web application.
- utils.py: Contains utility functions and helpers used across the project.
- readMe.txt: This file, providing documentation on the project setup and instructions on how to run the application.
- requirements.txt: Lists all Python dependencies required to run the project that should be installed using pip after activating the virtual environment.

Pre-requisites:
Python 3.x
MySQL
MongoDB
Flask
Virtual Environment Tools
pip for Python Package Management

Initial Setup
A. Environment Setup:
    1. Download the Project
    2. Navigate to Project Directory:
        cd path/to/OffbeatTravels
    3. Activate Virtual Environment:
        source offbeat-env/bin/activate   # On Windows use `offbeat-venv\Scripts\activate`
    4. Install Dependencies:
        pip install -r requirements.txt
B. Database Setup:
    MySQL
        1. Install MySQL
            macOS: brew install mysql
        2. Start MySQL Shell:
            mysql -u root -p 
        3. Create MySQL User:
            CREATE USER 'offbeat_traveler'@'localhost' IDENTIFIED BY '12345678';
            GRANT ALL PRIVILEGES ON *.* TO 'offbeat_traveler'@'localhost';
            FLUSH PRIVILEGES;
    MongoDB
        1. Install MongoDB (Link: https://www.mongodb.com/docs/manual/administration/install-community/)
        2. If you already have MongoDB with authentication, skip to to step 8
        3. Disable authentication:
            Edit config file:
                macOS: nano /opt/homebrew/etc/mongod.conf
            Comment out the security authorization line by adding a # in front of it:
                # security:
                #   authorization: enabled
        3. Start MongoDB: 
            macOS: sudo brew services start mongodb-community@7.0
        3. Access MongoDB Shell:
            mongosh
        4. Create Admin User in MongoDB:
            use admin
            db.createUser({
                user: "admin",
                pwd: "Dsci-551",
                roles: ["root"]
            });
        5. Stop MongoDB:
            macOS: sudo brew services stop mongodb-community@7.0
        6. Reenable authentication by removing the # added in front of the security authorization line in part 3
            macOS: nano /opt/homebrew/etc/mongod.conf
        7. Restart MongoDB:
            macOS: sudo brew services start mongodb-community@7.0
        8. Access MongoDB with Authentication:
            mongosh -u admin -p
        9. Create New MongoDB User:
            db.createUser({
              user: "offbeat_traveler",
              pwd: "12345678",
              roles: [{role: "readWrite", db: "travels"}],
            });

Running the Application:
1. Make sure that MySQL and MongoDB services are running and that the appropriate users were created.
2. In "OffbeatTravels" directory, set environment variables:
    macOS/Linux:
        export FLASK_APP=app.py
    Windows:
        set FLASK_APP=app.py
3. Initialize Database:
    python populate_faq.py
    python create_db.py
4. Start Flask Application:
    flask run

This will start the web server on http://127.0.0.1:5000/ by default