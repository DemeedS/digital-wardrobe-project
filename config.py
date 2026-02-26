# ============================================================
# CONFIG - app settings loaded from environment variables
# Includes Flask secret key, database URI, and Cloudinary
# ============================================================

import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

class Config:
    # ----------------------------------------
    # FLASK - core security key for sessions/cookies
    # ----------------------------------------
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable must be set")

    # ----------------------------------------
    # DATABASE - SQLite for local development
    # ----------------------------------------
    SQLALCHEMY_DATABASE_URI = 'sqlite:///wardrobe.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ----------------------------------------
    # CLOUDINARY - cloud image storage
    # Credentials loaded from .env file
    # ----------------------------------------
    CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
    CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')