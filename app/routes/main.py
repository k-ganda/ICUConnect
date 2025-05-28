from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required, logout_user
from app.models import User, Admin

bp = Blueprint('main', __name__)

@bp.route('/')
def home():
    return redirect(url_for('auth.login'))


@bp.route('/dashboard')
@login_required
def dashboard():
    if isinstance(current_user, Admin):
        # Base query for pending users
        pending_query = User.query.filter_by(is_approved=False)
        
        # Filter by hospital if not super admin
        if current_user.privilege_level != 'super':
            pending_query = pending_query.filter_by(hospital_id=current_user.hospital_id)
        
        # Add sorting by request date if you have that field
        # pending_query = pending_query.order_by(User.created_at.desc())
        
        pending_users = pending_query.all()
        
        # Get hospital name for the dashboard title
        hospital_name = current_user.hospital.name if current_user.privilege_level == 'hospital' else "All Hospitals"
        
        return render_template('admin/dashboard.html',
                            pending_users=pending_users,
                            hospital_name=hospital_name,
                            current_user=current_user)
    
    # For regular users
    return render_template('user/dashboard.html',
                         current_user=current_user)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))