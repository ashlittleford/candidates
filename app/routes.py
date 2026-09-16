from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, send_from_directory, Response
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import (
    User, Profile, GlobalSettings, FormationPanel, Resource, Standard, PanelDocument,
    AcademicRequirement, CandidateAcademicRequirement, FormationDay, FormationDayRSVP,
    CANDIDATE_DOCUMENT_CATEGORIES, PANEL_DOCUMENT_CATEGORIES
)
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
import os
import re
from collections import OrderedDict
from datetime import datetime, timedelta
import hashlib
import uuid

main = Blueprint('main', __name__)

FORMATION_DAY_DISPLAY_FORMAT = "%A %d %B %Y"

ALLOWED_UPLOAD_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'gif'}

def is_allowed_upload(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_UPLOAD_EXTENSIONS

def get_upcoming_formation_days(rsvp_user=None):
    """
    rsvp_user: if given, each entry includes that user's RSVP status
    ('attending' / 'not_attending' / None) for the day.
    Only days from today onward are included; past days (and their RSVPs)
    are kept in the database for the admin history view, not shown here.
    """
    days = FormationDay.query.filter(FormationDay.date >= datetime.now().date()).order_by(FormationDay.date).all()

    rsvp_by_day = {}
    if rsvp_user:
        rsvps = FormationDayRSVP.query.filter_by(user_id=rsvp_user.id).all()
        rsvp_by_day = {r.formation_day_id: r.status for r in rsvps}

    return [{
        'id': d.id,
        'label': d.label,
        'date': d.date.strftime(FORMATION_DAY_DISPLAY_FORMAT),
        'rsvp_status': rsvp_by_day.get(d.id)
    } for d in days]

def get_most_recent_formation_day_date(upcoming_dates):
    """
    Determines which formation day should be treated as "recent" for the
    Resources tab, based on Resource.formation_date values (decoupled from
    the upcoming-days list so pruning past formation days doesn't break it).
    """
    today = datetime.now().date()
    most_recent_dt = None
    most_recent_date = None

    resources = Resource.query.filter_by(category='formation_day').all()
    for r in resources:
        if not r.formation_date:
            continue
        clean_str = re.sub(r'^[a-zA-Z]+\s', '', r.formation_date).strip()
        try:
            dt = datetime.strptime(clean_str, "%d %B %Y").date()
        except ValueError:
            continue
        if dt <= today and (most_recent_dt is None or dt > most_recent_dt):
            most_recent_dt = dt
            most_recent_date = r.formation_date

    if most_recent_date is None and upcoming_dates:
        most_recent_date = upcoming_dates[0]['date']

    return most_recent_date

def get_formation_panel_dates_by_year(global_settings):
    """
    Parse GlobalSettings.formation_panel_dates as a plain comma-separated list of
    dates (no labels) and group them by year, sorted chronologically within each year.
    Tolerates leftover "Label: Date" entries from before labels were removed.
    """
    grouped = OrderedDict()
    if not global_settings or not global_settings.formation_panel_dates:
        return grouped

    parsed = []
    for raw in global_settings.formation_panel_dates.split(','):
        date_str = raw.strip()
        if not date_str:
            continue
        if ':' in date_str:
            date_str = date_str.split(':', 1)[1].strip()

        dt = None
        for fmt in ("%A %d %B %Y", "%d %B %Y"):
            try:
                dt = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue

        year = str(dt.year) if dt else 'Other'
        parsed.append((year, dt, date_str))

    parsed.sort(key=lambda item: (item[0], item[1] or datetime.max))

    for year, dt, date_str in parsed:
        grouped.setdefault(year, []).append(date_str)

    return grouped

def get_candidate_academic_requirements(user):
    """
    Get-or-create a CandidateAcademicRequirement row for every AcademicRequirement,
    for the given candidate, so the tab always shows the full current subject list.
    """
    requirements = AcademicRequirement.query.order_by(AcademicRequirement.sort_order, AcademicRequirement.id).all()
    existing = {c.requirement_id: c for c in CandidateAcademicRequirement.query.filter_by(user_id=user.id).all()}

    created = False
    rows = []
    for req in requirements:
        row = existing.get(req.id)
        if row is None:
            row = CandidateAcademicRequirement(user_id=user.id, requirement_id=req.id, status='not_completed')
            db.session.add(row)
            row.requirement = req
            created = True
        rows.append(row)

    if created:
        db.session.commit()

    return rows

def parse_semester_year(due_date):
    """Extract (semester, year) strings back out of a 'Semester N, YYYY' value."""
    if not due_date:
        return None, None
    match = re.match(r'Semester\s+(\d),\s*(\d{4})', due_date)
    if not match:
        return None, None
    return match.group(1), match.group(2)

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
            User.is_panel_member == False,
            User.is_archived == False
        ).all()
    else:
        candidates = []

    global_settings = GlobalSettings.query.first()
    formation_panel_dates_by_year = get_formation_panel_dates_by_year(global_settings)

    return render_template('panel_dashboard.html', candidates=candidates, global_settings=global_settings, formation_panel_dates_by_year=formation_panel_dates_by_year)

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

    upcoming_dates = get_upcoming_formation_days(rsvp_user=target_user)
    resources = Resource.query.all()
    standards = Standard.query.order_by(Standard.id).all()
    academic_requirements = get_candidate_academic_requirements(target_user)

    support_email = "support@uca.org.au"
    if global_settings:
        support_email = global_settings.support_email_default or "support@uca.org.au"
        if target_user.profile and target_user.profile.presbytery:
            presbytery = target_user.profile.presbytery
            if presbytery == "Generate Presbytery" and global_settings.support_email_generate_presbytery:
                support_email = global_settings.support_email_generate_presbytery
            elif presbytery == "Wimala Presbytery" and global_settings.support_email_wimala_presbytery:
                support_email = global_settings.support_email_wimala_presbytery
            elif presbytery == "POSSA" and global_settings.support_email_possa:
                support_email = global_settings.support_email_possa

    most_recent_date = get_most_recent_formation_day_date(upcoming_dates)
    formation_panel_dates_by_year = get_formation_panel_dates_by_year(global_settings)
    formation_panel_dates_flat = [d for dates in formation_panel_dates_by_year.values() for d in dates]

    return render_template('profile.html', user=target_user, global_settings=global_settings, upcoming_dates=upcoming_dates, resources=resources, standards=standards, academic_requirements=academic_requirements, support_email=support_email, most_recent_date=most_recent_date, document_categories=CANDIDATE_DOCUMENT_CATEGORIES, panel_report_categories=PANEL_DOCUMENT_CATEGORIES, formation_panel_dates_by_year=formation_panel_dates_by_year, formation_panel_dates_flat=formation_panel_dates_flat)

@main.route('/candidate/<int:user_id>/transition_phase3', methods=['POST'])
@login_required
def transition_phase3(user_id):
    target_user = User.query.get_or_404(user_id)

    allowed = False
    if current_user.is_admin:
        allowed = True
    elif current_user.is_panel_member:
        if target_user.profile and target_user.profile.formation_panel_id == current_user.formation_panel_id:
            allowed = True

    if not allowed:
        flash("Access denied to this profile.")
        return redirect(url_for('main.index'))

    if not target_user.profile:
        flash("This candidate has no profile to transition.")
        return redirect(url_for('main.index'))

    target_user.profile.phase = 3
    target_user.profile.transition_panel = True

    ordination_date = request.form.get('ordination_date')
    if ordination_date:
        target_user.profile.ordination_date = ordination_date

    current_church = request.form.get('current_church')
    if current_church:
        target_user.profile.current_church = current_church

    db.session.commit()
    flash(f'{target_user.name} has been transitioned to Phase 3.')
    return redirect(url_for('main.view_candidate_profile', user_id=target_user.id))

@main.route('/submit-document', methods=['GET', 'POST'])
def public_submit_document():
    global_settings = GlobalSettings.query.first()
    if not global_settings:
        global_settings = GlobalSettings()

    users = User.query.filter(User.is_admin == False, User.is_panel_member == False, User.is_archived == False).all()
    formation_panel_dates_by_year = get_formation_panel_dates_by_year(global_settings)

    if request.method == 'POST':
        user_id = request.form.get('user_id')
        category = request.form.get('category')
        day_label = request.form.get('day_label') or None

        if category not in PANEL_DOCUMENT_CATEGORIES:
            category = 'Other'

        # Validation
        valid_user_ids = {str(u.id) for u in users}
        if not user_id or user_id not in valid_user_ids or not request.form.get('category'):
             flash('Please select a candidate and document category.')
             return render_template('submit_document.html', users=users, global_settings=global_settings, categories=PANEL_DOCUMENT_CATEGORIES, formation_panel_dates_by_year=formation_panel_dates_by_year)

        # Handle files
        files = [f for f in request.files.getlist('file') if f.filename]
        if not files:
            flash('No selected file')
            return redirect(request.url)

        if not all(is_allowed_upload(f.filename) for f in files):
            flash('One or more files have an unsupported file type. Allowed: PDF, DOC, DOCX, JPG, PNG, GIF.')
            return redirect(request.url)

        for file in files:
            original_filename = secure_filename(file.filename)
            filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{original_filename}"
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))

            doc = PanelDocument(
                user_id=int(user_id),
                filename=filename,
                original_filename=original_filename,
                day_label=day_label,
                category=category,
                source='panel_member'
            )
            db.session.add(doc)

        db.session.commit()

        flash('Document submitted successfully!')
        return redirect(url_for('main.public_submit_document'))

    return render_template('submit_document.html', users=users, global_settings=global_settings, categories=PANEL_DOCUMENT_CATEGORIES, formation_panel_dates_by_year=formation_panel_dates_by_year)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            if getattr(user, 'is_archived', False):
                flash('This account has been archived')
            else:
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

@main.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            token = user.get_reset_token()
            reset_link = url_for('main.reset_token', token=token, _external=True)
            # TODO: Integrate with an email service (e.g., Flask-Mail) here.
            print(f"PASSWORD RESET LINK FOR {email}: {reset_link}") # For dev environment

        # Always display the same message to prevent email enumeration
        flash('If an account with that email exists, a password reset email has been sent.', 'info')
        return redirect(url_for('main.login'))
    return render_template('reset_request.html')

@main.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.verify_reset_token(token)
    if not user:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('main.reset_request'))
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if password != confirm_password:
            flash('Passwords do not match.')
            return render_template('reset_token.html')

        user.set_password(password)
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('main.login'))
    return render_template('reset_token.html')

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

    upcoming_dates = get_upcoming_formation_days(rsvp_user=current_user)
    resources = Resource.query.all()
    standards = Standard.query.order_by(Standard.id).all()
    academic_requirements = get_candidate_academic_requirements(current_user)

    support_email = "support@uca.org.au"
    if global_settings:
        support_email = global_settings.support_email_default or "support@uca.org.au"
        if current_user.profile and current_user.profile.presbytery:
            presbytery = current_user.profile.presbytery
            if presbytery == "Generate Presbytery" and global_settings.support_email_generate_presbytery:
                support_email = global_settings.support_email_generate_presbytery
            elif presbytery == "Wimala Presbytery" and global_settings.support_email_wimala_presbytery:
                support_email = global_settings.support_email_wimala_presbytery
            elif presbytery == "POSSA" and global_settings.support_email_possa:
                support_email = global_settings.support_email_possa

    most_recent_date = get_most_recent_formation_day_date(upcoming_dates)
    formation_panel_dates_by_year = get_formation_panel_dates_by_year(global_settings)
    formation_panel_dates_flat = [d for dates in formation_panel_dates_by_year.values() for d in dates]

    return render_template('profile.html', user=current_user, global_settings=global_settings, upcoming_dates=upcoming_dates, resources=resources, standards=standards, academic_requirements=academic_requirements, support_email=support_email, most_recent_date=most_recent_date, document_categories=CANDIDATE_DOCUMENT_CATEGORIES, panel_report_categories=PANEL_DOCUMENT_CATEGORIES, formation_panel_dates_by_year=formation_panel_dates_by_year, formation_panel_dates_flat=formation_panel_dates_flat)

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
            formation_panel_dates="13 February 2026, 19 June 2026, 20 November 2026",
            support_email_generate_presbytery="admin@generate.org.au",
            support_email_wimala_presbytery="admin@wimala.org.au",
            support_email_possa="admin@possa.org.au",
            support_email_default="support@uca.org.au"
        )
        db.session.add(settings)
        db.session.commit()

    if request.method == 'POST':
        settings.formation_panel_dates = request.form.get('formation_panel_dates')
        settings.support_email_generate_presbytery = request.form.get('support_email_generate_presbytery')
        settings.support_email_wimala_presbytery = request.form.get('support_email_wimala_presbytery')
        settings.support_email_possa = request.form.get('support_email_possa')
        settings.support_email_default = request.form.get('support_email_default')
        settings.student_chaplain_name = request.form.get('student_chaplain_name')
        settings.student_chaplain_email = request.form.get('student_chaplain_email')
        settings.student_chaplain_phone = request.form.get('student_chaplain_phone')
        db.session.commit()

        # Archive logic: any document tagged with a date no longer in the list gets archived
        new_dates_by_year = get_formation_panel_dates_by_year(settings)
        new_labels = [d for dates in new_dates_by_year.values() for d in dates]

        documents = PanelDocument.query.all()
        for doc in documents:
            if doc.day_label and doc.day_label not in new_labels:
                doc.is_archived = True

        db.session.commit()

        flash('Global settings updated successfully')
        return redirect(url_for('main.admin_dashboard'))

    formation_days = FormationDay.query.filter(
        FormationDay.date >= datetime.now().date()
    ).order_by(FormationDay.date).all()

    total_candidates = User.query.filter(
        User.is_admin == False, User.is_panel_member == False, User.is_archived == False
    ).count()

    rsvp_counts = {}
    for day_id, status, count in db.session.query(
        FormationDayRSVP.formation_day_id, FormationDayRSVP.status, db.func.count(FormationDayRSVP.id)
    ).group_by(FormationDayRSVP.formation_day_id, FormationDayRSVP.status).all():
        rsvp_counts.setdefault(day_id, {'attending': 0, 'not_attending': 0})[status] = count

    return render_template(
        'admin_global_settings.html', settings=settings, formation_days=formation_days,
        rsvp_counts=rsvp_counts, total_candidates=total_candidates
    )

@main.route('/admin/formation_days/add', methods=['POST'])
@login_required
def add_formation_day():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.profile'))

    label = request.form.get('label')
    date_str = request.form.get('date')

    if not date_str:
        flash('Please provide a date.')
        return redirect(url_for('main.admin_settings'))

    try:
        parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        flash('Invalid date format.')
        return redirect(url_for('main.admin_settings'))

    day = FormationDay(label=label.strip() if label else None, date=parsed_date)
    db.session.add(day)
    db.session.commit()
    flash('Formation day added.')
    return redirect(url_for('main.admin_settings'))

@main.route('/admin/formation_days/delete/<int:day_id>', methods=['POST'])
@login_required
def delete_formation_day(day_id):
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.profile'))

    day = FormationDay.query.get_or_404(day_id)
    db.session.delete(day)
    db.session.commit()
    flash('Formation day removed.')
    return redirect(url_for('main.admin_settings'))

@main.route('/formation_days/<int:day_id>/rsvp', methods=['POST'])
@login_required
def rsvp_formation_day(day_id):
    if current_user.is_admin or current_user.is_panel_member:
        flash('Only candidates can RSVP to formation days.')
        return redirect(url_for('main.index'))

    day = FormationDay.query.get_or_404(day_id)
    status = request.form.get('status')
    if status not in ('attending', 'not_attending'):
        flash('Invalid RSVP response.')
        return redirect(request.referrer or url_for('main.profile'))

    rsvp = FormationDayRSVP.query.filter_by(formation_day_id=day.id, user_id=current_user.id).first()
    if rsvp:
        rsvp.status = status
        rsvp.responded_at = datetime.utcnow()
    else:
        rsvp = FormationDayRSVP(formation_day_id=day.id, user_id=current_user.id, status=status)
        db.session.add(rsvp)

    db.session.commit()
    flash('Your RSVP has been recorded.')
    return redirect(request.referrer or url_for('main.profile'))

@main.route('/admin/formation_days/<int:day_id>/rsvps')
@login_required
def admin_formation_day_rsvps(day_id):
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.profile'))

    day = FormationDay.query.get_or_404(day_id)
    is_past = day.date < datetime.now().date()

    if is_past:
        # Historical day: only show candidates who actually responded at the time,
        # rather than every currently-active candidate (some may not have existed yet).
        rsvps = FormationDayRSVP.query.filter_by(formation_day_id=day.id).join(User).order_by(User.name).all()
        rows = [{'candidate': r.user, 'status': r.status, 'responded_at': r.responded_at} for r in rsvps]
    else:
        candidates = User.query.filter(
            User.is_admin == False, User.is_panel_member == False, User.is_archived == False
        ).order_by(User.name).all()

        rsvp_by_user = {r.user_id: r for r in FormationDayRSVP.query.filter_by(formation_day_id=day.id).all()}

        rows = []
        for candidate in candidates:
            rsvp = rsvp_by_user.get(candidate.id)
            rows.append({
                'candidate': candidate,
                'status': rsvp.status if rsvp else None,
                'responded_at': rsvp.responded_at if rsvp else None
            })

    return render_template('admin_formation_day_rsvps.html', day=day, rows=rows, is_past=is_past)

@main.route('/admin/formation_days/history')
@login_required
def admin_formation_days_history():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.profile'))

    past_days = FormationDay.query.filter(
        FormationDay.date < datetime.now().date()
    ).order_by(FormationDay.date.desc()).all()

    rsvp_counts = {}
    for day_id, status, count in db.session.query(
        FormationDayRSVP.formation_day_id, FormationDayRSVP.status, db.func.count(FormationDayRSVP.id)
    ).filter(FormationDayRSVP.formation_day_id.in_([d.id for d in past_days])).group_by(
        FormationDayRSVP.formation_day_id, FormationDayRSVP.status
    ).all():
        rsvp_counts.setdefault(day_id, {'attending': 0, 'not_attending': 0})[status] = count

    return render_template('admin_formation_days_history.html', past_days=past_days, rsvp_counts=rsvp_counts)

@main.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.profile'))

    global_settings = GlobalSettings.query.first()
    if not global_settings:
        global_settings = GlobalSettings()

    show_archived = request.args.get('show_archived', '0') == '1'

    if show_archived:
        users = User.query.filter(User.is_admin == False, User.is_panel_member == False).all()
        panel_members = User.query.filter_by(is_panel_member=True).all()
    else:
        users = User.query.filter(User.is_admin == False, User.is_panel_member == False, User.is_archived == False).all()
        panel_members = User.query.filter_by(is_panel_member=True, is_archived=False).all()

    panels = FormationPanel.query.all()
    return render_template('admin_dashboard.html', users=users, panels=panels, panel_members=panel_members, global_settings=global_settings, show_archived=show_archived)

@main.route('/admin/invite/candidate', methods=['GET', 'POST'])
@login_required
def invite_candidate():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.profile'))

    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')

        if User.query.filter_by(username=email).first() or User.query.filter_by(email=email).first():
            flash('User with this email already exists')
        else:
            token = str(uuid.uuid4())
            expiry = datetime.utcnow() + timedelta(days=7) # 7 days expiry

            # Create user with temporary username and password
            new_user = User(
                username=email, # Use email as temporary username
                email=email,
                name=name,
                is_admin=False,
                is_panel_member=False,
                invitation_token=token,
                invitation_expiry=expiry
            )
            new_user.set_password(str(uuid.uuid4())) # Random password

            # Create empty profile
            new_profile = Profile(user=new_user)
            db.session.add(new_user)
            db.session.add(new_profile)
            db.session.commit()

            # Simulate sending email
            invite_link = url_for('main.accept_invitation', token=token, _external=True)
            print(f"INVITATION LINK FOR {email}: {invite_link}") # For dev environment

            flash(f'Invitation sent to {email}. Link: {invite_link}')
            return redirect(url_for('main.admin_dashboard'))

    return render_template('admin_invite_user.html', role='Candidate')

@main.route('/admin/invite/panel_member', methods=['GET', 'POST'])
@login_required
def invite_panel_member():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.profile'))

    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        formation_panel_id = request.form.get('formation_panel_id')

        if User.query.filter_by(username=email).first() or User.query.filter_by(email=email).first():
            flash('User with this email already exists')
        else:
            token = str(uuid.uuid4())
            expiry = datetime.utcnow() + timedelta(days=7)

            new_user = User(
                username=email,
                email=email,
                name=name,
                is_admin=False,
                is_panel_member=True,
                formation_panel_id=formation_panel_id,
                invitation_token=token,
                invitation_expiry=expiry
            )
            new_user.set_password(str(uuid.uuid4()))

            db.session.add(new_user)
            db.session.commit()

            invite_link = url_for('main.accept_invitation', token=token, _external=True)
            print(f"INVITATION LINK FOR {email}: {invite_link}")

            flash(f'Invitation sent to {email}. Link: {invite_link}')
            return redirect(url_for('main.admin_dashboard') + '#members')

    panels = FormationPanel.query.all()
    return render_template('admin_invite_user.html', role='Panel Member', panels=panels)

@main.route('/setup-account/<token>', methods=['GET', 'POST'])
def accept_invitation(token):
    user = User.query.filter_by(invitation_token=token).first()

    if not user:
        flash('Invalid invitation token.')
        return redirect(url_for('main.login'))

    if user.invitation_expiry and user.invitation_expiry < datetime.utcnow():
        flash('Invitation expired.')
        return redirect(url_for('main.login'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match.')
            return render_template('setup_account.html', user=user)

        # Check if username is taken (if changed from email)
        if username != user.username:
             if User.query.filter_by(username=username).first():
                 flash('Username already taken.')
                 return render_template('setup_account.html', user=user)

        user.username = username
        user.set_password(password)
        user.invitation_token = None # Clear token
        user.invitation_expiry = None
        db.session.commit()

        login_user(user)
        flash('Account set up successfully.')
        return redirect(url_for('main.index'))

    return render_template('setup_account.html', user=user)

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

@main.route('/admin/toggle_archive/<int:user_id>', methods=['POST'])
@login_required
def toggle_archive(user_id):
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.profile'))

    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot archive yourself.')
        return redirect(url_for('main.admin_dashboard'))

    user.is_archived = not getattr(user, 'is_archived', False)
    db.session.commit()

    status = 'archived' if user.is_archived else 'unarchived'
    flash(f'User {user.username} has been {status}.')

    # Stay on the same view (show archived or not)
    return redirect(request.referrer or url_for('main.admin_dashboard'))

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
        user.profile.ready_for_mid_term_panel = True if request.form.get('ready_for_mid_term_panel') else False
        user.profile.mid_term_panel = True if request.form.get('mid_term_panel') else False
        user.profile.ready_for_transition_panel = True if request.form.get('ready_for_transition_panel') else False
        user.profile.transition_panel = True if request.form.get('transition_panel') else False
        user.profile.walking_on_country = True if request.form.get('walking_on_country') else False
        user.profile.presbytery = request.form.get('presbytery')
        user.profile.current_church = request.form.get('current_church')
        user.profile.ordination_date = request.form.get('ordination_date')
        # upcoming_formation_dates and formation_panel_dates are now global and not edited here

        if request.form.get('revert_to_phase_2'):
            user.profile.phase = 2

        # Academic requirement statuses (rows rendered per AcademicRequirement)
        for requirement_id in request.form.getlist('academic_requirement_id'):
            row = CandidateAcademicRequirement.query.filter_by(
                user_id=user.id, requirement_id=int(requirement_id)
            ).first()
            if not row:
                row = CandidateAcademicRequirement(user_id=user.id, requirement_id=int(requirement_id))
                db.session.add(row)
            row.status = request.form.get(f'academic_status_{requirement_id}', 'not_completed')

            semester = request.form.get(f'academic_semester_{requirement_id}')
            year = request.form.get(f'academic_year_{requirement_id}')
            row.due_date = f"Semester {semester}, {year}" if semester and year else None

        db.session.commit()
        flash('User updated successfully')
        return redirect(url_for('main.admin_dashboard'))

    panels = FormationPanel.query.all()
    academic_requirements = get_candidate_academic_requirements(user)
    for row in academic_requirements:
        row.semester_value, row.year_value = parse_semester_year(row.due_date)
    return render_template('admin_edit_profile.html', user=user, panels=panels, academic_requirements=academic_requirements)

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
        formation_date = request.form.get('formation_date') if category == 'formation_day' else None

        new_resource = Resource(title=title, type=res_type, category=category, formation_date=formation_date)

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
            if not is_allowed_upload(file.filename):
                flash('Unsupported file type. Allowed: PDF, DOC, DOCX, JPG, PNG, GIF.')
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
    upcoming_dates = get_upcoming_formation_days()

    return render_template('admin_resources.html', resources=resources, upcoming_dates=upcoming_dates)

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
        category = request.form.get('category')
        resource.category = category
        resource.formation_date = request.form.get('formation_date') if category == 'formation_day' else None
        resource.type = res_type

        if res_type == 'link':
            resource.url = request.form.get('url')
            # Optionally clear filename if switching types, or keep it.
            # resource.filename = None
        elif res_type == 'file':
            if 'file' in request.files:
                file = request.files['file']
                if file and file.filename != '':
                    if not is_allowed_upload(file.filename):
                        flash('Unsupported file type. Allowed: PDF, DOC, DOCX, JPG, PNG, GIF.')
                        return redirect(request.url)
                    # Delete old file if exists? Maybe better not to automatically delete for now.
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                    resource.filename = filename

        db.session.commit()
        flash('Resource updated successfully')
        return redirect(url_for('main.admin_resources'))

    upcoming_dates = get_upcoming_formation_days()

    return render_template('admin_edit_resource.html', resource=resource, upcoming_dates=upcoming_dates)

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

# --- Academic Requirements Management Routes ---

@main.route('/admin/academic_requirements')
@login_required
def admin_academic_requirements():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.profile'))

    requirements = AcademicRequirement.query.order_by(AcademicRequirement.sort_order, AcademicRequirement.id).all()
    return render_template('admin_academic_requirements.html', requirements=requirements)

@main.route('/admin/academic_requirements/create', methods=['GET', 'POST'])
@login_required
def create_academic_requirement():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.profile'))

    if request.method == 'POST':
        name = request.form.get('name')
        sort_order = request.form.get('sort_order') or 0

        req = AcademicRequirement(name=name, sort_order=int(sort_order))
        db.session.add(req)
        db.session.commit()
        flash('Academic requirement created successfully')
        return redirect(url_for('main.admin_academic_requirements'))

    return render_template('admin_edit_academic_requirement.html', requirement=None)

@main.route('/admin/academic_requirements/edit/<int:requirement_id>', methods=['GET', 'POST'])
@login_required
def edit_academic_requirement(requirement_id):
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.profile'))

    requirement = AcademicRequirement.query.get_or_404(requirement_id)

    if request.method == 'POST':
        requirement.name = request.form.get('name')
        requirement.sort_order = int(request.form.get('sort_order') or 0)

        db.session.commit()
        flash('Academic requirement updated successfully')
        return redirect(url_for('main.admin_academic_requirements'))

    return render_template('admin_edit_academic_requirement.html', requirement=requirement)

@main.route('/admin/academic_requirements/delete/<int:requirement_id>', methods=['POST'])
@login_required
def delete_academic_requirement(requirement_id):
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.profile'))

    requirement = AcademicRequirement.query.get_or_404(requirement_id)
    CandidateAcademicRequirement.query.filter_by(requirement_id=requirement.id).delete()
    db.session.delete(requirement)
    db.session.commit()
    flash('Academic requirement deleted')
    return redirect(url_for('main.admin_academic_requirements'))

@main.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    doc = PanelDocument.query.filter_by(filename=filename).first()
    if doc:
        allowed = current_user.is_admin or doc.user_id == current_user.id
        if not allowed and current_user.is_panel_member:
            owner = User.query.get(doc.user_id)
            allowed = bool(
                owner and owner.profile
                and owner.profile.formation_panel_id == current_user.formation_panel_id
            )
        if not allowed:
            flash('Access denied to this document.')
            return redirect(url_for('main.index'))
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

    # Resources (templates, book lists, etc.) are shared with any logged-in user.
    resource = Resource.query.filter_by(filename=filename).first()
    if resource:
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

    return "File not found", 404

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
    day_label = request.form.get('day_label')
    category = request.form.get('category')
    if category not in CANDIDATE_DOCUMENT_CATEGORIES:
        category = 'Other'

    for file in files:
        if file.filename == '':
            continue

        if file:
            if not is_allowed_upload(file.filename):
                flash(f'"{file.filename}" has an unsupported file type. Allowed: PDF, DOC, DOCX, JPG, PNG, GIF.')
                continue

            original_filename = secure_filename(file.filename)
            # Add timestamp to ensure uniqueness
            filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{original_filename}"
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))

            doc = PanelDocument(
                user_id=current_user.id,
                filename=filename,
                original_filename=original_filename,
                day_label=day_label,
                category=category,
                source='candidate'
            )
            db.session.add(doc)

    db.session.commit()
    flash('Documents uploaded successfully.')
    return redirect(url_for('main.profile'))

@main.route('/candidate/<int:user_id>/upload_report', methods=['POST'])
@login_required
def upload_panel_report(user_id):
    if not (current_user.is_panel_member or current_user.is_admin):
        flash('Only panel members can upload panel reports.')
        return redirect(url_for('main.profile'))

    target_user = User.query.get_or_404(user_id)

    if current_user.is_panel_member and not current_user.is_admin:
        if not target_user.profile or target_user.profile.formation_panel_id != current_user.formation_panel_id:
            flash('Access denied to this profile.')
            return redirect(url_for('main.panel_dashboard'))

    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('main.view_candidate_profile', user_id=user_id))

    files = request.files.getlist('file')
    category = request.form.get('category')
    if category not in PANEL_DOCUMENT_CATEGORIES:
        category = 'Other'

    for file in files:
        if file.filename == '':
            continue

        if not is_allowed_upload(file.filename):
            flash(f'"{file.filename}" has an unsupported file type. Allowed: PDF, DOC, DOCX, JPG, PNG, GIF.')
            continue

        original_filename = secure_filename(file.filename)
        filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{original_filename}"
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))

        doc = PanelDocument(
            user_id=target_user.id,
            filename=filename,
            original_filename=original_filename,
            category=category,
            source='panel_member'
        )
        db.session.add(doc)

    db.session.commit()
    flash('Report(s) uploaded successfully.')
    return redirect(url_for('main.view_candidate_profile', user_id=user_id))

@main.route('/profile/delete_document/<int:doc_id>', methods=['POST'])
@login_required
def delete_panel_document(doc_id):
    doc = PanelDocument.query.get_or_404(doc_id)

    # Allow admin, the candidate owner (for their own uploads only), or a panel member
    # (for panel-submitted reports) to delete. Candidates can't delete panel-submitted reports.
    can_delete = (
        current_user.is_admin
        or (doc.user_id == current_user.id and doc.source != 'panel_member')
        or (current_user.is_panel_member and doc.source == 'panel_member')
    )
    if not can_delete:
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

@main.route('/calendar/formation.ics')
@login_required
def download_ics():
    global_settings = GlobalSettings.query.first()
    if not global_settings:
        return "No settings found", 404

    events = []

    # Helper to parse and add events
    def add_events(raw_text, default_summary_prefix="Formation Day"):
        if not raw_text:
            return

        # Split by newline or comma
        if '\n' in raw_text:
            items = raw_text.split('\n')
        else:
            items = raw_text.split(',')

        for item in items:
            item = item.strip()
            if not item:
                continue

            label = None
            date_str = item

            if ':' in item:
                parts = item.split(':', 1)
                label = parts[0].strip()
                date_str = parts[1].strip()

            # Parse date
            dt = None
            # Try parsing with and without day name
            for fmt in ["%A %d %B %Y", "%d %B %Y"]:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue

            if dt:
                summary = f"{default_summary_prefix}: {label}" if label else default_summary_prefix

                # Generate a deterministic UID based on summary and date
                uid_source = f"{summary}-{dt.strftime('%Y%m%d')}"
                uid = hashlib.md5(uid_source.encode('utf-8')).hexdigest() + "@ucasa.formation"

                dtstamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')

                # Create ICS event block
                events.append(
                    "BEGIN:VEVENT\n"
                    f"UID:{uid}\n"
                    f"DTSTAMP:{dtstamp}\n"
                    f"SUMMARY:{summary}\n"
                    f"DTSTART;VALUE=DATE:{dt.strftime('%Y%m%d')}\n"
                    "END:VEVENT"
                )

    for day in FormationDay.query.filter(FormationDay.date >= datetime.now().date()).order_by(FormationDay.date).all():
        summary = f"Formation Day: {day.label}" if day.label else "Formation Day"
        uid_source = f"{summary}-{day.date.strftime('%Y%m%d')}"
        uid = hashlib.md5(uid_source.encode('utf-8')).hexdigest() + "@ucasa.formation"
        dtstamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        events.append(
            "BEGIN:VEVENT\n"
            f"UID:{uid}\n"
            f"DTSTAMP:{dtstamp}\n"
            f"SUMMARY:{summary}\n"
            f"DTSTART;VALUE=DATE:{day.date.strftime('%Y%m%d')}\n"
            "END:VEVENT"
        )

    add_events(global_settings.formation_panel_dates, "Formation Panel")

    ics_content = (
        "BEGIN:VCALENDAR\n"
        "VERSION:2.0\n"
        "PRODID:-//UCA SA//Formation//EN\n"
        + "\n".join(events) + "\n"
        "END:VCALENDAR"
    )

    return Response(
        ics_content,
        mimetype="text/calendar",
        headers={"Content-Disposition": "attachment;filename=formation_schedule.ics"}
    )
