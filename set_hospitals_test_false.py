#!/usr/bin/env python3
"""
Flask shell script to set specific hospitals to is_test=False
Run this with: flask shell < set_hospitals_test_false.py
"""

from app import create_app, db
from app.models import Hospital

# Create app context
app = create_app()

with app.app_context():
    # List of hospitals to set to is_test=False
    hospital_names = [
        "System Hospital",
        "JOOTRH",
        "Nightingale",
        "Koluoch Health Centre",
        "Hospital A",
        "Khan Hospital Kisumu",
        "St.Newreb",
        "Hospital B",
        "Hospital_C",
        "Hospital D",
        "Hospital E",
        "Hospital F",
        "Hospital G",
        "Hospital H"
    ]
    
    print("Setting hospitals to is_test=False...")
    
    for hospital_name in hospital_names:
        hospital = Hospital.query.filter_by(name=hospital_name).first()
        if hospital:
            hospital.is_test = False
            print(f"✓ Updated {hospital_name}")
        else:
            print(f"✗ Hospital '{hospital_name}' not found")
    
    # Commit changes
    try:
        db.session.commit()
        print("\n✅ Successfully updated all found hospitals!")
    except Exception as e:
        db.session.rollback()
        print(f"\n❌ Error committing changes: {e}")
    
    # Verify changes
    print("\nVerification - Hospitals with is_test=False:")
    updated_hospitals = Hospital.query.filter_by(is_test=False).all()
    for hospital in updated_hospitals:
        print(f"  - {hospital.name}")
    
    print(f"\nTotal hospitals with is_test=False: {len(updated_hospitals)}") 