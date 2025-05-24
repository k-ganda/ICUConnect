from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required
from app.models import User

bp = Blueprint('main', __name__)

@bp.route('/')
@login_required
def home():
    return redirect(url_for('main.dashboard'))

@bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_authenticated or not hasattr(current_user, 'privilege_level'):
        return redirect(url_for('auth.login'))
    
    # Get pending users based on admin type
    if current_user.privilege_level == 'super':
        pending_users = User.query.filter_by(is_approved=False).all()
    else:
        pending_users = User.query.filter_by(
            is_approved=False,
            hospital_id=current_user.hospital_id
        ).all()
    
    return render_template('admin/dashboard.html', pending_users=pending_users)