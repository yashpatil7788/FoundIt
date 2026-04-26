from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, make_response
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
import logging
import models

# Import configuration
from config import (
    SECRET_KEY,
    MAIL_SERVER,
    MAIL_PORT,
    MAIL_USERNAME,
    MAIL_PASSWORD,
    MAIL_USE_TLS,
    MAIL_USE_SSL,
    SESSION_TYPE,
    SESSION_FILE_DIR,
    SESSION_PERMANENT,
)

# Create the Flask app
app = Flask(__name__)
app.secret_key = SECRET_KEY

# Log app startup
logging.basicConfig(level=logging.INFO)
logging.info('FoundIt Flask app starting up...')

# Optional: Check DB connection at startup
try:
    from sqlalchemy import text
    db = models.SessionLocal()
    db.execute(text('SELECT 1'))
    db.close()
    logging.info('Database connection successful.')
except Exception as e:
    logging.error(f'Database connection failed: {e}')

# Original config continues...
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7)
app.config.update(
    MAIL_SERVER=MAIL_SERVER,
    MAIL_PORT=MAIL_PORT,
    MAIL_USERNAME=MAIL_USERNAME,
    MAIL_PASSWORD=MAIL_PASSWORD,
    MAIL_USE_TLS=MAIL_USE_TLS,
    MAIL_USE_SSL=MAIL_USE_SSL
)

# Initialize Flask-Mail via extensions
from extensions import mail
mail.init_app(app)

# Configure Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

# Initialize session support
from flask_session import Session
sess = Session()
app.config['SESSION_TYPE'] = SESSION_TYPE
app.config['SESSION_FILE_DIR'] = SESSION_FILE_DIR
app.config['SESSION_PERMANENT'] = SESSION_PERMANENT
# NOTE: For production, set SESSION_COOKIE_SECURE = True and use HTTPS
sess.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    db = models.SessionLocal()
    user = db.query(models.User).filter_by(id=user_id).first()
    db.close()
    if user:
        return user
    return None

# Import blueprints after app creation to avoid circular imports
from blueprints.auth import auth_bp
from blueprints.lost_and_found import lost_and_found_bp
from blueprints.marketplace import marketplace_bp

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(lost_and_found_bp)
app.register_blueprint(marketplace_bp)

@app.route('/')
def index():
    """Redirect to the most appropriate page based on login status"""
    if current_user.is_authenticated:
        return redirect(url_for('lost_and_found.dashboard'))
    return redirect(url_for('auth.login'))

# Context processor to inject user info into templates
@app.context_processor
def inject_user_info():
    if current_user.is_authenticated:
        db = models.SessionLocal()
        user = db.query(models.User).filter_by(id=current_user.id).first()
        db.close()
        if user:
            return {'get_user_info': lambda: user}
    return {'get_user_info': lambda: None}

# Handle 404 errors
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Handle 500 errors
@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

@app.route('/test_supabase')
def test_supabase():
    from models import test_supabase_connection
    return str(test_supabase_connection())

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
