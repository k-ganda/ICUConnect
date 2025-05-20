from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key-here'

    from app.routes import bp
    app.register_blueprint(bp)

    return app