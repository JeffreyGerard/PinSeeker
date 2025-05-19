from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.booking.golf_booking import book_tee_time
from app.models import User, BookingLog
from app import db

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@main.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied: Admins only.', 'danger')
        return redirect(url_for('main.dashboard'))
    users = User.query.all()
    bookings = BookingLog.query.order_by(BookingLog.timestamp.desc()).all()
    return render_template('admin_dashboard.html', users=users, bookings=bookings)

@main.route('/book_tee_time', methods=['GET', 'POST'])
@login_required
def book_tee_time_route():
    if request.method == 'POST':
        date = request.form.get('date')
        earliest_time = request.form.get('earliest_time')
        latest_time = request.form.get('latest_time')
        players = request.form.get('players')
        golf_course = request.form.get('golf_course')

        try:
            result = book_tee_time(
                date=date,
                earliest_time=earliest_time,
                latest_time=latest_time,
                players=players,
                golf_course=golf_course,
                email=current_user.golf_course_email,
                password=current_user.golf_course_password
            )
            status = 'Success' if 'Success' in result else 'Failed'
            booking_log = BookingLog(
                user_id=current_user.id,
                golf_course=golf_course,
                date=date,
                earliest_time=earliest_time,
                latest_time=latest_time,
                players=int(players),
                status=status,
                message=result
            )
            db.session.add(booking_log)
            db.session.commit()
            flash(result, 'success' if status == 'Success' else 'danger')
        except Exception as e:
            booking_log = BookingLog(
                user_id=current_user.id,
                golf_course=golf_course,
                date=date,
                earliest_time=earliest_time,
                latest_time=latest_time,
                players=int(players),
                status='Failed',
                message=str(e)
            )
            db.session.add(booking_log)
            db.session.commit()
            flash(f"Error booking tee time: {str(e)}", 'danger')

        return redirect(url_for('main.dashboard'))

    return render_template('book_tee_time.html')