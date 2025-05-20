from flask import Blueprint, render_template

bp = Blueprint('main', __name__)

@bp.route('/')
def home():
    return render_template('auth/login.html')

@bp.route('/login')
def login():
    return render_template('auth/login.html')

@bp.route('/signup')
def signup():
    return render_template('auth/signup.html')

@bp.route('/test')
def test():
    return "THIS IS A TEST ROUTE"