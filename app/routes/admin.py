from functools import wraps
from flask import Blueprint, abort, redirect, render_template, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from app.models import User, Admin, Bed, Hospital  # Add Hospital import
from app import db
from app.utils import send_email
import secrets

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
    page = request.args.get('page', 1, type=int)
    if current_user.privilege_level == 'super':
        pending_users = User.query.filter_by(is_approved=False).order_by(User.created_at.desc()).paginate(page=page, per_page=10)
    else:
        pending_users = User.query.filter_by(hospital_id=current_user.hospital_id, is_approved=False).order_by(User.created_at.desc()).paginate(page=page, per_page=10)
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
        # Send approval email to user
        try:
            send_email(
                subject="Your ICUConnect Account Has Been Approved!",
                recipients=[user.email],
                body=f"""Hello {user.name},\n\nYour account has been approved by your hospital admin. You can now log in to ICUConnect.\n\nThank you!\n\n- ICUConnect Team"""
            )
        except Exception as e:
            flash(f'User approved, but failed to send approval email: {e}', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Error approving user: {e}', 'danger')

    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/beds')
@login_required
@admin_required
def beds():
    page = request.args.get('page', 1, type=int)
    if current_user.privilege_level == 'super':
        beds = Bed.query.join(Hospital).order_by(Bed.id.desc()).paginate(page=page, per_page=10)
        hospitals = Hospital.query.order_by(Hospital.name).all()
    else:
        beds = Bed.query.filter_by(hospital_id=current_user.hospital_id).order_by(Bed.id.desc()).paginate(page=page, per_page=10)
        hospitals = None
    return render_template('admin/beds.html', beds=beds, hospitals=hospitals)

def get_next_bed_number(hospital_id):
    """Get the next available bed number for a hospital"""
    max_bed = db.session.query(db.func.max(Bed.bed_number)).filter_by(hospital_id=hospital_id).scalar()
    return (max_bed or 0) + 1

@admin_bp.route('/beds/add', methods=['POST'])
@login_required
@admin_required
def add_bed():
    error = None
    if current_user.privilege_level == 'super':
        hospital_id = request.form.get('hospital_id')
    else:
        hospital_id = current_user.hospital_id
    
    bed_number = request.form.get('bed_number')
    bed_type = request.form.get('bed_type', 'ICU')
    
    if not hospital_id:
        error = 'Hospital is required.'
    elif not bed_number:
        # Auto-assign bed number if not provided
        bed_number = get_next_bed_number(int(hospital_id))
    else:
        # Check if manually entered bed number already exists
        existing_bed = Bed.query.filter_by(hospital_id=hospital_id, bed_number=bed_number).first()
        if existing_bed:
            error = f'Bed number {bed_number} already exists for this hospital.'
    
    if error:
        # Re-render the beds page with the error
        page = 1
        if current_user.privilege_level == 'super':
            beds = Bed.query.join(Hospital).order_by(Bed.created_at.desc()).paginate(page=page, per_page=10)
            hospitals = Hospital.query.order_by(Hospital.name).all()
        else:
            beds = Bed.query.filter_by(hospital_id=current_user.hospital_id).order_by(Bed.created_at.desc()).paginate(page=page, per_page=10)
            hospitals = None
        return render_template('admin/beds.html', beds=beds, hospitals=hospitals, bed_error=error)
    
    try:
        bed = Bed(hospital_id=hospital_id, bed_number=bed_number, bed_type=bed_type)
        db.session.add(bed)
        db.session.commit()
        flash(f'Bed {bed_number} added successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding bed: {e}', 'danger')
    return redirect(url_for('admin.beds'))

@admin_bp.route('/beds/remove/<int:bed_id>', methods=['POST', 'GET'])
@login_required
@admin_required
def remove_bed(bed_id):
    bed = Bed.query.get_or_404(bed_id)
    
    # Super admins can remove any bed, hospital admins can only remove from their hospital
    if current_user.privilege_level != 'super' and bed.hospital_id != current_user.hospital_id:
        flash('You can only remove beds from your own hospital.', 'danger')
        return redirect(url_for('admin.beds'))
    
    # Check if bed is occupied
    if bed.is_occupied:
        flash(f'Cannot remove bed {bed.bed_number} - it is currently occupied.', 'warning')
        return redirect(url_for('admin.beds'))
    
    try:
        db.session.delete(bed)
        db.session.commit()
        flash(f'Bed {bed.bed_number} removed successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error removing bed: {e}', 'danger')
    return redirect(url_for('admin.beds'))

@admin_bp.route('/admins')
@login_required
@admin_required
def admins():
    page = request.args.get('page', 1, type=int)
    if current_user.privilege_level == 'super':
        admins = Admin.query.order_by(Admin.created_at.desc()).paginate(page=page, per_page=10)
        hospitals = Hospital.query.order_by(Hospital.name).all()
    else:
        admins = Admin.query.filter_by(hospital_id=current_user.hospital_id).order_by(Admin.created_at.desc()).paginate(page=page, per_page=10)
        hospitals = None
    return render_template('admin/admins.html', admins=admins, hospitals=hospitals)

@admin_bp.route('/admins/add', methods=['POST'])
@login_required
@admin_required
def add_admin():
    from flask import request, url_for
    email = request.form.get('email')
    name = request.form.get('name')
    hospital_id = request.form.get('hospital_id')
    # Remove password from form (no longer needed)
    if not email or not name or (current_user.privilege_level == 'super' and not hospital_id):
        flash('Email, name, and hospital are required.', 'danger')
        return redirect(url_for('admin.admins'))
    try:
        if current_user.privilege_level == 'super':
            admin = Admin(email=email, hospital_id=int(hospital_id), name=name)
        else:
            admin = Admin(email=email, hospital_id=current_user.hospital_id, name=name)
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        admin.reset_token = reset_token
        db.session.add(admin)
        db.session.commit()
        flash(f'Admin {email} added successfully.', 'success')
        # Send notification email with reset link
        try:
            from app.models import Hospital
            hospital = Hospital.query.get(admin.hospital_id)
            reset_url = url_for('admin.reset_password', token=reset_token, _external=True)
            send_email(
                subject="You have been added as an ICUConnect Admin",
                recipients=[admin.email],
                body=f"""Hello {admin.name},\n\nYou have been added as an admin for the hospital: {hospital.name}.\n\nTo set your password, please click the link below:\n{reset_url}\n\nIf you did not expect this, please ignore this email.\n\n- ICUConnect Team"""
            )
        except Exception as e:
            flash(f'Admin added, but failed to send notification email: {e}', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding admin: {e}', 'danger')
    return redirect(url_for('admin.admins'))

@admin_bp.route('/admins/remove/<int:admin_id>', methods=['POST', 'GET'])
@login_required
@admin_required
def remove_admin(admin_id):
    admin = Admin.query.get_or_404(admin_id)
    
    # Super admins can remove any admin, hospital admins can only remove from their hospital
    if current_user.privilege_level != 'super' and admin.hospital_id != current_user.hospital_id:
        flash('You can only remove admins from your own hospital.', 'danger')
        return redirect(url_for('admin.admins'))
    
    # Prevent removing yourself
    if admin.id == current_user.id:
        flash('You cannot remove yourself.', 'danger')
        return redirect(url_for('admin.admins'))
    
    try:
        # Check if admin has any approved users (optional: prevent removal if they do)
        approved_users = User.query.filter_by(admin_id=admin.id).count()
        if approved_users > 0:
            flash(f'Cannot remove admin {admin.email} - they have {approved_users} approved users. Please reassign users first.', 'warning')
            return redirect(url_for('admin.admins'))
        
        db.session.delete(admin)
        db.session.commit()
        flash(f'Admin {admin.email} removed successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error removing admin: {e}', 'danger')
    return redirect(url_for('admin.admins'))

# Super admin only: hospital management
@admin_bp.route('/hospitals')
@login_required
@admin_required
def hospitals():
    if current_user.privilege_level != 'super':
        abort(403)
    page = request.args.get('page', 1, type=int)
    hospitals = Hospital.query.order_by(Hospital.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('admin/hospitals.html', hospitals=hospitals)

@admin_bp.route('/hospitals/add', methods=['POST'])
@login_required
@admin_required
def add_hospital():
    if current_user.privilege_level != 'super':
        abort(403)
    from flask import request
    name = request.form.get('name')
    verification_code = request.form.get('verification_code')
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    level = request.form.get('level')

    if not name or not verification_code or not latitude or not longitude or not level:
        flash('All fields are required.', 'danger')
        return redirect(url_for('admin.hospitals'))
    try:
        hospital = Hospital(
            name=name,
            verification_code=verification_code,
            latitude=float(latitude),
            longitude=float(longitude),
            level=int(level)
        )
        db.session.add(hospital)
        db.session.commit()
        flash(f'Hospital {name} added successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding hospital: {e}', 'danger')
    return redirect(url_for('admin.hospitals'))

@admin_bp.route('/hospitals/remove/<int:hospital_id>', methods=['POST', 'GET'])
@login_required
@admin_required
def remove_hospital(hospital_id):
    if current_user.privilege_level != 'super':
        abort(403)
    hospital = Hospital.query.get_or_404(hospital_id)
    try:
        db.session.delete(hospital)
        db.session.commit()
        flash(f'Hospital {hospital.name} removed successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error removing hospital: {e}', 'danger')
    return redirect(url_for('admin.hospitals'))

@admin_bp.route('/hospitals/assign-admin', methods=['POST'])
@login_required
@admin_required
def assign_admin():
    if current_user.privilege_level != 'super':
        abort(403)
    from flask import request
    admin_id = request.form.get('admin_id')
    hospital_id = request.form.get('hospital_id')
    admin = Admin.query.get(admin_id)
    hospital = Hospital.query.get(hospital_id)
    if not admin or not hospital:
        flash('Invalid admin or hospital.', 'danger')
        return redirect(url_for('admin.hospitals'))
    try:
        admin.hospital_id = hospital.id
        db.session.commit()
        flash(f'Admin {admin.email} assigned to {hospital.name}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error assigning admin: {e}', 'danger')
    return redirect(url_for('admin.hospitals'))

@admin_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    from app.models import Admin
    admin = Admin.query.filter_by(reset_token=token).first()
    error_message = None
    if not admin:
        flash('Invalid or expired password reset link.', 'danger')
        return redirect(url_for('admin.admins'))
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        import re
        if not password or not confirm_password:
            error_message = 'Please fill in all fields.'
        elif password != confirm_password:
            error_message = 'Passwords do not match.'
        elif len(password) < 8 or not re.search(r'[A-Z]', password) or not re.search(r'[a-z]', password) or not re.search(r'\d', password) or not re.search(r'[^A-Za-z0-9]', password):
            error_message = 'Password must be at least 8 characters and include uppercase, lowercase, number, and special character.'
        else:
            admin.set_password(password)
            admin.reset_token = None
            db.session.commit()
            flash('Password set successfully! You can now log in.', 'success')
            # Send confirmation email
            try:
                send_email(
                    subject="ICUConnect Password Reset Successful",
                    recipients=[admin.email],
                    body=f"Hello {admin.name},\n\nYour password was reset successfully. You can now log in with your new password.\n\n- ICUConnect Team"
                )
            except Exception as e:
                flash(f'Password reset, but failed to send confirmation email: {e}', 'warning')
            return redirect(url_for('auth.login'))
    return render_template('admin/reset_password.html', token=token, error_message=error_message)
