# Here's the security key, here's where the database is, 
# and turn off that annoying warnings.

import os # environment variables

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')  # cookie signing key
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable must be set")
    SQLALCHEMY_DATABASE_URI = 'sqlite:///wardrobe.db' 
    SQLALCHEMY_TRACK_MODIFICATIONS = False # notifications for changes

