from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for
from flask_session import Session
from google.oauth2 import id_token
from google.auth.transport import requests
from dotenv import load_dotenv
import os
import re
import datetime
import bcrypt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pymongo import MongoClient
from bson import ObjectId
from functools import wraps
import secrets
import sqlite3

# Load environment variables
load_dotenv()

# Create Flask app
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
app = Flask(__name__, static_folder=frontend_dir, static_url_path='')

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')

# MongoDB Setup (or SQLite fallback)
mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/prescripto')

# --- Database Helper --- (Shared logic for Mongo and SQLite)
class Storage:
    def __init__(self):
        self.use_sqlite = False
        self.client = None
        self.db = None
        self.users = None
        self.reset_tokens = None # For MongoDB only

        try:
            self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
            self.client.server_info() # Trigger connection check
            self.db = self.client.prescripto
            self.users = self.db.users
            self.reset_tokens = self.db.password_reset_tokens
            print("Database: Connected to MongoDB")
        except Exception as e:
            print(f"Database: MongoDB connection failed ({e}). Falling back to SQLite.")
            self.use_sqlite = True
            self.sqlite_db = 'prescripto.db'
            self._init_sqlite()

    def _init_sqlite(self):
        conn = sqlite3.connect(self.sqlite_db)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT UNIQUE, 
                      password_hash TEXT, google_id TEXT, profile_picture TEXT, 
                      created_at DATETIME, last_login DATETIME)''')
        conn.commit()
        conn.close()

    def get_user_by_email(self, email):
        if not self.use_sqlite:
            return self.users.find_one({'email': email})
        else:
            conn = sqlite3.connect(self.sqlite_db)
            conn.row_factory = sqlite3.Row
            user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            conn.close()
            return dict(user) if user else None

    def insert_user(self, user_data):
        if not self.use_sqlite:
            return self.users.insert_one(user_data).inserted_id
        else:
            conn = sqlite3.connect(self.sqlite_db)
            # Convert datetime objects to ISO format strings for SQLite
            for key, value in user_data.items():
                if isinstance(value, datetime.datetime):
                    user_data[key] = value.isoformat()
            
            keys = ', '.join(user_data.keys())
            placeholders = ', '.join(['?'] * len(user_data))
            cursor = conn.execute(f"INSERT INTO users ({keys}) VALUES ({placeholders})", list(user_data.values()))
            conn.commit()
            last_id = cursor.lastrowid
            conn.close()
            return last_id

    def update_user_last_login(self, email):
        now = datetime.datetime.now()
        if not self.use_sqlite:
            self.users.update_one({'email': email}, {'$set': {'last_login': now}})
        else:
            conn = sqlite3.connect(self.sqlite_db)
            conn.execute("UPDATE users SET last_login = ? WHERE email = ?", (now.isoformat(), email))
            conn.commit()
            conn.close()

    def update_user_google_info(self, user_id, google_id, picture):
        if not self.use_sqlite:
            self.users.update_one(
                {'_id': user_id}, 
                {'$set': {
                    'google_id': google_id,
                    'profile_picture': picture,
                    'last_login': datetime.datetime.now()
                }}
            )
        else:
            conn = sqlite3.connect(self.sqlite_db)
            conn.execute("UPDATE users SET google_id = ?, profile_picture = ?, last_login = ? WHERE id = ?", 
                         (google_id, picture, datetime.datetime.now().isoformat(), user_id))
            conn.commit()
            conn.close()

storage = Storage()
users_coll = storage.users # For backward compatibility with existing code that uses users_coll
reset_tokens_coll = storage.reset_tokens # For backward compatibility, will be None if SQLite is used

# Initialize Session
Session(app)

# --- Helper Functions ---

def hash_password(password):
    # Hash and return as a string for easy storage
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    # Convert string back to bytes if necessary
    if isinstance(hashed, str):
        hashed = hashed.encode('utf-8')
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def send_email(to_email, subject, body):
    from_email = os.getenv('EMAIL_ADDRESS')
    from_password = os.getenv('EMAIL_PASSWORD')
    
    if not from_email or not from_password:
        print("Warning: Email credentials not set. Reset link:", body)
        return False

    msg = MIMEMultipart()
    msg['From'] = str(from_email)
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(str(from_email), str(from_password))
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

# --- Authentication Decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Routes ---

@app.route('/')
def home():
    """Serve the landing home page"""
    return send_from_directory(frontend_dir, 'home.html')

@app.route('/login')
def login():
    """Serve the login page"""
    if 'user' in session:
        return redirect(url_for('index'))
    return send_from_directory(frontend_dir, 'login.html')

@app.route('/logout')
def logout():
    """Clear session and logout"""
    session.clear()
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def index():
    """Serve the main frontend page index.html"""
    return send_from_directory(frontend_dir, 'index.html')

# --- Authentication API ---

# --- Authentication API ---

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    # Check if user already exists
    if storage.get_user_by_email(email):
        return jsonify({"status": "error", "message": "Email already registered"}), 400

    hashed = hash_password(password)
    try:
        user_id = storage.insert_user({
            'name': name,
            'email': email,
            'password_hash': hashed,
            'created_at': datetime.datetime.now(),
            'last_login': datetime.datetime.now()
        })
        return jsonify({"status": "success", "message": "User registered successfully"})
    except Exception as e:
        print(f"Registration DB Error: {e}")
        return jsonify({"status": "error", "message": "Database storage error. Please try again."}), 500

@app.route('/api/login', methods=['POST'])
def login_api():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    try:
        user = storage.get_user_by_email(email)
        if user and user.get('password_hash') and check_password(password, user['password_hash']):
            session['user'] = {
                'email': user['email'],
                'name': user['name'],
                'picture': user.get('profile_picture', f"https://ui-avatars.com/api/?name={user['name'].replace(' ', '+')}&background=e0f2fe&color=0284c7")
            }
            storage.update_user_last_login(email)
            return jsonify({"status": "success", "redirect": "/dashboard"})
    except Exception as e:
        print(f"Login DB Error: {e}")
        return jsonify({"status": "error", "message": "Database connection error."}), 500

    return jsonify({"status": "error", "message": "Invalid email or password"}), 401

@app.route('/upload')
@login_required
def upload():
    """Serve the upload prescription page"""
    return send_from_directory(frontend_dir, 'upload.html')

@app.route('/medicines')
@login_required
def medicines():
    """Serve the medicines list page"""
    return send_from_directory(frontend_dir, 'medicines.html')

@app.route('/history')
@login_required
def history():
    """Serve the prescription history page"""
    return send_from_directory(frontend_dir, 'history.html')

@app.route('/profile')
@login_required
def profile():
    """Serve the profile page"""
    return send_from_directory(frontend_dir, 'profile.html')

@app.route('/settings')
@login_required
def settings():
    """Serve the settings page"""
    return send_from_directory(frontend_dir, 'settings.html')

@app.route('/support')
@login_required
def support():
    """Serve the customer care page"""
    return send_from_directory(frontend_dir, 'customer-care.html')

@app.route('/api/config')
def get_config():
    """Return public configuration for the frontend"""
    return jsonify({
        "google_client_id": app.config.get('GOOGLE_CLIENT_ID') or "your_google_client_id_here"
    })

# --- API Endpoints ---
def user_info():
    """Return current user info from session"""
    if 'user' in session:
        return jsonify({"status": "success", "user": session['user']})
    return jsonify({"status": "error", "message": "Not authenticated"}), 401

@app.route('/api/google-login', methods=['POST'])
def google_login():
    """Verify Google token and create or sync session with MongoDB"""
    data = request.json
    token = data.get('token')

    try:
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), app.config['GOOGLE_CLIENT_ID'])

        # Find or create user in MongoDB/SQLite
        user = storage.get_user_by_email(idinfo['email'])
        if not user:
            # Create new user if not exists
            user_data = {
                'google_id': idinfo['sub'],
                'email': idinfo['email'],
                'name': idinfo['name'],
                'profile_picture': idinfo.get('picture'),
                'created_at': datetime.datetime.now(),
                'last_login': datetime.datetime.now()
            }
            storage.insert_user(user_data)
        else:
            # Update last login and sync picture
            storage.update_user_google_info(user['_id'] if '_id' in user else user['id'], idinfo['sub'], idinfo.get('picture'))

        session['user'] = {
            'email': idinfo['email'],
            'name': idinfo['name'],
            'picture': idinfo.get('picture')
        }
        return jsonify({"status": "success", "redirect": "/dashboard"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

# --- Forgot Password System ---

@app.route('/api/request-password-reset', methods=['POST'])
def request_password_reset():
    email = request.json.get('email')
    user = storage.get_user_by_email(email)
    
    if user:
        token = secrets.token_urlsafe(32)
        if not storage.use_sqlite:
            storage.reset_tokens.insert_one({
                'email': email,
                'token': token,
                'created_at': datetime.datetime.now()
            })
        else:
            conn = sqlite3.connect(storage.sqlite_db)
            conn.execute("CREATE TABLE IF NOT EXISTS reset_tokens (email TEXT, token TEXT, created_at DATETIME)")
            conn.execute("INSERT INTO reset_tokens (email, token, created_at) VALUES (?, ?, ?)", 
                         (email, token, datetime.datetime.now().isoformat()))
            conn.commit()
            conn.close()

        reset_link = f"{request.host_url}reset-password?token={token}"
        subject = "Reset Your Prescripto Password"
        body = f"Hello,\n\nClick the link below to reset your password:\n{reset_link}\n\nThis link will expire soon."
        
        if send_email(email, subject, body):
            return jsonify({"status": "success", "message": "Password reset link sent to your email"})
        else:
            print(f"DEBUG: Reset link for {email}: {reset_link}")
            return jsonify({"status": "success", "message": "Demo Mode: Email sending is not configured, but reset link was generated. Check backend console."})
    
    return jsonify({"status": "error", "message": "Email not found"}), 404

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    data = request.json
    token = data.get('token')
    new_password = data.get('password')

    token_data = None
    if not storage.use_sqlite:
        token_data = storage.reset_tokens.find_one({'token': token})
    else:
        conn = sqlite3.connect(storage.sqlite_db)
        conn.row_factory = sqlite3.Row
        token_data = conn.execute("SELECT * FROM reset_tokens WHERE token = ?", (token,)).fetchone()
        conn.close()
        if token_data: token_data = dict(token_data)

    if token_data:
        email = token_data['email']
        new_hashed = hash_password(new_password)
        
        if not storage.use_sqlite:
            storage.users.update_one({'email': email}, {'$set': {'password_hash': new_hashed}})
            storage.reset_tokens.delete_one({'token': token})
        else:
            conn = sqlite3.connect(storage.sqlite_db)
            conn.execute("UPDATE users SET password_hash = ? WHERE email = ?", (new_hashed, email))
            conn.execute("DELETE FROM reset_tokens WHERE token = ?", (token,))
            conn.commit()
            conn.close()

        return jsonify({"status": "success", "message": "Password updated successfully"})
    
    return jsonify({"status": "error", "message": "Invalid or expired token"}), 400

# --- Pages (Password Reset) ---

@app.route('/forgot-password')
def forgot_password_page():
    return send_from_directory(frontend_dir, 'forgot-password.html')

@app.route('/reset-password')
def reset_password_page():
    return send_from_directory(frontend_dir, 'reset-password.html')

@app.route('/generate_schedule', methods=['POST'])
@login_required
def generate_schedule():
    """
    API endpoint to process prescription instructions
    and return a daily schedule JSON response.
    """
    data = request.json
    instructions = data.get('instructions', '')
    
    # Initialize the required schedule dictionary with 4 time slots
    schedule = {
        "morning": [],
        "afternoon": [],
        "evening": [],
        "night": []
    }
    
    if not instructions:
        return jsonify(schedule)

    # Process instructions line by line
    lines = instructions.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        lower_line = line.lower()
        
        # Determine the medicine name
        keywords = ["after breakfast", "after lunch", "after dinner", "after food", "before sleep", "twice daily"]
        matched_keywords = [kw for kw in keywords if kw in lower_line]
        
        medicine = line
        for kw in matched_keywords:
            medicine = re.sub(rf'(?i){re.escape(kw)}', '', medicine)
            
        time_match = re.search(r'\b(1[0-2]|0?[1-9])(?::([0-5][0-9]))?\s*(am|pm)\b', lower_line)
        if time_match:
            medicine = re.sub(rf'(?i)(?:\bat\s+)?{re.escape(time_match.group(0))}', '', medicine)
            
        medicine = medicine.strip(' ,-:')
            
        if not medicine:
            continue

        is_morning = "after breakfast" in lower_line
        is_afternoon = "after lunch" in lower_line or "after food" in lower_line or "twice daily" in lower_line
        is_evening = "after dinner" in lower_line or "twice daily" in lower_line
        is_night = "before sleep" in lower_line
        
        if time_match:
            hour = int(time_match.group(1))
            ampm = time_match.group(3)
            
            if ampm == 'pm' and hour != 12:
                hour += 12
            elif ampm == 'am' and hour == 12:
                hour = 0
                
            if 5 <= hour < 12:
                is_morning = True
            elif 12 <= hour < 17:
                is_afternoon = True
            elif 17 <= hour < 21:
                is_evening = True
            else:
                is_night = True
        
        if is_morning:
            schedule["morning"].append(medicine)
        if is_afternoon:
            schedule["afternoon"].append(medicine)
        if is_evening:
            schedule["evening"].append(medicine)
        if is_night:
            schedule["night"].append(medicine)
            
    return jsonify(schedule)

if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=True, port=5000)
