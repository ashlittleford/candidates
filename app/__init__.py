from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import inspect, text
import os
import re
from markupsafe import Markup, escape

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

def bold_keywords_filter(text):
    if not text:
        return text
    # Escape the text first to prevent XSS
    text = str(escape(text))
    # Bold "Key educational units:"
    text = re.sub(r'(Key educational units:)', r'<strong>\1</strong>', text, flags=re.IGNORECASE)
    # Bold "LFD #:" variants
    text = re.sub(r'(LFD\s*\d+[:.])', r'<strong>\1</strong>', text, flags=re.IGNORECASE)
    return Markup(text)

def check_and_upgrade_schema(app):
    """
    Checks the database schema for missing columns and attempts to add them.
    This is a simple migration mechanism to handle schema changes without full Alembic setup.
    """
    with app.app_context():
        # Ensure the database tables exist first
        db.create_all()

        inspector = inspect(db.engine)
        if inspector.has_table("user"):
            columns = [col['name'] for col in inspector.get_columns("user")]
            if "email" not in columns:
                print("Missing column 'email' detected in 'user' table. Attempting to add it...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE user ADD COLUMN email VARCHAR(150)"))
                        conn.commit()
                    print("Successfully added 'email' column.")
                except Exception as e:
                    print(f"Failed to add 'email' column: {e}")

            if "invitation_token" not in columns:
                print("Missing column 'invitation_token' detected in 'user' table. Attempting to add it...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE user ADD COLUMN invitation_token VARCHAR(100)"))
                        conn.commit()
                    print("Successfully added 'invitation_token' column.")
                except Exception as e:
                    print(f"Failed to add 'invitation_token' column: {e}")

            if "invitation_expiry" not in columns:
                print("Missing column 'invitation_expiry' detected in 'user' table. Attempting to add it...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE user ADD COLUMN invitation_expiry DATETIME"))
                        conn.commit()
                    print("Successfully added 'invitation_expiry' column.")
                except Exception as e:
                    print(f"Failed to add 'invitation_expiry' column: {e}")

            if "is_archived" not in columns:
                print("Missing column 'is_archived' detected in 'user' table. Attempting to add it...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE user ADD COLUMN is_archived BOOLEAN DEFAULT 0"))
                        conn.commit()
                    print("Successfully added 'is_archived' column.")
                except Exception as e:
                    print(f"Failed to add 'is_archived' column: {e}")

            if db.engine.dialect.name == "postgresql":
                password_hash_col = next((col for col in inspector.get_columns("user") if col['name'] == 'password_hash'), None)
                if password_hash_col and getattr(password_hash_col['type'], 'length', None) and password_hash_col['type'].length < 255:
                    print("Widening 'password_hash' column in 'user' table to VARCHAR(255)...")
                    try:
                        with db.engine.connect() as conn:
                            conn.execute(text('ALTER TABLE "user" ALTER COLUMN password_hash TYPE VARCHAR(255)'))
                            conn.commit()
                        print("Successfully widened 'password_hash' column.")
                    except Exception as e:
                        print(f"Failed to widen 'password_hash' column: {e}")

        if inspector.has_table("profile"):
            columns = [col['name'] for col in inspector.get_columns("profile")]
            if "current_church" not in columns:
                print("Missing column 'current_church' detected in 'profile' table. Attempting to add it...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE profile ADD COLUMN current_church VARCHAR(150)"))
                        conn.commit()
                    print("Successfully added 'current_church' column.")
                except Exception as e:
                    print(f"Failed to add 'current_church' column: {e}")

        if inspector.has_table("resource"):
            columns = [col['name'] for col in inspector.get_columns("resource")]
            if "category" not in columns:
                print("Missing column 'category' detected in 'resource' table. Attempting to add it...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE resource ADD COLUMN category VARCHAR(50) DEFAULT 'general'"))
                        conn.commit()
                    print("Successfully added 'category' column.")
                except Exception as e:
                    print(f"Failed to add 'category' column: {e}")
            if "formation_date" not in columns:
                print("Missing column 'formation_date' detected in 'resource' table. Attempting to add it...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE resource ADD COLUMN formation_date VARCHAR(100)"))
                        conn.commit()
                    print("Successfully added 'formation_date' column.")
                except Exception as e:
                    print(f"Failed to add 'formation_date' column: {e}")

        if inspector.has_table("profile"):
            columns = [col['name'] for col in inspector.get_columns("profile")]

            if "code_of_ethics_signed" not in columns:
                print("Missing column 'code_of_ethics_signed' detected in 'profile' table. Attempting to add it...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE profile ADD COLUMN code_of_ethics_signed BOOLEAN DEFAULT 0"))
                        conn.commit()
                    print("Successfully added 'code_of_ethics_signed' column.")
                except Exception as e:
                    print(f"Failed to add 'code_of_ethics_signed' column: {e}")

            if "code_of_ethics_date" not in columns:
                print("Missing column 'code_of_ethics_date' detected in 'profile' table. Attempting to add it...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE profile ADD COLUMN code_of_ethics_date VARCHAR(50)"))
                        conn.commit()
                    print("Successfully added 'code_of_ethics_date' column.")
                except Exception as e:
                    print(f"Failed to add 'code_of_ethics_date' column: {e}")

            if "wwcc_cleared" not in columns:
                print("Missing column 'wwcc_cleared' detected in 'profile' table. Attempting to add it...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE profile ADD COLUMN wwcc_cleared BOOLEAN DEFAULT 0"))
                        conn.commit()
                    print("Successfully added 'wwcc_cleared' column.")
                except Exception as e:
                    print(f"Failed to add 'wwcc_cleared' column: {e}")

            if "wwcc_number" not in columns:
                print("Missing column 'wwcc_number' detected in 'profile' table. Attempting to add it...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE profile ADD COLUMN wwcc_number VARCHAR(100)"))
                        conn.commit()
                    print("Successfully added 'wwcc_number' column.")
                except Exception as e:
                    print(f"Failed to add 'wwcc_number' column: {e}")

            if "transition_panel" not in columns:
                print("Missing column 'transition_panel' detected in 'profile' table. Attempting to add it...")
                try:
                    with db.engine.connect() as conn:
                        # SQLite doesn't directly support BOOLEAN so we add an integer (which boolean is typically stored as) or boolean alias
                        conn.execute(text("ALTER TABLE profile ADD COLUMN transition_panel BOOLEAN DEFAULT 0"))
                        conn.commit()
                    print("Successfully added 'transition_panel' column.")
                except Exception as e:
                    print(f"Failed to add 'transition_panel' column: {e}")

            if "ready_for_mid_term_panel" not in columns:
                print("Missing column 'ready_for_mid_term_panel' detected in 'profile' table. Attempting to add it...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE profile ADD COLUMN ready_for_mid_term_panel BOOLEAN DEFAULT 0"))
                        conn.commit()
                    print("Successfully added 'ready_for_mid_term_panel' column.")
                except Exception as e:
                    print(f"Failed to add 'ready_for_mid_term_panel' column: {e}")

            if "ready_for_transition_panel" not in columns:
                print("Missing column 'ready_for_transition_panel' detected in 'profile' table. Attempting to add it...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE profile ADD COLUMN ready_for_transition_panel BOOLEAN DEFAULT 0"))
                        conn.commit()
                    print("Successfully added 'ready_for_transition_panel' column.")
                except Exception as e:
                    print(f"Failed to add 'ready_for_transition_panel' column: {e}")

            if "phase" not in columns:
                print("Missing column 'phase' detected in 'profile' table. Attempting to add it...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE profile ADD COLUMN phase INTEGER DEFAULT 2"))
                        conn.commit()
                    print("Successfully added 'phase' column.")
                except Exception as e:
                    print(f"Failed to add 'phase' column: {e}")

            if "ordination_date" not in columns:
                print("Missing column 'ordination_date' detected in 'profile' table. Attempting to add it...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE profile ADD COLUMN ordination_date VARCHAR(50)"))
                        conn.commit()
                    print("Successfully added 'ordination_date' column.")
                except Exception as e:
                    print(f"Failed to add 'ordination_date' column: {e}")
        if inspector.has_table("panel_document"):
            columns = [col['name'] for col in inspector.get_columns("panel_document")]
            if "is_archived" not in columns:
                print("Missing column 'is_archived' detected in 'panel_document' table. Attempting to add it...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE panel_document ADD COLUMN is_archived BOOLEAN DEFAULT 0"))
                        conn.commit()
                    print("Successfully added 'is_archived' column.")
                except Exception as e:
                    print(f"Failed to add 'is_archived' column: {e}")

            if "category" not in columns:
                print("Missing column 'category' detected in 'panel_document' table. Attempting to add it...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE panel_document ADD COLUMN category VARCHAR(50) DEFAULT 'Other'"))
                        conn.commit()
                    print("Successfully added 'category' column.")
                except Exception as e:
                    print(f"Failed to add 'category' column: {e}")

            if "source" not in columns:
                print("Missing column 'source' detected in 'panel_document' table. Attempting to add it...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE panel_document ADD COLUMN source VARCHAR(20) DEFAULT 'candidate'"))
                        conn.commit()
                    print("Successfully added 'source' column.")
                except Exception as e:
                    print(f"Failed to add 'source' column: {e}")

        if inspector.has_table("global_settings"):
            columns = [col['name'] for col in inspector.get_columns("global_settings")]

            if "support_email_generate_presbytery" not in columns:
                print("Missing column 'support_email_generate_presbytery' detected in 'global_settings' table. Attempting to add it...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE global_settings ADD COLUMN support_email_generate_presbytery VARCHAR(150) DEFAULT 'admin@generate.org.au'"))
                        conn.commit()
                    print("Successfully added 'support_email_generate_presbytery' column.")
                except Exception as e:
                    print(f"Failed to add 'support_email_generate_presbytery' column: {e}")

            if "support_email_wimala_presbytery" not in columns:
                print("Missing column 'support_email_wimala_presbytery' detected in 'global_settings' table. Attempting to add it...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE global_settings ADD COLUMN support_email_wimala_presbytery VARCHAR(150) DEFAULT 'admin@wimala.org.au'"))
                        conn.commit()
                    print("Successfully added 'support_email_wimala_presbytery' column.")
                except Exception as e:
                    print(f"Failed to add 'support_email_wimala_presbytery' column: {e}")

            if "support_email_possa" not in columns:
                print("Missing column 'support_email_possa' detected in 'global_settings' table. Attempting to add it...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE global_settings ADD COLUMN support_email_possa VARCHAR(150) DEFAULT 'admin@possa.org.au'"))
                        conn.commit()
                    print("Successfully added 'support_email_possa' column.")
                except Exception as e:
                    print(f"Failed to add 'support_email_possa' column: {e}")

            if "support_email_default" not in columns:
                print("Missing column 'support_email_default' detected in 'global_settings' table. Attempting to add it...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE global_settings ADD COLUMN support_email_default VARCHAR(150) DEFAULT 'support@uca.org.au'"))
                        conn.commit()
                    print("Successfully added 'support_email_default' column.")
                except Exception as e:
                    print(f"Failed to add 'support_email_default' column: {e}")

            if "student_chaplain_name" not in columns:
                print("Missing column 'student_chaplain_name' detected in 'global_settings' table. Attempting to add it...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE global_settings ADD COLUMN student_chaplain_name VARCHAR(150)"))
                        conn.commit()
                    print("Successfully added 'student_chaplain_name' column.")
                except Exception as e:
                    print(f"Failed to add 'student_chaplain_name' column: {e}")

            if "student_chaplain_email" not in columns:
                print("Missing column 'student_chaplain_email' detected in 'global_settings' table. Attempting to add it...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE global_settings ADD COLUMN student_chaplain_email VARCHAR(150)"))
                        conn.commit()
                    print("Successfully added 'student_chaplain_email' column.")
                except Exception as e:
                    print(f"Failed to add 'student_chaplain_email' column: {e}")

            if "student_chaplain_phone" not in columns:
                print("Missing column 'student_chaplain_phone' detected in 'global_settings' table. Attempting to add it...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE global_settings ADD COLUMN student_chaplain_phone VARCHAR(50)"))
                        conn.commit()
                    print("Successfully added 'student_chaplain_phone' column.")
                except Exception as e:
                    print(f"Failed to add 'student_chaplain_phone' column: {e}")

def create_app(test_config=None):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') != 'development'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['REMEMBER_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') != 'development'
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True

    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Render (like Heroku) provides postgres:// but SQLAlchemy requires postgresql://
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # Use absolute path to instance/site.db to avoid path issues
        base_dir = os.path.abspath(os.path.dirname(__file__))
        instance_path = os.path.join(base_dir, '..', 'instance')
        if not os.path.exists(instance_path):
            os.makedirs(instance_path)

        db_path = os.path.join(instance_path, 'site.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    # Kept outside static/ so uploaded files can't be fetched directly by URL,
    # bypassing the access control in the uploaded_file view.
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = 'main.login'

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.routes import main
    app.register_blueprint(main)

    app.jinja_env.filters['bold_keywords'] = bold_keywords_filter

    # Run schema check and upgrade
    if not test_config or test_config.get('SQLALCHEMY_DATABASE_URI') != 'sqlite:///:memory:':
         check_and_upgrade_schema(app)
         seed_standards(app)
         seed_academic_requirements(app)
         migrate_formation_days(app)
         migrate_academic_requirement_statuses(app)

    return app

def seed_standards(app):
    """
    Upserts the Standard table from standards_data.json on every boot, so
    corrected data always overwrites whatever is currently in the database.
    """
    from app.standards_loader import upsert_standards

    with app.app_context():
        try:
            upsert_standards()
        except Exception as e:
            print(f"Error seeding standards: {e}")

def seed_academic_requirements(app):
    """
    Checks if the AcademicRequirement table is empty and populates it from the JSON file.
    """
    import json
    from app.models import AcademicRequirement

    with app.app_context():
        try:
            if AcademicRequirement.query.count() == 0:
                print("Seeding Academic Requirements database from JSON...")
                json_path = os.path.join(app.root_path, 'academic_requirements_data.json')
                if os.path.exists(json_path):
                    with open(json_path, 'r') as f:
                        data = json.load(f)

                    for item in data:
                        req = AcademicRequirement(
                            id=item['id'],
                            name=item['name'],
                            sort_order=item.get('sort_order', 0)
                        )
                        db.session.add(req)
                    db.session.commit()
                    print("Academic Requirements seeded successfully.")
                else:
                    print(f"Warning: {json_path} not found. Skipping seeding.")
        except Exception as e:
            print(f"Error seeding academic requirements: {e}")

def migrate_formation_days(app):
    """
    One-time backfill: if the FormationDay table is empty and GlobalSettings has
    legacy free-text upcoming_formation_dates, parse it into FormationDay rows.
    """
    import re
    from datetime import datetime
    from app.models import FormationDay, GlobalSettings

    with app.app_context():
        try:
            if FormationDay.query.count() > 0:
                return

            settings = GlobalSettings.query.first()
            if not settings or not settings.upcoming_formation_dates:
                return

            raw = settings.upcoming_formation_dates
            items = raw.split('\n') if '\n' in raw else raw.split(',')

            print("Backfilling FormationDay rows from legacy upcoming_formation_dates...")
            for item in items:
                item = item.strip()
                if not item:
                    continue

                if ':' in item:
                    label, date_str = item.split(':', 1)
                    label = label.strip()
                    date_str = date_str.strip()
                else:
                    label = None
                    date_str = item

                clean_str = re.sub(r'^[a-zA-Z]+\s', '', date_str).strip()
                try:
                    parsed = datetime.strptime(clean_str, "%d %B %Y").date()
                except ValueError:
                    continue

                db.session.add(FormationDay(label=label, date=parsed))

            db.session.commit()
            print("FormationDay backfill complete.")
        except Exception as e:
            print(f"Error migrating formation days: {e}")

def migrate_academic_requirement_statuses(app):
    """
    One-time value migration: the old 'pending'/'in_progress' status values
    are renamed to 'not_completed'/'enrolled'.
    """
    from app.models import CandidateAcademicRequirement

    with app.app_context():
        try:
            updated = CandidateAcademicRequirement.query.filter_by(status='pending').update({'status': 'not_completed'})
            updated += CandidateAcademicRequirement.query.filter_by(status='in_progress').update({'status': 'enrolled'})
            if updated:
                db.session.commit()
                print(f"Migrated {updated} academic requirement status value(s).")
        except Exception as e:
            print(f"Error migrating academic requirement statuses: {e}")
