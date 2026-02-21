#  settings, database, login system, route departments putten togehter.
# import frameworks and libraries
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

# Flask application factory
def create_app(): 
    app = Flask(__name__)
    app.config.from_object('config.Config') # Load configuration from config.py

# Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

# Register blueprints
    from app.routes.auth import auth
    from app.routes.wardrobe import wardrobe
# Importing the blueprints for authentication and wardrobe management


# Register blueprints with the Flask application
    app.register_blueprint(auth)
    app.register_blueprint(wardrobe)

# Create database tables
    with app.app_context():
        db.create_all()

    return app