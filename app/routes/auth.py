from flask import Blueprint, render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, current_user
from app.models import Hospital, User, Admin
from app import db
import logging

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
                if not user.is_approved:
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
                                    hospitals=Hospital.query.filter_by(is_active=True).all(),
                                    show_error_modal=True,
                                    error_message=error_msg)

            # Validate hospital
            hospital = Hospital.query.get(required['hospital'])
            if not hospital:
                error_msg = "Invalid hospital selected"
                logger.error(error_msg)
                return render_template('auth/signup.html',
                                    hospitals=Hospital.query.filter_by(is_active=True).all(),
                                    show_error_modal=True,
                                    error_message=error_msg)

            # Check for duplicate email (User and Admin tables)
            if User.query.filter_by(email=required['email']).first() or \
               Admin.query.filter_by(email=required['email']).first():
                error_msg = "Email already registered"
                logger.warning(error_msg)
                return render_template('auth/signup.html',
                                    hospitals=Hospital.query.filter_by(is_active=True).all(),
                                    show_error_modal=True,
                                    error_message=error_msg)

            # Create user
            new_user = User(
                email=required['email'],
                name=required['name'],
                hospital_id=required['hospital'],
                employee_id=required['employee_id'],
                is_approved=False
            )
            new_user.set_password(required['password'])

            db.session.add(new_user)
            db.session.commit()

            logger.info(f"User created: {new_user.email}")
            return render_template('auth/signup.html',
                                hospitals=Hospital.query.filter_by(is_active=True).all(),
                                show_success_modal=True)

        except Exception as e:
            db.session.rollback()
            logger.exception(f"Signup failed: {str(e)}")
            return render_template('auth/signup.html',
                                hospitals=Hospital.query.filter_by(is_active=True).all(),
                                show_error_modal=True,
                                error_message=f"Server error: {str(e)}")

    # GET request
    return render_template('auth/signup.html',
                         hospitals=Hospital.query.filter_by(is_active=True).all(),
                         show_success_modal=False,
                         show_error_modal=False)

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))