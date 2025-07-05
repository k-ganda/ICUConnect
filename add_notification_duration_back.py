#!/usr/bin/env python3
"""Script to add notification_duration column back to user_settings table"""

from app import create_app, db
from app.models import UserSettings, Hospital

app = create_app()

with app.app_context():
    try:
        # Add the column if it doesn't exist
        db.engine.execute("ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS notification_duration INTEGER DEFAULT 120;")
        print("Successfully added notification_duration column back to user_settings table")
        
        # Update existing user settings to have the default value
        db.engine.execute("UPDATE user_settings SET notification_duration = 120 WHERE notification_duration IS NULL;")
        print("Updated existing user settings with default notification duration")
        
        # Verify the change
        user_settings = UserSettings.query.all()
        for setting in user_settings:
            print(f"User {setting.user_id}: notification_duration = {setting.notification_duration}")
            
    except Exception as e:
        print(f"Error: {e}")
        db.session.rollback() 