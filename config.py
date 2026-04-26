import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.environ.get('DB_PATH', '/tmp/lostnfound.db')  # legacy, not used with Supabase
POSTGRES_URI = os.environ.get('SUPABASE_DB_URL') or os.environ.get('POSTGRES_URI')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
SUPABASE_LOSTFOUND_BUCKET = os.environ.get('SUPABASE_LOSTFOUND_BUCKET', 'lostfound-images')
SUPABASE_MARKETPLACE_BUCKET = os.environ.get('SUPABASE_MARKETPLACE_BUCKET', 'marketplace-images')
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/tmp/uploads')  # legacy, not used with Supabase
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'samyacheat')

# Mail configuration for email verification
MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'campushubiiita@gmail.com')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'jibg odvb qvbn ecyp')
MAIL_USE_TLS = True
MAIL_USE_SSL = False

# Image processing configuration
MAX_IMAGE_SIZE = (1280, 720)
QUALITY = 85

# Session configuration
SESSION_TYPE = 'filesystem'
SESSION_FILE_DIR = os.environ.get('SESSION_FILE_DIR', '/tmp/flask_session')
SESSION_PERMANENT = False

# Ensure session directory exists at import time (for serverless cold starts)
os.makedirs(SESSION_FILE_DIR, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS