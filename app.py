from flask import Flask, render_template, session, redirect, request, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_bcrypt import Bcrypt
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

# Database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tasks.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Database Model
class User(db.Model):
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


# Routes
@app.route("/")
def index():
    tasks = Task.query.order_by(Task.created_at.desc()).all()
    return render_template("index.html", tasks=tasks)


@app.route("/", methods=['POST'])
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
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    flash("Task deleted.", category="success")
    return redirect(url_for("index"))


@app.route("/complete/<int:task_id>", methods=['GET'])
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    task.done = not task.done
    db.session.commit()
    flash("Task Updated.", category="success")
    return redirect(url_for("index"))


@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
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