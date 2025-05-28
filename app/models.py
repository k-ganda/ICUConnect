from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash



class Hospital(db.Model):
    """Hospitals table"""
    __tablename__ = 'hospitals'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    verification_code = db.Column(db.String(20), unique=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    total_icu_beds = db.Column(db.Integer, default=0)
    available_icu_beds = db.Column(db.Integer, default=0)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    level = db.Column(db.Integer)
    
    
    # Relationships
    admins = db.relationship('Admin', backref='hospital', lazy=True)
    users = db.relationship('User', backref='hospital', lazy=True)
    


class Admin(UserMixin, db.Model):
    """Admins table (separate from regular users)"""
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    privilege_level = db.Column(db.String(20), default='hospital')  # 'super' or 'hospital'
    verification_docs = db.Column(db.String(200))  # Path to uploaded docs
    is_verified = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer)  # ID of admin who created this account
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Password handling
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class User(UserMixin, db.Model):
    """Regular staff users table"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'))  # Who approved this user
    email = db.Column(db.String(120), unique=True, nullable=False)
    employee_id = db.Column(db.String(50), nullable=False )
    role = db.Column(db.String(30))  # 'doctor', 'nurse', etc.
    is_approved = db.Column(db.Boolean, default=False)
    approval_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(128))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Flask-Login loader for admins
@login_manager.user_loader
def load_admin(admin_id):
    return Admin.query.get(int(admin_id))

@login_manager.user_loader
def load_user(user_id):
    # Try admin first, then regular user
    admin = Admin.query.get(int(user_id))
    if admin:
        return admin
    return User.query.get(int(user_id))