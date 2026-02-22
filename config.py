# Here's the security key, here's where the database is, 
# and turn off that annoying warnings.

import os # environment variables

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key' # cookie signing key
    SQLALCHEMY_DATABASE_URI = 'sqlite:///wardrobe.db' 
    SQLALCHEMY_TRACK_MODIFICATIONS = False # notifications for changes

