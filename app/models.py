from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_panel_member = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(150))

    formation_panel_id = db.Column(db.Integer, db.ForeignKey('formation_panel.id'), nullable=True)
    formation_panel = db.relationship('FormationPanel', backref='panel_member_users', foreign_keys=[formation_panel_id])

    profile = db.relationship('Profile', backref='user', uselist=False, cascade="all, delete-orphan")
    panel_documents = db.relationship('PanelDocument', backref='user', lazy=True, cascade="all, delete-orphan")

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
    start_date = db.Column(db.String(50), default="")
    mid_term_panel = db.Column(db.Boolean, default=False)
    walking_on_country = db.Column(db.Boolean, default=False)
    upcoming_formation_dates = db.Column(db.Text, default="")
    formation_panel_dates = db.Column(db.Text, default="")
    presbytery = db.Column(db.String(100), nullable=True)
    supervisor = db.Column(db.String(150), nullable=True)
    current_church = db.Column(db.String(150), nullable=True)

    code_of_ethics_signed = db.Column(db.Boolean, default=False)
    code_of_ethics_date = db.Column(db.String(50), nullable=True)

    wwcc_cleared = db.Column(db.Boolean, default=False)
    wwcc_number = db.Column(db.String(100), nullable=True)

    @property
    def computed_formation_days_count(self):
        txt = self.formation_days_completed
        if not txt:
            return 0
        txt = txt.strip()
        if txt.isdigit():
            return int(txt)

        # Check for list
        if '\n' in txt:
            items = [x for x in txt.split('\n') if x.strip()]
            return len(items)
        elif ',' in txt:
            items = [x for x in txt.split(',') if x.strip()]
            # Check if it's just a single number with comma? Unlikely.
            return len(items)
        else:
            # Single item that is not a digit?
            return 1

    @property
    def formation_days_list_items(self):
        txt = self.formation_days_completed
        if not txt:
            return []
        txt = txt.strip()
        if txt.isdigit():
            return []

        if '\n' in txt:
             return [x.strip() for x in txt.split('\n') if x.strip()]
        elif ',' in txt:
             return [x.strip() for x in txt.split(',') if x.strip()]
        else:
             return [txt]

class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    type = db.Column(db.String(50), nullable=False) # 'file' or 'link'
    category = db.Column(db.String(50), default='general') # 'general' or 'panel_paper'
    url = db.Column(db.String(500), nullable=True)
    filename = db.Column(db.String(250), nullable=True)

class GlobalSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    upcoming_formation_dates = db.Column(db.Text, default="")
    formation_panel_dates = db.Column(db.Text, default="")

class Standard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attribute = db.Column(db.Text, nullable=False)
    beginning = db.Column(db.Text, default="") # Newline separated
    developing = db.Column(db.Text, default="") # Newline separated
    established = db.Column(db.Text, default="") # Newline separated
    lfd = db.Column(db.Text, default="") # Newline separated

    @property
    def beginning_list(self):
        if not self.beginning: return []
        return [x.strip() for x in self.beginning.split('\n') if x.strip()]

    @property
    def developing_list(self):
        if not self.developing: return []
        return [x.strip() for x in self.developing.split('\n') if x.strip()]

    @property
    def established_list(self):
        if not self.established: return []
        return [x.strip() for x in self.established.split('\n') if x.strip()]

    @property
    def lfd_list(self):
        if not self.lfd: return []
        return [x.strip() for x in self.lfd.split('\n') if x.strip()]
class PanelDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(250), nullable=False)
    original_filename = db.Column(db.String(250), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
