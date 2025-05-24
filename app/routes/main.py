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
    # Check if admin (Admin model)
    if isinstance(current_user, Admin):
        if current_user.privilege_level == 'super':
            pending_users = User.query.filter_by(is_approved=False).all()
        else:
            pending_users = User.query.filter_by(
                is_approved=False,
                hospital_id=current_user.hospital_id
            ).all()
        
        return render_template('admin/dashboard.html', 
                            pending_users=pending_users,
                            current_user=current_user)
    
    # For regular users (User model)
    return render_template('user/dashboard.html',
                         current_user=current_user)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))