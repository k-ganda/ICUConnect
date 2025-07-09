from datetime import datetime, date
import pytz
from flask import g
from flask_login import current_user
from flask_mail import Message
from flask import current_app

def get_local_timezone():
    """Get the local timezone based on the hospital's location"""
    if hasattr(g, 'hospital') and g.hospital:
        return g.hospital.get_timezone()
    # Fallback to Rwanda timezone if no hospital context
    return pytz.timezone('Africa/Kigali')

def to_local_time(utc_time, hospital=None):
    """Convert UTC time to local time"""
    if utc_time is None:
        return None
    if isinstance(utc_time, date) and not isinstance(utc_time, datetime):
        # If it's a date object, convert to datetime at midnight UTC
        utc_time = datetime.combine(utc_time, datetime.min.time())
    if utc_time.tzinfo is None:
        utc_time = pytz.UTC.localize(utc_time)
    timezone = hospital.get_timezone() if hospital else get_local_timezone()
    return utc_time.astimezone(timezone)

def to_utc_time(local_time, hospital=None):
    """Convert local time to UTC time"""
    if local_time is None:
        return None
    if isinstance(local_time, date) and not isinstance(local_time, datetime):
        # If it's a date object, convert to datetime at midnight local time
        local_time = datetime.combine(local_time, datetime.min.time())
    if local_time.tzinfo is None:
        timezone = hospital.get_timezone() if hospital else get_local_timezone()
        local_time = timezone.localize(local_time)
    return local_time.astimezone(pytz.UTC)

def get_current_local_time(hospital=None):
    """Get current time in local timezone"""
    timezone = hospital.get_timezone() if hospital else get_local_timezone()
    return datetime.now(timezone)

def get_current_utc_time():
    """Get current time in UTC"""
    return datetime.now(pytz.UTC)

def local_date_to_utc(local_date, hospital=None):
    """Convert a local date to UTC datetime at midnight"""
    if local_date is None:
        return None
    timezone = hospital.get_timezone() if hospital else get_local_timezone()
    local_dt = datetime.combine(local_date, datetime.min.time())
    return to_utc_time(local_dt, hospital)

def send_email(subject, recipients, body, html=None):
    """Send an email using Flask-Mail."""
    from app import mail  # Import here to avoid circular import
    from flask_mail import Message
    msg = Message(subject, recipients=recipients, body=body, html=html)
    mail.send(msg) 