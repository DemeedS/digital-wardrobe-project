# ============================================================
# MODELS - database tables for User and ClothingItem
# Includes user authentication and wardrobe item storage
# ============================================================

from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# ----------------------------------------
# USER LOADER - required by Flask-Login
# ----------------------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ----------------------------------------
# USER TABLE - stores account credentials
# ----------------------------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    items = db.relationship('ClothingItem', backref='owner', lazy=True)

    # Password management methods
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# ----------------------------------------
# CLOTHING ITEM TABLE - stores wardrobe items
# front_image_url - Cloudinary URL for front photo (optional)
# tag_image_url   - Cloudinary URL for tag photo (optional)
# ----------------------------------------
class ClothingItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(50), nullable=False)
    size = db.Column(db.String(20), nullable=False)
    material = db.Column(db.String(50), nullable=False)
    brand = db.Column(db.String(50), nullable=False)
    season = db.Column(db.String(20), nullable=False)
    favorite = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # ---- Phase 1: Cloudinary image storage ----
    front_image_url = db.Column(db.String(500), nullable=True)  # front photo URL
    tag_image_url = db.Column(db.String(500), nullable=True)    # tag photo URL