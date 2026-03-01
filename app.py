from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3
from twilio.rest import Client
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
from apscheduler.schedulers.background import BackgroundScheduler
from collections import Counter
import calendar
import os
from werkzeug.utils import secure_filename
import csv
from io import TextIOWrapper
import random
from dotenv import load_dotenv
import os

load_dotenv()



# ===============================
# APP CONFIG
# ===============================
app = Flask(__name__)
app.secret_key = "supersecretkey"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

UPLOAD_FOLDER = 'static/profile_pics'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ===============================
# TWILIO CONFIG
# ===============================import os

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# ===============================
# DATABASE INIT
# ===============================
def init_db():
    conn = sqlite3.connect("birthdays.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    profile_pic TEXT DEFAULT 'default.png'
)
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS birthdays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            date TEXT,
            relation TEXT,
            phone TEXT,
            user_id INTEGER
        )
    """)
    

    conn.commit()
    conn.close()

init_db()

# ===============================
# USER CLASS
# ===============================
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect("birthdays.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return User(user[0], user[1]) if user else None

# ===============================
# HOME (DASHBOARD)
# ===============================
@app.route("/")
@login_required
def home():

    search_query = request.args.get("search", "").lower()
    filter_type = request.args.get("filter", "all")
    sort_type = request.args.get("sort", "nearest")

    conn = sqlite3.connect("birthdays.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM birthdays WHERE user_id=?", (current_user.id,))
    birthdays = cursor.fetchall()
    conn.close()

    today = date.today()

    updated_birthdays = []
    upcoming_count = 0
    today_count = 0

    # ==============================
    # PROCESS EACH BIRTHDAY
    # ==============================
    for b in birthdays:

        try:
            # ULTRA SAFE DATE PARSING
            raw_date = str(b[2]).strip().split(" ")[0]
            b_date = datetime.fromisoformat(raw_date).date()
        except Exception:
            continue  # skip corrupted date rows safely

        # Next Birthday Calculation
        next_birthday = b_date.replace(year=today.year)
        if next_birthday < today:
            next_birthday = next_birthday.replace(year=today.year + 1)

        days_left = (next_birthday - today).days

        # Age Calculation
        current_age = today.year - b_date.year
        if next_birthday > today:
            current_age -= 1

        # SEARCH
        if search_query and search_query not in b[1].lower():
            continue

        # FILTER
        if filter_type == "today" and days_left != 0:
            continue
        if filter_type == "upcoming" and days_left == 0:
            continue

        # COUNT
        if days_left == 0:
            today_count += 1
        

        updated_birthdays.append({
            "id": b[0],
            "name": b[1],
            "date": raw_date,
            "relation": b[3],
            "phone": b[4],
            "days_left": days_left,
            "age": current_age,
            "turning_age": current_age + 1
        })

    # ==============================
    # SORTING
    # ==============================
    if sort_type == "nearest":
        updated_birthdays.sort(key=lambda x: x["days_left"])
    elif sort_type == "name":
        updated_birthdays.sort(key=lambda x: x["name"].lower())

    # ==============================
    # ANALYTICS SECTION
    # ==============================

    this_month = today.month

    this_month_count = sum(
        1 for b in updated_birthdays
        if datetime.fromisoformat(b["date"]).month == this_month
    )

    next_upcoming = (
        min(updated_birthdays, key=lambda x: x["days_left"])
        if updated_birthdays else None
    )

    if next_upcoming and next_upcoming["days_left"] > 0:
        upcoming_count = 1
    else:
        upcoming_count = 0

    relation_counts = Counter(b["relation"] for b in updated_birthdays)

    month_counts = Counter()
    for b in updated_birthdays:
        month = datetime.fromisoformat(b["date"]).month
        month_name = calendar.month_abbr[month]
        month_counts[month_name] += 1

    # ==============================
    # PAGINATION
    # ==============================

    page = request.args.get("page", 1, type=int)
    per_page = 3

    start = (page - 1) * per_page
    end = start + per_page

    total = len(updated_birthdays)
    paginated_birthdays = updated_birthdays[start:end]


    conn2 = sqlite3.connect("birthdays.db")
    cursor2 = conn2.cursor()
    cursor2.execute("SELECT profile_pic FROM users WHERE id=?", (current_user.id,))
    profile_pic = cursor2.fetchone()[0]
    conn2.close()

    # ==============================
    # RETURN TEMPLATE
    # ==============================

    return render_template(
        "index.html",
        birthdays=paginated_birthdays,
        upcoming_count=upcoming_count,
        today_count=today_count,
        page=page,
        total_pages=(total + per_page - 1) // per_page,
        this_month_count=this_month_count,
        next_upcoming=next_upcoming,
        relation_counts=relation_counts,
        month_counts=month_counts,
        profile_pic=profile_pic

    )
# ===============================
# ADD BIRTHDAY
# ===============================
@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        name = request.form["name"]
        birth_date = request.form["date"]
        relation = request.form["relation"]
        phone = request.form["phone"]

        conn = sqlite3.connect("birthdays.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO birthdays (name, date, relation, phone, user_id) VALUES (?, ?, ?, ?, ?)",
            (name, birth_date, relation, phone, current_user.id)
        )
        conn.commit()
        conn.close()
        return redirect(url_for("home"))
        

    return render_template("add.html")

# ===============================
# EDIT BIRTHDAY
# ===============================
@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit(id):
    conn = sqlite3.connect("birthdays.db")
    cursor = conn.cursor()

    if request.method == "POST":
        name = request.form["name"]
        birth_date = request.form["date"]
        relation = request.form["relation"]
        phone = request.form["phone"]

        cursor.execute("""
            UPDATE birthdays
            SET name=?, date=?, relation=?, phone=?
            WHERE id=? AND user_id=?
        """, (name, birth_date, relation, phone, id, current_user.id))

        conn.commit()
        conn.close()
        return redirect(url_for("home"))

    cursor.execute("SELECT * FROM birthdays WHERE id=? AND user_id=?", (id, current_user.id))
    birthday = cursor.fetchone()
    conn.close()

    return render_template("edit.html", b=birthday)

# ===============================
# DELETE
# ===============================
@app.route("/delete/<int:id>")
@login_required
def delete(id):
    conn = sqlite3.connect("birthdays.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM birthdays WHERE id=? AND user_id=?", (id, current_user.id))
    conn.commit()
    conn.close()
    return redirect(url_for("home"))

# ===============================
# AUTH
# ===============================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("birthdays.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            login_user(User(user[0], user[1]))
            return redirect(url_for("home"))
        flash("Invalid credentials")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        conn = sqlite3.connect("birthdays.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (request.form["username"], generate_password_hash(request.form["password"]))
        )
        conn.commit()
        conn.close()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# ===============================
# DAILY BIRTHDAY CHECK
# ===============================
def check_today_birthdays():
    today = date.today()

    conn = sqlite3.connect("birthdays.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, phone, date FROM birthdays")
    rows = cursor.fetchall()

    for name, phone, bdate in rows:
        birth_date = datetime.strptime(bdate.strip(), "%Y-%m-%d").date()
        next_birthday = birth_date.replace(year=today.year)
        if next_birthday < today:
            next_birthday = next_birthday.replace(year=today.year + 1)

        days_left = (next_birthday - today).days

        if days_left in (0, 1, 3):
            msg = f"🎉 Happy Birthday {name}! 🎂" if days_left == 0 else \
                  f"🔥 Kal {name} ka birthday hai!" if days_left == 1 else \
                  f"🎁 {name} ka birthday 3 din me hai!"

            twilio_client.messages.create(
                body=msg,
                from_=TWILIO_PHONE_NUMBER,
                to=f"whatsapp:{phone}"
            )

    conn.close()

scheduler = BackgroundScheduler()
scheduler.add_job(check_today_birthdays, 'cron', hour=9, minute=0)
scheduler.start()

# ===============================
# PROFILE PAGE
# ===============================
@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():

    conn = sqlite3.connect("birthdays.db")
    cursor = conn.cursor()

    cursor.execute("SELECT profile_pic FROM users WHERE id=?", (current_user.id,))
    profile_pic = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM birthdays WHERE user_id=?", (current_user.id,))
    total_birthdays = cursor.fetchone()[0]

    if request.method == "POST":

        # Profile picture upload
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']

            if file.filename != "":
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                cursor.execute(
                    "UPDATE users SET profile_pic=? WHERE id=?",
                    (filename, current_user.id)
                )
                conn.commit()

        # Password update
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")

        if current_password and new_password:
            cursor.execute("SELECT password FROM users WHERE id=?", (current_user.id,))
            user = cursor.fetchone()

            if user and check_password_hash(user[0], current_password):
                new_hashed = generate_password_hash(new_password)
                cursor.execute("UPDATE users SET password=? WHERE id=?", (new_hashed, current_user.id))
                conn.commit()
                flash("Password updated successfully ✅")
            else:
                flash("Current password incorrect ❌")

    conn.close()

    return render_template(
        "profile.html",
        username=current_user.username,
        total_birthdays=total_birthdays,
        profile_pic=profile_pic
    )
@app.route("/import_csv", methods=["POST"])
@login_required
def import_csv():

    file = request.files.get("csv_file")

    if not file:
        flash("No file selected")
        return redirect(url_for("home"))

    if not file.filename.endswith(".csv"):
        flash("Please upload a CSV file")
        return redirect(url_for("home"))

    stream = TextIOWrapper(file.stream, encoding='utf-8')
    csv_reader = csv.reader(stream)
    next(csv_reader)  # skip header

    conn = sqlite3.connect("birthdays.db")
    cursor = conn.cursor()

    for row in csv_reader:
        if len(row) != 4:
            continue

        name, birth_date, relation, phone = row

        cursor.execute("""
            INSERT INTO birthdays (name, date, relation, phone, user_id)
            VALUES (?, ?, ?, ?, ?)
        """, (name, birth_date, relation, phone, current_user.id))

    conn.commit()
    conn.close()

    flash("CSV Imported Successfully ✅")
    return redirect(url_for("home"))


def generate_wish(name, relation, wish_type):
    
    formal = [
        f"Wishing you a very happy birthday, {name}. May this year bring you success and happiness.",
        f"Many happy returns of the day, {name}. Wishing you good health and prosperity.",
        f"Happy Birthday, {name}. May your future be filled with achievements."
    ]

    funny = [
        f"Happy Birthday {name}! You're not old, you're just vintage 😆",
        f"{name}, age is just a number... a very big one now 😂",
        f"Another year older, wiser... and closer to back pain 😜"
    ]

    emotional = [
        f"{name}, you are truly special to me. I'm grateful to have you in my life. Happy Birthday ❤️",
        f"Happy Birthday {name}. May our bond grow stronger every year 💖",
        f"{name}, life is brighter because of you. Stay blessed always 🌟"
    ]

    short = [
        f"Happy B'day {name}! 🎉",
        f"Many many happy returns {name}! 🥳",
        f"Stay blessed {name}! 🎂"
    ]

    wishes = {
        "formal": formal,
        "funny": funny,
        "emotional": emotional,
        "short": short
    }

    return random.choice(wishes[wish_type])

@app.route("/generate_wish/<int:id>/<wish_type>")
@login_required
def generate_wish_route(id, wish_type):

    conn = sqlite3.connect("birthdays.db")
    cursor = conn.cursor()

    cursor.execute("SELECT name, relation FROM birthdays WHERE id=? AND user_id=?", (id, current_user.id))
    person = cursor.fetchone()

    conn.close()

    if not person:
        return "Not Found"

    name, relation = person

    message = generate_wish(name, relation, wish_type)

    return message
@app.route("/test")
def test_message():
    message = twilio_client.messages.create(
        body="🔥 Test from BirthdayPro 🚀",
        from_="whatsapp:+14155238886",
        to="whatsapp:+918085970428"
    )
    return f"Message SID: {message.sid}"

    

# ===============================
# RUN
# ===============================
# ======= LAST PART OF FILE =======
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
    