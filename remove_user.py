#!/usr/bin/env python3
"""
Flask shell script to remove a user by email.
Usage: python remove_user.py
"""

from app import create_app, db
from app.models import User, UserSettings

def remove_user_by_email(email):
    """Remove a user and their settings by email address."""
    app = create_app()
    
    with app.app_context():
        try:
            # Find the user by email
            user = User.query.filter_by(email=email).first()
            
            if not user:
                print(f"❌ User with email '{email}' not found in the database.")
                return False
            
            print(f"🔍 Found user: {user.name} (ID: {user.id})")
            print(f"   Email: {user.email}")
            print(f"   Hospital ID: {user.hospital_id}")
            print(f"   Role: {user.role}")
            print(f"   Employee ID: {user.employee_id}")
            print(f"   Is Approved: {user.is_approved}")
            print(f"   Is Verified: {user.is_verified}")
            
            # Check if user has settings
            user_settings = UserSettings.query.filter_by(user_id=user.id).first()
            if user_settings:
                print(f"   Has user settings: Yes")
            else:
                print(f"   Has user settings: No")
            
            # Confirm deletion
            confirm = input(f"\n⚠️  Are you sure you want to delete user '{email}'? (yes/no): ")
            
            if confirm.lower() in ['yes', 'y']:
                # Delete user settings first (if exists)
                if user_settings:
                    db.session.delete(user_settings)
                    print("   ✅ Deleted user settings")
                
                # Delete the user
                db.session.delete(user)
                db.session.commit()
                
                print(f"✅ Successfully deleted user '{email}' from the database.")
                return True
            else:
                print("❌ Deletion cancelled by user.")
                return False
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error deleting user: {str(e)}")
            return False

if __name__ == '__main__':
    email_to_remove = 'kateamimo@gmail.com'
    print(f"🚀 Starting user removal process for: {email_to_remove}")
    print("=" * 60)
    
    success = remove_user_by_email(email_to_remove)
    
    if success:
        print("\n🎉 User removal completed successfully!")
    else:
        print("\n💥 User removal failed or was cancelled.")
    
    print("=" * 60) 