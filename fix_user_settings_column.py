#!/usr/bin/env python3
"""Script to add notification_duration column to user_settings table"""

import psycopg2
from psycopg2 import sql

# Database connection parameters
DB_PARAMS = {
    'host': 'localhost',
    'database': 'icuconnectdb',
    'user': 'flaskuser',
    'password': 'icu123'
}

def add_user_settings_notification_duration():
    """Add notification_duration column to user_settings table"""
    try:
        # Connect to the database
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
        
        # Add the column if it doesn't exist
        cursor.execute("""
            ALTER TABLE user_settings 
            ADD COLUMN IF NOT EXISTS notification_duration INTEGER DEFAULT 120;
        """)
        
        # Update existing user settings to have the default value
        cursor.execute("""
            UPDATE user_settings 
            SET notification_duration = 120 
            WHERE notification_duration IS NULL;
        """)
        
        # Commit the changes
        conn.commit()
        
        # Verify the change
        cursor.execute("SELECT user_id, notification_duration FROM user_settings LIMIT 5;")
        user_settings = cursor.fetchall()
        
        print("Successfully added notification_duration column to user_settings table")
        print("Sample user notification durations:")
        for setting in user_settings:
            print(f"  User {setting[0]}: {setting[1]} seconds")
            
    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    add_user_settings_notification_duration() 