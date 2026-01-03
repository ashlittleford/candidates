from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, Profile, GlobalSettings, FormationPanel, Resource, Standard
from app.standards_loader import load_standards
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime

main = Blueprint('main', __name__)

@main.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('main.admin_dashboard'))
        elif current_user.is_panel_member:
            return redirect(url_for('main.panel_dashboard'))
        else:
            return redirect(url_for('main.profile'))
    return redirect(url_for('main.login'))

@main.route('/panel_dashboard')
@login_required
def panel_dashboard():
    if not current_user.is_panel_member:
        flash("Access denied")
        return redirect(url_for('main.index'))

    # Get candidates belonging to the same formation panel
    if current_user.formation_panel_id:
        candidates = User.query.join(Profile).filter(
            Profile.formation_panel_id == current_user.formation_panel_id,
            User.is_admin == False,
            User.is_panel_member == False
        ).all()
    else:
        candidates = []

    return render_template('panel_dashboard.html', candidates=candidates)

@main.route('/candidate/<int:user_id>')
@login_required
def view_candidate_profile(user_id):
    # Determine if viewer is allowed
    target_user = User.query.get_or_404(user_id)

    allowed = False
    if current_user.is_admin:
        allowed = True
    elif current_user.is_panel_member:
        # Check if target user belongs to same panel
        if target_user.profile and target_user.profile.formation_panel_id == current_user.formation_panel_id:
            allowed = True

    if not allowed:
        flash("Access denied to this profile.")
        return redirect(url_for('main.index'))

    # Reuse the logic from profile() view
    global_settings = GlobalSettings.query.first()
    if not global_settings:
        global_settings = GlobalSettings()

    upcoming_dates_raw = global_settings.upcoming_formation_dates
    upcoming_dates = []

    if upcoming_dates_raw:
        if '\n' in upcoming_dates_raw:
            raw_list = upcoming_dates_raw.split('\n')
        else:
            raw_list = upcoming_dates_raw.split(',')

        for item in raw_list:
            item = item.strip()
            if not item:
                continue

            parts = item.split(':', 1)
            if len(parts) > 1:
                label = parts[0].strip()
                date_str = parts[1].strip()
                upcoming_dates.append({'label': label, 'date': date_str})
            else:
                upcoming_dates.append({'label': None, 'date': item})

    resources = Resource.query.all()
    standards = Standard.query.order_by(Standard.id).all()

    return render_template('profile.html', user=target_user, global_settings=global_settings, upcoming_dates=upcoming_dates, resources=resources, standards=standards)

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
         flash("Admins should use the dashboard.")
         return redirect(url_for('main.admin_dashboard'))

    global_settings = GlobalSettings.query.first()
    # If for some reason settings don't exist, create a temporary empty one (shouldn't happen with correct init_db)
    if not global_settings:
        global_settings = GlobalSettings()

    # Parse upcoming_formation_dates
    # Supports newline or comma separation
    # Supports "Label: Date" format
    upcoming_dates_raw = global_settings.upcoming_formation_dates
    upcoming_dates = []

    if upcoming_dates_raw:
        if '\n' in upcoming_dates_raw:
            raw_list = upcoming_dates_raw.split('\n')
        else:
            raw_list = upcoming_dates_raw.split(',')

        for item in raw_list:
            item = item.strip()
            if not item:
                continue

            parts = item.split(':', 1)
            if len(parts) > 1:
                label = parts[0].strip()
                date_str = parts[1].strip()
                upcoming_dates.append({'label': label, 'date': date_str})
            else:
                upcoming_dates.append({'label': None, 'date': item})

    resources = Resource.query.all()
    standards = Standard.query.order_by(Standard.id).all()
    return render_template('profile.html', user=current_user, global_settings=global_settings, upcoming_dates=upcoming_dates, resources=resources, standards=standards)

@main.route('/profile/update_supervisor', methods=['POST'])
@login_required
def update_supervisor():
    if current_user.is_admin:
        flash("Admins cannot have supervisors.")
        return redirect(url_for('main.admin_dashboard'))

    supervisor_name = request.form.get('supervisor')
    current_user.profile.supervisor = supervisor_name
    db.session.commit()
    flash('Supervisor updated successfully.')
    return redirect(url_for('main.profile'))

@main.route('/profile/update_church', methods=['POST'])
@login_required
def update_church():
    if current_user.is_admin:
        flash("Admins cannot edit their church.")
        return redirect(url_for('main.admin_dashboard'))

    church_name = request.form.get('current_church')
    current_user.profile.current_church = church_name
    db.session.commit()
    flash('Current church updated successfully.')
    return redirect(url_for('main.profile'))

@main.route('/profile/update_code_of_ethics', methods=['POST'])
@login_required
def update_code_of_ethics():
    if current_user.is_admin:
        flash("Admins cannot edit their profile directly.")
        return redirect(url_for('main.admin_dashboard'))

    # Handling checkboxes: if checked, value is 'on', otherwise key is missing
    current_user.profile.code_of_ethics_signed = True if request.form.get('code_of_ethics_signed') else False
    current_user.profile.code_of_ethics_date = request.form.get('code_of_ethics_date')

    db.session.commit()
    flash('Code of Ethics updated successfully.')
    return redirect(url_for('main.profile'))

@main.route('/profile/update_wwcc', methods=['POST'])
@login_required
def update_wwcc():
    if current_user.is_admin:
        flash("Admins cannot edit their profile directly.")
        return redirect(url_for('main.admin_dashboard'))

    current_user.profile.wwcc_cleared = True if request.form.get('wwcc_cleared') else False
    current_user.profile.wwcc_number = request.form.get('wwcc_number')

    db.session.commit()
    flash('WWCC updated successfully.')
    return redirect(url_for('main.profile'))

@main.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.profile'))

    settings = GlobalSettings.query.first()
    if not settings:
        settings = GlobalSettings(
            upcoming_formation_dates="Monday 2 March 2026, Monday 13 April 2026, Monday 4 May 2026, Monday 1 June 2026, Monday 3 August 2026, Monday 7 September 2026, Monday 12 October 2026, Monday 2 November 2026",
            formation_panel_dates="First: 13 February 2026, Second: 19 June 2026, Third: 20 November 2026"
        )
        db.session.add(settings)
        db.session.commit()

    if request.method == 'POST':
        settings.upcoming_formation_dates = request.form.get('upcoming_formation_dates')
        settings.formation_panel_dates = request.form.get('formation_panel_dates')
        db.session.commit()
        flash('Global settings updated successfully')
        return redirect(url_for('main.admin_dashboard'))

    return render_template('admin_global_settings.html', settings=settings)

@main.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.profile'))
    users = User.query.filter(User.is_admin == False, User.is_panel_member == False).all()
    panel_members = User.query.filter_by(is_panel_member=True).all()
    panels = FormationPanel.query.all()
    return render_template('admin_dashboard.html', users=users, panels=panels, panel_members=panel_members)

@main.route('/admin/create_panel_member', methods=['GET', 'POST'])
@login_required
def create_panel_member():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.profile'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        formation_panel_id = request.form.get('formation_panel_id')

        if User.query.filter_by(username=username).first():
            flash('Username already exists')
        else:
            new_user = User(username=username, name=name, is_panel_member=True, formation_panel_id=formation_panel_id)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Panel Member created successfully')
            return redirect(url_for('main.admin_dashboard') + '#members')

    panels = FormationPanel.query.all()
    return render_template('admin_create_panel_member.html', panels=panels)

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

        # Handle Formation Panel Selection
        panel_id = request.form.get('formation_panel_id')
        if panel_id:
            user.profile.formation_panel_id = int(panel_id)
        else:
            user.profile.formation_panel_id = None

        user.profile.formation_days_completed = request.form.get('formation_days_completed')
        user.profile.start_date = request.form.get('start_date')
        user.profile.mid_term_panel = True if request.form.get('mid_term_panel') else False
        user.profile.walking_on_country = True if request.form.get('walking_on_country') else False
        user.profile.presbytery = request.form.get('presbytery')
        user.profile.current_church = request.form.get('current_church')
        # upcoming_formation_dates and formation_panel_dates are now global and not edited here

        db.session.commit()
        flash('User updated successfully')
        return redirect(url_for('main.admin_dashboard'))

    panels = FormationPanel.query.all()
    return render_template('admin_edit_profile.html', user=user, panels=panels)

@main.route('/admin/bulk_add_formation_day', methods=['POST'])
@login_required
def bulk_add_formation_day():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.profile'))

    user_ids = request.form.getlist('user_ids')
    formation_day = request.form.get('formation_day')

    if not user_ids or not formation_day:
        flash('No users selected or formation day empty')
        return redirect(url_for('main.admin_dashboard'))

    for user_id in user_ids:
        user = User.query.get(user_id)
        if user:
            if not user.profile:
                user.profile = Profile(user=user)
                db.session.add(user.profile)

            if not user.profile.formation_days_completed:
                 user.profile.formation_days_completed = formation_day
            else:
                 # Avoid duplicates if possible
                 if formation_day not in user.profile.formation_days_completed:
                     user.profile.formation_days_completed += "\n" + formation_day

    db.session.commit()
    flash('Formation day added to selected profiles')
    return redirect(url_for('main.admin_dashboard'))

# --- Formation Panel Management Routes ---

@main.route('/admin/panels')
@login_required
def admin_panels():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.profile'))
    return redirect(url_for('main.admin_dashboard') + '#panels')

@main.route('/admin/panels/create', methods=['GET', 'POST'])
@login_required
def create_panel():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.profile'))

    if request.method == 'POST':
        chair_name = request.form.get('chair_name')
        members = request.form.get('members')

        new_panel = FormationPanel(chair_name=chair_name, members=members)
        db.session.add(new_panel)
        db.session.commit()
        flash('Formation Panel created successfully')
        return redirect(url_for('main.admin_dashboard') + '#panels')

    return render_template('admin_create_edit_panel.html', panel=None)

@main.route('/admin/panels/edit/<int:panel_id>', methods=['GET', 'POST'])
@login_required
def edit_panel(panel_id):
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.profile'))

    panel = FormationPanel.query.get_or_404(panel_id)

    if request.method == 'POST':
        panel.chair_name = request.form.get('chair_name')
        panel.members = request.form.get('members')
        db.session.commit()
        flash('Formation Panel updated successfully')
        return redirect(url_for('main.admin_dashboard') + '#panels')

    return render_template('admin_create_edit_panel.html', panel=panel)

# --- Resource Management Routes ---

@main.route('/admin/resources', methods=['GET', 'POST'])
@login_required
def admin_resources():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.profile'))

    if request.method == 'POST':
        title = request.form.get('title')
        res_type = request.form.get('type')
        category = request.form.get('category')

        new_resource = Resource(title=title, type=res_type, category=category)

        if res_type == 'link':
            new_resource.url = request.form.get('url')
        elif res_type == 'file':
            if 'file' not in request.files:
                flash('No file part')
                return redirect(request.url)
            file = request.files['file']
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            if file:
                filename = secure_filename(file.filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                new_resource.filename = filename

        db.session.add(new_resource)
        db.session.commit()
        flash('Resource added successfully')
        return redirect(url_for('main.admin_resources'))

    resources = Resource.query.all()
    return render_template('admin_resources.html', resources=resources)

@main.route('/admin/resources/edit/<int:resource_id>', methods=['GET', 'POST'])
@login_required
def edit_resource(resource_id):
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.profile'))

    resource = Resource.query.get_or_404(resource_id)

    if request.method == 'POST':
        resource.title = request.form.get('title')
        res_type = request.form.get('type')
        resource.category = request.form.get('category')
        resource.type = res_type

        if res_type == 'link':
            resource.url = request.form.get('url')
            # Optionally clear filename if switching types, or keep it.
            # resource.filename = None
        elif res_type == 'file':
            if 'file' in request.files:
                file = request.files['file']
                if file and file.filename != '':
                    # Delete old file if exists? Maybe better not to automatically delete for now.
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                    resource.filename = filename

        db.session.commit()
        flash('Resource updated successfully')
        return redirect(url_for('main.admin_resources'))

    return render_template('admin_edit_resource.html', resource=resource)

@main.route('/admin/resources/delete/<int:resource_id>', methods=['POST'])
@login_required
def delete_resource(resource_id):
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.profile'))

    resource = Resource.query.get_or_404(resource_id)

    # Optionally delete the file from filesystem
    if resource.filename:
        try:
            os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], resource.filename))
        except:
            pass # File might not exist or permission error

    db.session.delete(resource)
    db.session.commit()
    flash('Resource deleted successfully')
    return redirect(url_for('main.admin_resources'))

# --- Standards Management Routes ---

@main.route('/admin/standards')
@login_required
def admin_standards():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.profile'))

    standards = Standard.query.order_by(Standard.id).all()
    return render_template('admin_standards.html', standards=standards)

@main.route('/admin/standards/edit/<int:standard_id>', methods=['GET', 'POST'])
@login_required
def edit_standard(standard_id):
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.profile'))

    standard = Standard.query.get_or_404(standard_id)

    if request.method == 'POST':
        standard.attribute = request.form.get('attribute')
        standard.beginning = request.form.get('beginning')
        standard.developing = request.form.get('developing')
        standard.established = request.form.get('established')
        standard.lfd = request.form.get('lfd')

        db.session.commit()
        flash('Standard updated successfully')
        return redirect(url_for('main.admin_standards'))

    return render_template('admin_edit_standard.html', standard=standard)

@main.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@main.route('/profile/upload_document', methods=['POST'])
@login_required
def upload_panel_document():
    if current_user.is_admin or current_user.is_panel_member:
        flash("Only candidates can upload formation panel documents.")
        return redirect(url_for('main.profile'))

    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('main.profile'))

    files = request.files.getlist('file')

    for file in files:
        if file.filename == '':
            continue

        if file:
            original_filename = secure_filename(file.filename)
            # Add timestamp to ensure uniqueness
            filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{original_filename}"
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))

            doc = PanelDocument(
                user_id=current_user.id,
                filename=filename,
                original_filename=original_filename
            )
            db.session.add(doc)

    db.session.commit()
    flash('Documents uploaded successfully.')
    return redirect(url_for('main.profile'))

@main.route('/profile/delete_document/<int:doc_id>', methods=['POST'])
@login_required
def delete_panel_document(doc_id):
    doc = PanelDocument.query.get_or_404(doc_id)

    # Allow admin or owner to delete
    if doc.user_id != current_user.id and not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('main.profile'))

    try:
        os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], doc.filename))
    except:
        pass # File might be missing

    db.session.delete(doc)
    db.session.commit()
    flash('Document deleted.')

    # Redirect back to appropriate page
    if current_user.id == doc.user_id:
        return redirect(url_for('main.profile'))
    else:
        # If admin deleted it, where should they go? Admin dashboard?
        # Actually admin views candidate profile via view_candidate_profile
        return redirect(request.referrer or url_for('main.admin_dashboard'))
