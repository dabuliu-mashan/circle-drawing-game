from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
import random
import string
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# 修改数据库配置以支持Vercel环境
if os.environ.get('VERCEL_ENV') == 'production':
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tmp/game.db'
else:
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

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True) 