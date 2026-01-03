from app import create_app, db
from app.models import User, Profile, GlobalSettings

app = create_app()

with app.app_context():
    db.create_all()

    # Create Admin
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', name='Administrator', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)

    # Create Sample Candidate
    if not User.query.filter_by(username='candidate').first():
        candidate = User(username='candidate', name='John Doe', is_admin=False)
        candidate.set_password('password123')
        # Create Profile
        profile = Profile(
            user=candidate,
            formation_panel_details="Rev. Smith, Dr. Jones",
            formation_days_completed="Day 1 (Jan), Day 2 (Mar)",
            walking_on_country=True,
            upcoming_formation_dates="Day 3 (Jun 15), Day 4 (Aug 20)",
            formation_panel_dates="Panel 1: May, Panel 2: Sep, Panel 3: Nov"
        )
        db.session.add(candidate)
        db.session.add(profile)

    # Initialize Global Settings
    if not GlobalSettings.query.first():
        # Use defaults or take from the sample candidate if desired, but better to start clean or with placeholder
        settings = GlobalSettings(
            upcoming_formation_dates="Monday 2 March 2026, Monday 13 April 2026, Monday 4 May 2026, Monday 1 June 2026, Monday 3 August 2026, Monday 7 September 2026, Monday 12 October 2026, Monday 2 November 2026",
            formation_panel_dates="Term 1: Friday 13 February 2026, Term 2: Friday 19 June 2026, Term 3: Friday 20 November 2026"
        )
        db.session.add(settings)

    db.session.commit()
    print("Database initialized.")
