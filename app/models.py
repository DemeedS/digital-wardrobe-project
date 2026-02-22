# database for user, clothing item models, including user authentication and password management.

from app import db, login_manager 
from flask_login import UserMixin # default implementations for user authentication methods
from werkzeug.security import generate_password_hash, check_password_hash # hashing pswrd.

# user loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# user table
class User(UserMixin, db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(12), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    items = db.relationship('ClothingItem', backref='owner', lazy=True)

# password management methods
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# clothing item table
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