from flask_login import UserMixin
from app import db
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    golf_course_email = db.Column(db.String(120), nullable=True)
    golf_course_password = db.Column(db.String(120), nullable=True)
    role = db.Column(db.String(20), default='user')  # 'user' or 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.username}>'

class BookingLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    golf_course = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(10), nullable=False)  # MM-DD-YYYY
    earliest_time = db.Column(db.String(10), nullable=False)  # H:MMAM/PM
    latest_time = db.Column(db.String(10), nullable=False)
    players = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), nullable=False)  # 'Success' or 'Failed'
    message = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('bookings', lazy=True))

    def __repr__(self):
        return f'<BookingLog {self.user.username} {self.golf_course} {self.date}>'