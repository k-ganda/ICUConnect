from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app.utils import to_local_time, to_utc_time, get_current_local_time
import pytz



class Hospital(db.Model):
    """Hospitals table"""
    __tablename__ = 'hospitals'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    verification_code = db.Column(db.String(20), unique=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    level = db.Column(db.Integer)
    timezone = db.Column(db.String(50), default='Africa/Kigali')  # Default to Rwanda timezone
    
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
    
    def get_timezone(self):
        """Get the timezone object for this hospital"""
        return pytz.timezone(self.timezone)



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
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Password handling
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return f"admin-{self.id}"

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
    created_at = db.Column(db.DateTime, default=datetime.now)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(512))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    
    def get_id(self):
        return f"user-{self.id}"


class UserSettings(db.Model):
    """User notification and preference settings"""
    __tablename__ = 'user_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Notification preferences
    audio_notifications = db.Column(db.Boolean, default=True)
    visual_notifications = db.Column(db.Boolean, default=True)
    browser_notifications = db.Column(db.Boolean, default=False)
    
    # Audio settings
    audio_volume = db.Column(db.Float, default=0.7)  # 0.0 to 1.0
    audio_enabled = db.Column(db.Boolean, default=False)  # User has explicitly enabled audio
    
    # Notification types
    referral_notifications = db.Column(db.Boolean, default=True)
    bed_status_notifications = db.Column(db.Boolean, default=True)
    system_notifications = db.Column(db.Boolean, default=True)
    
    # Timing preferences
    notification_duration = db.Column(db.Integer, default=120)  # seconds
    auto_escalate = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    user = db.relationship('User', backref='settings')
    
    def __repr__(self):
        return f"<UserSettings(user_id={self.user_id})>"


# Flask-Login loader for admins
@login_manager.user_loader
def load_user(id_with_type):
    try:
        user_type, id_str = id_with_type.split('-', 1)
        if user_type == 'admin':
            return Admin.query.get(int(id_str))
        elif user_type == 'user':
            return User.query.get(int(id_str))
    except Exception:
        return None

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
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    admission_time = db.Column(db.DateTime, default=datetime.utcnow)
    discharge_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='Active')
    
    # Relationships
    bed = db.relationship('Bed', back_populates='current_admission')
    
    @property
    def local_admission_time(self):
        """Get admission time in local timezone"""
        return to_local_time(self.admission_time)
    
    @property
    def local_discharge_time(self):
        """Get discharge time in local timezone"""
        return to_local_time(self.discharge_time)
    
    @property
    def masked_patient_name(self):
        """Returns masked name for display purposes"""
        return "*****"
    
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
    def local_admission_time(self):
        """Get admission time in local timezone"""
        return to_local_time(self.admission_time)
    
    @property
    def local_discharge_time(self):
        """Get discharge time in local timezone"""
        return to_local_time(self.discharge_time)
    
    @property
    def patient_initials(self):
        return ''.join([name[0] for name in self.patient_name.split()[:2]]).upper()
    
    @property
    def length_of_stay(self):
        return (self.discharge_time - self.admission_time).days

class ReferralRequest(db.Model):
    """Referral requests between hospitals"""
    __tablename__ = 'referral_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    requesting_hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    target_hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('admissions.id'), nullable=True)
    
    # Patient details for referral
    
    patient_age = db.Column(db.Integer)
    patient_gender = db.Column(db.String(10))
    reason_for_referral = db.Column(db.Text, nullable=False)
    urgency_level = db.Column(db.String(20), default='Medium')  # High/Medium/Low
    special_requirements = db.Column(db.Text)  # Equipment, specialists needed
    primary_diagnosis = db.Column(db.String(255))
    current_treatment = db.Column(db.Text)
    
    
    # Communication details
    contact_method = db.Column(db.String(20))  # SMS/Call/Email
    contact_number = db.Column(db.String(20))
    contact_email = db.Column(db.String(120))
    
    # Status tracking
    status = db.Column(db.String(20), default='Pending')  # Pending/Accepted/Rejected/Escalated
    priority = db.Column(db.Integer, default=1)  # 1=highest priority
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    responded_at = db.Column(db.DateTime)
    escalated_at = db.Column(db.DateTime)
    
    # Relationships
    requesting_hospital = db.relationship('Hospital', foreign_keys=[requesting_hospital_id])
    target_hospital = db.relationship('Hospital', foreign_keys=[target_hospital_id])
    patient = db.relationship('Admission')
    responses = db.relationship('ReferralResponse', back_populates='referral_request')
    
    @property
    def time_since_created(self):
        """Get time elapsed since referral was created"""
        return (datetime.utcnow() - self.created_at).total_seconds() / 60  # in minutes
    
    @property
    def needs_escalation(self):
        """Check if referral needs escalation based on time and priority"""
        if self.status == 'Pending':
            if self.urgency_level == 'High' and self.time_since_created > 5:
                return True
            elif self.urgency_level == 'Medium' and self.time_since_created > 15:
                return True
            elif self.time_since_created > 30:
                return True
        return False

class ReferralResponse(db.Model):
    """Responses to referral requests"""
    __tablename__ = 'referral_responses'
    
    id = db.Column(db.Integer, primary_key=True)
    referral_request_id = db.Column(db.Integer, db.ForeignKey('referral_requests.id'), nullable=False)
    responding_hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    
    # Response details
    response_type = db.Column(db.String(20), nullable=False)  # Accept/Reject/Request_Info
    response_message = db.Column(db.Text)
    available_beds = db.Column(db.Integer)
    estimated_arrival_time = db.Column(db.String(50))  # "30 minutes", "2 hours"
    
    # Contact details of responding person
    responder_name = db.Column(db.String(100))
    responder_phone = db.Column(db.String(20))
    responder_email = db.Column(db.String(120))
    
    # Timestamps
    responded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    referral_request = db.relationship('ReferralRequest', back_populates='responses')
    responding_hospital = db.relationship('Hospital')
    
    def __repr__(self):
        return f"<ReferralResponse(id={self.id}, type={self.response_type})>"

class PatientTransfer(db.Model):
    """Patient transfer tracking between hospitals"""
    __tablename__ = 'patient_transfers'
    
    id = db.Column(db.Integer, primary_key=True)
    referral_request_id = db.Column(db.Integer, db.ForeignKey('referral_requests.id'), nullable=False)
    
    # Transfer details
    from_hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    to_hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    
    # Patient information
    patient_name = db.Column(db.String(100), nullable=False)
    patient_age = db.Column(db.Integer)
    patient_gender = db.Column(db.String(10))
    primary_diagnosis = db.Column(db.String(255))
    urgency_level = db.Column(db.String(20), default='Medium')  # High/Medium/Low
    special_requirements = db.Column(db.Text)
    
    # Transfer status
    status = db.Column(db.String(20), default='En Route')  # 'En Route' or 'Admitted'
    
    # Timestamps
    transfer_initiated_at = db.Column(db.DateTime, default=datetime.utcnow)
    en_route_at = db.Column(db.DateTime, default=datetime.utcnow)
    admitted_at = db.Column(db.DateTime)
    
    # Contact information
    contact_name = db.Column(db.String(100))
    contact_phone = db.Column(db.String(20))
    contact_email = db.Column(db.String(120))
    
    # Notes and updates
    transfer_notes = db.Column(db.Text)
    arrival_notes = db.Column(db.Text)
    
    # Relationships
    referral_request = db.relationship('ReferralRequest', backref='transfers')
    from_hospital = db.relationship('Hospital', foreign_keys=[from_hospital_id])
    to_hospital = db.relationship('Hospital', foreign_keys=[to_hospital_id])
    
    @property
    def local_transfer_initiated_at(self):
        """Get transfer initiated time in local timezone"""
        return to_local_time(self.transfer_initiated_at)
    
    @property
    def local_en_route_at(self):
        """Get en route time in local timezone"""
        return to_local_time(self.en_route_at)
    
    @property
    def local_admitted_at(self):
        """Get admitted time in local timezone"""
        return to_local_time(self.admitted_at) if self.admitted_at else None
    
    @property
    def time_since_en_route(self):
        """Get time since patient went en route"""
        if self.status == 'En Route':
            return datetime.utcnow() - self.en_route_at
        return None
    
    @property
    def transfer_duration(self):
        """Get total transfer duration if completed"""
        if self.admitted_at:
            return self.admitted_at - self.transfer_initiated_at
        return None
    
    def __repr__(self):
        return f"<PatientTransfer(id={self.id}, status={self.status}, patient={self.patient_name})>"

class HospitalContact(db.Model):
    """Contact information for hospitals"""
    __tablename__ = 'hospital_contacts'
    
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    
    # Contact details
    contact_type = db.Column(db.String(20), nullable=False)  # Emergency/Referral/General
    contact_name = db.Column(db.String(100))
    phone_number = db.Column(db.String(20))
    email = db.Column(db.String(120))
    whatsapp = db.Column(db.String(20))
    
    # Availability
    is_primary = db.Column(db.Boolean, default=False)  # Primary contact for referrals
    is_active = db.Column(db.Boolean, default=True)
    preferred_contact_method = db.Column(db.String(20))  # SMS/Call/Email/WhatsApp
    
    # Response time tracking
    avg_response_time = db.Column(db.Float)  # in minutes
    last_response_time = db.Column(db.DateTime)
    
    # Relationships
    hospital = db.relationship('Hospital', backref='contacts')
    
    def __repr__(self):
        return f"<HospitalContact {self.contact_name} ({self.contact_type})>"