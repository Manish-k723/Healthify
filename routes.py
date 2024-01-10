import os
from functools import wraps
from flask import Flask, request, render_template, url_for, flash, redirect, session, jsonify
from sqlalchemy import func
from datetime import datetime
from PIL import Image

from models import db, User, article, query, exercise, yoga
from app import app

def auth_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if "user_id" not in session:
            flash("Login required.", 'danger')
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return inner

def admin_auth_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        user = User.query.get(session.get("user_id"))
        if user.is_admin:
            return func(*args, **kwargs)
        else:
            flash("Logged out ! You are not an Admin.", "danger")
            return redirect(url_for("logout"))
    return inner

@app.route('/')
def index():
    try:
        user = User.query.get(session["user_id"])
        if user:
            return redirect(url_for("home"))
        else:
            return redirect(url_for("login"))
    except:
        return redirect(url_for("login"))

@app.route('/login', methods=["GET",'POST'])
def login():
    if request.method == "GET":
        return render_template('login.html')
    username = request.form.get('username')
    password = request.form.get('password')
    if username =="" or password =="":
        flash("Username or Password cannot be empty.", "danger")
        return redirect(url_for('login'))
    user = User.query.filter_by(username = username).first()
    if not user:
        flash("User doesnot exist. Please register and try again.", "danger")
        return redirect(url_for('login'))
    if not user.check_password(password):
        flash("Incorrect Password", "danger")
        return redirect(url_for('login'))
    session["user_id"] = user.id
    return redirect(url_for('home'))

@app.route('/admin', methods=['GET','POST'])
def admin():
    if request.method == "GET":
        return render_template("adminLogin.html")
    username = request.form.get('username')
    password = request.form.get('password')
    if username =="" or password =="":
        flash("Username or Password cannot be empty.", "danger")
        return redirect(url_for('admin'))
    user = User.query.filter_by(username = username).first()
    if not user.is_admin:
        flash("You are not authorized to view this page, please login to continue", "danger")
        return redirect(url_for('login'))
    if not user:
        flash("User doesnot exist. Please register and try again.", "danger")
        return redirect(url_for('admin'))
    if not user.check_password(password):
        flash("Incorrect Password", "danger")
        return redirect(url_for('admin'))
    session["user_id"] = user.id  
    return redirect(url_for("adminHome"))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for("login"))

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == "GET":
        return render_template('register.html')
    username =request.form.get("username")
    name = request.form.get("name")
    email = request.form.get("email")
    dob_str = request.form['dob']
    gender = request.form.get('gender')
    who = request.form.get("who")
    password = request.form.get("password")

    today = datetime.today().date()
    dob = datetime.strptime(dob_str, '%Y-%m-%d').date()

    age = today.year - dob.year
    print(username, name, email, password, dob_str, age, dob, gender, who)
    if username =="" or password =="":
        flash("Username or Password cannot be empty.", "danger")
        return redirect(url_for('register'))
    # if age<15:
    #     flash("User must be at least 15 years old.", "danger")
    #     return redirect(url_for('register'))
    if User.query.filter_by(username = username).first():
        flash("This username is already in use. Please choose another", "danger")
        return redirect(url_for('register'))
    user = User(username=username, name = name, email=email, gender = gender, who=who, dob = dob, password=password)
    db.session.add(user)
    db.session.commit()
    flash("User added Succesfully", "success")
    return redirect(url_for("login"))

@app.route('/home')
@auth_required
def home():
    user = User.query.get(session["user_id"])
    if user.is_admin:
        flash("You are an admin, continue as admin", "info")
        return redirect(url_for('admin'))
    else:
        return render_template('home.html', user = user)

@app.route('/update_pregnancy_status', methods=['POST'])
def update_pregnancy_status():
    data = request.get_json()
    pregnant = data.get('pregnant', False)
    user = User.query.get(session["user_id"])
    if user:
        user.pregnant = pregnant
        db.session.commit()
        return jsonify(success=True)
    else:
        return jsonify(success=False)

@app.route('/adminHome')
@auth_required
@admin_auth_required
def adminHome():
    articles = article.query.join(User, article.CreatorId == User.id).all()
    return render_template("admin.html", user = User.query.get(session["user_id"]), articles = articles,  need = True)

@app.route('/addArticle', methods=['GET', 'POST'])
@auth_required
def addArticle():
    user = User.query.get(session["user_id"])
    if request.method=="GET":
        return render_template("addArticle.html", user = user)
    title = request.form.get('title')
    abstract = request.form.get('abstract')
    content = request.form.get('content')
    image_file = request.files['image']
    if image_file:
        image_filename = image_file.filename
        filepath = os.path.join(app.config['IMAGE_UPLOAD_FOLDER'], image_filename)

        img = Image.open(image_file)
        img = img.resize((850, 480))
        img.save(filepath)

    if user.is_admin:
        status = "publish"
        creator = "Healthify"
    else:
        status = "pending"
        creator = user.name
    new_article = article(title=title, abstract = abstract, content=content, imagepath=image_filename, CreatorId=user.id, creator=creator, status = status)
    db.session.add(new_article)
    db.session.commit()
    if user.is_admin:
        flash("Article added successfully!", "success")
        return redirect(url_for("adminHome"))
    flash("Article Submitted! We will publish this article after reviewing.", "success")
    return redirect(url_for("read_articles"))
    
@app.route('/adminHome/<int:articleId>/<string:newStatus>')
@auth_required
@admin_auth_required
def updateStatus(articleId, newStatus):
    art = db.session.query(article).filter_by(id = articleId).one()
    art.status = newStatus
    db.session.commit()
    return redirect(url_for('adminHome'))

@app.route('/healthifyArticles/<int:articleId>')
def readArticle(articleId):
    user = User.query.get(session["user_id"])
    art = db.session.query(article).filter_by(id = articleId).one()
    return render_template("readArticle.html", article = art, user = user)

@app.route('/mother')
@auth_required
def mother():
    return "This is Playlist"

@app.route('/mental_health_check_up')
@auth_required
def mental_health_check_up():
    user = User.query.get(session["user_id"])
    if user.who == "Student":
        return render_template("student_mental_health.html", user = user)
    else:
        return render_template("wp_mental_health.html", user = user)

@app.route('/read_articles')
@auth_required
def read_articles():
    articles = db.session.query(article).order_by(article.impressions.desc()).all()
    return render_template("articles.html", articles = articles)

@app.route('/update-impression', methods=['POST'])
@auth_required
def update_impression():
    article_id = request.form.get('article_id')
    impression = request.form.get('impression')
    art = article.query.get(article_id)
    if impression == 'up':
        art.impressions += 1
    else:
        art.impressions -=1
    db.session.commit()
    return redirect(url_for("readArticle", articleId = art.id))

@app.route('/profile')
@auth_required
def profile():
    user = User.query.get(session["user_id"])
    return render_template("profile.html", user = user)

@app.route('/contact')
@auth_required
def contact():
    return "This is contact"

# https://en.wikipedia.org/wiki/Mental_health
# https://mentalhealthdeltadivision.com/interactive-games/