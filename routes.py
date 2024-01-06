import os
from functools import wraps
from flask import Flask, request, render_template, url_for, flash, redirect, session
from sqlalchemy import func

from models import db, User, article, query, exercise, yoga
from app import app

@app.route('/')
def index():
    return "Hello world"
