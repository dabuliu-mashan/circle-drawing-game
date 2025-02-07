from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user
import random
import string
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///game.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    best_score = db.Column(db.Float, default=0)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def generate_username():
    adjectives = ['快乐', '开心', '可爱', '聪明', '勇敢']
    nouns = ['画家', '艺术家', '玩家', '达人', '高手']
    number = ''.join(random.choices(string.digits, k=4))
    return random.choice(adjectives) + random.choice(nouns) + number

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/game')
@login_required
def game():
    return render_template('game.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    if not username:
        username = generate_username()
    
    if User.query.filter_by(username=username).first():
        return jsonify({'error': '用户名已存在'}), 400
    
    user = User(username=username)
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return jsonify({'success': True, 'username': username})

@app.route('/submit_score', methods=['POST'])
@login_required
def submit_score():
    score_value = request.json.get('score')
    if score_value is None:
        return jsonify({'error': '未提供分数'}), 400
    
    score = Score(user_id=current_user.id, score=score_value)
    db.session.add(score)
    
    if score_value > current_user.best_score:
        current_user.best_score = score_value
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/leaderboard')
def leaderboard():
    top_users = User.query.order_by(User.best_score.desc()).limit(10).all()
    return render_template('leaderboard.html', users=top_users)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 