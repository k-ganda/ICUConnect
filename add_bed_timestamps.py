#!/usr/bin/env python3
"""
Script to add created_at timestamps to existing beds.
Usage: python add_bed_timestamps.py
"""

from app import create_app, db
from app.models import Bed
from datetime import datetime

def add_bed_timestamps():
    """Add created_at timestamps to beds that don't have them."""
    app = create_app()
    
    with app.app_context():
        try:
            # Find beds without created_at timestamps
            beds_without_timestamp = Bed.query.filter(Bed.created_at.is_(None)).all()
            
            if not beds_without_timestamp:
                print("✅ All beds already have timestamps.")
                return True
            
            print(f"🔍 Found {len(beds_without_timestamp)} beds without timestamps.")
            
            # Add timestamps to existing beds
            current_time = datetime.utcnow()
            for bed in beds_without_timestamp:
                bed.created_at = current_time
                print(f"   📅 Added timestamp to Bed {bed.bed_number} (Hospital {bed.hospital_id})")
            
            db.session.commit()
            print(f"✅ Successfully added timestamps to {len(beds_without_timestamp)} beds.")
            return True
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error adding timestamps: {str(e)}")
            return False

if __name__ == '__main__':
    print("🚀 Starting bed timestamp update process...")
    print("=" * 60)
    
    success = add_bed_timestamps()
    
    if success:
        print("\n🎉 Bed timestamp update completed successfully!")
    else:
        print("\n💥 Bed timestamp update failed.")
    
    print("=" * 60) 