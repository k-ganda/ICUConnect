from functools import wraps
from flask import Blueprint, abort, redirect, render_template, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from app.models import User, Admin
from app import db

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not isinstance(current_user, Admin):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    pending_users = User.query.filter_by(
        hospital_id=current_user.hospital_id,
        is_approved=False
    ).all()
    return render_template('admin/dashboard.html', pending_users=pending_users)

@admin_bp.route('/approve-user/<int:user_id>')
@login_required
@admin_required
def approve_user(user_id):
    user = User.query.get_or_404(user_id)
    if current_user.privilege_level == 'hospital' and current_user.hospital_id != user.hospital_id:
        flash('You can only approve users from your own hospital', 'danger')
        return redirect(url_for('admin.dashboard'))

    try:
        user.is_approved = True
        user.admin_id = current_user.id
        user.approval_date = datetime.utcnow()
        db.session.commit()
        flash(f'Successfully approved {user.email}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error approving user: {e}', 'danger')

    return redirect(url_for('admin.dashboard'))
