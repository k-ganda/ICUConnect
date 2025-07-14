import re
from flask import Blueprint, render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, current_user
from app.models import Hospital, User, Admin
from app import db
import logging
from app.utils import send_email
import secrets

auth_bp = Blueprint('auth', __name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        errors = {}

        admin = Admin.query.filter_by(email=email).first()
        user = User.query.filter_by(email=email).first()

        if not admin and not user:
            errors['email'] = "Email does not exist"
        else:
            if admin:
                if not admin.check_password(password):
                    errors['password'] = "Incorrect password"
            elif user:
                if not user.is_verified:
                    errors['email'] = "Please verify your email address before logging in."
                elif not user.is_approved:
                    errors['email'] = "Your account is pending approval"
                elif not user.check_password(password):
                    errors['password'] = "Incorrect password"

        if errors:
            # Render the login template with errors and keep email filled in
            return render_template('auth/login.html', errors=errors, email=email)

        # Login successful, redirect accordingly
        if admin:
            login_user(admin)
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('user.dashboard'))

    # GET request — show login form empty
    return render_template('auth/login.html', errors=None, email='')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            logger.debug(f"Raw form data: {request.form}")

            # Validate and sanitize inputs
            required = {
                'email': request.form.get('email', '').strip(),
                'password': request.form.get('password', '').strip(),
                'name': request.form.get('name', '').strip(),
                'hospital': request.form.get('hospital'),
                'employee_id': request.form.get('employee_id', '').strip()
            }

            # Check for empty fields
            if not all(required.values()):
                missing = [k for k, v in required.items() if not v]
                error_msg = f"Missing required fields: {', '.join(missing)}"
                logger.warning(error_msg)
                return render_template('auth/signup.html',
                                    hospitals=Hospital.query.filter_by(is_active=True, is_test=False).all(),
                                    show_error_modal=True,
                                    error_message=error_msg)

            # General email validation
            def is_valid_email(email):
                pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
                return re.match(pattern, email) is not None
            if not is_valid_email(required['email']):
                error_msg = "Please use a valid email address."
                logger.warning(error_msg)
                return render_template('auth/signup.html',
                                    hospitals=Hospital.query.filter_by(is_active=True, is_test=False).all(),
                                    show_error_modal=True,
                                    error_message=error_msg)

            # Validate hospital
            hospital = Hospital.query.get(required['hospital'])
            if not hospital:
                error_msg = "Invalid hospital selected"
                logger.error(error_msg)
                return render_template('auth/signup.html',
                                    hospitals=Hospital.query.filter_by(is_active=True, is_test=False).all(),
                                    show_error_modal=True,
                                    error_message=error_msg)

            # Check for duplicate email (User and Admin tables)
            if User.query.filter_by(email=required['email']).first() or \
               Admin.query.filter_by(email=required['email']).first():
                error_msg = "Email already registered"
                logger.warning(error_msg)
                return render_template('auth/signup.html',
                                    hospitals=Hospital.query.filter_by(is_active=True, is_test=False).all(),
                                    show_error_modal=True,
                                    error_message=error_msg)

            # Create user with verification token
            verification_token = secrets.token_urlsafe(32)
            new_user = User(
                email=required['email'],
                name=required['name'],
                hospital_id=required['hospital'],
                employee_id=required['employee_id'],
                is_approved=False,
                is_verified=False,
                verification_token=verification_token
            )
            new_user.set_password(required['password'])

            db.session.add(new_user)
            db.session.commit()

            logger.info(f"User created: {new_user.email}")

            # Send verification email
            try:
                verify_url = url_for('auth.verify_email', token=verification_token, _external=True)
                send_email(
                    subject="Verify your ICUConnect email address",
                    recipients=[new_user.email],
                    body=f"""Welcome to ICUConnect, {new_user.name}!\n\nPlease verify your email address by clicking the link below:\n{verify_url}\n\nIf you did not sign up, please ignore this email.\n\n- ICUConnect Team"""
                )
            except Exception as e:
                logger.warning(f"Failed to send verification email: {e}")

            # Notify hospital admin(s) and super admins
            try:
                hospital_admins = Admin.query.filter_by(hospital_id=hospital.id).all()
                super_admins = Admin.query.filter_by(privilege_level='super').all()
                admin_emails = [a.email for a in hospital_admins + super_admins if a.email]
                if admin_emails:
                    send_email(
                        subject="New User Signup Pending Approval",
                        recipients=admin_emails,
                        body=f"""A new user has signed up for your hospital on ICUConnect.\n\nName: {new_user.name}\nEmail: {new_user.email}\nEmployee ID: {new_user.employee_id}\n\nPlease log in to your admin dashboard to review and approve this user.\n\n- ICUConnect System"""
                    )
            except Exception as e:
                logger.warning(f"Failed to notify admin(s): {e}")

            return render_template('auth/signup.html',
                                hospitals=Hospital.query.filter_by(is_active=True, is_test=False).all(),
                                show_success_modal=True)

        except Exception as e:
            db.session.rollback()
            logger.exception(f"Signup failed: {str(e)}")
            return render_template('auth/signup.html',
                                hospitals=Hospital.query.filter_by(is_active=True, is_test=False).all(),
                                show_error_modal=True,
                                error_message=f"Server error: {str(e)}")

    # GET request
    return render_template('auth/signup.html',
                         hospitals=Hospital.query.filter_by(is_active=True, is_test=False).all(),
                         show_success_modal=False,
                         show_error_modal=False)

@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()
    if not user:
        flash('Invalid or expired verification link.', 'danger')
        return redirect(url_for('auth.login'))
    if user.is_verified:
        flash('Email already verified. Please log in.', 'info')
        return redirect(url_for('auth.login'))
    user.is_verified = True
    user.verification_token = None
    db.session.commit()
    flash('Email verified successfully! You can now log in (once approved by admin).', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    from app.models import User, Admin
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash('Please enter your email address.', 'danger')
            return redirect(url_for('auth.forgot_password'))
        user = User.query.filter_by(email=email).first()
        admin = Admin.query.filter_by(email=email).first()
        if not user and not admin:
            flash('If the email exists in our system, a reset link will be sent.', 'info')
            return redirect(url_for('auth.forgot_password'))
        reset_token = secrets.token_urlsafe(32)
        reset_url = None
        if user:
            user.verification_token = reset_token
            db.session.commit()
            reset_url = url_for('auth.reset_password', token=reset_token, _external=True)
        elif admin:
            admin.reset_token = reset_token
            db.session.commit()
            reset_url = url_for('admin.reset_password', token=reset_token, _external=True)
        try:
            send_email(
                subject="ICUConnect Password Reset",
                recipients=[email],
                body=f"""A password reset was requested for your ICUConnect account.\n\nTo reset your password, click the link below:\n{reset_url}\n\nIf you did not request this, please ignore this email.\n\n- ICUConnect Team"""
            )
        except Exception as e:
            flash(f'Failed to send reset email: {e}', 'danger')
            return redirect(url_for('auth.forgot_password'))
        flash('If the email exists in our system, a reset link has been sent to your email.', 'info')
        return redirect(url_for('auth.forgot_password'))
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    from app.models import User
    user = User.query.filter_by(verification_token=token).first()
    error_message = None
    if not user:
        flash('Invalid or expired password reset link.', 'danger')
        return redirect(url_for('auth.login'))
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
            user.set_password(password)
            user.verification_token = None
            db.session.commit()
            flash('Password set successfully! You can now log in.', 'success')
            # Send confirmation email
            try:
                send_email(
                    subject="ICUConnect Password Reset Successful",
                    recipients=[user.email],
                    body=f"Hello {user.name},\n\nYour password was reset successfully. You can now log in with your new password.\n\n- ICUConnect Team"
                )
            except Exception as e:
                flash(f'Password reset, but failed to send confirmation email: {e}', 'warning')
            return redirect(url_for('auth.login'))
    return render_template('admin/reset_password.html', token=token, error_message=error_message)