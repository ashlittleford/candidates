from app import create_app, db
from app.models import User, Profile, GlobalSettings, FormationPanel, Resource, Standard
import os
import json

app = create_app()

with app.app_context():
    # Ensure instance directory exists
    if not os.path.exists('instance'):
        os.makedirs('instance')

    # Check for existing DB file logic is flawed if create_app creates empty file.
    # Instead, check if Admin exists.

    db.create_all()

    # Create Admin
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', name='Administrator', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        print("Created Admin user.")
    else:
        print("Admin user already exists.")

    # Create Sample Panels
    if not FormationPanel.query.first():
        panel1 = FormationPanel(chair_name="Rev. Smith", members="Dr. Jones, Rev. Brown, Ms. White")
        panel2 = FormationPanel(chair_name="Rev. Williams", members="Mr. Black, Dr. Green, Rev. Gray")
        panel3 = FormationPanel(chair_name="Dr. Taylor", members="Rev. Wilson, Ms. Evans, Mr. Thomas")
        panel4 = FormationPanel(chair_name="Rev. Roberts", members="Dr. Lee, Rev. Harris, Ms. Clark")

        db.session.add(panel1)
        db.session.add(panel2)
        db.session.add(panel3)
        db.session.add(panel4)
        db.session.commit() # Commit to get IDs
        print("Created Formation Panels.")
    else:
        print("Formation Panels already exist.")
        panel1 = FormationPanel.query.filter_by(chair_name="Rev. Smith").first()

    # Create Sample Candidate
    if not User.query.filter_by(username='candidate').first():
        candidate = User(username='candidate', name='John Doe', is_admin=False)
        candidate.set_password('password123')
        # Create Profile
        profile = Profile(
            user=candidate,
            formation_panel_id=panel1.id if panel1 else None, # Link to Panel 1
            presbytery="Wimala Presbytery",
            current_church="Encounter Henley",
            formation_days_completed="Day 1 (Jan), Day 2 (Mar)",
            start_date="March 2023",
            walking_on_country=True,
            upcoming_formation_dates="Day 3 (Jun 15), Day 4 (Aug 20)",
            formation_panel_dates="Panel 1: May, Panel 2: Sep, Panel 3: Nov"
        )
        db.session.add(candidate)
        db.session.add(profile)
        print("Created Candidate user.")
    else:
        print("Candidate user already exists.")

    # Create Sample Panel Member
    if not User.query.filter_by(username='panel_member').first():
        panel_member = User(username='panel_member', name='Dr. Jones', is_panel_member=True, formation_panel_id=panel1.id if panel1 else None)
        panel_member.set_password('password123')
        db.session.add(panel_member)
        print("Created Panel Member user.")
    else:
        print("Panel Member user already exists.")

    # Initialize Global Settings
    if not GlobalSettings.query.first():
        # Use defaults
        settings = GlobalSettings(
            upcoming_formation_dates="Monday 2 March 2026, Monday 13 April 2026, Monday 4 May 2026, Monday 1 June 2026, Monday 3 August 2026, Monday 7 September 2026, Monday 12 October 2026, Monday 2 November 2026",
        formation_panel_dates="First: 13 February 2026, Second: 19 June 2026, Third: 20 November 2026"
        )
        db.session.add(settings)
        print("Created Global Settings.")
    else:
        print("Global Settings already exist.")

    # Initialize Standards
    if Standard.query.count() == 0:
        json_path = os.path.join(app.root_path, 'standards_data.json')
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                data = json.load(f)

            print(f"Found {len(data)} standards in JSON. Populating database...")

            for item in data:
                # Join lists with newlines
                beginning_text = "\n".join(item.get('beginning', []))
                developing_text = "\n".join(item.get('developing', []))
                established_text = "\n".join(item.get('established', []))
                lfd_text = "\n".join(item.get('lfd', []))

                std = Standard(
                    id=item['id'],
                    attribute=item['attribute'],
                    beginning=beginning_text,
                    developing=developing_text,
                    established=established_text,
                    lfd=lfd_text
                )
                db.session.add(std)
            print("Standards populated.")
        else:
            print(f"Warning: {json_path} not found.")
    else:
        print("Standards already exist in DB.")

    db.session.commit()
    print("Database initialized.")
