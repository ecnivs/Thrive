import os
from dotenv import load_dotenv

load_dotenv()

# Config
SECRET_KEY = os.getenv('SECRET_KEY')
SQLALCHEMY_DATABASE_URI = 'sqlite:///users.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False
UPLOAD_FOLDER = 'static/uploads'
MAX_CONTENT_LENGTH = 5 * 1024 * 1024 # 5 MB

