from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from datetime import datetime
import os
from app.utils import get_current_local_time, to_local_time

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Configure database URI to point explicitly to instance folder
    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI='postgresql://flaskuser:icu123@localhost/icuconnectdb',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': 10,
            'max_overflow': 20,
            'pool_pre_ping': True,
            'pool_recycle': 3600
        }
    )
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Add teardown appcontext
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()
        
    @app.context_processor
    def inject_user_data():
        """Makes user data available in all templates"""
        if current_user.is_authenticated and hasattr(current_user, 'get_type'):
            return {
                'current_user_type': current_user.get_type(),
                'current_user_hospital': current_user.get_hospital()
            }
        return {}

    with app.app_context():
        # Register blueprints
        from app.routes.main import bp as main_bp
        from app.routes.auth import auth_bp
        from app.routes.admin import admin_bp
        from app.routes.user_routes import user_bp
        from app.routes.admission_routes import admission_bp
        from app.routes.discharge_routes import discharge_bp
        from app.routes.prediction_routes import prediction_bp
        
        app.register_blueprint(main_bp)
        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(admin_bp, url_prefix='/admin')
        app.register_blueprint(user_bp, url_prefix='/user')
        app.register_blueprint(admission_bp, url_prefix='/admissions')
        app.register_blueprint(discharge_bp, url_prefix='/discharges')
        app.register_blueprint(prediction_bp, url_prefix='/api')
        
        # Global context processor for all templates
        @app.context_processor
        def inject_globals():
            def get_greeting():
                hour = get_current_local_time().hour
                if hour < 12:
                    return 'morning'
                elif hour < 18:
                    return 'afternoon'
                return 'evening'

            def current_datetime():
                return get_current_local_time().strftime("%A, %B %d, %Y, %I:%M:%S %p")

            return dict(get_greeting=get_greeting, current_datetime=current_datetime)
        
        # Initialize database
        _initialize_database(app)

    return app

def _initialize_database(app, reset=False):
    """Initialize or update the PostgreSQL database."""
    from flask_migrate import init, migrate, upgrade
    from app.models import Hospital, Admin
    import shutil
    import os

    try:
        # Migration setup (same as before)
        migrations_path = os.path.join(os.getcwd(), 'migrations')
        if reset and os.path.exists(migrations_path):
            shutil.rmtree(migrations_path)

        if not os.path.exists(migrations_path):
            init(directory=migrations_path)

        migrate(message='Initial migration', directory=migrations_path)
        upgrade(directory=migrations_path)

        # Create tables
        db.create_all()

        # Check if system hospital exists before creating
        if not Hospital.query.filter_by(name="System Hospital").first():
            hospital = Hospital(name="System Hospital", verification_code="SYSADMIN")
            db.session.add(hospital)
            db.session.commit()

            # Only create admin if it doesn't exist
            if not Admin.query.first():
                admin = Admin(
                    hospital_id=hospital.id,
                    email="admin@icuconnect.com",
                    privilege_level="super"
                )
                admin.set_password("temp1234")
                db.session.add(admin)
                db.session.commit()

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Database initialization error: {str(e)}")
        raise