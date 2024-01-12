import os, random
from functools import wraps
from flask import Flask, request, render_template, url_for, flash, redirect, session, jsonify
from sqlalchemy import func
from datetime import datetime
from PIL import Image
import nltk, joblib
from nltk.sentiment import SentimentIntensityAnalyzer
nltk.download('vader_lexicon')
sia = SentimentIntensityAnalyzer()

from models import db, User, article, query, Exercise, yogaPoses, Yoga, exercisePoses
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
        health = {
            "Weight":"70kg",
            "Height":"175cm",
            "BMI":22.9,
            "BP" : "120/80 mmHG",
            "Heart Rate": "72 bpm"
        }
        meal_recommendations = {
            "BreakFast": "Fruits",
            "Lunch": "Delightful",
            "Dinner": "Light dinner"
        }
        return render_template('home.html', user = user, health = health, meal_recommendations= meal_recommendations)

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

@app.route('/read_articles')
@auth_required
def read_articles():
    articles = db.session.query(article).order_by(article.impressions.desc()).all()
    return render_template("articles.html", articles = articles)

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

@app.route('/predict_for_student', methods=["POST"])
@auth_required
def predict_student():
    user = User.query.get(session["user_id"])
    name = request.form.get('name')
    age = int(request.form.get('age'))
    scaler = joblib.load('models\scalingStudent.joblib')
    scaled_age = scaler.transform([[age]])
    gender = int(request.form.get('gender'))
    married = int(request.form.get('married'))
    grade = int(request.form.get("gradeLevel"))
    cllge = int(request.form.get("tier"))
    course= int(request.form.get("course"))
    gpa = int(request.form.get("gpa"))
    income = int(request.form.get("income"))
    mood = int(request.form.get("overallMood"))
    changes = request.form.get("lifeChanges")
    feelingDown = int(request.form.get("feelingDown"))
    lostInterest = int(request.form.get("lostInterest"))
    anxiety = int(request.form.get("feltAnxiety"))
    additionalComments = request.form.get("additionalComments")
    inpt = [gender, scaled_age[0][0], cllge, grade, married, anxiety]
    gpa = gpa/2.5
    if gpa < 2:
        inpt.extend([0, 0, 0, 0])
    elif gpa<2.5:
        inpt.extend([1, 0, 0, 0])
    elif gpa<3:
        inpt.extend([0, 1, 0, 0])
    elif gpa<3.5:
        inpt.extend([0, 0, 1, 0])
    else:
        inpt.extend([0, 0, 0, 1])
    if course <5:
        crse = [1 if i == course else 0 for i in range(1, 5)]
        inpt.extend(crse)
    else:
        inpt.extend([0, 0, 0, 0])
    if income <= 2:
        inpt.extend([1,0])
    elif income>5:
        inpt.extend([0,1])
    else:
        inpt.extend([0,0])
    predictor = joblib.load('models\student_predictor2.joblib')
    w1 =  round(predictor.predict([inpt])[0]*random.uniform(4.3, 5), 1)
    if w1 == 0 and married == 1:
        w1 = round(random.uniform(0,1.5), 1)
    elif w1==0 and income<=5:
        w1 = round(random.uniform(1.5, 2.5), 1)
    elif w1 == 0:
        w1 = round(random.uniform(2.5, 4), 1)
    s1 = sia.polarity_scores(changes)
    if s1["compound"]> 0.15:
            w2 = min(5, mood+2)
    elif s1["compound"]< -0.15:
        w2 = max(0, mood-2)
    else:   w2=mood
    w3 = round(feelingDown+lostInterest*0.5, 1)
    w3 = min(w3, 5)
    w4 = round(sia.polarity_scores(additionalComments)["compound"]*5,1)
    w5 = round((w1+w2+w3+min(w4, 0))/4,1)
    analyses = mental_health_check_up_result(w1 = w1,w2= w2,w3= w3,w4= w4)
    return render_template('result.html', analyses=analyses, w1 = w1, w2= w2, w3= w3, w4= w4, w5=w5)

@app.route('/predict_for_wp', methods=["POST"])
@auth_required
def predict_wp():
    user = User.query.get(session["user_id"])
    name = request.form.get('name')
    age = int(request.form.get('age'))
    gender = int(request.form.get('gender'))
    married = int(request.form.get('married'))
    yoe = int(request.form.get("yoe"))
    field= int(request.form.get("field"))
    rating = float(request.form.get("rating"))
    salary = int(request.form.get("salary"))
    mood = int(request.form.get("overallMood"))
    changes = request.form.get("lifeChanges")
    feelingDown = int(request.form.get("feelingDown"))
    lostInterest = int(request.form.get("lostInterest"))
    anxiety = int(request.form.get("feltAnxiety"))
    additionalComments = request.form.get("additionalComments")
    scaler = joblib.load('models\scaling.joblib')
    scaled_param = scaler.transform([[age, yoe]])
    inpt = [gender, scaled_param[0][0], scaled_param[0][1], married, anxiety]
    if salary < 2:
        inpt.extend([1, 0])
    elif salary>5:
        inpt.extend([0, 1])
    else:
        inpt.extend([0, 0])
    if field <6:
        job = [1 if i == field else 0 for i in range(1, 6)]
        inpt.extend(job)
    else:
        inpt.extend([0, 0, 0, 0, 0])

    if rating < 2:
        inpt.extend([0, 0, 0, 0])
    elif rating<2.8:
        inpt.extend([1, 0, 0, 0])
    elif rating<3.6:
        inpt.extend([0, 1, 0, 0])
    elif rating<4.2:
        inpt.extend([0, 0, 1, 0])
    else:
        inpt.extend([0, 0, 0, 1])
    predictor = joblib.load('models\employed_predictor.joblib')
    w1 =  round(predictor.predict([inpt])[0]*random.uniform(4.3, 5), 1)
    if w1 == 0 and married == 1 and salary <= 4:
        w1 = round(random.uniform(0,1.5), 1)
    elif w1==0 and age>30 and salary<=6:
        w1 = round(random.uniform(1.5, 2.5), 1)
    elif w1 == 0:
        w1 = round(random.uniform(2.5, 4), 1)
    s1 = sia.polarity_scores(changes)
    if s1["compound"]> 0.15:
            w2 = min(5, mood+2)
    elif s1["compound"]< -0.15:
        w2 = max(0, mood-2)
    else:   w2=mood
    w3 = round(feelingDown+lostInterest*0.5, 1)
    w3 = min(w3, 5)
    w4 = round(sia.polarity_scores(additionalComments)["compound"]*5,1)
    w5 = round((w1+w2+w3+min(w4, 0))/4,1)
    analyses = mental_health_check_up_result(w1 = w1,w2= w2,w3= w3,w4= w4)
    return render_template('result.html', analyses=analyses, w1 = w1, w2= w2, w3= w3, w4= w4, w5=w5)

def mental_health_check_up_result(w1, w2, w3, w4):
    if w1 < 3:
        basic_analysis = "Based on the assessment of basic info, your score suggests there might be potential concerns that warrant further attention, related to your life and your surronding. It's advisable to consider seeking professional advice like us to gain a deeper understanding and address any issues effectively. Remember, early intervention is often key to achieving the best outcomes.➡️"
    else:
        basic_analysis = "Your basic score is good. This is a strong indication of your commitment to maintaining a positive lifestyle and well-being practices. It's important to continue with your current routines that contribute to this success. Consistency in healthy habits, such as regular exercise, balanced nutrition, and adequate rest, plays a crucial role in sustaining your overall well-being. Additionally, consider exploring new wellness activities or strategies that align with your lifestyle to further enhance your well-being and maintain this positive trajectory.😊"

    # General Well-being Analysis (w2)
    if w2 < 2:
        general_wellbeing_analysis = "Your score has revealed a low score in general well-being, which is a significant indicator that you may be experiencing heightened levels of stress. It's crucial to recognize this and take proactive steps to address it. Managing stress is key to improving your overall well-being. Consider adopting stress-reduction techniques such as mindfulness, meditation, or yoga. Regular physical activity and ensuring adequate sleep are also vital. Moreover, it's important to seek support, whether it be from friends, family, or professional counselors. They can provide a supportive network and offer strategies to help you cope more effectively. Remember, acknowledging the need for help and taking action is a positive step towards better health and well-being.🧠"
    elif 2 <= w2 < 3.5:
        general_wellbeing_analysis = "Your results show a moderate level of general well-being. This is a good foundation, but there's room for enhancement to elevate your overall sense of wellness. It's beneficial to explore various activities that can positively influence your mood and promote relaxation. Consider engaging in hobbies or interests that bring you joy and satisfaction. Activities like creative arts, gardening, or spending time in nature can be incredibly uplifting. Additionally, practices such as mindfulness meditation, yoga, or tai chi can significantly contribute to relaxation and mental balance. Experimenting with different forms of exercise or relaxation techniques can help you discover what works best for you, leading to an improved sense of well-being.⭕"
    else:
        general_wellbeing_analysis = "Your assessment indicates good general well-being, which is a testament to the effective strategies you're currently implementing. It's important to maintain these positive habits to continue feeling balanced and upbeat. Staying consistent with your current practices, whether they involve regular exercise, a balanced diet, mindfulness practices, or engaging in activities you enjoy, is key. Additionally, it's beneficial to remain open to adjusting your routines as needed to adapt to changing circumstances or to further enhance your well-being. Regular self-reflection can be useful in this regard, helping you to stay attuned to your needs and well-being. Keep up the great work, and remember that maintaining a positive and balanced lifestyle is a dynamic and ongoing process.😀"

    # Emotional Well-being Analysis (w3)
    if w3 < 2:
        emotional_analysis = "Receiving a low score in emotional well-being can be a sign to pause and reflect on your current emotional state. It's important to acknowledge your feelings and understand that seeking support is a positive step. Consider opening up and discussing your emotions with someone you trust, whether it's a close friend, family member, or a mental health professional. Sharing your feelings can provide relief, bring new perspectives, and help in finding coping strategies. Remember, emotional well-being is crucial for overall health, and taking steps to address it, such as practicing self-care, engaging in activities that bring you joy, or seeking professional help, can lead to significant improvements in your quality of life.➡️"
    elif 2 <= w3 < 3.5:
        emotional_analysis = "Your results indicating average emotional well-being suggest that you are generally managing well, but there may be room for further improvement. It's important to stay mindful of your emotions and reactions in different situations. Regular self-reflection can help you better understand your emotional patterns and triggers, which is key to maintaining and enhancing emotional balance. Consider incorporating practices such as mindfulness or journaling to gain deeper insights into your emotional state. Also, engaging in activities that promote relaxation and joy, like hobbies or exercise, can positively impact your emotional health. Remember, emotional well-being is an ongoing process, and being proactive about managing your emotions can lead to greater overall happiness and stability.♾️"
    else:
        emotional_analysis = "Congratulations on achieving a high score in emotional well-being! This is a clear indication of your strong ability to manage and understand your emotions effectively. To maintain this level of emotional health, it's important to continue nurturing your emotional well-being. Regular practices that contribute to this, such as mindfulness, meditation, or engaging in activities that you find fulfilling and enjoyable, should be maintained. Also, consider exploring new methods of self-care and emotional growth, such as reading self-help books, attending workshops, or even trying new hobbies. Keeping a balanced lifestyle, staying connected with supportive friends and family, and allowing yourself time for relaxation and reflection are also key components of sustaining high emotional well-being.🤠"

    # Assuming w4 is a measure of openness or additional concerns
    if w4 < 1.5:
    #     additional_comments_analysis = ""
    # elif 1.5 <= w4 < 3.5:
        additional_comments_analysis = '''Based on your feedback, it's clear that you have significant additional concerns that need attention. Addressing these concerns should be a priority for you. It's important to take proactive steps to manage and resolve these issues, as they can impact your overall well-being. Consider breaking down these concerns into manageable parts and tackling them one at a time. Seeking support from professionals, such as counselors or therapists, can be extremely beneficial in providing guidance and strategies to cope with and resolve these issues. Additionally, turning to trusted friends or family members for support can provide emotional comfort and practical advice. 
        Remember, acknowledging and addressing your concerns is a vital step towards improving your situation and enhancing your quality of life.🧠'''
    else:
        additional_comments_analysis = "Your feedback indicates that you have minimal additional concerns at this time, which suggests that you might be managing your current situation well. However, it's important to remember that it's completely okay to open up more if you feel the need to in the future. Whether you have new issues that arise or if you simply want to discuss things further, feel free to share. Opening up about your experiences, thoughts, or concerns can provide not only relief but also new insights or solutions. Remember, seeking support or advice when needed is a healthy and proactive way to address any aspect of your life, whether it's a small concern or a more significant issue.😄"

    analyses = {
        'basic_analysis': basic_analysis,
        'general_wellbeing_analysis': general_wellbeing_analysis,
        'emotional_analysis': emotional_analysis,
        'additional_comments_analysis': additional_comments_analysis
    }

    return analyses

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

@app.route('/addYoga', methods = ["GET", "POST"])
@auth_required
@admin_auth_required
def addYoga():
    user = User.query.get(session["user_id"])
    if request.method == "GET":
        yogas = Yoga.query.all()
        return render_template("yoga.html", yogas = yogas, user = user)
    yogaTitle = request.form.get('name')
    description = request.form.get('description')
    image_file = request.files['imageFile']
    if image_file:
        image_filename = image_file.filename
        filepath = os.path.join(app.config['IMAGE_UPLOAD_FOLDER'], image_filename)
        image_file.save(filepath)
    yoga = Yoga(name=yogaTitle, description = description, imagepath = image_filename) # genre=albumGenre
    db.session.add(yoga)
    db.session.commit()
    flash("Discpline added Succesfully", "success")
    return redirect(url_for("addYoga"))

@app.route('/addExercise', methods = ["GET", "POST"])
@auth_required
@admin_auth_required
def addExercise():
    user = User.query.get(session["user_id"])
    if request.method == "GET":
        exercises = Exercise.query.all()
        return render_template("exercise.html", exercises = exercises,user = user)
    exerciseTitle = request.form.get('name')
    description = request.form.get('description')
    image_file = request.files['imageFile']
    if image_file:
        image_filename = image_file.filename
        filepath = os.path.join(app.config['IMAGE_UPLOAD_FOLDER'], image_filename)
        image_file.save(filepath)
    exercise = Exercise(name=exerciseTitle, description = description, imagepath = image_filename) # genre=albumGenre
    db.session.add(exercise)
    db.session.commit()
    flash("Discpline added Succesfully", "success")
    return redirect(url_for("addExercise"))
    
@app.route('/add-yogaPose/<int:yid>', methods=["GET", "POST"])
@auth_required
@admin_auth_required
def addYogaPose(yid):
    user = User.query.get(session["user_id"])
    if request.method == "GET":
        poses = yogaPoses.query.filter_by(yoga_id= yid).all()
        return render_template("addYogaPose.html", poses = poses, user =user)
    title = request.form.get("title")
    duration = request.form.get("duration")
    steps = request.form.get("steps")
    new_pose = yogaPoses(posename = title, duration=duration, steps = steps, yoga_id = yid)
    db.session.add(new_pose)
    db.session.commit()
    flash("Yoga Pose added Succesfully", "success")
    return redirect(url_for("addYogaPose", yid = yid))

@app.route('/add-exercisePose/<int:eid>', methods=["GET", "POST"])
@auth_required
@admin_auth_required
def addexercisePose(eid):
    user = User.query.get(session["user_id"])
    if request.method == "GET":
        exercises = exercisePoses.query.filter_by(exercise_id= eid).all()
        return render_template("addExercisePose.html", exercises = exercises, user = user)
    title = request.form.get("title")
    duration = request.form.get("duration")
    steps = request.form.get("steps")
    new_pose = exercisePoses(posename = title, duration=duration, steps = steps, exercise_id = eid)
    db.session.add(new_pose)
    db.session.commit()
    flash("Exercise added Succesfully", "success")
    return redirect(url_for("addexercisePose", eid = eid))
    

@app.route('/contact')
@auth_required
def contact():
    return "This is contact"

# https://en.wikipedia.org/wiki/Mental_health
# 