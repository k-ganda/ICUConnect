from flask import Blueprint, render_template
from flask_login import current_user, login_required
from app.models import User

bp = Blueprint('main', __name__)

@bp.route('/')
@login_required
def home():
    return render_template('auth/login.html')

@bp.route('/hospital/<int:hospital_id>')
@login_required
def hospital_dashboard(hospital_id):
    
    return f"Hospital {hospital_id} Dashboard"

@bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_authenticated or current_user.privilege_level not in ['super', 'hospital']:
        abort(403)
    
    pending_users = User.query.filter_by(
        is_approved=False,
        hospital_id=current_user.hospital_id
    ).all()
    
    return render_template('admin/dashboard.html', pending_users=pending_users)