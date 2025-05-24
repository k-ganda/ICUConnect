from datetime import datetime
from flask import Blueprint, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import User, Admin
from app import db

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/approve-user/<int:user_id>')
@login_required
def approve_user(user_id):
    # Verify current user is an admin (Admin model)
    if not isinstance(current_user, Admin):
        flash('Unauthorized access - admin privileges required', 'danger')
        return redirect(url_for('auth.login'))
    
    # Get user to approve
    user = User.query.get_or_404(user_id)
    
    # Verify admin has permission for this hospital
    if current_user.privilege_level == 'hospital' and current_user.hospital_id != user.hospital_id:
        flash('You can only approve users from your own hospital', 'danger')
        return redirect(url_for('main.dashboard'))
    
    try:
        # Approve the user with tracking
        user.is_approved = True
        user.admin_id = current_user.id  # Using admin_id field from your model
        user.approval_date = datetime.utcnow()
        db.session.commit()
        
        flash(f'Successfully approved {user.email}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error approving user: {str(e)}', 'danger')
    
    return redirect(url_for('main.dashboard'))