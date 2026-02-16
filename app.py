from flask import Flask, render_template, session, redirect, request, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, login_user, logout_user, current_user, UserMixin
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, EqualTo, Length, Email
from datetime import datetime
from flask_bcrypt import Bcrypt
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "Login"

# Session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

# Database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tasks.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Database Model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    priority = db.Column(db.String(20), default="Medium")
    done = db.Column(db.Boolean, default=False)
    due_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

# Create DB
with app.app_context():
    db.create_all()


# Registration & Login Forms
class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired(), Length(min=2, max=30)])
    email = StringField("Email", validators=[InputRequired(), Email()])
    password = PasswordField("Password", validators=[InputRequired(), Length(min=6)])
    confirm_password = PasswordField("Confirm Password", validators=[InputRequired(), EqualTo("password")])
    submit = SubmitField("Register")

class LoginForm(FlaskForm):
    email = StringField("email", validators=[InputRequired(), Email()])
    password = StringField("password", validators=[InputRequired()])
    submit = SubmitField("Login")

# User authentication
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/register", methods=["POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        new_user = User(username = form.username.data, email = form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("User registered successfully.", category="success")
        return redirect(url_for("login"))
    
    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            flash("Login successful.", category="success")
            return redirect(url_for("index"))
        else:
            flash("Login failed. Check Email & password.", category="error")
    
    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("User logged out.", category="success")
    return redirect(url_for("login"))


# Routes for handling tasks
@app.route("/")
@login_required
def index():
    tasks = Task.query.order_by(Task.created_at.desc()).all()
    return render_template("index.html", tasks=tasks)


@app.route("/", methods=['POST'])
@login_required
def add_task():
    title = request.form.get("title")
    priority = request.form.get("priority")
    due_date = request.form.get("due_date")

    if not title:
        flash("Task title is required!", category="error")
        return redirect(url_for("index"))
    
    newTask = Task(
        title = title,
        priority = priority,
        due_date = datetime.strptime(due_date, "%Y-%m-%d") if due_date else None
    )

    db.session.add(newTask)
    db.session.commit()

    flash("Task added successfully.", category="success")
    return redirect(url_for("index"))


@app.route("/delete/<int:task_id>", methods=['GET'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    flash("Task deleted.", category="success")
    return redirect(url_for("index"))


@app.route("/complete/<int:task_id>", methods=['GET'])
@login_required
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    task.done = not task.done
    db.session.commit()
    flash("Task Updated.", category="success")
    return redirect(url_for("index"))


@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)

    if request.method == "POST":
        task.title = request.form.get("title")
        task.priority = request.form.get("priority")
        due_date = request.form.get("due_date")
        task.due_date = datetime.strptime(due_date, "%Y-%m-%d") if due_date else None

        db.session.commit()
        flash("Task Updated successfully", category="success")
        return redirect(url_for("index"))
    return render_template("edit.html", task=task)

