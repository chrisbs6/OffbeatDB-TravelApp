import pandas as pd
from datetime import datetime, timedelta, time
from sqlalchemy.orm import sessionmaker
from models import db, Place, Flight, Week, flight_week_link

def convert_inr_to_usd(inr):
    """ Convert INR to USD with proper handling for NaN values. """
    return round(inr / 82, 2) if not pd.isna(inr) else 0

def parse_time(time_str):
    """ Safely parse time strings to datetime.time objects. """
    try:
        return datetime.strptime(time_str, '%H:%M:%S').time()
    except ValueError:
        return None

def parse_duration_to_time(duration_str):
    """ Convert HH:MM format strings to time objects, adding seconds if missing. """
    parts = duration_str.split(':')
    if len(parts) == 2:
        parts.append('00')  # Append seconds if missing
    try:
        return datetime.strptime(':'.join(parts), '%H:%M:%S').time()
    except ValueError as e:
        print(f"Error parsing duration: {duration_str}, Error: {e}")
        return None

def add_flights_from_csv(file_path):
    df = pd.read_csv(file_path)
    place_codes = df[['origin', 'destination']].stack().unique()
    places = Place.query.filter(Place.code.in_(place_codes)).all()
    place_dict = {place.code: place for place in places}

    for index, row in df.iterrows():
        origin = place_dict.get(row['origin'])
        destination = place_dict.get(row['destination'])

        if not origin or not destination:
            continue  # Skip rows with invalid origin or destination

        depart_time = parse_time(row['depart_time'])
        duration = parse_duration_to_time(row['duration'])
        arrival_time = parse_time(row['arrival_time'])
        if not all([depart_time, duration, arrival_time]):
            continue

        flight = Flight(
            origin_id=origin.id,
            destination_id=destination.id,
            depart_time=depart_time,
            duration=duration,
            arrival_time=arrival_time,
            flight_no=row['flight_no'],
            airline=row['airline_code'],
            economy_fare=convert_inr_to_usd(row['economy_fare']),
            business_fare=convert_inr_to_usd(row['business_fare']),
            first_fare=convert_inr_to_usd(row['first_fare']),
            depart_weekday=row['depart_weekday'],
            arrival_weekday=row['arrival_weekday']
        )
        db.session.add(flight)
    db.session.commit()
    print("Flights added to the database.")

def create_week_days():
    """ Generate weeks and days without redundancy checks. """
    num_weeks = 6
    day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    for week_number in range(1, num_weeks + 1):
        for weekday, name in enumerate(day_names):
            week_day = Week(number=week_number, weekday=weekday, name=name)
            db.session.add(week_day)
    db.session.commit()

def add_places_from_csv(file_path):
    df = pd.read_csv(file_path)
    codes = df['code'].unique()
    existing_places = Place.query.filter(Place.code.in_(codes)).all()
    existing_place_dict = {place.code: place for place in existing_places}

    for _, row in df.iterrows():
        place = existing_place_dict.get(row['code'])
        if place:
            place.city = row['city']
            place.airport = row['airport']
            place.country = row['country']
        else:
            place = Place(city=row['city'], airport=row['airport'], code=row['code'], country=row['country'])
            db.session.add(place)

    db.session.commit()
    print("Places updated or added to the database.")