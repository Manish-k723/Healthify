from dotenv import load_dotenv
import os
from app import app
load_dotenv()

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS')
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
app.config['IMAGE_UPLOAD_FOLDER'] = 'static/images'