import requests
import os
from dotenv import load_dotenv
from models import db, Route, Train, Stop, Schedule, TrainStatus  # Your SQLAlchemy models
from sqlalchemy.exc import IntegrityError
from main import create_app, db
from datetime import datetime

load_dotenv()  # Load environment variables

# API credentials
MBTA_API_KEY = os.getenv('MBTA_API_KEY')
MBTA_BASE_URL = os.getenv('MBTA_BASE_URL')

app = create_app()

ROUTE_ID_MAPPING = {
    "Green-B": 1,
    "Green-C": 2,
    "Green-D": 3,
    "Green-E": 4
}


# Function to fetch data from MBTA API
def fetch_data_from_mbta(endpoint):
    url = f"{MBTA_BASE_URL}/{endpoint}"
    headers = {
        'Authorization': f'Bearer {MBTA_API_KEY}'
    }
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else None

# Function to load routes
def load_routes():
    data = fetch_data_from_mbta("routes")
    if data:
        for route in data['data']:
            try:
                # Map route_id to integer
                mapped_id = ROUTE_ID_MAPPING.get(route['id'])
                if mapped_id is None:
                    print(f"Skipping route {route['attributes']['long_name']} (not mapped).")
                    continue

                # Check if route already exists
                route_entry = Route.query.filter_by(route_id=mapped_id).first()
                if not route_entry:
                    # Prepare the route attributes
                    route_entry = Route(
                        route_id=mapped_id,
                        route_name=f"{route['attributes']['long_name']}",  # e.g., "Green Line B"
                        route_type="Light Rail",  # Assuming Light Rail for all Green Line routes
                        route_color="Green"      # Assuming Green for all Green Line routes
                    )
                    try:
                    # Adding route to the session
                        db.session.add(route_entry)
                        db.session.commit()
                        print(f"Route added: {route['attributes']['long_name']}")
                    except IntegrityError as e:
                        db.session.rollback()  # Clear the failed transaction state
                        print(f"Error adding route {route['attributes']['long_name']}: {e}")
                    print(f"Route added: {route['attributes']['long_name']}")
                else:
                    print(f"Route {route['attributes']['long_name']} already exists.")
            except IntegrityError:
                db.session.rollback()
                print(f"Error adding route {route['attributes']['long_name']}.")
            except Exception as e:
                print(f"An error occurred: {e}")


def load_stops():
    green_line_routes = ["Green-B", "Green-C", "Green-D", "Green-E"]  # Specify Green Line routes
    data = fetch_data_from_mbta("stops?filter[route]=" + ",".join(green_line_routes))  # Filter by Green Line routes
    if not data or 'data' not in data:
        print("No stop data available or malformed response.")
        return

    for stop in data['data']:
        try:
            # Extract stop attributes
            stop_id = stop['id']  # API-provided stop_id
            stop_name = stop['attributes'].get('name', 'Unknown Stop')[:100]  # Ensure max length is 100
            latitude = stop['attributes'].get('latitude', None)
            longitude = stop['attributes'].get('longitude', None)

            # Check if stop already exists
            stop_entry = Stop.query.filter_by(stop_code=stop_id).first()
            if not stop_entry:
                # Prepare the stop entry
                stop_entry = Stop(
                    stop_name=stop_name,
                    stop_code=stop_id,  # Use API stop_id as stop_code
                    latitude=latitude,
                    longitude=longitude
                )
                db.session.add(stop_entry)
                db.session.commit()
                print(f"Stop added: {stop_name}")
            else:
                print(f"Stop {stop_name} already exists.")
        except IntegrityError as e:
            db.session.rollback()
            print(f"Integrity error adding stop {stop_name}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


# Function to load train schedules
def load_schedules():
    data = fetch_data_from_mbta("schedules")
    if data:
        for schedule in data['data']:
            try:
                # Query to ensure no duplicate schedule
                existing_schedule = Schedule.query.filter_by(
                    train_id=schedule['relationships']['train']['data']['id'],
                    stop_id=schedule['relationships']['stop']['data']['id']
                ).first()

                if not existing_schedule:
                    train_schedule = Schedule(
                        train_id=schedule['relationships']['train']['data']['id'],
                        stop_id=schedule['relationships']['stop']['data']['id'],
                        arrival_time=schedule['attributes']['arrival_time']
                    )
                    db.session.add(train_schedule)
                    db.session.commit()
                    print(f"Schedule added for Train ID: {train_schedule.train_id}")
                else:
                    print(f"Schedule for Train ID: {schedule['relationships']['train']['data']['id']} already exists.")

            except IntegrityError:
                db.session.rollback()  # Handle integrity errors
                print(f"Error adding schedule for Train ID: {schedule['relationships']['train']['data']['id']}.")


def load_trains():
    # Fetch vehicle data filtered by Green Line routes
    data = fetch_data_from_mbta("vehicles")
    
    if data:
        for vehicle in data['data']:
            try:
                train_id = vehicle['id']  # Get the vehicle ID
                train_id = train_id.split('-')[1] if '-' in train_id else train_id
                route = vehicle['relationships']['route']['data']['id']  # Extract route ID from relationships
                print("train_id: ", train_id)
                # Map the route ID to its full name (mapped_route) from the mapping dictionary
                mapped_route = ROUTE_ID_MAPPING.get(route)
                
                if mapped_route is None:
                    print(f"Skipping vehicle {train_id} (route not mapped).")
                    continue

                # Check if the vehicle already exists in the database
                vehicle_entry = Train.query.filter_by(train_id=train_id).first()  # Change vehicle_id to train_id

                if not vehicle_entry:
                    # If the vehicle doesn't exist, create a new entry
                    vehicle_entry = Train(
                        train_id=train_id,
                        route=mapped_route  # Use the mapped route name
                    )
                    db.session.add(vehicle_entry)
                    db.session.commit()
                    print(f"Vehicle added: {train_id} with route {mapped_route}")
                else:
                    # If the vehicle exists, update its route
                    vehicle_entry.route = mapped_route
                    db.session.commit()
                    print(f"Vehicle updated: {train_id} with route {mapped_route}")

            except IntegrityError as e:
                db.session.rollback()
                print(f"Error adding/updating vehicle {train_id}: {e}")
            except Exception as e:
                print(f"An error occurred: {e}")

def load_train_status():
    # Fetch vehicle data filtered by status-related info
    data = fetch_data_from_mbta("vehicles")  # Assuming "vehicles" endpoint gives status-related info
    
    if data:
        for vehicle in data['data']:
            try:
                train_id = vehicle['id']  # Get the vehicle ID
                # Check if the train is part of the Green Line
                if not train_id.startswith('G'):  # Ensure it starts with 'G'
                    continue
                
                train_id = train_id.split('-')[1] if '-' in train_id else train_id  # Extract relevant part of train_id
                
                # Extract status-related information
                status_value = vehicle['attributes'].get('current_status', 'UNKNOWN') 

                # Extract current_stop_id from the stop relationship
                current_stop_id = vehicle['relationships']['stop']['data']['id'] if 'stop' in vehicle['relationships'] and vehicle['relationships']['stop']['data'] else None
                print("current stop id: ", current_stop_id)
                
                # Ensure current_stop_id is an integer
                if current_stop_id is not None:
                    try:
                        current_stop_id = int(current_stop_id)  # Convert to integer
                        print(f"Current Stop ID to store: {current_stop_id}")
                    except ValueError:
                        print(f"Invalid stop ID: {current_stop_id}. It must be an integer.")
                        continue  # Skip this entry if conversion fails

                last_updated = vehicle['attributes'].get('updated_at', None)
                
                if last_updated:
                    last_updated = datetime.fromisoformat(last_updated)  # Convert to datetime object

                # Check if the stop ID exists in the stop table
                if not Stop.query.filter_by(stop_id=current_stop_id).first():
                    print(f"Stop ID {current_stop_id} does not exist in the stop table. Skipping update.")
                    continue  # Skip this entry if the stop ID does not exist

                # Check if the train status already exists in the database
                train_status_entry = TrainStatus.query.filter_by(train_id=train_id).first()

                if not train_status_entry:
                    # If the train status doesn't exist, create a new entry
                    train_status_entry = TrainStatus(
                        train_id=train_id,
                        status=status_value,
                        current_stop_id=current_stop_id,  # Store the current stop ID here
                        last_updated=last_updated
                    )
                    db.session.add(train_status_entry)
                    db.session.commit()
                    print(f"Train status added for Train ID: {train_id} with status {status_value}")
                else:
                    # If the train status exists, update its attributes
                    train_status_entry.status = status_value
                    train_status_entry.current_stop_id = current_stop_id  # Update the current stop ID
                    train_status_entry.last_updated = last_updated
                    db.session.commit()
                    print(f"Train status updated for Train ID: {train_id} with status {status_value}")

            except IntegrityError as e:
                db.session.rollback()
                print(f"Error adding/updating train status for Train ID: {train_id}: {e}")
            except Exception as e:
                print(f"An error occurred: {e}")



def load_all_data():
    #load_routes()
    #load_stops()
    #load_schedules()
    #load_trains()
    load_train_status()

if __name__ == "__main__":
    with app.app_context():
        load_all_data()
