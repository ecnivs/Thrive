from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB limit

# Create the upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    profile = db.relationship('Profile', backref='user', uselist=False)

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(150), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    profile_picture = db.Column(db.String(150), nullable=True)

# Create database tables if they do not exist
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    if 'username' in session:
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
        flash("Registration successful! Please fill out your profile.", "success")
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
        flash("Profile saved successfully!", "success")
        return redirect(url_for('user_profile', user_id=user_id))

    return render_template('profile_form.html', user_id=user_id, profile=profile)

@app.route('/user/<int:user_id>')
def user_profile(user_id):
    profile = Profile.query.filter_by(user_id=user_id).first()
    user = User.query.get(user_id)

    if profile is None or user is None:
        flash("Profile not found.", "error")
        return redirect(url_for('home'))

    return render_template('user_profile.html', profile=profile, user=user)

@app.route('/search', methods=['GET', 'POST'])
def search_users():
    if request.method == 'POST':
        search_query = request.form['search_query']
        users = User.query.join(Profile).filter(
            (User.username.ilike(f'%{search_query}%')) | 
            (Profile.name.ilike(f'%{search_query}%'))
        ).options(joinedload(User.profile)).all()
        return render_template('search_results.html', users=users, search_query=search_query)

    return render_template('search.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    return redirect(url_for('login_page'))

if __name__ == "__main__":
    app.run(debug=True)

