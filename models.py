from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import app

db = SQLAlchemy(app)

class User(UserMixin, db.Model):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(32), unique = True, nullable=False)
    passhash = db.Column(db.String(512), nullable = False)
    name = db.Column(db.String(32), nullable=True)
    gender = db.Column(db.String(30), nullable = False)
    email = db.Column(db.String(120), unique =True, nullable = False)
    dob = db.Column(db.Date, nullable = True)
    who = db.Column(db.String(30), nullable = False)
    weight = db.Column(db.Integer, nullable = True)
    height = db.Column(db.Integer, nullable = True)
    bmi_score = db.Column(db.Integer, nullable = True)
    bp = db.Column(db.Integer, nullable = True)
    sl = db.Column(db.Integer, nullable = True)
    pregnant = db.Column(db.Boolean, default = False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)

    @property
    def password(self):
        raise AttributeError("Password is not a readable attribute")

    @password.setter
    def password(self, password):
        self.passhash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.passhash, password)

# class user_health_details(db.Model):
#     __tablename__ = 'user_health_details'
#     user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable = False)
    
class article(db.Model):
    __tablename__="article"
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(60), nullable = False)
    abstract = db.Column(db.String(420), nullable = False)
    content = db.Column(db.String(1024), nullable = False)
    imagepath = db.Column(db.String(255), nullable=False)
    impressions = db.Column(db.Integer, default = 0)
    CreatorId = db.Column(db.Integer, db.ForeignKey('User.id'), nullable = False)
    creator = db.Column(db.String(35), nullable = False)
    status = db.Column(db.String(12), default="pending")

class query(db.Model):
    __tablename__= "query"
    query_id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(60), nullable = False)
    description = db.Column(db.String(260), nullable = False)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable = False)

class Yoga(db.Model):
    __tablename__ = 'Yoga'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(40), nullable = False)
    imagepath = db.Column(db.String(120), nullable = False)
    description = db.Column(db.String(120), nullable = False)

class yogaPoses(db.Model):
    __tablename__ = 'yogaPoses'
    id = db.Column(db.Integer, primary_key = True)
    posename = db.Column(db.String(30), nullable = False)
    duration = db.Column(db.String(30), nullable = False)
    steps = db.Column(db.String(200), nullable = True)
    yoga_id = db.Column(db.Integer, db.ForeignKey('Yoga.id'), nullable = False)

class Exercise(db.Model):
    __tablename__ = 'Exercise'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(40), nullable = False)
    imagepath = db.Column(db.String(120), nullable = False)
    description = db.Column(db.String(120), nullable = False)

class exercisePoses(db.Model):
    __tablename__ = 'exercisePoses'
    id = db.Column(db.Integer, primary_key = True)
    posename = db.Column(db.String(30), nullable = False)
    duration = db.Column(db.String(30), nullable = False)
    steps = db.Column(db.String(200), nullable = True)
    exercise_id = db.Column(db.Integer, db.ForeignKey('Exercise.id'), nullable = False)

with app.app_context():
    db.create_all()
    admin = User.query.filter_by(is_admin=True).first()
    if not admin:
        admin = User(username="admin", name = "admin", password="admin133", who="Other", email="admin@healthify.in", is_admin=True, gender = "Male")
        db.session.add(admin)
        db.session.commit()
