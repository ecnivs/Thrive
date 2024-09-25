from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Profile model
class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    bio = db.Column(db.Text, nullable=False)

# Create database tables
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
        session['user_id'] = user.id  # Store user_id in session
        return redirect(url_for('home'))
    else:
        flash("Invalid credentials, please try again.", "error")
        return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already taken. Please choose a different one.", "error")
            return render_template('signup.html')  # Render the signup template again

        new_user = User(username=username, password=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()
        
        session['username'] = username  # Store username in session
        session['user_id'] = new_user.id  # Store user_id in session
        flash("Registration successful! Please fill out your profile.", "success")
        return redirect(url_for('profile_form', user_id=new_user.id))

    return render_template('signup.html')

@app.route('/profile/<int:user_id>', methods=['GET', 'POST'])
def profile_form(user_id):
    profile = Profile.query.filter_by(user_id=user_id).first()
    
    if request.method == 'POST':
        name = request.form['name']
        bio = request.form['bio']
        
        # Update the profile fields
        profile.name = name
        profile.bio = bio
        
        db.session.commit()  # Save the changes to the database
        flash("Profile updated successfully!", "success")
        return redirect(url_for('user_profile', user_id=user_id))
    
    return render_template('profile_form.html', user_id=user_id, profile=profile)

@app.route('/user/<int:user_id>')
def user_profile(user_id):
    user = User.query.get(user_id)
    profile = Profile.query.filter_by(user_id=user_id).first()
    return render_template('user_profile.html', user=user, profile=profile)

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    return redirect(url_for('login_page'))

if __name__ == "__main__":
    app.run(debug=True)
