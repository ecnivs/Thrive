from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload
from werkzeug.exceptions import RequestEntityTooLarge
from models import *
import os
import re

# initialize
app = Flask(__name__)
app.config.from_object('config')

# Create the upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
db.init_app(app)

# Create database tables if they do not exist
with app.app_context():
    db.create_all()

@app.errorhandler(RequestEntityTooLarge)
def handle_large_file_error(error):
    flash("The uploaded file must be smaller than 5 MB.", "error")
    return redirect(url_for('profile_form', user_id=session.get('user_id')))

@app.context_processor
def inject():
    if 'username' in session:
        return {
            'current_user' : User.query.get(session['user_id']),
            'current_profile': Profile.query.filter_by(user_id=session['user_id']).first()}
    return {}

@app.route('/', methods=['GET', 'POST'])
def home():
    if 'username' in session:
        user = User.query.get(session['user_id'])
        profile = Profile.query.filter_by(user_id=session['user_id']).first()
        if request.method == 'POST':
            return search_users()
        return render_template('index.html', username=session['username'], user=user, profile=profile)
    return redirect(url_for('login_page'))

@app.route('/login')
def login_page():
    if 'username' in session:
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username'].strip()
    password = request.form['password'].strip()
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
        username = request.form['username'].lower().strip()
        password = request.form['password'].strip()

        if not re.match("^[a-z0-9_-]+$", username):
            flash("Username cannot contain special characters.", "error")
            return redirect(url_for('signup'))

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already taken. Please choose a different one.", "error")
            return redirect(url_for('signup'))

        new_user = User(username=username, password=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()

        default_name = "Just Another User"
        new_profile = Profile(user_id=new_user.id, name=default_name, bio="", gender="")
        db.session.add(new_profile)
        db.session.commit()

        if new_user.id != 1:
            follow_relationship = Follow(follower_id=new_user.id, followed_id=1)
            db.session.add(follow_relationship)
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
        name = request.form['name'].strip()
        bio = request.form['bio'].strip()
        gender = request.form['gender']

        if gender == 'Custom':
            custom_gender = request.form['custom_gender'].strip()
            if custom_gender:
                gender = custom_gender

        if 'picture' in request.files:
            file = request.files['picture']
            if file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    os.makedirs(app.config['UPLOAD_FOLDER'])

                if profile and profile.profile_picture:
                    old_picture_path = os.path.join(app.config['UPLOAD_FOLDER'], profile.profile_picture)
                    if os.path.exists(old_picture_path):
                        os.remove(old_picture_path)

                profile.profile_picture = filename
                file.save(file_path)

        if profile:
            if name:
                profile.name = name
            profile.bio = bio
            profile.gender = gender
        else:
            profile = Profile(user_id=user_id, name=name, bio=bio, gender=gender)
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

    followers = User.query.join(Follow, User.id == Follow.follower_id).filter(Follow.followed_id == user_id).all()
    following = User.query.join(Follow, User.id == Follow.followed_id).filter(Follow.follower_id == user_id).all()

    followers_count = len(followers)
    following_count = len(following)

    is_following = False
    if 'user_id' in session:
        current_user = User.query.get(session['user_id'])
        is_following = current_user.is_following(user)

    return render_template('user_profile.html', 
                           profile=profile, 
                           user=user, 
                           followers=followers, 
                           following=following, 
                           followers_count=followers_count, 
                           following_count=following_count, 
                           is_following=is_following)

@app.route('/follow/<int:user_id>', methods=['POST'])
def follow(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_to_follow = User.query.get_or_404(user_id)
    current_user = User.query.get(session['user_id'])

    if not current_user.is_following(user_to_follow):
        current_user.follow(user_to_follow)
        db.session.commit()

    return redirect(url_for('user_profile', user_id=user_id))

@app.route('/unfollow/<int:user_id>', methods=['POST'])
def unfollow(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_to_unfollow = User.query.get_or_404(user_id)
    current_user = User.query.get(session['user_id'])

    if current_user.is_following(user_to_unfollow):
        current_user.unfollow(user_to_unfollow)
        db.session.commit()

    return redirect(url_for('user_profile', user_id=user_id))

@app.route('/search', methods=['POST'])
def search_users():
    search_query = request.form['search_query'].strip()
    if not search_query:
        return redirect(url_for('home'))
    return redirect(url_for('search_results', query=search_query))

@app.route('/search_results')
def search_results():
    search_query = request.args.get('query')
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
