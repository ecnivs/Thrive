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

# Create database tables
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    if 'username' in session:
        return render_template('index.html', username=session['username'])
    else:
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

        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for('login_page'))

    return render_template('signup.html') 

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login_page'))

if __name__ == "__main__":
    app.run(debug=True)

