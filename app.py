from flask import Flask, request, render_template, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
import config
import models
import routes