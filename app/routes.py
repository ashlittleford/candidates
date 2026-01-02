from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, Profile
from werkzeug.security import generate_password_hash

main = Blueprint('main', __name__)

@main.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('main.admin_dashboard'))
        else:
            return redirect(url_for('main.profile'))
    return redirect(url_for('main.login'))

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('main.index'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main.route('/profile')
@login_required
def profile():
    if current_user.is_admin:
         # Admins don't strictly have a "candidate profile", but maybe they can see a generic one or redirect to dashboard
         flash("Admins should use the dashboard.")
         return redirect(url_for('main.admin_dashboard'))
    return render_template('profile.html', user=current_user)

@main.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.profile'))
    users = User.query.filter_by(is_admin=False).all()
    return render_template('admin_dashboard.html', users=users)

@main.route('/admin/create', methods=['GET', 'POST'])
@login_required
def create_user():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.profile'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')

        if User.query.filter_by(username=username).first():
            flash('Username already exists')
        else:
            new_user = User(username=username, name=name)
            new_user.set_password(password)
            # Create empty profile
            new_profile = Profile(user=new_user)
            db.session.add(new_user)
            db.session.add(new_profile)
            db.session.commit()
            flash('User created successfully')
            return redirect(url_for('main.admin_dashboard'))
    return render_template('admin_create_user.html')

@main.route('/admin/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.profile'))

    user = User.query.get_or_404(user_id)
    if not user.profile:
        user.profile = Profile(user=user)
        db.session.add(user.profile)
        db.session.commit()

    if request.method == 'POST':
        user.name = request.form.get('name')
        user.profile.formation_panel_details = request.form.get('formation_panel_details')
        user.profile.formation_days_completed = request.form.get('formation_days_completed')
        user.profile.walking_on_country = True if request.form.get('walking_on_country') else False
        user.profile.upcoming_formation_dates = request.form.get('upcoming_formation_dates')
        user.profile.formation_panel_dates = request.form.get('formation_panel_dates')

        db.session.commit()
        flash('User updated successfully')
        return redirect(url_for('main.admin_dashboard'))

    return render_template('admin_edit_profile.html', user=user)
