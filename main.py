from flask import Flask, render_template
from models import db, User, Post

app = Flask(__name__)
app.config['SQLALCHEMY_DATABSE_URI'] = 'sqlite://site.db'

@app.route('/')
def home():
    return render_template('base.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
