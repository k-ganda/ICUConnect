import os
import sys

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import db, create_app
from app.models import Hospital
import pytz

def update_hospital_timezones():
    """Update all hospital records to have the default timezone if None."""
    app = create_app()
    with app.app_context():
        # First, update any None timezones
        hospitals = Hospital.query.filter(Hospital.timezone.is_(None)).all()
        for hospital in hospitals:
            hospital.timezone = 'Africa/Kigali'
        
        # Then, ensure all hospitals have a valid timezone
        all_hospitals = Hospital.query.all()
        for hospital in all_hospitals:
            if not hospital.timezone or hospital.timezone not in pytz.all_timezones:
                hospital.timezone = 'Africa/Kigali'
        
        db.session.commit()
        print(f"Updated {len(hospitals)} hospitals with default timezone")
        print("Verified all hospitals have valid timezone settings")

if __name__ == '__main__':
    update_hospital_timezones() 