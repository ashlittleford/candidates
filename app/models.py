from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(150))
    profile = db.relationship('Profile', backref='user', uselist=False, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class FormationPanel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chair_name = db.Column(db.String(150), nullable=False)
    members = db.Column(db.Text, default="") # Stores comma or newline separated members

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    formation_panel_id = db.Column(db.Integer, db.ForeignKey('formation_panel.id'), nullable=True)
    formation_panel = db.relationship('FormationPanel', backref='profiles')

    # Deprecated field, keeping for now or we can ignore it since we are resetting DB
    formation_panel_details = db.Column(db.Text, default="")

    formation_days_completed = db.Column(db.Text, default="")

    @property
    def computed_formation_days_count(self):
        if not self.formation_days_completed:
            return 0

        # Check if it's just a number
        s = self.formation_days_completed.strip()
        if s.isdigit():
            return int(s)

        # Otherwise split
        # Split by newline if present, otherwise comma
        if '\n' in s:
            items = s.split('\n')
        else:
            items = s.split(',')

        # Filter empty
        items = [i.strip() for i in items if i.strip()]
        return len(items)

    @property
    def formation_days_list_items(self):
        if not self.formation_days_completed:
            return []

        s = self.formation_days_completed.strip()
        if s.isdigit():
            return []

        if '\n' in s:
            items = s.split('\n')
        else:
            items = s.split(',')

        return [i.strip() for i in items if i.strip()]

    walking_on_country = db.Column(db.Boolean, default=False)
    upcoming_formation_dates = db.Column(db.Text, default="")
    formation_panel_dates = db.Column(db.Text, default="")
    presbytery = db.Column(db.String(100), nullable=True)

class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    type = db.Column(db.String(50), nullable=False) # 'file' or 'link'
    url = db.Column(db.String(500), nullable=True)
    filename = db.Column(db.String(250), nullable=True)

class GlobalSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    upcoming_formation_dates = db.Column(db.Text, default="")
    formation_panel_dates = db.Column(db.Text, default="")
