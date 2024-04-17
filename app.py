import os
from datetime import datetime

from flask import Flask, request, jsonify, render_template, redirect
from sqlalchemy.exc import IntegrityError

from flask_api_key import APIKeyManager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase

from auth_lib import encode, is_valid

import uuid

app = Flask(__name__)
my_key_manager = APIKeyManager(app)

class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
app.config["FLASK_API_KEY_PREFIX"] = "ss"

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", default = "my_secret_key")



# initialize the app with the extension
db.init_app(app)


class User(db.Model):
    __tablename__ = 'users'

    uuid = db.Column(db.String(36), primary_key=True, default=str(uuid.uuid4()), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)

    def __init__(self, username):
        self.username = username

    def __repr__(self):
        return '<User %r>' % self.username


class Score(db.Model):
    __tablename__ = 'scores'

    id = db.Column(db.Integer, primary_key=True)
    user_uuid = db.Column(db.String(36), ForeignKey('users.uuid'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('scores', lazy=True))

    def __init__(self, user_uuid, score):
        self.user_uuid = user_uuid
        self.score = score

    def __repr__(self):
        return '<Score %r>' % self.score


with app.app_context():
    db.create_all()

@app.route('/')
def hello_world():  # put application's code here
    #print(app.secret_key)
    return redirect("/scores", code=302)

@app.route('/keys/create', methods=['POST'])
def create_key():
    data = request.get_json()
    if 'key_id' in data.keys():
        my_key = my_key_manager.create("hello")
        print(my_key)
        #print(my_key.secret)
        return jsonify({'key': my_key.secret})
    else:
        return jsonify({'error': 'key_id not in request'}), 400

@app.route('/users')
def get_all_users():  # put application's code here
    return 'Hello World!'

@app.route('/users/create', methods=['POST'])
def create_new_user():  # put application's code here
    data = request.get_json()
    if 'username' in data.keys():
        try:
            new_user = User(username=data.get('username'))
            db.session.add(new_user)
            db.session.commit()
            return jsonify({'uuid': new_user.uuid, 'key':encode(new_user.username, new_user.uuid, app.secret_key)})
        except IntegrityError:
            db.session.rollback()
            return jsonify({"error":'username already exists'}), 400
    else:
        return jsonify({'error': 'username not in request'}), 400

@app.route('/scores', methods=['GET', 'POST'])
def get_all_scores():
    if request.method == 'POST':
        top_scores = Score.query.order_by(Score.score.desc()).limit(20).all()
        return jsonify([{'user': score.user.username, 'score': score.score, 'date':score.timestamp} for score in top_scores])
    else:
        return render_template('scores.html', scores=Score.query.order_by(Score.score.desc()).all())

@app.route('/scores/create', methods=['POST'])
def upload_score():
    data = request.get_json()
    if 'username' in data.keys() and 'uuid' in data.keys() and 'secret' in data.keys() and'score' in data.keys():
        if is_valid(data.get('secret'), data.get('username'), data.get('uuid'), app.secret_key):
            new_score = Score(user_uuid=data.get('uuid'), score=data.get('score'))
            db.session.add(new_score)
            db.session.commit()
            return jsonify({'score': new_score.score})
        else:
            return jsonify({'error': 'invalid secret'}), 400
    else:
        return jsonify({'error': 'missing data'}), 400


if __name__ == '__main__':
    app.run()
