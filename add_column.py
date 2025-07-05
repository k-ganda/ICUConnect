#!/usr/bin/env python3
"""Script to add notification_duration column to hospitals table"""

from app import create_app, db
from app.models import Hospital

app = create_app()

with app.app_context():
    try:
        # Add the column if it doesn't exist
        db.engine.execute("ALTER TABLE hospitals ADD COLUMN IF NOT EXISTS notification_duration INTEGER DEFAULT 120;")
        print("Successfully added notification_duration column to hospitals table")
        
        # Update existing hospitals to have the default value
        db.engine.execute("UPDATE hospitals SET notification_duration = 120 WHERE notification_duration IS NULL;")
        print("Updated existing hospitals with default notification duration")
        
        # Verify the change
        hospitals = Hospital.query.all()
        for hospital in hospitals:
            print(f"Hospital: {hospital.name}, Notification Duration: {hospital.notification_duration}")
            
    except Exception as e:
        print(f"Error: {e}")
        db.session.rollback() 