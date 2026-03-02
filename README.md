# 🚀 BirthdayPro  
### Smart Birthday Reminder & WhatsApp Automation System

BirthdayPro is a production-ready Flask web application designed to manage birthdays intelligently and automate reminder notifications via WhatsApp.

It combines authentication, automation, analytics, API integration, and deployment into a complete full-stack system.

🌐 Live App: https://birthday-v.onrender.com

---

# 📌 Project Vision

BirthdayPro solves a common real-world problem — forgetting important birthdays.

This system allows users to:
- Securely manage birthdays
- Track upcoming events
- Generate personalized wishes
- Receive automated WhatsApp reminders
- Analyze birthday insights

The project demonstrates real-world backend engineering, automation, API usage, and deployment practices.

---

# 🧠 Core Capabilities

## 🔐 Secure Authentication System
- User Registration
- Login / Logout
- Password hashing (Werkzeug)
- Session management (Flask-Login)

---

## 🎂 Birthday Management System
- Add Birthday
- Edit Birthday
- Delete Birthday
- Pagination
- Search functionality
- Filter (Today / Upcoming / All)
- Sorting (Nearest / Alphabetical)

Each user has isolated birthday records.

---

## 📊 Smart Dashboard Analytics
- Total Birthday Count
- Upcoming Birthdays
- Today's Birthdays
- This Month Statistics
- Relation-based Distribution
- Month-wise Distribution
- Next Upcoming Highlight

---

## 📥 CSV Bulk Import
- Upload birthday list
- Automatic validation
- User-based data isolation

---

## 🔔 Automated WhatsApp Reminders

Integrated with Twilio API.

Automated reminders are sent:
- 🎉 On Birthday
- 🔥 1 Day Before
- 🎁 3 Days Before

Background job handled by APScheduler (runs daily at 9 AM).

---

## ✨ AI-Style Wish Generator

Dynamic birthday message generation:
- Formal
- Funny
- Emotional
- Short

---

## 👤 Profile Management
- Profile Picture Upload
- Password Update
- Birthday Count Display

---

# 🏗 System Architecture

Frontend:
- HTML
- CSS
- Jinja2 Templates

Backend:
- Flask (Python)

Database:
- SQLite

Authentication:
- Flask-Login

Automation:
- APScheduler

External API:
- Twilio WhatsApp API

Deployment:
- Render (Gunicorn based production server)

---

# 📂 Project Structure

birthday-V/
│
├── app.py
├── birthdays.db
├── requirements.txt
├── static/
│   └── profile_pics/
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── add.html
│   ├── edit.html
│   └── profile.html
└── README.md


# ⚙️ Local Setup Guide

## 1️⃣ Clone Repository

git clone https://github.com/YOUR_USERNAME/birthday-V.git
cd birthday-V

## 2️⃣ Create Virtual Environment

python -m venv venv

Activate:


Mac/Linux:
source venv/bin/activate

## 3️⃣ Install Dependencies

pip install -r requirements.txt

## 4️⃣ Create Environment File

Create `.env` file:

TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=your_twilio_number

## 5️⃣ Run Application

python app.py

Server runs at:
http://127.0.0.1:8080

# 🌍 Production Deployment

Hosted on Render using:
- Gunicorn WSGI Server
- Environment Variables
- Python 3 Runtime

Live URL:
https://birthday-v.onrender.com


# 🧪 What This Project Demonstrates

✔ Full Stack Development  
✔ Backend Architecture Design  
✔ Secure Authentication  
✔ Database CRUD Operations  
✔ Scheduled Background Tasks  
✔ Third-party API Integration  
✔ Production Deployment  
✔ Environment Configuration  
✔ Version Control (Git)  
✔ Real-world Problem Solving  


# 🔮 Future Scope

- Public SEO Landing Page
- PostgreSQL Migration
- Email Reminders
- Admin Dashboard
- SaaS Multi-Tenant Version
- Subscription Integration
- Mobile Optimization
