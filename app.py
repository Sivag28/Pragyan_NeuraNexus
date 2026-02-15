"""
AI Patient Triage System - Enhanced Hackathon Version
Features: Risk Classification, Department Recommendation, Explainability, EHR Loading, Voice Input, MongoDB Integration, User Authentication
"""

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

import os
import joblib
import pandas as pd
import numpy as np
import json
from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import base64
import io
from datetime import datetime
from collections import defaultdict
import heapq
from functools import wraps

# MongoDB Integration
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# Authentication
import hashlib
import secrets

# MongoDB Configuration
MONGO_URI = os.environ.get('MONGO_URI')
MONGO_DB_NAME = 'patientDB'
MONGO_COLLECTION_NAME = 'patients'

# Global MongoDB client and database
mongo_client = None
mongo_db = None
mongo_collection = None
mongo_connected = False

def init_mongodb():
    """Initialize MongoDB connection"""
    global mongo_client, mongo_db, mongo_collection, mongo_connected
    
    try:
        mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Test the connection
        mongo_client.admin.command('ping')
        mongo_db = mongo_client[MONGO_DB_NAME]
        mongo_collection = mongo_db[MONGO_COLLECTION_NAME]
        mongo_connected = True
        print(f"MongoDB Atlas connected successfully!")
        print(f"Database: {MONGO_DB_NAME}")
        print(f"Collection: {MONGO_COLLECTION_NAME}")
        return True
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        mongo_connected = False
        print(f"MongoDB Atlas connection failed: {e}")
        print("Continuing with CSV storage only...")
        return False
    except Exception as e:
        mongo_connected = False
        print(f"MongoDB error: {e}")
        return False

def save_patient_to_mongodb(record: dict):
    """Save a patient record to MongoDB Atlas"""
    global mongo_collection, mongo_connected
    
    if not mongo_connected or mongo_collection is None:
        return False
    
    try:
        # Add timestamp for MongoDB document
        record['created_at'] = datetime.now()
        record['updated_at'] = datetime.now()
        
        # Insert the record
        result = mongo_collection.insert_one(record)
        return True
    except Exception as e:
        print(f"Failed to save patient to MongoDB: {e}")
        return False

def get_patients_from_mongodb(limit: int = None, query: dict = None):
    """Get patients from MongoDB Atlas"""
    global mongo_collection, mongo_connected
    
    if not mongo_connected or mongo_collection is None:
        return []
    
    try:
        cursor = mongo_collection.find(query or {})
        
        if limit:
            cursor = cursor.limit(limit)
        
        # Convert ObjectId to string for JSON serialization
        patients = []
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            patients.append(doc)
        
        return patients
    except Exception as e:
        print(f"Failed to get patients from MongoDB: {e}")
        return []

def search_patients_in_mongodb(search_query: str):
    """Search patients in MongoDB by various fields"""
    global mongo_collection, mongo_connected
    
    if not mongo_connected or mongo_collection is None:
        return []
    
    try:
        # Create search query for multiple fields
        query = {
            '$or': [
                {'patient_id': {'$regex': search_query, '$options': 'i'}},
                {'symptoms': {'$regex': search_query, '$options': 'i'}},
                {'gender': {'$regex': search_query, '$options': 'i'}},
                {'recommended_department': {'$regex': search_query, '$options': 'i'}}
            ]
        }
        
        cursor = mongo_collection.find(query).limit(20)
        
        patients = []
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            patients.append(doc)
        
        return patients
    except Exception as e:
        print(f"Failed to search patients in MongoDB: {e}")
        return []

def get_mongodb_status():
    """Get MongoDB connection status"""
    global mongo_connected, mongo_client
    
    return {
        'connected': mongo_connected,
        'uri': MONGO_URI.split('@')[-1] if '@' in MONGO_URI else MONGO_URI,  # Hide credentials
        'database': MONGO_DB_NAME,
        'collection': MONGO_COLLECTION_NAME
    }
# Optional Hugging Face integration (non-intrusive)
try:
    import hf_integration as hf_integration
except Exception:
    hf_integration = None

# Chatbot integration
try:
    from chatbot_rules import get_chatbot
except Exception:
    get_chatbot = None

app = Flask(__name__)

# Secret key for sessions
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Add CORS headers to all responses
@app.after_request
def add_cors_headers(response):
    """Add CORS headers to all responses"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

# Handle OPTIONS requests for CORS preflight
@app.route('/<path:path>', methods=['OPTIONS'])
@app.route('/', methods=['OPTIONS'])
def handle_options(path='_'):
    """Handle OPTIONS requests for CORS preflight"""
    return '', 204

# User collection for authentication
users_collection = None

def init_users_collection():
    """Initialize the users collection in MongoDB"""
    global users_collection, mongo_db, mongo_connected
    
    if mongo_connected and mongo_db is not None:
        try:
            users_collection = mongo_db['users']
            # Create index on email for fast lookups
            users_collection.create_index('email', unique=True)
            print("Users collection initialized successfully!")
            return users_collection
        except Exception as e:
            print(f"Error initializing users collection: {e}")
            return None
    return None


# Helper function to convert numpy types to Python native types for JSON serialization
def convert_to_native(obj):
    """Recursively convert numpy types to Python native types for JSON serialization"""
    if isinstance(obj, dict):
        return {k: convert_to_native(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_native(item) for item in obj]
    elif hasattr(obj, 'item'):  # numpy types
        return obj.item()
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj

# Columns we persist for each patient entry
PATIENT_CSV_COLUMNS = [
    'patient_id', 'age', 'gender', 'blood_pressure_systolic', 'blood_pressure_diastolic',
    'heart_rate', 'temperature', 'oxygen_saturation', 'pain_level', 'symptoms',
    'pre_existing_conditions', 'risk_level', 'recommended_department'
]


def save_patient_record(record: dict):
    """Append a patient record to the CSV at DATA_PATH and MongoDB.

    Ensures columns match PATIENT_CSV_COLUMNS and creates the file with header
    if it does not exist yet. Also saves to MongoDB if connected.
    Generates a unique patient_id if the provided one already exists.
    """
    try:
        patient_id = record.get('patient_id')
        
        # Check if patient_id already exists in CSV and generate unique one if needed
        if patient_id and os.path.exists(DATA_PATH):
            try:
                existing_df = pd.read_csv(DATA_PATH)
                existing_ids = set(existing_df['patient_id'].astype(str).tolist())
                
                # If patient_id already exists, generate a new unique one
                if str(patient_id) in existing_ids:
                    # Generate unique ID based on timestamp
                    patient_id = f"P_{int(datetime.now().timestamp() * 1000)}"
                    record['patient_id'] = patient_id
                    print(f"Generated unique patient_id: {patient_id}")
            except Exception:
                pass  # If we can't read the file, proceed anyway
        
        # Normalize record to expected columns
        normalized = {col: record.get(col, None) for col in PATIENT_CSV_COLUMNS}

        # Ensure DATA_PATH exists or create with header when writing
        write_header = not os.path.exists(DATA_PATH)

        df_rec = pd.DataFrame([normalized], columns=PATIENT_CSV_COLUMNS)

        # Append to CSV (preserve header only when file missing)
        df_rec.to_csv(DATA_PATH, mode='a', header=write_header, index=False)
        
        # Also save to MongoDB if connected
        if mongo_connected and mongo_collection is not None:
            try:
                record['created_at'] = datetime.now()
                record['updated_at'] = datetime.now()
                mongo_collection.insert_one(record)
                print(f"Patient {record.get('patient_id')} saved to MongoDB")
            except Exception as mongo_err:
                print(f"Failed to save patient to MongoDB: {mongo_err}")
        
        return True
    except Exception as e:
        # Log error server-side and continue
        print(f"Failed to save patient record: {e}")
        return False

# Model and encoder paths
MODEL_PATH = 'risk_model.pkl'
DEPT_MODEL_PATH = 'dept_model.pkl'
SCALER_PATH = 'scaler.pkl'
RISK_ENCODER_PATH = 'risk_encoder.pkl'
DEPT_ENCODER_PATH = 'dept_encoder.pkl'
SYMPTOMS_ENCODER_PATH = 'symptoms_encoder.pkl'
DATA_PATH = 'synthetic_patients.csv'
DEPARTMENT_CAPACITY_FILE = 'department_capacity.json'

# Default department capacity configuration (max patients per department for load balancing)
DEFAULT_DEPARTMENT_CAPACITY = {
    'Cardiology': 10,
    'Pulmonology': 12,
    'Emergency': 15,
    'Neurology': 8,
    'General Surgery': 10,
    'General Medicine': 20,
    'Orthopedics': 8,
    'ENT': 6,
    'Dermatology': 5,
    'Gastroenterology': 7,
    'Vascular Surgery': 5,
    'Infectious Disease': 8
}

# Load or initialize department capacity from file
def load_department_capacity():
    """Load department capacity from JSON file, or use defaults if not found"""
    global DEPARTMENT_CAPACITY
    if os.path.exists(DEPARTMENT_CAPACITY_FILE):
        try:
            with open(DEPARTMENT_CAPACITY_FILE, 'r') as f:
                DEPARTMENT_CAPACITY = json.load(f)
                return DEPARTMENT_CAPACITY
        except Exception as e:
            print(f"Error loading capacity file: {e}")
    # Fall back to defaults
    DEPARTMENT_CAPACITY = DEFAULT_DEPARTMENT_CAPACITY.copy()
    save_department_capacity()
    return DEPARTMENT_CAPACITY

def save_department_capacity():
    """Save current department capacity to JSON file"""
    try:
        with open(DEPARTMENT_CAPACITY_FILE, 'w') as f:
            json.dump(DEPARTMENT_CAPACITY, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving capacity file: {e}")
        return False

DEPARTMENT_CAPACITY = {}

# Department mapping based on symptoms
DEPARTMENT_MAPPING = {
    'chest_pain': 'Cardiology',
    'shortness_of_breath': 'Pulmonology',
    'difficulty_breathing': 'Emergency',
    'chest_pain_difficulty_breathing': 'Emergency',
    'headache': 'Neurology',
    'headache_nausea': 'Neurology',
    'headache_dizziness': 'Neurology',
    'headache_mild_cough': 'Neurology',
    'abdominal_pain': 'General Surgery',
    'abdominal_pain_fever': 'General Surgery',
    'abdominal_pain_nausea': 'Gastroenterology',
    'cough': 'Pulmonology',
    'cough_weakness': 'Pulmonology',
    'persistent_cough': 'Pulmonology',
    'fever_cough': 'Pulmonology',
    'shortness_of_breath_wheezing': 'Pulmonology',
    'cough_blood': 'Pulmonology',
    'fatigue': 'General Medicine',
    'fever_fatigue': 'General Medicine',
    'fatigue_cough': 'Pulmonology',
    'fatigue_shortness_of_breath': 'Pulmonology',
    'mild_cough': 'General Medicine',
    'mild_fatigue': 'General Medicine',
    'sore_throat': 'ENT',
    'sore_throat_cough': 'ENT',
    'dizziness': 'Neurology',
    'general_discomfort': 'General Medicine',
    'mild_discomfort': 'General Medicine',
    'minor_symptoms': 'General Medicine',
    'back_pain': 'Orthopedics',
    'joint_pain_swelling': 'Orthopedics',
    'leg_pain_swelling': 'Vascular Surgery',
    'leg_swelling': 'Cardiology',
    'chest_discomfort': 'Cardiology',
    'chest_pain_sweating': 'Cardiology',
    'chest_pain_palpitations': 'Cardiology',
    'severe_chest_pain': 'Emergency',
    'chest_pain_confusion_sweating': 'Emergency',
    'shortness_of_breath_confusion': 'Emergency',
    'shortness_of_breath_fatigue': 'Pulmonology',
    'fever_chills': 'Infectious Disease',
    'skin_rash': 'Dermatology'
}

# Global state for real-time triage system (Phase 2)
# Tracks patient queues and department load
DEPARTMENT_QUEUES = {dept: [] for dept in DEPARTMENT_CAPACITY.keys()}
PATIENT_REGISTRY = {}  # Track all patients and their status
TRIAGE_SESSION_ID = None


@app.route('/update-department-capacity', methods=['POST'])
def update_department_capacity():
    """Update the capacity for a specific department"""
    try:
        data = request.get_json()
        department = data.get('department')
        capacity = data.get('capacity')
        
        if not department or capacity is None:
            return jsonify({
                'success': False,
                'error': 'Department and capacity are required'
            }), 400
        
        # Validate capacity is a positive integer
        try:
            capacity = int(capacity)
            if capacity <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': 'Capacity must be a positive integer'
            }), 400
        
        # Check if department exists
        if department not in DEPARTMENT_CAPACITY:
            return jsonify({
                'success': False,
                'error': f'Department {department} not found'
            }), 400
        
        # Update the capacity
        old_capacity = DEPARTMENT_CAPACITY[department]
        DEPARTMENT_CAPACITY[department] = capacity
        
        # Save to file for persistence
        save_department_capacity()
        
        return jsonify({
            'success': True,
            'message': f'Capacity for {department} updated from {old_capacity} to {capacity}',
            'department': department,
            'old_capacity': old_capacity,
            'new_capacity': capacity
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/get-department-capacity', methods=['GET'])
def get_department_capacity():
    """Get the current department capacity configuration"""
    try:
        return jsonify({
            'success': True,
            'department_capacity': DEPARTMENT_CAPACITY
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

class TriagePatient:
    """Represents a patient in the triage system"""
    def __init__(self, patient_id, risk_level, department, arrival_time=None):
        self.patient_id = patient_id
        self.risk_level = risk_level
        self.department = department
        self.arrival_time = arrival_time or datetime.now()
        self.queue_position = None
        self.priority_score = self._calculate_priority()
        
    def _calculate_priority(self):
        """Calculate priority score (higher = more urgent)"""
        risk_scores = {'high': 100, 'medium': 50, 'low': 10}
        age_minutes = (datetime.now() - self.arrival_time).total_seconds() / 60
        base_score = risk_scores.get(self.risk_level, 10)
        # Add bonus for wait time (patients who waited longer get priority)
        wait_bonus = min(age_minutes * 0.1, 30)  # Max 30 point bonus
        return base_score + wait_bonus
    
    def __lt__(self, other):
        """For heapq priority queue - higher priority score = lower heap value"""
        return self.priority_score > other.priority_score


def train_models():
    """Train the risk prediction and department recommendation models"""
    print("Training enhanced models...")
    
    # Load the dataset
    df = pd.read_csv(DATA_PATH)
    
    # Prepare features for risk prediction
    symptoms_encoder = LabelEncoder()
    df['symptoms_encoded'] = symptoms_encoder.fit_transform(df['symptoms'])
    
    risk_encoder = LabelEncoder()
    df['risk_level_encoded'] = risk_encoder.fit_transform(df['risk_level'])
    
    dept_encoder = LabelEncoder()
    df['dept_encoded'] = dept_encoder.fit_transform(df['recommended_department'])
    
    # Feature columns for risk prediction
    risk_feature_cols = ['age', 'blood_pressure_systolic', 'blood_pressure_diastolic', 
                        'heart_rate', 'temperature', 'oxygen_saturation', 'pain_level']
    
    X = df[risk_feature_cols]
    y_risk = df['risk_level_encoded']
    y_dept = df['dept_encoded']
    
    # Split data
    X_train, X_test, y_risk_train, y_risk_test = train_test_split(X, y_risk, test_size=0.2, random_state=42)
    _, _, y_dept_train, y_dept_test = train_test_split(X, y_dept, test_size=0.2, random_state=42)
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train Risk Prediction Model (Random Forest)
    risk_model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
    risk_model.fit(X_train_scaled, y_risk_train)
    
    # Train Department Recommendation Model (Gradient Boosting)
    dept_model = GradientBoostingClassifier(n_estimators=100, random_state=42, max_depth=5)
    dept_model.fit(X_train_scaled, y_dept_train)
    
    # Evaluate models
    risk_accuracy = risk_model.score(X_test_scaled, y_risk_test)
    dept_accuracy = dept_model.score(X_test_scaled, y_dept_test)
    print(f"Risk Model accuracy: {risk_accuracy:.2f}")
    print(f"Department Model accuracy: {dept_accuracy:.2f}")
    
    # Save models and preprocessing objects
    joblib.dump(risk_model, MODEL_PATH)
    joblib.dump(dept_model, DEPT_MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    joblib.dump(risk_encoder, RISK_ENCODER_PATH)
    joblib.dump(dept_encoder, DEPT_ENCODER_PATH)
    joblib.dump(symptoms_encoder, SYMPTOMS_ENCODER_PATH)
    
    print("Models trained and saved successfully!")
    return risk_model, dept_model, scaler, risk_encoder, dept_encoder, symptoms_encoder

def load_models():
    """Load the trained models and preprocessing objects"""
    if os.path.exists(MODEL_PATH) and os.path.exists(DEPT_MODEL_PATH):
        risk_model = joblib.load(MODEL_PATH)
        dept_model = joblib.load(DEPT_MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        risk_encoder = joblib.load(RISK_ENCODER_PATH)
        dept_encoder = joblib.load(DEPT_ENCODER_PATH)
        symptoms_encoder = joblib.load(SYMPTOMS_ENCODER_PATH)
        print("Models loaded successfully!")
        return risk_model, dept_model, scaler, risk_encoder, dept_encoder, symptoms_encoder
    else:
        return train_models()

# Load models on startup
print("Loading AI Patient Triage System (Hackathon Version)...")
risk_model, dept_model, scaler, risk_encoder, dept_encoder, symptoms_encoder = load_models()

# Load persistent department capacity configuration
DEPARTMENT_CAPACITY = load_department_capacity()
print(f"Department capacity loaded. Total capacity: {sum(DEPARTMENT_CAPACITY.values())} beds")

# Reinitialize DEPARTMENT_QUEUES with loaded capacity
DEPARTMENT_QUEUES = {dept: [] for dept in DEPARTMENT_CAPACITY.keys()}

# Initialize MongoDB connection
print("Initializing MongoDB Atlas connection...")
init_mongodb()

# Initialize users collection
print("Initializing users collection...")
init_users_collection()

# ==================== MongoDB Status Endpoint ====================

@app.route('/mongodb/status', methods=['GET'])
def mongodb_status():
    """Get MongoDB Atlas connection status"""
    try:
        status = get_mongodb_status()
        return jsonify({
            'success': True,
            'mongodb': status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

# ==================== Authentication Routes ====================

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    """Verify a password against a hash"""
    return hash_password(password) == hashed

@app.route('/login')
def login_page():
    """Render the login page"""
    # If user is already logged in, redirect to index
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/register')
def register_page():
    """Render the registration page"""
    # If user is already logged in, redirect to index
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    """Handle login request"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({
                'success': False,
                'error': 'Email and password are required'
            }), 400
        
        # Check if users collection is available
        if users_collection is None:
            return jsonify({
                'success': False,
                'error': 'Database not available. Please try again later.'
            }), 500
        
        # Find user by email
        user = users_collection.find_one({'email': email})
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'Invalid email or password'
            }), 401
        
        # Verify password
        if not verify_password(password, user.get('password', '')):
            return jsonify({
                'success': False,
                'error': 'Invalid email or password'
            }), 401
        
        # Set session
        session['user_id'] = str(user.get('_id'))
        session['user_name'] = user.get('name', '')
        session['user_email'] = user.get('email', '')
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'redirect': '/',
            'user': {
                'name': user.get('name', ''),
                'email': user.get('email', '')
            }
        })
        
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({
            'success': False,
            'error': 'An error occurred during login'
        }), 500

@app.route('/register', methods=['POST'])
def register():
    """Handle registration request"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not name or not email or not password:
            return jsonify({
                'success': False,
                'error': 'Name, email, and password are required'
            }), 400
        
        if len(password) < 6:
            return jsonify({
                'success': False,
                'error': 'Password must be at least 6 characters long'
            }), 400
        
        # Check if users collection is available
        if users_collection is None:
            return jsonify({
                'success': False,
                'error': 'Database not available. Please try again later.'
            }), 500
        
        # Check if email already exists
        existing_user = users_collection.find_one({'email': email})
        if existing_user:
            return jsonify({
                'success': False,
                'error': 'Email already registered'
            }), 409
        
        # Create new user
        new_user = {
            'name': name,
            'email': email,
            'password': hash_password(password),
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        # Insert user into database
        result = users_collection.insert_one(new_user)
        
        if result.inserted_id:
            return jsonify({
                'success': True,
                'message': 'Account created successfully! Please login.'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to create account. Please try again.'
            }), 500
        
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({
            'success': False,
            'error': 'An error occurred during registration'
        }), 500

@app.route('/logout', methods=['POST'])
def logout():
    """Handle logout request"""
    try:
        # Clear session
        session.clear()
        return jsonify({
            'success': True,
            'message': 'Logged out successfully',
            'redirect': '/login'
        })
    except Exception as e:
        print(f"Logout error: {e}")
        return jsonify({
            'success': False,
            'error': 'An error occurred during logout'
        }), 500

@app.route('/check-auth', methods=['GET'])
def check_auth():
    """Check if user is authenticated"""
    if 'user_id' in session:
        return jsonify({
            'success': True,
            'authenticated': True,
            'user': {
                'name': session.get('user_name', ''),
                'email': session.get('user_email', '')
            }
        })
    return jsonify({
        'success': True,
        'authenticated': False
    })

@app.route('/')
def index():
    """Render the main page - requires authentication"""
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    """Make a risk prediction and department recommendation based on patient data"""
    try:
        data = request.get_json()
        
        # Extract features
        age = float(data.get('age', 0))
        bp_systolic = float(data.get('blood_pressure_systolic', 0))
        bp_diastolic = float(data.get('blood_pressure_diastolic', 0))
        heart_rate = float(data.get('heart_rate', 0))
        temperature = float(data.get('temperature', 0))
        oxygen_saturation = float(data.get('oxygen_saturation', 0))
        pain_level = int(data.get('pain_level', 0))
        symptoms = data.get('symptoms', '')
        
        # Create feature DataFrame
        feature_cols = ['age', 'blood_pressure_systolic', 'blood_pressure_diastolic', 
                       'heart_rate', 'temperature', 'oxygen_saturation', 'pain_level']
        features = pd.DataFrame([[age, bp_systolic, bp_diastolic, heart_rate, 
                                temperature, oxygen_saturation, pain_level]], 
                               columns=feature_cols)
        
        # Scale features
        features_scaled = scaler.transform(features)
        
        # Make risk prediction
        risk_prediction = risk_model.predict(features_scaled)[0]
        risk_level = risk_encoder.inverse_transform([risk_prediction])[0]
        
        # Get risk probabilities
        risk_proba = risk_model.predict_proba(features_scaled)[0]
        risk_confidence = max(risk_proba) * 100
        
        # Make department prediction
        dept_prediction = dept_model.predict(features_scaled)[0]
        recommended_dept = dept_encoder.inverse_transform([dept_prediction])[0]
        
        # Get department confidence
        dept_proba = dept_model.predict_proba(features_scaled)[0]
        dept_confidence = max(dept_proba) * 100
        
        # Generate explainability factors
        explainability = generate_explainability(age, bp_systolic, bp_diastolic, heart_rate, 
                                                  temperature, oxygen_saturation, pain_level, risk_level)
        # Persist the patient entry to CSV so dashboards and analyses include this submission
        patient_id = data.get('patient_id', f"P_{int(datetime.now().timestamp() * 1000)}")
        patient_record = {
            'patient_id': patient_id,
            'age': age,
            'gender': data.get('gender', None),
            'blood_pressure_systolic': bp_systolic,
            'blood_pressure_diastolic': bp_diastolic,
            'heart_rate': heart_rate,
            'temperature': temperature,
            'oxygen_saturation': oxygen_saturation,
            'pain_level': pain_level,
            'symptoms': symptoms,
            'pre_existing_conditions': data.get('pre_existing_conditions', None),
            'risk_level': risk_level,
            'recommended_department': recommended_dept
        }
        save_patient_record(patient_record)
        
        return jsonify({
            'success': True,
            'risk_level': risk_level,
            'risk_confidence': f"{risk_confidence:.1f}%",
            'recommended_department': recommended_dept,
            'dept_confidence': f"{dept_confidence:.1f}%",
            'explainability': explainability,
            'message': f'Patient assessed as {risk_level} risk. Recommended: {recommended_dept}.'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

def generate_explainability(age, bp_systolic, bp_diastolic, heart_rate, temperature, oxygen_saturation, pain_level, risk_level):
    """Generate explainability factors for the prediction"""
    factors = []
    
    # Age factor
    if age > 65:
        factors.append({'factor': 'Age > 65', 'contribution': 'high', 'description': 'Advanced age increases health risks'})
    elif age < 18:
        factors.append({'factor': 'Age < 18', 'contribution': 'medium', 'description': 'Young patients require special consideration'})
    
    # Blood pressure factor
    if bp_systolic > 140 or bp_diastolic > 90:
        factors.append({'factor': 'High Blood Pressure', 'contribution': 'high', 'description': f'BP {bp_systolic}/{bp_diastolic} mmHg indicates hypertension'})
    elif bp_systolic < 90 or bp_diastolic < 60:
        factors.append({'factor': 'Low Blood Pressure', 'contribution': 'medium', 'description': f'BP {bp_systolic}/{bp_diastolic} mmHg indicates hypotension'})
    
    # Heart rate factor
    if heart_rate > 100:
        factors.append({'factor': 'Tachycardia', 'contribution': 'medium', 'description': f'Heart rate {heart_rate} bpm indicates elevated heart activity'})
    elif heart_rate < 60:
        factors.append({'factor': 'Bradycardia', 'contribution': 'medium', 'description': f'Heart rate {heart_rate} bpm indicates slow heart activity'})
    
    # Temperature factor
    if temperature > 100.4:
        factors.append({'factor': 'Fever', 'contribution': 'medium', 'description': f'Temperature {temperature}°F indicates fever'})
    
    # Oxygen saturation factor
    if oxygen_saturation < 95:
        factors.append({'factor': 'Low Oxygen', 'contribution': 'high', 'description': f'O2 saturation {oxygen_saturation}% indicates potential hypoxia'})
    
    # Pain level factor
    if pain_level >= 7:
        factors.append({'factor': 'High Pain', 'contribution': 'high', 'description': f'Pain level {pain_level}/10 indicates severe pain'})
    elif pain_level >= 4:
        factors.append({'factor': 'Moderate Pain', 'contribution': 'medium', 'description': f'Pain level {pain_level}/10 indicates moderate discomfort'})
    
    # Risk level summary
    if risk_level == 'high':
        factors.append({'factor': 'Overall Risk', 'contribution': 'critical', 'description': 'Patient requires immediate medical attention'})
    elif risk_level == 'medium':
        factors.append({'factor': 'Overall Risk', 'contribution': 'moderate', 'description': 'Patient requires monitoring and follow-up'})
    else:
        factors.append({'factor': 'Overall Risk', 'contribution': 'low', 'description': 'Patient condition appears stable'})
    
    return factors

@app.route('/predict-batch', methods=['POST'])
def predict_batch():
    """Make predictions for multiple patients (Real-time Triage Simulation)"""
    try:
        patients = request.get_json().get('patients', [])
        results = []
        
        feature_cols = ['age', 'blood_pressure_systolic', 'blood_pressure_diastolic', 
                       'heart_rate', 'temperature', 'oxygen_saturation', 'pain_level']
        
        for patient in patients:
            # Extract only the feature columns needed
            patient_features = {col: patient.get(col, 0) for col in feature_cols}
            features = pd.DataFrame([patient_features], columns=feature_cols)
            features_scaled = scaler.transform(features)
            
            risk_pred = risk_model.predict(features_scaled)[0]
            risk_level = risk_encoder.inverse_transform([risk_pred])[0]
            
            dept_pred = dept_model.predict(features_scaled)[0]
            recommended_dept = dept_encoder.inverse_transform([dept_pred])[0]
            # Persist each patient record
            pid = patient.get('patient_id', f"P_{int(datetime.now().timestamp() * 1000)}")
            patient_record = {
                'patient_id': pid,
                'age': patient.get('age', None),
                'gender': patient.get('gender', None),
                'blood_pressure_systolic': patient.get('blood_pressure_systolic', None),
                'blood_pressure_diastolic': patient.get('blood_pressure_diastolic', None),
                'heart_rate': patient.get('heart_rate', None),
                'temperature': patient.get('temperature', None),
                'oxygen_saturation': patient.get('oxygen_saturation', None),
                'pain_level': patient.get('pain_level', None),
                'symptoms': patient.get('symptoms', None),
                'pre_existing_conditions': patient.get('pre_existing_conditions', None),
                'risk_level': risk_level,
                'recommended_department': recommended_dept,
               
            }
            save_patient_record(patient_record)

            results.append({
                'patient_id': pid,
                'risk_level': risk_level,
                'recommended_department': recommended_dept
            })
        
        # Sort by risk level (high first)
        risk_order = {'high': 0, 'medium': 1, 'low': 2}
        results.sort(key=lambda x: risk_order.get(x['risk_level'], 3))
        
        return jsonify({
            'success': True,
            'results': results,
            'total_patients': len(results)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/model-info', methods=['GET'])
def model_info():
    """Get information about the models"""
    return jsonify({
        'risk_model_type': 'Random Forest Classifier',
        'dept_model_type': 'Gradient Boosting Classifier',
        'features': ['age', 'blood_pressure_systolic', 'blood_pressure_diastolic', 
                    'heart_rate', 'temperature', 'oxygen_saturation', 'pain_level'],
        'risk_levels': list(risk_encoder.classes_),
        'departments': list(dept_encoder.classes_)
    })


@app.route('/hf/available', methods=['GET'])
def hf_available():
    """Health check for optional Hugging Face integration."""
    try:
        if hf_integration is None:
            return jsonify({'success': True, 'hf_available': False, 'message': 'hf_integration module not installed'}), 200
        return jsonify({'success': True, 'hf_available': hf_integration.available()}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/hf/configure', methods=['POST'])
def hf_configure():
    """Configure the Hugging Face API token.
    
    Request body:
    {
        "token": "hf_xxxxxxxxxxxxx"
    }
    
    Returns:
    {
        "success": true,
        "message": "Token configured successfully",
        "status": {
            "token_set": true,
            "token_prefix": "hf_tWSayYg...",
            "model": "sentence-transformers/all-MiniLM-L6-v2",
            "use_api": true
        }
    }
    """
    try:
        if hf_integration is None:
            return jsonify({'success': False, 'error': 'hf_integration module not installed'}), 503
            
        data = request.get_json()
        token = data.get('token', '')
        
        if not token:
            return jsonify({'success': False, 'error': 'No token provided'}), 400
        
        # Set the token
        success = hf_integration.set_token(token)
        
        if success:
            status = hf_integration.get_token_status()
            return jsonify({
                'success': True,
                'message': 'Token configured successfully',
                'status': status
            })
        else:
            return jsonify({'success': False, 'error': 'Invalid token format'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/hf/status', methods=['GET'])
def hf_status():
    """Get the current status of the Hugging Face integration."""
    try:
        if hf_integration is None:
            return jsonify({'success': True, 'hf_available': False, 'message': 'hf_integration module not installed'}), 200
        
        status = hf_integration.get_token_status()
        status['hf_available'] = hf_integration.available()
        
        return jsonify({'success': True, 'status': status}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/hf/embedding', methods=['POST'])
def hf_embedding():
    """Return a text embedding using the local Hugging Face model (optional).

    This endpoint is additive and does not alter existing prediction endpoints.
    """
    try:
        data = request.get_json()
        text = data.get('text', '')
        if not text:
            return jsonify({'success': False, 'error': 'No text provided'}), 400

        if hf_integration is None:
            return jsonify({'success': False, 'error': 'hf_integration not available'}), 503

        emb = hf_integration.get_embedding(text)
        if emb is None:
            return jsonify({'success': False, 'error': 'embedding failed or HF unavailable'}), 503

        return jsonify({'success': True, 'embedding_length': len(emb), 'embedding': emb})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/fairness-analysis', methods=['GET'])
def fairness_analysis():
    """Perform comprehensive bias and fairness analysis on the model"""
    try:
        df = pd.read_csv(DATA_PATH)
        # validate columns
        if 'risk_level' not in df.columns:
            return jsonify({'success': False, 'error': 'Dataset missing required column: risk_level'}), 400
        
        # 1. Demographic Fairness Analysis - Age Groups
        age_groups = {
            'young (< 35)': df[df['age'] < 35], 
            'middle (35-60)': df[(df['age'] >= 35) & (df['age'] < 60)],
            'senior (60+)': df[df['age'] >= 60]
        }
        
        age_fairness = {}
        for group_name, group_df in age_groups.items():
            if len(group_df) > 0:
                risk_dist = group_df['risk_level'].value_counts().to_dict()
                high_risk_pct = (risk_dist.get('high', 0) / len(group_df)) * 100
                age_fairness[group_name] = {
                    'count': len(group_df),
                    'high_risk_percentage': round(high_risk_pct, 2),
                    'risk_distribution': risk_dist,
                    'avg_age': round(group_df['age'].mean(), 1),
                    'avg_pain_level': round(group_df['pain_level'].mean(), 2)
                }
        
        # 2. Gender Fairness Analysis
        gender_fairness = {}
        if 'gender' in df.columns:
            for gender in df['gender'].dropna().unique():
                gender_df = df[df['gender'] == gender]
                if len(gender_df) > 0:
                    risk_dist = gender_df['risk_level'].value_counts().to_dict()
                    high_risk_pct = (risk_dist.get('high', 0) / len(gender_df)) * 100
                    gender_fairness[gender] = {
                        'count': len(gender_df),
                        'high_risk_percentage': round(high_risk_pct, 2),
                        'risk_distribution': risk_dist,
                        'avg_heart_rate': round(gender_df['heart_rate'].mean(), 1)
                    }
        
        # 3. Pre-existing Conditions Fairness Analysis
        conditions_fairness = {}
        if 'pre_existing_conditions' in df.columns:
            conditions = df['pre_existing_conditions'].dropna().unique()
            for condition in conditions:
                cond_df = df[df['pre_existing_conditions'] == condition]
                if len(cond_df) > 0:
                    risk_dist = cond_df['risk_level'].value_counts().to_dict()
                    high_risk_pct = (risk_dist.get('high', 0) / len(cond_df)) * 100
                    conditions_fairness[condition] = {
                        'count': len(cond_df),
                        'high_risk_percentage': round(high_risk_pct, 2),
                        'risk_distribution': risk_dist,
                        'avg_bp_systolic': round(cond_df['blood_pressure_systolic'].mean(), 1)
                    }
        
        # 4. Calculate Fairness Metrics
        fairness_metrics = calculate_fairness_metrics(age_fairness, gender_fairness)
        
        return jsonify({
            'success': True,
            'demographic_fairness': {
                'age_groups': age_fairness,
                'gender': gender_fairness,
                'pre_existing_conditions': conditions_fairness
            },
            'fairness_metrics': fairness_metrics,
            'message': 'Comprehensive fairness analysis completed successfully'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

def calculate_fairness_metrics(age_fairness, gender_fairness):
    """Calculate fairness metrics including disparate impact, equal opportunity, statistical parity"""
    metrics = {}
    
    # Statistical Parity Difference (SPD) across age groups
    if age_fairness:
        age_high_risk = [v['high_risk_percentage'] for v in age_fairness.values() if v.get('count', 0) > 0]
        if age_high_risk and len(age_high_risk) > 1:
            spd_age = max(age_high_risk) - min(age_high_risk)
            metrics['age_statistical_parity_difference'] = round(spd_age, 2)
            metrics['age_disparity_assessment'] = 'High Disparity' if spd_age > 15 else 'Moderate Disparity' if spd_age > 5 else 'Low Disparity'
    
    # Disparate Impact Ratio across gender
    if gender_fairness and len(gender_fairness) >= 2:
        gender_high_risk = [v['high_risk_percentage'] for v in gender_fairness.values() if v.get('count', 0) > 0]
        if gender_high_risk and len(gender_high_risk) >= 2 and max(gender_high_risk) > 0:
            min_val = min(gender_high_risk)
            max_val = max(gender_high_risk)
            if min_val > 0 and max_val > 0:
                di_ratio = min_val / max_val
                metrics['gender_disparate_impact_ratio'] = round(di_ratio, 3)
                metrics['gender_disparity_assessment'] = 'Potential Bias' if di_ratio < 0.80 else 'Fair'
    
    return metrics

@app.route('/department-fairness', methods=['GET'])
def department_fairness():
    """Analyze fairness at department level and identify overcrowding"""
    try:
        df = pd.read_csv(DATA_PATH)
        
        # Analyze how patients are distributed across departments
        dept_analysis = {}
        for dept in df['recommended_department'].unique():
            dept_df = df[df['recommended_department'] == dept]
            risk_dist = dept_df['risk_level'].value_counts().to_dict()
            
            # Calculate metrics
            high_risk_count = risk_dist.get('high', 0)
            medium_risk_count = risk_dist.get('medium', 0)
            
            dept_analysis[dept] = {
                'total_patients': len(dept_df),
                'capacity': DEPARTMENT_CAPACITY.get(dept, 10),
                'utilization_percentage': round((len(dept_df) / DEPARTMENT_CAPACITY.get(dept, 10)) * 100, 1),
                'high_risk_count': high_risk_count,
                'medium_risk_count': medium_risk_count,
                'risk_distribution': risk_dist,
                'avg_wait_time_estimate_minutes': round(len(dept_df) * 1.5, 1),  # Estimate: 1.5 min per patient
                'overcrowding_status': 'OVERCROWDED' if (len(dept_df) / DEPARTMENT_CAPACITY.get(dept, 10)) > 1.0 else 'AT CAPACITY' if (len(dept_df) / DEPARTMENT_CAPACITY.get(dept, 10)) > 0.8 else 'AVAILABLE'
            }
        
        # Identify fairness issues
        fairness_issues = []
        high_risk_patients_per_dept = {k: v['high_risk_count'] for k, v in dept_analysis.items()}
        max_risk_dept = max(high_risk_patients_per_dept, key=high_risk_patients_per_dept.get)
        
        if dept_analysis[max_risk_dept]['utilization_percentage'] > 100:
            fairness_issues.append({
                'issue': 'Overcrowded High-Risk Department',
                'department': max_risk_dept,
                'severity': 'CRITICAL',
                'recommendation': f'Redistribute high-risk patients from {max_risk_dept} to available departments'
            })
        
        return jsonify({
            'success': True,
            'department_analysis': dept_analysis,
            'fairness_issues': fairness_issues,
            'message': 'Department-level fairness analysis completed'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/bias-detection', methods=['GET'])
def bias_detection():
    """Detect potential biases in model predictions and provide mitigation recommendations"""
    try:
        df = pd.read_csv(DATA_PATH)
        
        biases_found = []
        recommendations = []
        
        # Check for age-based bias
        young_high_risk = len(df[(df['age'] < 35) & (df['risk_level'] == 'high')])
        senior_high_risk = len(df[(df['age'] >= 60) & (df['risk_level'] == 'high')])
        young_total = len(df[df['age'] < 35])
        senior_total = len(df[df['age'] >= 60])
        
        if young_total > 0 and senior_total > 0:
            young_rate = young_high_risk / young_total
            senior_rate = senior_high_risk / senior_total
            
            bias_ratio = young_rate / senior_rate if senior_rate > 0 else 0
            if bias_ratio < 0.7 or bias_ratio > 1.3:
                biases_found.append({
                    'bias_type': 'Age-based Risk Classification',
                    'severity': 'HIGH' if abs(bias_ratio - 1) > 0.5 else 'MEDIUM',
                    'description': f'Young patients: {young_rate*100:.1f}% high-risk vs Senior: {senior_rate*100:.1f}% high-risk',
                    'bias_ratio': round(bias_ratio, 3)
                })
                recommendations.append({
                    'recommendation': 'Review age weighting in risk model',
                    'action': 'Audit model feature importance for age-related features',
                    'priority': 'High'
                })
        
        # Check for gender-based bias
        if 'gender' in df.columns:
            # Drop null gender values and get unique genders
            valid_genders = df['gender'].dropna().unique()
            
            if len(valid_genders) >= 2:
                risk_rates = []
                for gender in valid_genders:
                    gender_df = df[df['gender'] == gender]
                    if len(gender_df) > 0:
                        high_risk_count = len(gender_df[gender_df['risk_level'] == 'high'])
                        risk_pct = high_risk_count / len(gender_df)
                        risk_rates.append((gender, risk_pct))
                
                # Only calculate bias if we have at least 2 valid gender groups with risk rates
                if len(risk_rates) >= 2:
                    rates_sorted = sorted(risk_rates, key=lambda x: x[1])
                    # Get the highest and lowest non-zero rates
                    non_zero_rates = [r for r in rates_sorted if r[1] > 0]
                    if len(non_zero_rates) >= 2:
                        bias_ratio = non_zero_rates[0][1] / non_zero_rates[1][1]
                        if bias_ratio < 0.8:
                            biases_found.append({
                                'bias_type': 'Gender-based Risk Classification',
                                'severity': 'MEDIUM',
                                'description': f'{non_zero_rates[0][0]}: {non_zero_rates[0][1]*100:.1f}% vs {non_zero_rates[1][0]}: {non_zero_rates[1][1]*100:.1f}%',
                                'bias_ratio': round(bias_ratio, 3)
                            })
                            recommendations.append({
                                'recommendation': 'Evaluate gender representation in training data',
                                'action': 'Ensure balanced gender representation and revalidate model',
                                'priority': 'High'
                            })
        
        return jsonify({
            'success': True,
            'biases_detected': biases_found,
            'mitigation_recommendations': recommendations,
            'bias_summary': f'{len(biases_found)} potential biases detected',
            'message': 'Bias detection analysis completed'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/resource-allocation', methods=['GET'])
def resource_allocation():
    """Analyze resource allocation across departments"""
    try:
        df = pd.read_csv(DATA_PATH)
        
        # Allocate resources based on risk levels and patient volume
        allocation_plan = {}
        total_high_risk = len(df[df['risk_level'] == 'high'])
        total_medium_risk = len(df[df['risk_level'] == 'medium'])
        total_low_risk = len(df[df['risk_level'] == 'low'])
        
        for dept in df['recommended_department'].unique():
            dept_df = df[df['recommended_department'] == dept]
            high_risk_count = len(dept_df[dept_df['risk_level'] == 'high'])
            medium_risk_count = len(dept_df[dept_df['risk_level'] == 'medium'])
            
            # Calculate resource allocation score (weighted by risk)
            risk_weighted_score = (high_risk_count * 3) + (medium_risk_count * 1.5)
            
            allocation_plan[dept] = {
                'current_patients': len(dept_df),
                'high_risk_patients': high_risk_count,
                'medium_risk_patients': medium_risk_count,
                'risk_weighted_score': round(risk_weighted_score, 1),
                'recommended_staff': max(2, int((high_risk_count * 2 + medium_risk_count * 1) / 3) + 1),
                'recommended_beds': max(DEPARTMENT_CAPACITY.get(dept, 10), len(dept_df) + 2),
                'recommended_equipment': []
            }
            
            # Recommend equipment based on patient types
            if high_risk_count > 0:
                allocation_plan[dept]['recommended_equipment'].extend(['ICU Monitoring', 'Emergency Cart'])
            if 'Cardiology' in dept:
                allocation_plan[dept]['recommended_equipment'].extend(['ECG Machine', 'Defibrillator'])
            if 'Pulmonology' in dept:
                allocation_plan[dept]['recommended_equipment'].extend(['Oxygen Supply', 'Ventilator'])
        
        # Calculate total resource needs
        total_staff = sum(v['recommended_staff'] for v in allocation_plan.values())
        
        return jsonify({
            'success': True,
            'allocation_plan': allocation_plan,
            'total_recommended_staff': total_staff,
            'risk_distribution': {
                'high_risk_total': total_high_risk,
                'medium_risk_total': total_medium_risk,
                'low_risk_total': total_low_risk
            },
            'message': 'Resource allocation analysis completed'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/wearable-import', methods=['POST'])
def wearable_import():
    """Import patient data from wearable device JSON"""
    try:
        data = request.get_json()
        
        # Extract vital signs from wearable data
        wearable_data = data.get('wearable_data', {})
        
        # Map wearable data to our format
        patient_data = {
            'age': wearable_data.get('age', 0),
            'gender': data.get('gender', wearable_data.get('gender', None)),
            'blood_pressure_systolic': wearable_data.get('systolic_bp', 0),
            'blood_pressure_diastolic': wearable_data.get('diastolic_bp', 0),
            'heart_rate': wearable_data.get('heart_rate', 0),
            'temperature': wearable_data.get('body_temperature', 98.6),
            'oxygen_saturation': wearable_data.get('spo2', 98),
            'pain_level': wearable_data.get('pain_level', 0),
            'symptoms': wearable_data.get('symptoms', '')
        }
        
        # Make prediction with proper feature columns
        feature_cols = ['age', 'blood_pressure_systolic', 'blood_pressure_diastolic', 
                       'heart_rate', 'temperature', 'oxygen_saturation', 'pain_level']
        features = pd.DataFrame([[patient_data[col] for col in feature_cols]], 
                               columns=feature_cols)
        features_scaled = scaler.transform(features)
        
        risk_pred = risk_model.predict(features_scaled)[0]
        risk_level = risk_encoder.inverse_transform([risk_pred])[0]
        
        dept_pred = dept_model.predict(features_scaled)[0]
        recommended_dept = dept_encoder.inverse_transform([dept_pred])[0]
        # Persist wearable-imported patient
        patient_id = wearable_data.get('patient_id', f"P_{int(datetime.now().timestamp() * 1000)}")
        record = {
            'patient_id': patient_id,
            'age': patient_data.get('age'),
            'gender': data.get('gender', None),
            'blood_pressure_systolic': patient_data.get('blood_pressure_systolic'),
            'blood_pressure_diastolic': patient_data.get('blood_pressure_diastolic'),
            'heart_rate': patient_data.get('heart_rate'),
            'temperature': patient_data.get('temperature'),
            'oxygen_saturation': patient_data.get('oxygen_saturation'),
            'pain_level': patient_data.get('pain_level'),
            'symptoms': patient_data.get('symptoms'),
            'pre_existing_conditions': data.get('pre_existing_conditions', None),
            'risk_level': risk_level,
            'recommended_department': recommended_dept
        }
        save_patient_record(record)

        # Calculate confidences and explainability
        try:
            risk_proba = risk_model.predict_proba(features_scaled)[0]
            risk_confidence = max(risk_proba) * 100
        except Exception:
            risk_confidence = None

        try:
            dept_proba = dept_model.predict_proba(features_scaled)[0]
            dept_confidence = max(dept_proba) * 100
        except Exception:
            dept_confidence = None

        explainability = generate_explainability(
            patient_data.get('age', 0),
            patient_data.get('blood_pressure_systolic', 0),
            patient_data.get('blood_pressure_diastolic', 0),
            patient_data.get('heart_rate', 0),
            patient_data.get('temperature', 0),
            patient_data.get('oxygen_saturation', 0),
            patient_data.get('pain_level', 0),
            risk_level
        )

        return jsonify({
            'success': True,
            'patient_data': patient_data,
            'risk_level': risk_level,
            'risk_confidence': f"{risk_confidence:.1f}%" if risk_confidence is not None else None,
            'recommended_department': recommended_dept,
            'dept_confidence': f"{dept_confidence:.1f}%" if dept_confidence is not None else None,
            'explainability': explainability,
            'patient_id': patient_id,
            'message': 'Data imported from wearable device successfully'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


# ==================== EHR/EMR DOCUMENT IMPORT ====================

@app.route('/ehr-import', methods=['POST'])
def ehr_import():
    """Import patient data from EHR/EMR document (JSON format)"""
    try:
        # Check if request has file upload or JSON data
        ehr_data = None
        
        # Try to get JSON data first
        if request.is_json:
            ehr_data = request.get_json()
        # Check for file upload
        elif 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                return jsonify({'success': False, 'error': 'No file selected'}), 400
            
            # Read JSON file
            import json
            try:
                ehr_data = json.load(file)
            except json.JSONDecodeError as e:
                return jsonify({'success': False, 'error': f'Invalid JSON file: {str(e)}'}), 400
        else:
            # Try to parse as form data
            ehr_data = request.get_json(silent=True)
            if not ehr_data:
                return jsonify({'success': False, 'error': 'No EHR data provided'}), 400
        
        # Extract patient data from EHR format
        # Support multiple EHR formats: FHIR-like, custom JSON, etc.
        patient_data = extract_ehr_patient_data(ehr_data)
        
        if not patient_data:
            return jsonify({
                'success': False, 
                'error': 'Could not extract patient data from EHR document. Please ensure the document contains required fields.'
            }), 400
        
        # Make prediction with extracted data
        feature_cols = ['age', 'blood_pressure_systolic', 'blood_pressure_diastolic', 
                       'heart_rate', 'temperature', 'oxygen_saturation', 'pain_level']
        features = pd.DataFrame([[patient_data[col] for col in feature_cols]], 
                               columns=feature_cols)
        features_scaled = scaler.transform(features)
        
        risk_pred = risk_model.predict(features_scaled)[0]
        risk_level = risk_encoder.inverse_transform([risk_pred])[0]
        
        # Get risk confidence
        risk_proba = risk_model.predict_proba(features_scaled)[0]
        risk_confidence = max(risk_proba) * 100
        
        dept_pred = dept_model.predict(features_scaled)[0]
        recommended_dept = dept_encoder.inverse_transform([dept_pred])[0]
        
        # Get department confidence
        dept_proba = dept_model.predict_proba(features_scaled)[0]
        dept_confidence = max(dept_proba) * 100
        
        # Generate explainability
        explainability = generate_explainability(
            patient_data['age'],
            patient_data['blood_pressure_systolic'],
            patient_data['blood_pressure_diastolic'],
            patient_data['heart_rate'],
            patient_data['temperature'],
            patient_data['oxygen_saturation'],
            patient_data['pain_level'],
            risk_level
        )
        
        # Add EHR-specific explainability factor
        explainability.insert(0, {
            'factor': 'EHR Document Import',
            'contribution': 'info',
            'description': 'Data extracted from EHR/EMR electronic health record'
        })
        
        # Persist EHR-imported patient
        patient_id = patient_data.get('patient_id', f"P_{int(datetime.now().timestamp() * 1000)}")
        record = {
            'patient_id': patient_id,
            'age': patient_data.get('age'),
            'gender': patient_data.get('gender'),
            'blood_pressure_systolic': patient_data.get('blood_pressure_systolic'),
            'blood_pressure_diastolic': patient_data.get('blood_pressure_diastolic'),
            'heart_rate': patient_data.get('heart_rate'),
            'temperature': patient_data.get('temperature'),
            'oxygen_saturation': patient_data.get('oxygen_saturation'),
            'pain_level': patient_data.get('pain_level'),
            'symptoms': patient_data.get('symptoms', ''),
            'pre_existing_conditions': patient_data.get('pre_existing_conditions'),
            'risk_level': risk_level,
            'recommended_department': recommended_dept
        }
        save_patient_record(record)

        return jsonify({
            'success': True,
            'patient_data': patient_data,
            'risk_level': risk_level,
            'risk_confidence': f"{risk_confidence:.1f}%",
            'recommended_department': recommended_dept,
            'dept_confidence': f"{dept_confidence:.1f}%",
            'explainability': explainability,
            'patient_id': patient_id,
            'message': 'Data imported from EHR/EMR document successfully'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


def extract_ehr_patient_data(ehr_data):
    """Extract patient data from various EHR document formats"""
    
    # Try to extract data from different EHR formats
    
    # Format 1: FHIR-like structure (Patient resource)
    if 'resourceType' in ehr_data and ehr_data.get('resourceType') == 'Patient':
        return extract_fhir_patient(ehr_data)
    
    # Format 2: Direct patient object
    if 'patient' in ehr_data:
        ehr_data = ehr_data['patient']
    
    # Format 3: Standard fields (our internal format)
    required_fields = ['age']
    if any(field in ehr_data for field in required_fields):
        return extract_standard_patient(ehr_data)
    
    # Format 4: Look for vital signs in various locations
    # Try common EHR field names
    patient = {}
    
    # Age
    patient['age'] = ehr_data.get('age') or ehr_data.get('Age') or ehr_data.get('patient_age') or 0
    
    # Gender
    patient['gender'] = ehr_data.get('gender') or ehr_data.get('Gender') or ehr_data.get('sex') or ''
    
    # Blood Pressure - handle various formats
    bp = ehr_data.get('blood_pressure') or ehr_data.get('bloodPressure') or ehr_data.get('BP') or {}
    if isinstance(bp, dict):
        patient['blood_pressure_systolic'] = bp.get('systolic') or bp.get('systolic_bp') or bp.get('Systolic') or 0
        patient['blood_pressure_diastolic'] = bp.get('diastolic') or bp.get('diastolic_bp') or bp.get('Diastolic') or 0
    elif isinstance(bp, str):
        # Parse "120/80" format
        try:
            parts = bp.split('/')
            patient['blood_pressure_systolic'] = int(parts[0])
            patient['blood_pressure_diastolic'] = int(parts[1])
        except:
            patient['blood_pressure_systolic'] = 0
            patient['blood_pressure_diastolic'] = 0
    else:
        patient['blood_pressure_systolic'] = ehr_data.get('blood_pressure_systolic') or ehr_data.get('systolic_bp') or 0
        patient['blood_pressure_diastolic'] = ehr_data.get('blood_pressure_diastolic') or ehr_data.get('diastolic_bp') or 0
    
    # Heart Rate
    patient['heart_rate'] = ehr_data.get('heart_rate') or ehr_data.get('HeartRate') or ehr_data.get('hr') or ehr_data.get('pulse') or 0
    
    # Temperature
    patient['temperature'] = ehr_data.get('temperature') or ehr_data.get('Temperature') or ehr_data.get('temp') or 98.6
    
    # Oxygen Saturation
    patient['oxygen_saturation'] = ehr_data.get('oxygen_saturation') or ehr_data.get('OxygenSaturation') or ehr_data.get('spo2') or ehr_data.get('SpO2') or 98
    
    # Pain Level
    patient['pain_level'] = ehr_data.get('pain_level') or ehr_data.get('PainLevel') or ehr_data.get('pain') or 0
    
    # Symptoms
    patient['symptoms'] = ehr_data.get('symptoms') or ehr_data.get('Symptoms') or ehr_data.get('chief_complaint') or ''
    
    # Pre-existing Conditions
    patient['pre_existing_conditions'] = ehr_data.get('pre_existing_conditions') or ehr_data.get('conditions') or ehr_data.get('medical_history') or ''
    
    # Patient ID
    patient['patient_id'] = ehr_data.get('patient_id') or ehr_data.get('patientId') or ehr_data.get('id') or ''
    
    return patient if patient.get('age', 0) > 0 else None


def extract_fhir_patient(fhir_patient):
    """Extract patient data from FHIR-like Patient resource"""
    patient = {}
    
    # Extract identifier (patient ID)
    identifiers = fhir_patient.get('identifier', [])
    if identifiers:
        patient['patient_id'] = identifiers[0].get('value', '')
    
    # Extract demographics from FHIR
    name_arr = fhir_patient.get('name', [])
    if name_arr and len(name_arr) > 0:
        name = name_arr[0]
        # FHIR name structure - could extract for full name if needed
    
    # Extract gender
    patient['gender'] = fhir_patient.get('gender', '')
    
    # Extract birthDate (calculate age)
    birth_date = fhir_patient.get('birthDate', '')
    if birth_date:
        from datetime import datetime
        try:
            birth = datetime.strptime(birth_date, '%Y-%m-%d')
            today = datetime.now()
            patient['age'] = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        except:
            patient['age'] = 0
    else:
        patient['age'] = 0
    
    # Extract vitals from FHIR Observation resources
    # This would require processing bundled resources - simplified for now
    patient['blood_pressure_systolic'] = 0
    patient['blood_pressure_diastolic'] = 0
    patient['heart_rate'] = 0
    patient['temperature'] = 98.6
    patient['oxygen_saturation'] = 98
    patient['pain_level'] = 0
    patient['symptoms'] = ''
    patient['pre_existing_conditions'] = ''
    
    return patient


def extract_standard_patient(data):
    """Extract patient data from standard format"""
    return {
        'patient_id': data.get('patient_id', ''),
        'age': data.get('age', 0),
        'gender': data.get('gender', ''),
        'blood_pressure_systolic': data.get('blood_pressure_systolic', 0),
        'blood_pressure_diastolic': data.get('blood_pressure_diastolic', 0),
        'heart_rate': data.get('heart_rate', 0),
        'temperature': data.get('temperature', 98.6),
        'oxygen_saturation': data.get('oxygen_saturation', 98),
        'pain_level': data.get('pain_level', 0),
        'symptoms': data.get('symptoms', ''),
        'pre_existing_conditions': data.get('pre_existing_conditions', '')
    }


# ==================== PHASE 2: REAL-TIME TRIAGE SIMULATION ====================

@app.route('/init-triage-session', methods=['POST'])
def init_triage_session():
    """Initialize a new triage session"""
    global TRIAGE_SESSION_ID, DEPARTMENT_QUEUES, PATIENT_REGISTRY
    
    try:
        TRIAGE_SESSION_ID = f"SESSION_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        DEPARTMENT_QUEUES = {dept: [] for dept in DEPARTMENT_CAPACITY.keys()}
        PATIENT_REGISTRY = {}
        
        return jsonify({
            'success': True,
            'session_id': TRIAGE_SESSION_ID,
            'message': f'Triage session {TRIAGE_SESSION_ID} initialized',
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/triage-patient', methods=['POST'])
def triage_patient():
    """Triage a single patient with load balancing"""
    global PATIENT_REGISTRY, DEPARTMENT_QUEUES
    
    try:
        data = request.get_json()
        patient_id = data.get('patient_id', f"P_{int(datetime.now().timestamp() * 1000)}")
        
        # Extract features
        age = float(data.get('age', 0))
        bp_systolic = float(data.get('blood_pressure_systolic', 0))
        bp_diastolic = float(data.get('blood_pressure_diastolic', 0))
        heart_rate = float(data.get('heart_rate', 0))
        temperature = float(data.get('temperature', 0))
        oxygen_saturation = float(data.get('oxygen_saturation', 0))
        pain_level = int(data.get('pain_level', 0))
        
        # Create feature DataFrame
        feature_cols = ['age', 'blood_pressure_systolic', 'blood_pressure_diastolic', 
                       'heart_rate', 'temperature', 'oxygen_saturation', 'pain_level']
        features = pd.DataFrame([[age, bp_systolic, bp_diastolic, heart_rate, 
                                temperature, oxygen_saturation, pain_level]], 
                               columns=feature_cols)
        
        # Make predictions
        features_scaled = scaler.transform(features)
        risk_pred = risk_model.predict(features_scaled)[0]
        risk_level = risk_encoder.inverse_transform([risk_pred])[0]
        
        dept_pred = dept_model.predict(features_scaled)[0]
        primary_dept = dept_encoder.inverse_transform([dept_pred])[0]
        
        # Load balancing: if primary dept is at capacity, suggest alternative
        assigned_dept = primary_dept
        if len(DEPARTMENT_QUEUES.get(primary_dept, [])) >= DEPARTMENT_CAPACITY.get(primary_dept, 10):
            # Find alternative department with lowest load
            alternative_depts = {dept: len(queue) for dept, queue in DEPARTMENT_QUEUES.items()}
            assigned_dept = min(alternative_depts, key=alternative_depts.get)
        
        # Create and register patient
        triage_patient_obj = TriagePatient(patient_id, risk_level, assigned_dept)
        DEPARTMENT_QUEUES[assigned_dept].append(triage_patient_obj)
        PATIENT_REGISTRY[patient_id] = triage_patient_obj
        # Persist triage entry (single)
        save_patient_record({
            'patient_id': patient_id,
            'age': age,
            'gender': data.get('gender', None),
            'blood_pressure_systolic': bp_systolic,
            'blood_pressure_diastolic': bp_diastolic,
            'heart_rate': heart_rate,
            'temperature': temperature,
            'oxygen_saturation': oxygen_saturation,
            'pain_level': pain_level,
            'symptoms': data.get('symptoms', None),
            'pre_existing_conditions': data.get('pre_existing_conditions', None),
            'risk_level': risk_level,
            'recommended_department': assigned_dept
        })
        
        # Calculate wait time
        queue_size = len(DEPARTMENT_QUEUES[assigned_dept])
        avg_service_time = 2.5  # minutes per patient
        wait_time = queue_size * avg_service_time
        
        return jsonify({
            'success': True,
            'patient_id': patient_id,
            'risk_level': risk_level,
            'assigned_department': assigned_dept,
            'primary_department': primary_dept,
            'load_balanced': assigned_dept != primary_dept,
            'queue_position': len(DEPARTMENT_QUEUES[assigned_dept]),
            'estimated_wait_time_minutes': round(wait_time, 1),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/triage-batch-stream', methods=['POST'])
def triage_batch_stream():
    """Stream process multiple patients incrementally"""
    global PATIENT_REGISTRY, DEPARTMENT_QUEUES
    
    try:
        data = request.get_json()
        patients = data.get('patients', [])
        
        results = []
        
        for patient in patients:
            patient_id = patient.get('patient_id', f"P_{int(datetime.now().timestamp() * 1000)}")
            
            # Extract features
            feature_cols = ['age', 'blood_pressure_systolic', 'blood_pressure_diastolic', 
                           'heart_rate', 'temperature', 'oxygen_saturation', 'pain_level']
            patient_features = {col: float(patient.get(col, 0)) for col in feature_cols}
            features = pd.DataFrame([patient_features], columns=feature_cols)
            
            # Make predictions
            features_scaled = scaler.transform(features)
            risk_pred = risk_model.predict(features_scaled)[0]
            risk_level = risk_encoder.inverse_transform([risk_pred])[0]
            
            dept_pred = dept_model.predict(features_scaled)[0]
            primary_dept = dept_encoder.inverse_transform([dept_pred])[0]
            
            # Load balancing
            assigned_dept = primary_dept
            if len(DEPARTMENT_QUEUES.get(primary_dept, [])) >= DEPARTMENT_CAPACITY.get(primary_dept, 10):
                alternative_depts = {dept: len(queue) for dept, queue in DEPARTMENT_QUEUES.items()}
                assigned_dept = min(alternative_depts, key=alternative_depts.get)
            
            # Register patient
            triage_patient_obj = TriagePatient(patient_id, risk_level, assigned_dept)
            DEPARTMENT_QUEUES[assigned_dept].append(triage_patient_obj)
            PATIENT_REGISTRY[patient_id] = triage_patient_obj
            # Persist triage entry for batch
            save_patient_record({
                'patient_id': patient_id,
                'age': patient.get('age', None),
                'gender': patient.get('gender', None),
                'blood_pressure_systolic': patient.get('blood_pressure_systolic', None),
                'blood_pressure_diastolic': patient.get('blood_pressure_diastolic', None),
                'heart_rate': patient.get('heart_rate', None),
                'temperature': patient.get('temperature', None),
                'oxygen_saturation': patient.get('oxygen_saturation', None),
                'pain_level': patient.get('pain_level', None),
                'symptoms': patient.get('symptoms', None),
                'pre_existing_conditions': patient.get('pre_existing_conditions', None),
                'risk_level': risk_level,
                'recommended_department': assigned_dept
            })
            # Calculate metrics
            queue_size = len(DEPARTMENT_QUEUES[assigned_dept])
            wait_time = queue_size * 2.5
            
            results.append({
                'patient_id': patient_id,
                'risk_level': risk_level,
                'assigned_department': assigned_dept,
                'queue_position': queue_size,
                'estimated_wait_time_minutes': round(wait_time, 1)
            })
        
        return jsonify({
            'success': True,
            'patients_processed': len(results),
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/department-status', methods=['GET'])
def department_status():
    """Get real-time status of all departments"""
    global DEPARTMENT_QUEUES, PATIENT_REGISTRY
    
    try:
        status = {}
        
        for dept, queue in DEPARTMENT_QUEUES.items():
            capacity = DEPARTMENT_CAPACITY.get(dept, 10)
            utilization = (len(queue) / capacity) * 100
            
            # Count by risk level
            high_risk = sum(1 for p in queue if p.risk_level == 'high')
            medium_risk = sum(1 for p in queue if p.risk_level == 'medium')
            low_risk = sum(1 for p in queue if p.risk_level == 'low')
            
            # Estimate wait times
            avg_service_time = 2.5
            wait_time = len(queue) * avg_service_time
            
            # Determine status
            if utilization > 100:
                dept_status = 'CRITICAL'
                warning = 'OVERCROWDED - Immediate action needed'
            elif utilization > 80:
                dept_status = 'AT_CAPACITY'
                warning = 'Near capacity - Monitor closely'
            elif utilization > 50:
                dept_status = 'BUSY'
                warning = 'High load'
            else:
                dept_status = 'AVAILABLE'
                warning = None
            
            status[dept] = {
                'current_patients': len(queue),
                'capacity': capacity,
                'utilization_percentage': round(utilization, 1),
                'status': dept_status,
                'warning': warning,
                'high_risk_count': high_risk,
                'medium_risk_count': medium_risk,
                'low_risk_count': low_risk,
                'estimated_wait_time_minutes': round(wait_time, 1)
            }
        
        return jsonify({
            'success': True,
            'session_id': TRIAGE_SESSION_ID,
            'department_status': status,
            'total_patients_in_system': len(PATIENT_REGISTRY),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/queue-priority', methods=['GET'])
def queue_priority():
    """Get prioritized queue for a specific department with optional category filtering"""
    try:
        department = request.args.get('department', 'Emergency')
        category = request.args.get('category', 'all')  # all, high, medium, low, or department name
        
        if department not in DEPARTMENT_QUEUES:
            return jsonify({'success': False, 'error': 'Invalid department'}), 400
        
        queue = DEPARTMENT_QUEUES[department]
        
        # Apply category filter
        filtered_queue = queue
        if category != 'all':
            category_lower = category.lower()
            if category_lower in ['high', 'medium', 'low']:
                filtered_queue = [p for p in queue if p.risk_level.lower() == category_lower]
            elif category in DEPARTMENT_QUEUES:
                # Filter by department
                filtered_queue = [p for p in queue if p.department == category]
        
        # Sort by priority score (dynamic - recalculated at request time)
        prioritized_queue = sorted(filtered_queue, key=lambda p: p._calculate_priority(), reverse=True)
        
        # Return ALL patients (no limit)
        queue_list = []
        for idx, patient in enumerate(prioritized_queue):
            queue_list.append({
                'position': idx + 1,
                'patient_id': patient.patient_id,
                'risk_level': patient.risk_level,
                'priority_score': round(patient._calculate_priority(), 2),
                'wait_time_minutes': round((datetime.now() - patient.arrival_time).total_seconds() / 60, 1),
                'arrival_time': patient.arrival_time.isoformat()
            })
        
        total_in_queue = len(queue)
        filtered_count = len(prioritized_queue)
        
        return jsonify({
            'success': True,
            'department': department,
            'category_filter': category,
            'prioritized_queue': queue_list,
            'total_in_queue': total_in_queue,
            'filtered_count': filtered_count,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/resource-utilization', methods=['GET'])
def resource_utilization():
    """Get resource utilization metrics across all departments"""
    global DEPARTMENT_QUEUES, PATIENT_REGISTRY
    
    try:
        utilization_metrics = {}
        total_utilization = 0
        
        for dept, queue in DEPARTMENT_QUEUES.items():
            capacity = DEPARTMENT_CAPACITY.get(dept, 10)
            current = len(queue)
            utilization = (current / capacity) * 100
            total_utilization += utilization
            
            # Risk-weighted utilization (high-risk patients count more)
            risk_weights = {'high': 1.5, 'medium': 1.0, 'low': 0.5}
            weighted_load = sum(risk_weights.get(p.risk_level, 1) for p in queue)
            weighted_utilization = (weighted_load / capacity) * 100
            
            utilization_metrics[dept] = {
                'capacity': capacity,
                'current_patients': current,
                'utilization_percentage': round(utilization, 1),
                'weighted_utilization_percentage': round(weighted_utilization, 1),
                'efficiency_score': round((100 - min(utilization, 100)) + (weighted_utilization / 2), 1)
            }
        
        avg_utilization = total_utilization / len(DEPARTMENT_QUEUES)
        
        return jsonify({
            'success': True,
            'utilization_metrics': utilization_metrics,
            'average_utilization_percentage': round(avg_utilization, 1),
            'total_patients_in_system': len(PATIENT_REGISTRY),
            'system_efficiency_score': round((100 - min(avg_utilization, 100)) * 1.2, 1),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/dashboard')
def dashboard():
    """Render the visual dashboard"""
    return render_template('dashboard.html')


@app.route('/dashboard-data', methods=['GET'])
def dashboard_data():
    """Return aggregated data for dashboard visualizations"""
    try:
        df = pd.read_csv(DATA_PATH)
        # Validate required columns
        required_cols = {'risk_level', 'age', 'recommended_department'}
        missing = required_cols - set(df.columns)
        if missing:
            return jsonify({'success': False, 'error': f'Missing columns in dataset: {sorted(list(missing))}'}), 400

        # Allow optional filtering via query params (department, risk_level)
        base_df = df.copy()
        dept_filter = request.args.get('department')
        risk_filter = request.args.get('risk_level')
        if dept_filter:
            base_df = base_df[base_df['recommended_department'] == dept_filter]
        if risk_filter:
            base_df = base_df[base_df['risk_level'] == risk_filter]

        # Risk distribution (dataset or filtered)
        risk_distribution = base_df['risk_level'].value_counts().to_dict()

        # Demographic fairness (reuse age groups calculations)
        age_groups = {
            'young (< 35)': base_df[base_df['age'] < 35],
            'middle (35-60)': base_df[(base_df['age'] >= 35) & (base_df['age'] < 60)],
            'senior (60+)': base_df[base_df['age'] >= 60]
        }
        age_fairness = {}
        for group_name, group_df in age_groups.items():
            if len(group_df) > 0:
                rd = group_df['risk_level'].value_counts().to_dict()
                high_pct = (rd.get('high', 0) / len(group_df)) * 100
                age_fairness[group_name] = {
                    'count': len(group_df),
                    'high_risk_percentage': round(high_pct, 2),
                    'risk_distribution': rd
                }

        # Gender fairness (use base_df if filtered, guard zero-length groups)
        gender_fairness = {}
        gender_source = base_df if 'gender' in base_df.columns else df
        if 'gender' in gender_source.columns:
            for g in gender_source['gender'].dropna().unique():
                gdf = gender_source[gender_source['gender'] == g]
                count = len(gdf)
                rd = gdf['risk_level'].value_counts().to_dict() if count > 0 else {}
                high_pct = (rd.get('high', 0) / count) * 100 if count > 0 else 0.0
                gender_fairness[g] = {'count': count, 'high_risk_percentage': round(high_pct, 2)}

        fairness_metrics = calculate_fairness_metrics(age_fairness, gender_fairness)

        # Department status from historical patient data (CSV)
        dept_status = {}
        for dept in DEPARTMENT_CAPACITY.keys():
            capacity = DEPARTMENT_CAPACITY.get(dept, 10)
            # Count patients from CSV for this department
            dept_df = df[df['recommended_department'] == dept] if 'recommended_department' in df.columns else pd.DataFrame()
            current = len(dept_df)
            # Guard against zero capacity
            if capacity and capacity > 0:
                utilization = round((current / capacity) * 100, 1)
            else:
                utilization = 0.0
            high = len(dept_df[dept_df['risk_level'] == 'high']) if 'risk_level' in dept_df.columns and len(dept_df) > 0 else 0
            dept_status[dept] = {
                'current_patients': current,
                'capacity': capacity,
                'utilization_percentage': utilization,
                'high_risk_count': high
            }

        # Allocation summary (simple): reuse resource allocation logic on dataset
        allocation = {}
        total_staff = 0
        for dept in df['recommended_department'].unique():
            ddf = df[df['recommended_department'] == dept]
            high = len(ddf[ddf['risk_level'] == 'high'])
            medium = len(ddf[ddf['risk_level'] == 'medium'])
            rec_staff = max(2, int((high * 2 + medium * 1) / 3) + 1)
            allocation[dept] = {'recommended_staff': rec_staff, 'current_patients': len(ddf)}
            total_staff += rec_staff

        # Build patient list for selection
        patient_list = []
        if 'patient_id' in df.columns:
            for _, row in df.iterrows():
                patient_list.append({
                    'patient_id': row['patient_id'],
                    'age': row.get('age'),
                    'risk_level': row.get('risk_level'),
                    'department': row.get('recommended_department')
                })

        # Support single patient selection via query param
        patient_id = request.args.get('patient_id')
        selected_patient = None
        if patient_id and 'patient_id' in df.columns:
            sel = df[df['patient_id'].astype(str) == str(patient_id)]
            if not sel.empty:
                r = sel.iloc[0]
                
                # Re-predict to get confidence scores and explainability
                age = float(r.get('age', 0))
                bp_systolic = float(r.get('blood_pressure_systolic', 0))
                bp_diastolic = float(r.get('blood_pressure_diastolic', 0))
                heart_rate = float(r.get('heart_rate', 0))
                temperature = float(r.get('temperature', 0))
                oxygen_saturation = float(r.get('oxygen_saturation', 0))
                pain_level = int(r.get('pain_level', 0))
                
                # Create feature DataFrame for prediction
                feature_cols = ['age', 'blood_pressure_systolic', 'blood_pressure_diastolic', 
                               'heart_rate', 'temperature', 'oxygen_saturation', 'pain_level']
                features = pd.DataFrame([[age, bp_systolic, bp_diastolic, heart_rate, 
                                        temperature, oxygen_saturation, pain_level]], 
                                       columns=feature_cols)
                features_scaled = scaler.transform(features)
                
                # Make predictions
                risk_pred = risk_model.predict(features_scaled)[0]
                risk_level = risk_encoder.inverse_transform([risk_pred])[0]
                
                # Get risk confidence
                risk_proba = risk_model.predict_proba(features_scaled)[0]
                risk_confidence = max(risk_proba) * 100
                
                # Make department prediction
                dept_pred = dept_model.predict(features_scaled)[0]
                recommended_dept = dept_encoder.inverse_transform([dept_pred])[0]
                
                # Get department confidence
                dept_proba = dept_model.predict_proba(features_scaled)[0]
                dept_confidence = max(dept_proba) * 100
                
                # Generate explainability
                explainability = generate_explainability(age, bp_systolic, bp_diastolic, heart_rate, 
                                                          temperature, oxygen_saturation, pain_level, risk_level)
                
                selected_patient = {
                    'patient_id': r['patient_id'],
                    'age': r.get('age'),
                    'gender': r.get('gender'),
                    'blood_pressure_systolic': r.get('blood_pressure_systolic'),
                    'blood_pressure_diastolic': r.get('blood_pressure_diastolic'),
                    'heart_rate': r.get('heart_rate'),
                    'temperature': r.get('temperature'),
                    'oxygen_saturation': r.get('oxygen_saturation'),
                    'pain_level': r.get('pain_level'),
                    'symptoms': r.get('symptoms'),
                    'risk_level': risk_level,
                    'risk_confidence': f"{risk_confidence:.1f}%",
                    'recommended_department': recommended_dept,
                    'dept_confidence': f"{dept_confidence:.1f}%",
                    'explainability': explainability
                }

        # Convert all data to native Python types for JSON serialization
        response_data = {
            'success': True,
            'risk_distribution': convert_to_native(risk_distribution),
            'demographic_fairness': convert_to_native({'age_groups': age_fairness, 'gender': gender_fairness}),
            'fairness_metrics': convert_to_native(fairness_metrics),
            'department_status': convert_to_native(dept_status),
            'allocation_summary': convert_to_native({'total_recommended_staff': total_staff, 'allocation': allocation}),
            'patient_list': convert_to_native(patient_list),
            'selected_patient': convert_to_native(selected_patient)
        }
        
        return jsonify(response_data)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ==================== Patient Search API ====================

@app.route('/search-patient', methods=['POST'])
def search_patient():
    """Search for patients by ID or other criteria"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip().lower()
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'No search query provided'
            }), 400
        
        # Load the patient data
        df = pd.read_csv(DATA_PATH)
        
        # Search by patient_id (case-insensitive)
        # Also search by other fields like symptoms, gender
        matching_patients = df[
            df['patient_id'].astype(str).str.lower().str.contains(query, na=False) |
            df['symptoms'].astype(str).str.lower().str.contains(query, na=False) |
            df['gender'].astype(str).str.lower().str.contains(query, na=False) |
            df['recommended_department'].astype(str).str.lower().str.contains(query, na=False)
        ]
        
        # Get up to 20 results
        results = matching_patients.head(20)
        
        patients = []
        for _, row in results.iterrows():
            patients.append({
                'patient_id': str(row['patient_id']),
                'age': int(row['age']) if pd.notna(row['age']) else 0,
                'gender': str(row['gender']) if pd.notna(row['gender']) else '',
                'blood_pressure_systolic': int(row['blood_pressure_systolic']) if pd.notna(row['blood_pressure_systolic']) else 0,
                'blood_pressure_diastolic': int(row['blood_pressure_diastolic']) if pd.notna(row['blood_pressure_diastolic']) else 0,
                'heart_rate': int(row['heart_rate']) if pd.notna(row['heart_rate']) else 0,
                'temperature': float(row['temperature']) if pd.notna(row['temperature']) else 0,
                'oxygen_saturation': int(row['oxygen_saturation']) if pd.notna(row['oxygen_saturation']) else 0,
                'pain_level': int(row['pain_level']) if pd.notna(row['pain_level']) else 0,
                'symptoms': str(row['symptoms']) if pd.notna(row['symptoms']) else '',
                'pre_existing_conditions': str(row['pre_existing_conditions']) if pd.notna(row['pre_existing_conditions']) else '',
                'risk_level': str(row['risk_level']) if pd.notna(row['risk_level']) else '',
                'recommended_department': str(row['recommended_department']) if pd.notna(row['recommended_department']) else ''
            })
        
        return jsonify({
            'success': True,
            'patients': patients,
            'count': len(patients),
            'message': f'Found {len(patients)} patient(s) matching "{query}"'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/get-patient-record', methods=['POST'])
def get_patient_record():
    """Get detailed record for a specific patient"""
    try:
        data = request.get_json()
        patient_id = data.get('patient_id', '').strip()
        
        if not patient_id:
            return jsonify({
                'success': False,
                'error': 'No patient ID provided'
            }), 400
        
        # Load the patient data
        df = pd.read_csv(DATA_PATH)
        
        # Find the patient by ID
        matching_patients = df[df['patient_id'].astype(str) == str(patient_id)]
        
        if matching_patients.empty:
            # Try partial match
            matching_patients = df[df['patient_id'].astype(str).str.contains(str(patient_id), na=False)]
        
        if matching_patients.empty:
            return jsonify({
                'success': False,
                'error': 'Patient not found'
            }), 404
        
        # Get the first matching record
        row = matching_patients.iloc[0]
        
        patient = {
            'patient_id': str(row['patient_id']),
            'age': int(row['age']) if pd.notna(row['age']) else 0,
            'gender': str(row['gender']) if pd.notna(row['gender']) else '',
            'blood_pressure_systolic': int(row['blood_pressure_systolic']) if pd.notna(row['blood_pressure_systolic']) else 0,
            'blood_pressure_diastolic': int(row['blood_pressure_diastolic']) if pd.notna(row['blood_pressure_diastolic']) else 0,
            'heart_rate': int(row['heart_rate']) if pd.notna(row['heart_rate']) else 0,
            'temperature': float(row['temperature']) if pd.notna(row['temperature']) else 0,
            'oxygen_saturation': int(row['oxygen_saturation']) if pd.notna(row['oxygen_saturation']) else 0,
            'pain_level': int(row['pain_level']) if pd.notna(row['pain_level']) else 0,
            'symptoms': str(row['symptoms']) if pd.notna(row['symptoms']) else '',
            'pre_existing_conditions': str(row['pre_existing_conditions']) if pd.notna(row['pre_existing_conditions']) else '',
            'risk_level': str(row['risk_level']) if pd.notna(row['risk_level']) else '',
            'recommended_department': str(row['recommended_department']) if pd.notna(row['recommended_department']) else ''
        }
        
        return jsonify({
            'success': True,
            'patient': patient,
            'message': 'Patient record retrieved successfully'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


# ==================== Recent Patients API ====================

@app.route('/get-recent-patients', methods=['GET'])
def get_recent_patients():
    """Get the most recent patients from the database"""
    try:
        # Load the patient data
        df = pd.read_csv(DATA_PATH)
        
        # Get the last 10 patients (most recent based on CSV order)
        recent_patients = df.tail(10)
        
        patients = []
        for _, row in recent_patients.iterrows():
            patients.append({
                'patient_id': str(row['patient_id']),
                'age': int(row['age']) if pd.notna(row['age']) else 0,
                'gender': str(row['gender']) if pd.notna(row['gender']) else '',
                'symptoms': str(row['symptoms']) if pd.notna(row['symptoms']) else '',
                'risk_level': str(row['risk_level']) if pd.notna(row['risk_level']) else '',
                'recommended_department': str(row['recommended_department']) if pd.notna(row['recommended_department']) else ''
            })
        
        return jsonify({
            'success': True,
            'patients': patients,
            'count': len(patients)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


# ==================== Document Upload API ====================

@app.route('/upload-document', methods=['POST'])
def upload_document():
    """Handle document upload and extract patient data"""
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Get file extension
        filename = file.filename.lower()
        patient_data = None
        extracted_text = ""
        
        if filename.endswith('.pdf'):
            # Extract text from PDF
            try:
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    extracted_text += page.extract_text() + "\n"
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Failed to read PDF: {str(e)}'
                }), 400
                
        elif filename.endswith('.docx'):
            # Extract text from DOCX
            try:
                import docx
                doc = docx.Document(file)
                for para in doc.paragraphs:
                    extracted_text += para.text + "\n"
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Failed to read DOCX: {str(e)}'
                }), 400
                
        elif filename.endswith(('.jpg', '.jpeg', '.png')):
            # Extract text from image using OCR
            try:
                from PIL import Image
                import pytesseract
                
                # Save uploaded file temporarily
                import tempfile
                import os
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=filename) as tmp:
                    file.save(tmp.name)
                    tmp_path = tmp.name
                
                # Perform OCR
                img = Image.open(tmp_path)
                extracted_text = pytesseract.image_to_string(img)
                
                # Clean up temp file
                os.unlink(tmp_path)
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Failed to process image: {str(e)}'
                }), 400
        else:
            return jsonify({
                'success': False,
                'error': 'Unsupported file format. Please upload PDF, DOCX, JPG, or PNG.'
            }), 400
        
        # Try to extract patient data from the text
        patient_data = extract_patient_data_from_text(extracted_text)
        
        if patient_data:
            return jsonify({
                'success': True,
                'message': 'Patient data extracted successfully',
                'patient_data': patient_data,
                'extracted_text': extracted_text[:500]  # Return first 500 chars for verification
            })
        else:
            # Even if we couldn't parse structured data, return the extracted text
            return jsonify({
                'success': True,
                'message': 'Document uploaded. Could not extract structured patient data. Please enter manually.',
                'extracted_text': extracted_text[:1000]
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


def extract_patient_data_from_text(text):
    """Extract patient data from extracted text using pattern matching"""
    import re
    
    patient = {}
    text_lower = text.lower()
    
    # Extract age
    age_patterns = [
        r'age[:\s]+(\d+)',
        r'patient.{0,20}age[:\s]+(\d+)',
        r'(\d+)\s*(?:years?|yr)',
    ]
    for pattern in age_patterns:
        match = re.search(pattern, text_lower)
        if match:
            patient['age'] = int(match.group(1))
            break
    
    # Extract gender
    if 'male' in text_lower or 'male' in text_lower:
        patient['gender'] = 'male'
    elif 'female' in text_lower:
        patient['gender'] = 'female'
    
    # Extract blood pressure (e.g., 120/80 or 120/80 mmHg)
    bp_patterns = [
        r'bp[:\s]+(\d+)[/\s]+(\d+)',
        r'blood\s*pressure[:\s]+(\d+)[/\s]+(\d+)',
        r'(\d{2,3})/(\d{2,3})\s*(?:mmhg|mm hg)?',
    ]
    for pattern in bp_patterns:
        match = re.search(pattern, text_lower)
        if match:
            patient['blood_pressure_systolic'] = int(match.group(1))
            patient['blood_pressure_diastolic'] = int(match.group(2))
            break
    
    # Extract heart rate
    hr_patterns = [
        r'heart\s*rate[:\s]+(\d+)',
        r'hr[:\s]+(\d+)',
        r'pulse[:\s]+(\d+)',
        r'(\d+)\s*(?:bpm|beats?\s*per\s*minute)',
    ]
    for pattern in hr_patterns:
        match = re.search(pattern, text_lower)
        if match:
            patient['heart_rate'] = int(match.group(1))
            break
    
    # Extract temperature
    temp_patterns = [
        r'temperature[:\s]+(\d+\.?\d*)',
        r'temp[:\s]+(\d+\.?\d*)',
        r'(\d+\.?\d*)\s*(?:°|degrees?)\s*(?:f|fahrenheit)',
    ]
    for pattern in temp_patterns:
        match = re.search(pattern, text_lower)
        if match:
            patient['temperature'] = float(match.group(1))
            break
    
    # Extract oxygen saturation
    o2_patterns = [
        r'o2[:\s]+(\d+)',
        r'spo2[:\s]+(\d+)',
        r'oxygen[:\s]+(\d+)',
        r'saturation[:\s]+(\d+)',
        r'(\d+)\s*%',
    ]
    for pattern in o2_patterns:
        match = re.search(pattern, text_lower)
        if match:
            val = int(match.group(1))
            if 50 <= val <= 100:  # Valid SpO2 range
                patient['oxygen_saturation'] = val
                break
    
    # Extract pain level
    pain_patterns = [
        r'pain[:\s]+(?:level\s*)?(\d+)',
        r'pain\s*score[:\s]+(\d+)',
    ]
    for pattern in pain_patterns:
        match = re.search(pattern, text_lower)
        if match:
            patient['pain_level'] = int(match.group(1))
            break
    
    # Extract symptoms
    symptoms_keywords = [
        'chest pain', 'shortness of breath', 'headache', 'abdominal pain',
        'cough', 'fatigue', 'sore throat', 'dizziness', 'back pain',
        'nausea', 'vomiting', 'fever', 'chills', 'coughing blood'
    ]
    found_symptoms = []
    for symptom in symptoms_keywords:
        if symptom in text_lower:
            found_symptoms.append(symptom.replace(' ', '_'))
    
    if found_symptoms:
        patient['symptoms'] = ','.join(found_symptoms)
    
    # Extract conditions
    conditions_keywords = [
        'diabetes', 'hypertension', 'heart disease', 'asthma', 'copd',
        'arthritis', 'thyroid', 'kidney disease', 'cancer'
    ]
    found_conditions = []
    for condition in conditions_keywords:
        if condition in text_lower:
            found_conditions.append(condition.replace(' ', '_'))
    
    if found_conditions:
        patient['pre_existing_conditions'] = ','.join(found_conditions)
    
    # Only return patient data if we found at least some vital signs
    if patient and (patient.get('age') or patient.get('blood_pressure_systolic') or patient.get('heart_rate')):
        return patient
    
    return None


# ==================== Chatbot API ====================

@app.route('/chatbot/message', methods=['POST'])
def chatbot_message():
    """Handle chatbot messages from hospital staff"""
    try:
        if get_chatbot is None:
            return jsonify({
                'success': False,
                'error': 'Chatbot not available'
            }), 503
        
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({
                'success': False,
                'error': 'Empty message'
            }), 400
        
        chatbot = get_chatbot()
        response = chatbot.process_message(user_message)
        
        return jsonify({
            'success': True,
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/chatbot/history', methods=['GET'])
def chatbot_history():
    """Get chatbot conversation history"""
    try:
        if get_chatbot is None:
            return jsonify({
                'success': False,
                'error': 'Chatbot not available'
            }), 503
        
        chatbot = get_chatbot()
        history = chatbot.get_conversation_history()
        
        return jsonify({
            'success': True,
            'history': history
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/chatbot/clear', methods=['POST'])
def chatbot_clear():
    """Clear chatbot conversation history"""
    try:
        if get_chatbot is None:
            return jsonify({
                'success': False,
                'error': 'Chatbot not available'
            }), 503
        
        chatbot = get_chatbot()
        chatbot.clear_history()
        
        return jsonify({
            'success': True,
            'message': 'Chat history cleared'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
