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
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    level = db.Column(db.Integer)
    
    @property
    def total_beds(self):
        return len(self.beds)
    
    @property
    def available_beds(self):
        return len([bed for bed in self.beds if not bed.is_occupied])
    
    # Relationships
    beds = db.relationship('Bed', backref='hospital', lazy=True)
    admins = db.relationship('Admin', backref='hospital', lazy=True)
    users = db.relationship('User', backref='hospital', lazy=True)
    


class Admin(UserMixin, db.Model):
    """Admins table (separate from regular users)"""
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(512))
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
    password_hash = db.Column(db.String(512))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Flask-Login loader for admins
@login_manager.user_loader
def load_user(user_id):
    # Try User first (since regular users are more common)
    user = User.query.get(int(user_id))
    if user:
        return user
    # Then try Admin
    return Admin.query.get(int(user_id))

class Bed(db.Model):
    __tablename__ = 'beds'
    
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    bed_number = db.Column(db.Integer, nullable=False)
    is_occupied = db.Column(db.Boolean, default=False)
    bed_type = db.Column(db.String(50), default='ICU')  # Could be ICU, General, etc.
    
    # Relationship to admission
    current_admission = db.relationship('Admission', back_populates='bed', uselist=False)
    
    __table_args__ = (
        db.UniqueConstraint('hospital_id', 'bed_number', name='_hospital_bed_uc'),
    )
    def __repr__(self):
        return f"<Bed {self.bed_number} ({'Occupied' if self.is_occupied else 'Available'})>"

class Admission(db.Model):
    __tablename__ = 'admissions'
    
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    patient_name = db.Column(db.String(100), nullable=False)
    bed_id = db.Column(db.Integer, db.ForeignKey('beds.id'), nullable=False)
    doctor = db.Column(db.String(100), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default='Medium')  # High/Medium/Low
    admission_time = db.Column(db.DateTime, default=datetime.utcnow)
    discharge_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='Active')
    
    # Relationships
    bed = db.relationship('Bed', back_populates='current_admission')
    
    @property
    def patient_initials(self):
        return ''.join([name[0] for name in self.patient_name.split()[:2]]).upper()
    
    @property
    def length_of_stay(self):
        if self.discharge_time:
            return (self.discharge_time - self.admission_time).total_seconds() / 86400  # in days
        return (datetime.utcnow() - self.admission_time).total_seconds() / 86400
    

class Discharge(db.Model):
    __tablename__ = 'discharges'
    
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    patient_name = db.Column(db.String(100), nullable=False)
    bed_number = db.Column(db.Integer, nullable=False)
    admission_time = db.Column(db.DateTime, nullable=False)
    discharge_time = db.Column(db.DateTime, default=datetime.utcnow)
    discharging_doctor = db.Column(db.String(100), nullable=False)
    discharge_type = db.Column(db.String(50), nullable=False)  # Recovered/Transferred/Other
    notes = db.Column(db.Text)
    
    @property
    def patient_initials(self):
        return ''.join([name[0] for name in self.patient_name.split()[:2]]).upper()
    
    @property
    def length_of_stay(self):
        return (self.discharge_time - self.admission_time).days