import os
from dotenv import load_dotenv
from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash
from models import Feedback, Route, db, Train, Stop, TravelGroup, Schedule, Alert, FavoriteStop, GroupMembership, User, TrainStatus
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib
from sqlalchemy.sql import text

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    db.init_app(app)

    # Register routes
    register_routes(app)

    return app

def register_routes(app):
    @app.route('/', methods=['POST', 'GET'])
    def login():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            print(f"Received login attempt with email: {email}")
           
            user = User.query.filter_by(email=email).first()
            
            if user is None:
                print("User  not found.")
                flash('Invalid email or password. Please try again.', 'danger')
                return render_template('login.html')

            print(f"Stored password hash (first 50 chars): {user.password}")
            hashed_input_password = hashlib.sha256(password.encode('utf-8')).hexdigest()[:50]
            print(f"Hashed entered password (first 50 chars): {hashed_input_password}")

            if user.password == hashed_input_password:
                print("Password is correct, login successful.")
                flash('Login successful!', 'success')
                session['first_name'] = user.first_name
                session['last_name'] = user.last_name
                session['email'] = user.email
                session['user_id'] = user.user_id
                return redirect(url_for('index'))  
            else:
                print("Incorrect password.")
                flash('Invalid email or password. Please try again.', 'danger')
                return render_template('login.html')

        return render_template('login.html')

    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        if request.method == 'POST':
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            email = request.form['email']
            password = request.form['password']

            if User.query.filter_by(email=email).first():
                flash('Email already exists. Please use a different email.', 'danger')
                return render_template('login.html')
            
            hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()[:50]

            new_user = User(first_name=first_name, last_name=last_name, email=email, password=hashed_password, created_at=datetime.utcnow())
            db.session.add(new_user)
            db.session.commit()

            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        return render_template('login.html')

    @app.route('/logout', methods=["GET", "POST"])
    def logout():
        session.clear()  # This clears all session data
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))

    @app.route('/dashboard', methods=['GET', 'POST'])
    def index():
        uid = session.get('user_id')
        if uid is None:
            return render_template("login.html")

        """Home route to display live trains, schedules, and alerts."""
        green_line_routes = ['Green-A', 'Green-B', 'Green-C', 'Green-D', 'Green-E']
        status_mapping = {
            'INCOMING_AT': 'Incoming',
            'IN_TRANSIT_TO': 'In Transit To',
            'ON_SCHEDULE': 'On Schedule',
            'DELAYED': 'Delayed',
            'CANCELLED': 'Cancelled',
            'STOPPED_AT': "Stopped at"
        }

        # Fetch train details
        all_trains = Train.query.all()
        trains = all_trains[-10:][::-1]  # Get the last 10 records
        trainStatus_dict = {
            train.train_id: TrainStatus.query.filter_by(train_id=train.train_id).first()
            for train in trains
        }

        # Fetch corresponding stop names for the trains
        stop_names = {}
        for train in trains:
            schedules = TrainStatus.query.filter_by(train_id=train.train_id).all()
            for schedule in schedules:
                stop = Stop.query.get(schedule.current_stop_id)
                if stop:
                    stop_names[schedule.current_stop_id] = stop.stop_name 

        # Get schedules
        schedules = Schedule.query.all()
        filtered_schedules = schedules[-10:][::-1]

        alerts = Alert.query.all()
        processed_alerts = []
        for alert in alerts:
            processed_alerts.append({
                'Alert ID': alert.alert_id,
                'Text': alert.alert_text,
                'Type': alert.alert_type,
                'Expires At': alert.expires_at.strftime("%Y-%m-%d %H:%M:%S") if alert.expires_at else 'N/A'
            })

        # Fetch routes with route names
        routes = Route.query.with_entities(Route.route_id, Route.route_name).all()
        selected_route = None
        selected_stop = None

        # Initialize stops as an empty list
        stops = []

        # Handle POST request
        if request.method == 'POST':
            selected_route = request.form.get('route')
            selected_stop = request.form.get('stop')

            # Filter schedules by stop_id
            if selected_stop:
                filtered_schedules = [schedule for schedule in schedules if schedule.stop_id == int(selected_stop)]

        # Fetch favorite stops for the logged-in user
        user_id = session.get('user_id')
        favorite_stops = FavoriteStop.query.filter_by(user_id=user_id).all() if user_id else []

        return render_template(
            'index.html',
            trains=trains,
            trainStatus_dict=trainStatus_dict,
            schedules=filtered_schedules,
            stop_names=stop_names,
            alerts=processed_alerts,
            routes=routes,  # Pass the route names and IDs to the template
            selected_route=selected_route,
            selected_stop=selected_stop,
            favorite_stops=favorite_stops,
            stops=stops
        )



    @app.route('/user-profile')
    def userProfile():
        uid = session.get('user_id')
        if uid is None:
            return render_template("login.html")
        return render_template("user.html")

    @app.route('/user-profile/edit-profile', methods=["POST", "GET"])
    def editUserProfile():
        uid = session.get('user_id')
        if uid is None:
            return render_template("login.html")
        if request.method == 'POST':
            user_id = session["user_id"]
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            email = request.form.get('email')
            
            if not first_name or not last_name or not email:
                flash('All fields are required. Please fill out all fields.', 'danger')
                return redirect(url_for('editUserProfile'))
            
            user = User.query.filter_by(user_id=user_id).first()

            if user:
                user.first_name = first_name
                user.last_name = last_name
                user.email = email
                db.session.commit()

                session['first_name'] = first_name
                session['last_name'] = last_name
                session['email'] = email

                flash('Profile updated successfully!', 'success')
                return redirect(url_for('userProfile'))  
            else:
                flash('User  not found!', 'danger')
                return redirect(url_for('login'))  
            
        user_id = session.get("user_id")
        user = User.query.filter_by(user_id=user_id).first()

        if user:
            return render_template('edit_profile.html', user=user)  
        else:
            flash('User  not found, please log in.', 'danger')
            return redirect(url_for('login'))  
        
    @app.route('/get_stops_by_route', methods=['GET'])
    def get_stops_by_route():
        uid = session.get('user_id')
        if uid is None:
            return render_template("login.html")
        route_name = request.args.get('route')
        if route_name:
            stops = db.session.execute(text("CALL GetStopsByRoute(:route_name)"), {'route_name': route_name}).fetchall()
            stops_list = [{'id': stop[0], 'name': stop[1]} for stop in stops]
            return jsonify(stops_list)
        return jsonify([])

    @app.route('/add_favorite', methods=['POST'])
    def add_favorite():
        user_id = session.get('user_id')
        stop_id = request.form.get('stop')
        route_value = request.form.get('route')

        if user_id and stop_id and route_value:
            try:
                favorite_stop = FavoriteStop(user_id=user_id, stop_id=stop_id)
                db.session.add(favorite_stop)
                db.session.commit()
                flash('Stop added to favorites!', 'success')
            except Exception as e:
                print(f"Error adding favorite stop: {e}")
                flash('Failed to add favorite stop. Please try again.', 'danger')
        else:
            flash('Failed to add favorite stop. Please try again.', 'danger')

        return redirect(url_for('index'))  

    @app.route('/stops')
    def stops():
        uid = session.get('user_id')
        if uid is None:
            return render_template("login.html")
        return render_template('stops.html')

    @app.route('/green-line-stops', methods=['GET'])
    def greenLineStops():
        uid = session.get('user_id')
        if uid is None:
            return render_template("login.html")
        ROUTE_ID_MAPPING = {
            "Green-B": 1,
            "Green-C": 2,
            "Green-D": 3,
            "Green-E": 4
        }
        route_stops = {}
        for route_name, route_id in ROUTE_ID_MAPPING.items():
            stops = db.session.execute(text("CALL GetStopsByRoute(:route_id)"), {'route_id': route_id}).fetchall()
            route_stops[route_name] = [{'id': stop[0], 'name': stop[1]} for stop in stops]

        return render_template('green-line-stops.html', route_stops=route_stops)

    @app.route('/schedules', methods=['GET'])
    def schedules():
        uid = session.get('user_id')
        if uid is None:
            return render_template("login.html")
        schedules = (
            db.session.query(
                Schedule.schedule_id,
                Schedule.train_id,
                Route.route_name,
                Stop.stop_name,
                Schedule.arrival_time,
                Schedule.departure_time,
                Schedule.travel_time_minutes
            )
            .join(Train, Schedule.train_id == Train.train_id)
            .join(Route, Train.route == Route.route_id)  # Adjusted to match route_id
            .join(Stop, Schedule.stop_id == Stop.stop_id)
            .all()
        )
        
        return render_template('schedules.html', schedules=schedules)


    @app.route('/alerts', methods=['GET'])
    def alerts():
        uid = session.get('user_id')
        if uid is None:
            return render_template("login.html")
        alerts = Alert.query.all()
        processed_alerts = []
        for alert in alerts:
            processed_alerts.append({
                'Alert ID': alert.alert_id,
                'Text': alert.alert_text,
                'Type': alert.alert_type,
                'Expires At': alert.expires_at.strftime("%Y-%m-%d %H:%M:%S") if alert.expires_at else 'N/A'
            })
        return render_template("alerts.html", alerts=processed_alerts)

    @app.route('/travel-groups', methods=['GET', 'POST'])
    def travel_groups():
        uid = session.get('user_id')
        if uid is None:
            return render_template("login.html")
        
        available_routes = Route.query.all()
        user_id = session.get('user_id')  # Get the user ID from the session
        
        if user_id:
            # Query to get the groups that the user has created
            created_groups = db.session.query(TravelGroup).filter(TravelGroup.created_by_user_id == user_id).all()
            
            # Query to get the groups that the user is part of but has not created
            joined_groups = db.session.query(TravelGroup).join(GroupMembership).filter(
                GroupMembership.user_id == user_id,
                TravelGroup.group_id == GroupMembership.group_id,
                TravelGroup.created_by_user_id != user_id  # Ensure the user has not created the group
            ).all()

            # Debugging: print the result to check
            print("Created Groups:", created_groups)
            print("Joined Groups:", joined_groups)

            return render_template(
                'groups.html', 
                available_routes=available_routes,
                joined_groups=joined_groups,
                created_groups=created_groups
            )
        else:
            flash('You need to log in to view your travel groups.', 'danger')
            return redirect(url_for('login'))


        
    @app.route('/leave_group', methods=['POST'])
    def leave_group():
        uid = session.get('user_id')
        if uid is None:
            return render_template("login.html")
        
        group_id = request.form.get('group_id')
        print(f"Group ID: {group_id}, User ID: {uid}")  # Debugging line to ensure the correct values are passed

        if group_id:
            try:
                membership = GroupMembership.query.filter_by(user_id=uid, group_id=group_id).first()
                if membership:
                    db.session.delete(membership)
                    db.session.commit()
                    flash('You have left the group successfully!', 'success')
                else:
                    flash('You are not part of this group.', 'warning')
            except Exception as e:
                print(f"Error leaving group: {e}")
                flash('Failed to leave the group. Please try again.', 'danger')
        else:
            flash('Group ID is missing.', 'danger')

        return redirect(url_for('travel_groups'))



    @app.route('/delete_group', methods=['POST'])
    def delete_group():
        user_id = session.get('user_id')
        group_id = request.form.get('group_id')

        if user_id and group_id:
            try:
                # Check if the user is the creator of the group
                group = TravelGroup.query.filter_by(group_id=group_id, created_by_user_id=user_id).first()
                if group:
                    db.session.delete(group)
                    db.session.commit()
                    return redirect(url_for('travel_groups'))
                else:
                    return redirect(url_for('travel_groups'))
            except Exception as e:
                print(f"Error deleting group: {e}")
                return redirect(url_for('travel_groups'))

        return redirect(url_for('travel_groups'))
    
    @app.route('/join_group', methods=['POST'])
    def join_group():
        uid = session.get('user_id')
        if uid is None:
            return render_template("login.html")
        user_id = session.get('user_id')  # Get the user ID from the session
        group_id = request.form.get('group_id')  # Get the group ID from the form

        if user_id and group_id:
            try:
                # Call the stored procedure AddUser ToGroup
                db.session.execute(text("CALL AddUserToGroup(:group_id, :user_id)"), { 'group_id': group_id,'user_id': user_id})
                db.session.commit()
                flash('You have successfully joined the group!', 'success')
            except Exception as e:
                print(f"Error joining group: {e}")  # Log the error
                flash('Failed to join the group. Please try again.', 'danger')
        else:
            flash('User  ID or Group ID is missing.', 'danger')

        return redirect(url_for('travel_groups')) 
    
    @app.route('/create_group', methods=['GET','POST'])
    def create_group():
        uid = session.get('user_id')
        if uid is None:
            return render_template("login.html")
        group_name = request.form['group_name']
        group_id = request.form['group_id']
        description = request.form['description']
        route_id = request.form['route_id']
        user_id = session.get('user_id')

        print(group_name, group_id, description, route_id, user_id)  # Debugging

        if not user_id:
            flash('You must be logged in to create a group.')
            return redirect(url_for('login'))
        
        existing_group = db.session.execute(
            text("SELECT COUNT(*) FROM travel_group WHERE group_id = :groupId"),
            {'groupId': group_id}
        ).fetchone()
        print(existing_group[0])

        if existing_group[0] > 0:  # If the count is greater than 0, the group_id exists
            flash('This Group ID is already taken. Please enter a different Group ID.')
            return redirect(url_for('travel_groups')) 

        try:
            db.session.execute(text("CALL CreateTravelGroup(:groupId, :createdByUserId, :groupName, :groupDescription, :routeId)"),
                        {'groupId': group_id, 'createdByUserId': user_id, 'groupName': group_name, 'groupDescription': description, 'routeId': route_id})
            db.session.commit()
            flash('Group created successfully!')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}')
        finally:
            db.session.close()
            db.session.close()

        return redirect(url_for('travel_groups'))
    
    @app.route('/feedback', methods=['GET', 'POST'])
    def feedback():
        user_id = session.get('user_id')
        available_routes = Route.query.all()  # Fetch all available routes

        # Fetch all feedback with route names
        all_feedback = db.session.query(
            Feedback.feedback_id,
            Feedback.feedback_text,
            Feedback.rating,
            Route.route_name
        ).join(Route, Feedback.route_id == Route.route_id).all()

        # Fetch user-specific feedback with route names
        user_feedback = (
            db.session.query(
                Feedback.feedback_id,
                Feedback.feedback_text,
                Feedback.rating,
                Route.route_name
            )
            .join(Route, Feedback.route_id == Route.route_id)
            .filter(Feedback.user_id == user_id)
            .all()
            if user_id
            else []
        )

        return render_template(
            'feedback.html',
            available_routes=available_routes,
            user_feedback=user_feedback,
            route_feedback=all_feedback,
        )


    
    @app.route('/delete_feedback/<int:feedback_id>', methods=['POST'])
    def delete_feedback(feedback_id):
        uid = session.get('user_id')
        if uid is None:
            return render_template("login.html")
        user_id = session.get('user_id')
        if user_id:
            feedback = Feedback.query.filter_by(feedback_id=feedback_id, user_id=user_id).first()
            if feedback:
                db.session.delete(feedback)
                db.session.commit()
                flash('Feedback deleted successfully!', 'success')
            else:
                flash('Feedback not found or you do not have permission to delete it.', 'danger')
        else:
            flash('You need to log in to delete feedback.', 'danger')
        
        return redirect(url_for('feedback'))  # Redirect back to the feedback page
    

    @app.route('/create_feedback', methods=['GET', 'POST'])
    def create_feedback():
        user_id = session.get('user_id')
        if user_id is None:
            flash('You must be logged in to submit feedback.')
            return redirect(url_for('login'))

        if request.method == 'POST':
            feedback_text = request.form.get('feedback_text')
            rating = request.form.get('rating')
            route_id = request.form.get('route_id')

            # Validate input
            if not feedback_text or not rating or not route_id:
                flash('All fields are required.')
                return redirect(url_for('feedback'))

            try:
                db.session.execute(text("CALL create_feedback(:user_id, :feedback_text, :rating, :route_id )"),
                                   {
                        'user_id': user_id,
                        'feedback_text': feedback_text,
                        'rating': int(rating),
                        'route_id': int(route_id),
                    })

                db.session.commit()
                flash('Feedback submitted successfully!')
            except Exception as e:
                db.session.rollback()
                flash(f'An error occurred: {str(e)}')
            finally:
                db.session.close()

            return redirect(url_for('feedback'))
        flash('Feedback submitted successfully!', 'success')
        flash(f'An error occurred: {str(e)}', 'error')


        # If GET, show feedback creation form
        available_routes = Route.query.all()
        return render_template('create_feedback.html', available_routes=available_routes)

    


    

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True)