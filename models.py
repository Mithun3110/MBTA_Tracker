from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Stop(db.Model):
    __tablename__ = 'STOP'

    stop_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    stop_name = db.Column(db.String(100), nullable=False)
    stop_code = db.Column(db.String(50), nullable=True)
    stop_sequence = db.Column(db.Integer, nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    # Optional: For easier string representation of the object
    def __repr__(self):
        return f'<Stop {self.stop_name} (ID: {self.stop_id})>'

class User(db.Model):
    __tablename__ = 'USER'

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.first_name} {self.last_name}>'

class Train(db.Model):
    __tablename__ = 'TRAIN'

    train_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    route = db.Column(db.String(50), nullable=False)
    
    
    def __repr__(self):
        return f'<Train {self.train_id} - {self.route}>'

class TrainStatus(db.Model):
    __tablename__ = 'TRAIN_STATUS'

    train_id = db.Column(db.Integer, db.ForeignKey('TRAIN.train_id'), primary_key=True)
    status = db.Column(db.String(50), nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, primary_key=True)
    current_stop_id = db.Column(db.Integer, db.ForeignKey('STOP.stop_id'), nullable=True)

    current_stop = db.relationship('Stop', backref=db.backref('trains', lazy=True))
    
    train = db.relationship('Train', backref=db.backref('statuses', lazy=True))

    def __repr__(self):
        return f'<TrainStatus {self.train_id} - {self.status}>'

class Route(db.Model):
    __tablename__ = 'ROUTE'

    route_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    route_name = db.Column(db.String(50), nullable=False)
    route_type = db.Column(db.String(50), nullable=True)
    route_color = db.Column(db.String(20), nullable=True)

    def __repr__(self):
        return f'<Route {self.route_name}>'

class Schedule(db.Model):
    __tablename__ = 'SCHEDULE'

    schedule_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    train_id = db.Column(db.Integer, db.ForeignKey('TRAIN.train_id'), nullable=False)
    stop_id = db.Column(db.Integer, db.ForeignKey('STOP.stop_id'), nullable=False)
    arrival_time = db.Column(db.DateTime, nullable=True)
    departure_time = db.Column(db.DateTime, nullable=True)
    travel_time_minutes = db.Column(db.Integer, nullable=True)

    train = db.relationship('Train', backref=db.backref('schedules', lazy=True))
    stop = db.relationship('Stop', backref=db.backref('schedules', lazy=True))

    def __repr__(self):
        return f'<Schedule {self.train_id} at stop {self.stop_id}>'

class Alert(db.Model):
    __tablename__ = 'ALERT'

    alert_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    alert_text = db.Column(db.Text, nullable=False)
    alert_type = db.Column(db.String(50), nullable=True)
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    stop_id = db.Column(db.Integer, db.ForeignKey('STOP.stop_id'), nullable=True)

    stop = db.relationship('Stop', backref=db.backref('alerts', lazy=True))

    def __repr__(self):
        return f'<Alert {self.alert_id} - {self.alert_text[:50]}>'

class Event(db.Model):
    __tablename__ = 'EVENT'

    event_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_name = db.Column(db.String(100), nullable=False)
    event_description = db.Column(db.Text, nullable=True)
    event_date = db.Column(db.DateTime, nullable=True)
    affected_stop_id = db.Column(db.Integer, db.ForeignKey('STOP.stop_id'), nullable=True)
    severity = db.Column(db.String(50), nullable=True)

    affected_stop = db.relationship('Stop', backref=db.backref('events', lazy=True))

    def __repr__(self):
        return f'<Event {self.event_id} - {self.event_name}>'

class TravelGroup(db.Model):
    __tablename__ = 'TRAVEL_GROUP'

    group_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('USER.user_id'), nullable=False)
    group_name = db.Column(db.String(100), nullable=False)
    descript = db.Column(db.Text, nullable=True)
    route_id = db.Column(db.Integer, db.ForeignKey('ROUTE.route_id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    created_by_user = db.relationship('User', backref=db.backref('travel_groups', lazy=True))
    route = db.relationship('Route', backref=db.backref('travel_groups', lazy=True))

    def __repr__(self):
        return f'<TravelGroup {self.group_name} - {self.created_by_user.first_name}>'

class Feedback(db.Model):
    __tablename__ = 'FEEDBACK'

    feedback_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('USER.user_id'), nullable=False)
    feedback_text = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    route_id = db.Column(db.Integer, db.ForeignKey('ROUTE.route_id'), nullable=True)  


    user = db.relationship('User', backref=db.backref('feedback', lazy=True))

    def __repr__(self):
        return f'<Feedback {self.rating} - {self.feedback_text[:50]}>'

class FavoriteStop(db.Model):
    __tablename__ = 'FAVORITE_STOP'

    favorite_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('USER.user_id'), nullable=False)
    stop_id = db.Column(db.Integer, db.ForeignKey('STOP.stop_id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('favorite_stops', lazy=True))
    stop = db.relationship('Stop', backref=db.backref('favorite_stops', lazy=True))

    def __repr__(self):
        return f'<FavoriteStop {self.user.first_name} at {self.stop.stop_name}>'

class UserAlertSubscription(db.Model):
    __tablename__ = 'USER_ALERT_SUBSCRIPTION'

    user_id = db.Column(db.Integer, db.ForeignKey('USER.user_id'), primary_key=True)
    alert_id = db.Column(db.Integer, db.ForeignKey('ALERT.alert_id'), primary_key=True)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('alert_subscriptions', lazy=True))
    alert = db.relationship('Alert', backref=db.backref('subscriptions', lazy=True))

    def __repr__(self):
        return f'<UserAlertSubscription {self.user.first_name} subscribed to {self.alert.alert_text[:50]}>'

class EventAlert(db.Model):
    __tablename__ = 'EVENT_ALERT'

    event_id = db.Column(db.Integer, db.ForeignKey('EVENT.event_id'), primary_key=True)
    alert_id = db.Column(db.Integer, db.ForeignKey('ALERT.alert_id'), primary_key=True)

    event = db.relationship('Event', backref=db.backref('alerts', lazy=True))
    alert = db.relationship('Alert', backref=db.backref('events', lazy=True))

    def __repr__(self):
        return f'<EventAlert {self.event.event_name} linked to {self.alert.alert_text[:50]}>'

class GroupMembership(db.Model):
    __tablename__ = 'GROUP_MEMBERSHIP'

    group_id = db.Column(db.Integer, db.ForeignKey('TRAVEL_GROUP.group_id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('USER.user_id'), primary_key=True)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    group = db.relationship('TravelGroup', backref=db.backref('members', lazy=True))
    user = db.relationship('User', backref=db.backref('groups', lazy=True))

    def __repr__(self):
        return f'<GroupMembership {self.user.first_name} in {self.group.group_name}>'