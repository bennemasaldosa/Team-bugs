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

# Load environment variables
load_dotenv()

# Create Flask app
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
app = Flask(__name__, static_folder=frontend_dir, static_url_path='')

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')

# MongoDB Setup
mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/prescripto')
client = MongoClient(mongo_uri)
db = client.get_database()
users_coll = db.users
reset_tokens_coll = db.password_reset_tokens

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

    hashed = hash_password(password)
    try:
        user_id = users_coll.insert_one({
            'name': name,
            'email': email,
            'password_hash': hashed,
            'created_at': datetime.datetime.now(),
            'last_login': datetime.datetime.now()
        }).inserted_id
        return jsonify({"status": "success", "message": "User registered successfully"})
    except Exception as e:
        print(f"Registration DB Error: {e}")
        return jsonify({"status": "error", "message": "Database connection error. Is MongoDB running?"}), 500

@app.route('/api/login', methods=['POST'])
def login_api():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    is_demo = data.get('is_demo', False)

    if is_demo:
        session['user'] = {
            'email': email or "demo.user@prescripto.com",
            'name': "Demo User",
            'picture': "https://ui-avatars.com/api/?name=Demo+User&background=e0f2fe&color=0284c7"
        }
        return jsonify({"status": "success", "redirect": "/dashboard"})

    try:
        user = users_coll.find_one({'email': email})
        if user and user.get('password_hash') and check_password(password, user['password_hash']):
            session['user'] = {
                'email': user['email'],
                'name': user['name'],
                'picture': user.get('profile_picture', f"https://ui-avatars.com/api/?name={user['name'].replace(' ', '+')}&background=e0f2fe&color=0284c7")
            }
            users_coll.update_one({'_id': user['_id']}, {'$set': {'last_login': datetime.datetime.now()}})
            return jsonify({"status": "success", "redirect": "/dashboard"})
    except Exception as e:
        print(f"Login DB Error: {e}")
        return jsonify({"status": "error", "message": "Database connection error. Please check backend logs."}), 500

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

        # Find or create user in MongoDB
        user = users_coll.find_one({'email': idinfo['email']})
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
            users_coll.insert_one(user_data)
        else:
            # Update last login and sync picture
            users_coll.update_one(
                {'_id': user['_id']}, 
                {'$set': {
                    'google_id': idinfo['sub'],
                    'last_login': datetime.datetime.now(),
                    'profile_picture': idinfo.get('picture')
                }}
            )

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
    data = request.json
    email = data.get('email')

    user = users_coll.find_one({'email': email})
    if not user:
        # For security, don't reveal if user exists. Just return success.
        return jsonify({"status": "success", "message": "If this email is registered, a reset link will be sent."})

    # Generate token
    token = secrets.token_urlsafe(32)
    expires = datetime.datetime.now() + datetime.timedelta(hours=1)

    reset_tokens_coll.update_one(
        {'email': email},
        {'$set': {'token': token, 'expires': expires}},
        upsert=True
    )

    # Send email (In a real app, use the actual domain)
    reset_link = f"{request.host_url}reset-password?token={token}"
    email_body = f"Hello {user['name']},\n\nYou requested to reset your Prescripto password. Click the link below to set a new password:\n\n{reset_link}\n\nThis link will expire in 1 hour."
    
    if send_email(email, "Reset your Prescripto password", email_body):
        return jsonify({"status": "success", "message": "Reset link sent to your email."})
    else:
        return jsonify({"status": "error", "message": "Failed to send email. Please try again later."}), 500

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    data = request.json
    token = data.get('token')
    new_password = data.get('new_password')

    token_record = reset_tokens_coll.find_one({'token': token})
    if not token_record or token_record['expires'] < datetime.datetime.now():
        return jsonify({"status": "error", "message": "Invalid or expired token"}), 400

    email = token_record['email']
    hashed = hash_password(new_password)

    users_coll.update_one({'email': email}, {'$set': {'password_hash': hashed}})
    reset_tokens_coll.delete_one({'email': email})

    return jsonify({"status": "success", "message": "Password updated successfully"})

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
