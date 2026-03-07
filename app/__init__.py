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

def create_app(test_config=None):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    # Use absolute path to instance/site.db to avoid path issues
    base_dir = os.path.abspath(os.path.dirname(__file__))
    instance_path = os.path.join(base_dir, '..', 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)

    db_path = os.path.join(instance_path, 'site.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads')
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

    return app

def seed_standards(app):
    """
    Checks if the Standard table is empty and populates it from the JSON file.
    """
    import json
    from app.models import Standard

    with app.app_context():
        # Ensure table exists first (created by db.create_all() in check_and_upgrade_schema or init_db)
        # But check_and_upgrade_schema only does specific upgrades.
        # db.create_all() is typically called in init_db.py, but we can call it here to be safe if it's cheap?
        # Actually, check_and_upgrade_schema calls db.create_all(). So we are good.

        try:
            if Standard.query.count() == 0:
                print("Seeding Standards database from JSON...")
                json_path = os.path.join(app.root_path, 'standards_data.json')
                if os.path.exists(json_path):
                    with open(json_path, 'r') as f:
                        data = json.load(f)

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
                    db.session.commit()
                    print("Standards seeded successfully.")
                else:
                    print(f"Warning: {json_path} not found. Skipping seeding.")
        except Exception as e:
            print(f"Error seeding standards: {e}")
