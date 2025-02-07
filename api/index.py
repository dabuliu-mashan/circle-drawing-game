from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
import random
import string
import os
from datetime import timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=31)

# 使用内存数据库
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index'

# 在每次请求前确保数据库表存在
@app.before_request
def before_request():
    if not hasattr(app, 'db_initialized'):
        db.create_all()
        app.db_initialized = True

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
    if current_user.is_authenticated:
        return redirect(url_for('game'))
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username', generate_username())
    
    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': '用户名已存在'})
    
    user = User(username=username)
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return jsonify({'success': True})

@app.route('/game')
@login_required
def game():
    return render_template('game.html')

@app.route('/submit_score', methods=['POST'])
@login_required
def submit_score():
    data = request.get_json()
    score = float(data.get('score', 0))
    
    # 记录分数
    new_score = Score(user_id=current_user.id, score=score)
    db.session.add(new_score)
    
    # 更新最高分
    if score > current_user.best_score:
        current_user.best_score = score
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/leaderboard')
@login_required
def leaderboard():
    users = User.query.order_by(User.best_score.desc()).all()
    return render_template('leaderboard.html', users=users)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True) 