from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload
from models import *
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

# Create the upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
db.init_app(app)

# Create database tables if they do not exist
with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def home():
    if 'username' in session:
        if request.method == 'POST':
            return search_users()
        return render_template('index.html', username=session['username'])
    return redirect(url_for('login_page'))

@app.route('/login')
def login_page():
    if 'username' in session:
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password, password):
        session['username'] = username
        session['user_id'] = user.id
        return redirect(url_for('home'))
    else:
        flash("Invalid credentials, please try again.", "error")
        return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username'].lower()
        password = request.form['password']

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already taken. Please choose a different one.", "error")
            return render_template('signup.html')

        new_user = User(username=username, password=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()
        
        session['username'] = username
        session['user_id'] = new_user.id
        flash("Account created successfully! Please fill out your profile.", "success")
        return redirect(url_for('profile_form', user_id=new_user.id))

    return render_template('signup.html')

@app.route('/profile/<int:user_id>', methods=['GET', 'POST'])
def profile_form(user_id):
    profile = Profile.query.filter_by(user_id=user_id).first()
    
    if 'user_id' not in session or session['user_id'] != user_id:
        flash("You are not authorized to edit this profile.", "error")
        return redirect(url_for('home'))

    if request.method == 'POST':
        name = request.form['name']
        bio = request.form['bio']

        if 'picture' in request.files:
            file = request.files['picture']
            if file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                if profile:
                    if profile.profile_picture:
                        old_picture_path = os.path.join(app.config['UPLOAD_FOLDER'], profile.profile_picture)
                        if os.path.exists(old_picture_path):
                            os.remove(old_picture_path)

                    profile.profile_picture = filename
                else:
                    profile = Profile(user_id=user_id, name=name, bio=bio, profile_picture=filename)
                    db.session.add(profile)

                file.save(file_path)

        if profile:
            profile.name = name
            profile.bio = bio
        else:
            profile = Profile(user_id=user_id, name=name, bio=bio)
            db.session.add(profile)

        db.session.commit()
        return redirect(url_for('user_profile', user_id=user_id))

    return render_template('profile_form.html', user_id=user_id, profile=profile)

@app.route('/user/<int:user_id>')
def user_profile(user_id):
    profile = Profile.query.filter_by(user_id=user_id).first()
    user = User.query.get(user_id)

    if profile is None or user is None:
        return redirect(url_for('home'))

    return render_template('user_profile.html', profile=profile, user=user)

@app.route('/search', methods=['POST'])
def search_users():
    search_query = request.form['search_query'].strip()

    if not search_query:
        return redirect(url_for('home'))

    current_user_id = session.get('user_id')

    users = User.query.join(Profile).filter(
        (User.username.ilike(f'%{search_query}%')) | 
        (Profile.name.ilike(f'%{search_query}%'))
    ).filter(User.id != current_user_id).options(joinedload(User.profile)).all()

    return render_template('search_results.html', users=users, search_query=search_query)

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    return redirect(url_for('login_page'))

if __name__ == "__main__":
    app.run(debug=True)

