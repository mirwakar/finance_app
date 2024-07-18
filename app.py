from flask import Flask, render_template, request, redirect, session, url_for
from models import db, User, Transfer
import hashlib
from cryptography.fernet import Fernet
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

key = Fernet.generate_key()
cipher_suite = Fernet(key)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def encrypt(data):
    return cipher_suite.encrypt(data.encode()).decode()


def decrypt(data):
    return cipher_suite.decrypt(data.encode()).decode()


@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('user_menu'))
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == hash_password(password):
            session['user_id'] = user.id
            return redirect(url_for('user_menu'))
        else:
            return 'Login yoki parol noto‘g‘ri'
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not User.query.filter_by(username=username).first():
            new_user = User(username=username, password=hash_password(password))
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        else:
            return 'Foydalanuvchi allaqachon mavjud'
    return render_template('register.html')


@app.route('/user_menu')
def user_menu():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return render_template('user_menu.html', balance=user.balance)
    return redirect(url_for('login'))


@app.route('/add_balance', methods=['GET', 'POST'])
def add_balance():
    if 'user_id' in session:
        if request.method == 'POST':
            amount = float(request.form['amount'])
            user = User.query.get(session['user_id'])
            user.balance += amount
            db.session.commit()
            return redirect(url_for('user_menu'))
        return render_template('add_balance.html')
    return redirect(url_for('login'))


@app.route('/transfer_money', methods=['GET', 'POST'])
def transfer_money():
    if 'user_id' in session:
        if request.method == 'POST':
            to_username = request.form['to_user']
            amount = float(request.form['amount'])
            from_user = User.query.get(session['user_id'])
            to_user = User.query.filter_by(username=to_username).first()
            if to_user and from_user.balance >= amount:
                from_user.balance -= amount
                to_user.balance += amount
                new_transfer = Transfer(from_user_id=from_user.id, to_user_id=to_user.id, amount=amount)
                db.session.add(new_transfer)
                db.session.commit()
                return redirect(url_for('user_menu'))
            else:
                return 'Foydalanuvchi mavjud emas yoki balans yetarli emas'
        return render_template('transfer_money.html')
    return redirect(url_for('login'))


@app.route('/transfer_history', methods=['GET', 'POST'])
def transfer_history():
    if 'user_id' in session:
        user_id = session['user_id']
        if request.method == 'POST':
            period = request.form['period']
            if period == 'day':
                start_date = datetime.now() - timedelta(days=1)
            elif period == 'week':
                start_date = datetime.now() - timedelta(weeks=1)
            elif period == 'month':
                start_date = datetime.now() - timedelta(days=30)
            else:
                start_date = datetime.min

            history = Transfer.query.filter(
                (Transfer.from_user_id == user_id) | (Transfer.to_user_id == user_id),
                Transfer.timestamp >= start_date
            ).all()
            return render_template('transfer_history.html', history=history)
        return render_template('transfer_history.html', history=[])
    return redirect(url_for('login'))


@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user_id' in session:
        user_id = session['user_id']
        user = User.query.get(user_id)
        db.session.delete(user)
        db.session.commit()
        session.pop('user_id', None)
        return redirect(url_for('register'))
    return redirect(url_for('login'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
