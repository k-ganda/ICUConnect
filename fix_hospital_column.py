#!/usr/bin/env python3
"""Script to add notification_duration column to hospitals table"""

import psycopg2
from psycopg2 import sql

# Database connection parameters
DB_PARAMS = {
    'host': 'localhost',
    'database': 'icuconnectdb',
    'user': 'flaskuser',
    'password': 'icu123'
}

def add_hospital_notification_duration():
    """Add notification_duration column to hospitals table"""
    try:
        # Connect to the database
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
        
        # Add the column if it doesn't exist
        cursor.execute("""
            ALTER TABLE hospitals 
            ADD COLUMN IF NOT EXISTS notification_duration INTEGER DEFAULT 120;
        """)
        
        # Update existing hospitals to have the default value
        cursor.execute("""
            UPDATE hospitals 
            SET notification_duration = 120 
            WHERE notification_duration IS NULL;
        """)
        
        # Commit the changes
        conn.commit()
        
        # Verify the change
        cursor.execute("SELECT name, notification_duration FROM hospitals;")
        hospitals = cursor.fetchall()
        
        print("Successfully added notification_duration column to hospitals table")
        print("Current hospital notification durations:")
        for hospital in hospitals:
            print(f"  {hospital[0]}: {hospital[1]} seconds")
            
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
    add_hospital_notification_duration() 