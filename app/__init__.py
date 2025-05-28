from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import os

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Configure database URI to point explicitly to instance folder
    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(app.instance_path, 'icuconnect.db') + '?check_same_thread=False',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,
            'pool_recycle': 3600,
        }
    )

    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)
    migrate = Migrate(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Add teardown appcontext
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()

    with app.app_context():
        # Register blueprints
        from app.routes.main import bp as main_bp
        from app.routes.auth import auth_bp
        from app.routes.admin import admin_bp
        from app.routes.user_routes import user_bp
        
        app.register_blueprint(main_bp)
        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(admin_bp, url_prefix='/admin')
        app.register_blueprint(user_bp, url_prefix='/user')
        
        # Initialize database
        _initialize_database()

    return app

def _initialize_database():
    """Initialize database with proper error handling"""
    from app.models import Hospital, Admin
    
    try:
        # Create tables if they don't exist
        db.create_all()
        
        # Create first admin if none exists
        if not Admin.query.first():
            hospital = Hospital(name="System Hospital", verification_code="SYSADMIN")
            db.session.add(hospital)
            db.session.commit()
            
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
        print(f"Database initialization error: {str(e)}")
        raise