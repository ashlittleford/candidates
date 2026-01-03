from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import inspect, text
import os

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

def check_and_upgrade_schema(app):
    """
    Checks the database schema for missing columns and attempts to add them.
    This is a simple migration mechanism to handle schema changes without full Alembic setup.
    """
    with app.app_context():
        # Ensure the database tables exist first
        db.create_all()

        inspector = inspect(db.engine)
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
