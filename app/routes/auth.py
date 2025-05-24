from flask import Blueprint, render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user
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
        
        # Try admin first
        admin = Admin.query.filter_by(email=email).first()
        if admin and admin.check_password(password):
            login_user(admin)
            flash('Admin login successful!', 'success')
            return redirect(url_for('main.dashboard'))
        
        # Then try user
        user = User.query.filter_by(email=email).first()
        if user:
            if not user.is_approved:
                flash('Your account is pending approval', 'warning')
                return redirect(url_for('auth.login'))
            if user.check_password(password):
                login_user(user, remember=False)
                flash('Login successful!', 'success')
                return redirect(url_for('user.dashboard'))
        
        flash('Invalid credentials or unapproved account', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            logger.debug("Form data: %s", request.form)
            
            # Validate required fields
            required = {
                'email': request.form.get('email'),
                'password': request.form.get('password'),
                'name': request.form.get('name'),
                'hospital': request.form.get('hospital'),
                'employee_id': request.form.get('employee_id')
            }
            
            if not all(required.values()):
                missing = [k for k, v in required.items() if not v]
                logger.warning("Missing fields: %s", missing)
                flash(f"Missing required fields: {', '.join(missing)}", 'danger')
                return render_template('auth/signup.html', 
                                    hospitals=Hospital.query.filter_by(is_active=True).all(),
                                    show_success_modal=False)
            
            # Verify hospital exists
            hospital = Hospital.query.get(required['hospital'])
            if not hospital:
                logger.error("Invalid hospital ID: %s", required['hospital'])
                flash("Invalid hospital selection", 'danger')
                return render_template('auth/signup.html', 
                                    hospitals=Hospital.query.filter_by(is_active=True).all(),
                                    show_success_modal=False)
            
            # Check for existing email
            if User.query.filter_by(email=required['email']).first():
                logger.warning("Duplicate email: %s", required['email'])
                flash("Email already registered", 'danger')
                return render_template('auth/signup.html', 
                                    hospitals=Hospital.query.filter_by(is_active=True).all(),
                                    show_success_modal=False)
            
            # Create new user
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
            logger.info("New user created: %s", new_user.email)
            
            # Render with success modal
            return render_template('auth/signup.html',
                                 hospitals=Hospital.query.filter_by(is_active=True).all(),
                                 show_success_modal=True)
            
        except Exception as e:
            db.session.rollback()
            logger.exception("Signup failed")
            flash(f"Signup error: {str(e)}", 'danger')
            return render_template('auth/signup.html', 
                                hospitals=Hospital.query.filter_by(is_active=True).all(),
                                show_success_modal=False)
    
    # GET request
    return render_template('auth/signup.html',
                         hospitals=Hospital.query.filter_by(is_active=True).all(),
                         show_success_modal=False)

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))