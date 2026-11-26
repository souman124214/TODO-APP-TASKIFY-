from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import date
import sqlite3

app = Flask(__name__)
app.secret_key = "taskify_change_this_secret_key"

DATABASE = "tasks.db"


# Database connection
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# Initialize database and migrate old tasks table
def init_db():
    with get_db() as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                completed INTEGER DEFAULT 0
            )
        """)

        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(tasks)")
        }

        if "priority" not in columns:
            conn.execute(
                "ALTER TABLE tasks ADD COLUMN priority TEXT DEFAULT 'Medium'"
            )

        if "due_date" not in columns:
            conn.execute(
                "ALTER TABLE tasks ADD COLUMN due_date TEXT"
            )

        if "category" not in columns:
            conn.execute(
                "ALTER TABLE tasks ADD COLUMN category TEXT DEFAULT 'Personal'"
            )


init_db()


# Login protection
def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")
        return func(*args, **kwargs)
    return wrapper


# Registration
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Please fill in all fields.")
            return redirect("/register")

        if len(password) < 6:
            flash("Password must contain at least 6 characters.")
            return redirect("/register")

        hashed_password = generate_password_hash(password)

        try:
            with get_db() as conn:
                conn.execute(
                    "INSERT INTO users (username, password) VALUES (?, ?)",
                    (username, hashed_password)
                )

            flash("Account created successfully!")
            return redirect("/login")

        except sqlite3.IntegrityError:
            flash("Username already exists!")

    return render_template("register.html")


# Login
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        with get_db() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            ).fetchone()

        if user and check_password_hash(user["password"], password):

            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]

            return redirect("/")

        flash("Invalid username or password!")

    return render_template("login.html")


# Dashboard
@app.route("/")
@login_required
def index():

    search = request.args.get("search", "").strip()
    category = request.args.get("category", "")

    query = """
        SELECT * FROM tasks
        WHERE user_id = ?
    """

    params = [session["user_id"]]

    if search:
        query += " AND title LIKE ?"
        params.append(f"%{search}%")

    if category in ["College", "Personal", "Project"]:
        query += " AND category = ?"
        params.append(category)

    query += " ORDER BY completed ASC, id DESC"

    with get_db() as conn:

        tasks = conn.execute(query, params).fetchall()

        stats = conn.execute("""
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) AS completed,
                SUM(CASE WHEN completed = 0 THEN 1 ELSE 0 END) AS pending
            FROM tasks
            WHERE user_id = ?
        """, (session["user_id"],)).fetchone()

    return render_template(
        "index.html",
        tasks=tasks,
        username=session["username"],
        stats=stats,
        today=date.today().isoformat(),
        search=search,
        category=category
    )


# Add task
@app.route("/add", methods=["POST"])
@login_required
def add():

    title = request.form.get("title", "").strip()
    priority = request.form.get("priority", "Medium")
    due_date = request.form.get("due_date") or None
    category = request.form.get("category", "Personal")

    if priority not in ["High", "Medium", "Low"]:
        priority = "Medium"

    if category not in ["College", "Personal", "Project"]:
        category = "Personal"

    if title:

        with get_db() as conn:
            conn.execute("""
                INSERT INTO tasks
                (user_id, title, priority, due_date, category)
                VALUES (?, ?, ?, ?, ?)
            """, (
                session["user_id"],
                title,
                priority,
                due_date,
                category
            ))

        flash("Task added successfully!")

    return redirect("/")


# Complete task
@app.route("/complete/<int:id>", methods=["POST"])
@login_required
def complete(id):

    with get_db() as conn:
        conn.execute("""
            UPDATE tasks
            SET completed = CASE
                WHEN completed = 0 THEN 1
                ELSE 0
            END
            WHERE id = ? AND user_id = ?
        """, (id, session["user_id"]))

    return redirect("/")


# Delete task
@app.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete(id):

    with get_db() as conn:
        conn.execute(
            "DELETE FROM tasks WHERE id = ? AND user_id = ?",
            (id, session["user_id"])
        )

    flash("Task deleted!")
    return redirect("/")


# Dark mode preference is stored in browser using JavaScript


# Logout
@app.route("/logout")
@login_required
def logout():

    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)