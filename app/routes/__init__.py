from flask import Blueprint, render_template

pages_bp = Blueprint('pages', __name__)

@pages_bp.route('/')
def index():
    return render_template('index.html')

@pages_bp.route('/login')
def login():
    return render_template('login.html')

@pages_bp.route('/register')
def register():
    return render_template('register.html')

@pages_bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@pages_bp.route('/profile')
def profile():
    return render_template('profile.html')

@pages_bp.route('/forum')
def forum():
    return render_template('forum.html')

@pages_bp.route('/groups')
def groups():
    return render_template('groups.html')

@pages_bp.route('/messages')
def messages():
    return render_template('messages.html')

@pages_bp.route('/documents')
def documents():
    return render_template('documents.html')

@pages_bp.route('/search')
def search():
    return render_template('search.html')

@pages_bp.route('/global')
def global_mode():
    return render_template('global.html')

@pages_bp.route('/career')
def career():
    return render_template('career.html')