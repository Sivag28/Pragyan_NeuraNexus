# AI Patient Triage System - Deployment Guide

> **Important**: For Flask applications, **Render** is the recommended deployment platform. Vercel requires significant restructuring for Flask apps.

---

## Quick Deploy Options

### Option 1: Deploy to Render (Recommended) ✅

Render is the easiest and most reliable option for Flask applications.

#### Step-by-Step:

1. **Push code to GitHub**
   
```
bash
   git add .
   git commit -m "Prepare for deployment"
   git push origin main
   
```

2. **Connect to Render**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New Web Service"
   - Connect your GitHub repository
   - Configure the following:

3. **Configuration**:
   - **Name**: `ai-patient-triage`
   - **Runtime**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

4. **Environment Variables** (in Render dashboard):
   - `MONGO_URI`: Your MongoDB Atlas connection string
   - `SECRET_KEY`: Generate with: `python -c "import secrets; print(secrets.token_hex(32))"`

5. **Deploy**: Click "Create Web Service"

**Your app will be available at**: `https://ai-patient-triage.onrender.com`

---

### Option 2: Deploy to Vercel ⚠️

Vercel requires restructuring the Flask app to work with serverless functions. We've prepared the basic configuration.

#### Prerequisites:
- Vercel account
- Project pushed to GitHub

#### Step-by-Step:

1. **Install Vercel CLI** (optional):
   
```
bash
   npm i -g vercel
   
```

2. **Deploy**:
   
```
bash
   vercel
   
```

3. **Or connect via GitHub**:
   - Go to [Vercel Dashboard](https://vercel.com/dashboard)
   - Click "Add New Project"
   - Import your GitHub repository
   - Configure:
     - Framework Preset: `Python`
     - Build Command: (leave empty)
     - Output Directory: (leave empty)
   - Add Environment Variables:
     - `MONGO_URI`: Your MongoDB Atlas connection string
     - `SECRET_KEY`: Generate with: `python -c "import secrets; print(secrets.token_hex(32))"`

#### Note on Vercel Limitations:
- Vercel is optimized for static sites and serverless functions
- Flask session management may not work perfectly
- Some features may need adjustments
- For production, **Render is strongly recommended**

---

## Files Prepared for Deployment

| File | Purpose |
|------|---------|
| `Procfile` | Required for Render deployment |
| `runtime.txt` | Python version for Render |
| `requirements.txt` | Python dependencies (updated with gunicorn) |
| `vercel.json` | Vercel configuration |
| `api/index.py` | Vercel serverless handler |

---

# AI Patient Triage System - Deployment Guide (Full)

This guide provides comprehensive instructions for deploying the AI Patient Triage System in various environments.

This guide provides comprehensive instructions for deploying the AI Patient Triage System in various environments.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Development Deployment](#local-development-deployment)
3. [Production Deployment Options](#production-deployment-options)
4. [Environment Variables](#environment-variables)
5. [Database Setup](#database-setup)
6. [Verifying Deployment](#verifying-deployment)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements
- Python 3.8 or higher
- pip (Python package manager)
- Git (for version control)
- MongoDB Atlas account (for cloud database)

### Required Files
Ensure these files are present in your project directory:
- `app.py` - Main Flask application
- `requirements.txt` - Python dependencies
- `risk_model.pkl` - Trained risk prediction model
- `dept_model.pkl` - Trained department recommendation model
- `scaler.pkl` - Feature scaler
- `risk_encoder.pkl` - Risk level encoder
- `dept_encoder.pkl` - Department encoder
- `symptoms_encoder.pkl` - Symptoms encoder
- `synthetic_patients.csv` - Training dataset
- `department_capacity.json` - Department capacity configuration
- `templates/` - HTML templates
- `static/` - CSS and JavaScript files

---

## Local Development Deployment

### Step 1: Clone or Navigate to Project

```
bash
cd /path/to/ai_patient_triage
```

### Step 2: Create Virtual Environment (Recommended)

**Windows:**
```
cmd
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```
bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```
bash
pip install -r requirements.txt
```

### Step 4: Set Environment Variables (Optional for Local Development)

```
bash
# Windows
set MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/patientDB?appName=AppName
set SECRET_KEY=your-secret-key-here

# macOS/Linux
export MONGO_URI="mongodb+srv://username:password@cluster.mongodb.net/patientDB?appName=AppName"
export SECRET_KEY="your-secret-key-here"
```

### Step 5: Run the Application

```
bash
python app.py
```

The application will start on `http://localhost:5000`. Open your browser and navigate to:
```
http://localhost:5000
```

---

## Production Deployment Options

### Option 1: Render.com (Recommended - Free Tier Available)

Render is the easiest option for deploying Flask applications with a free tier.

#### Step 1: Prepare Your Project
1. Create a `Procfile` in your project root:
```
web: gunicorn app:app
```

2. Create `runtime.txt`:
```
python-3.10.12
```

3. Update `requirements.txt` to include gunicorn:
```
txt
flask>=2.3.0
gunicorn>=20.1.0
scikit-learn>=1.3.0
joblib>=1.3.0
pandas>=2.0.0
numpy>=1.24.0
# ... other dependencies
```

#### Step 2: Deploy to Render
1. Push your code to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Click "New Web Service"
4. Connect your GitHub repository
5. Configure:
   - **Name**: ai-patient-triage
   - **Runtime**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
6. Add Environment Variables:
   - `MONGO_URI`: Your MongoDB Atlas connection string
   - `SECRET_KEY`: Generate a secure key
7. Click "Create Web Service"

#### Step 3: Access Your Deployment
Your app will be available at `https://ai-patient-triage.onrender.com`

---

### Option 2: Railway

#### Step 1: Prepare Project
1. Create `railway.json`:
```
json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS_PYTHON_PIP"
  },
  "deploy": {
    "numReplicas": 1,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

#### Step 2: Deploy to Railway
1. Install Railway CLI: `npm i -g @railway/cli`
2. Login: `railway login`
3. Initialize: `railway init`
4. Add environment variables: `railway variables set MONGO_URI=...`
5. Deploy: `railway up`

---

### Option 3: Heroku

#### Step 1: Prepare Project
1. Create `Procfile`:
```
web: gunicorn app:app --workers 4
```

2. Create `runtime.txt`:
```
python-3.10.12
```

#### Step 2: Deploy to Heroku
```
bash
# Install Heroku CLI
# https://devcenter.heroku.com/articles/heroku-cli

heroku create ai-patient-triage
heroku config:set MONGO_URI="your-mongodb-uri"
heroku config:set SECRET_KEY="your-secret-key"
git push heroku main
```

---

### Option 4: PythonAnywhere (Easiest for Beginners)

1. Create account at [PythonAnywhere](https://www.pythonanywhere.com)
2. Go to "Web" tab
3. Add new web app → Flask → Python 3.10
4. Edit `WSGI configuration file` to point to your app
5. Open bash console and run:
```
bash
pip install -r requirements.txt
```
6. Reload the web app

---

### Option 5: Docker Deployment

#### Step 1: Create Dockerfile
```
dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose port
EXPOSE 5000

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

#### Step 2: Create .dockerignore
```
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info/
dist/
build/
.git/
.gitignore/
README.md
*.md
```

#### Step 3: Build and Run
```
bash
# Build the image
docker build -t ai-patient-triage .

# Run the container
docker run -d -p 5000:5000 \
  -e MONGO_URI="your-mongodb-uri" \
  -e SECRET_KEY="your-secret-key" \
  --name triage-app \
  ai-patient-triage
```

#### Step 4: Deploy with Docker Compose
```
yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - MONGO_URI=${MONGO_URI}
      - SECRET_KEY=${SECRET_KEY}
    restart: unless-stopped
```

```bash
# Run with docker-compose
docker-compose up -d
```

---

### Option 6: Cloud Platforms (AWS, GCP, Azure)

#### AWS Elastic Beanstalk
```bash
# Install EB CLI
pip install awsebcli

# Initialize EB application
eb init -p python-3.10 ai-patient-triage

# Create environment and deploy
eb create production --instance-type t3.micro
```

#### Google Cloud Run
```bash
# Build and push container
gcloud builds submit --tag gcr.io/PROJECT_ID/ai-patient-triage

# Deploy
gcloud run deploy ai-patient-triage \
  --image gcr.io/PROJECT_ID/ai-patient-triage \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

---

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `MONGO_URI` | MongoDB Atlas connection string | Yes | Built-in demo URI |
| `SECRET_KEY` | Flask session secret key | Yes | Auto-generated |
| `FLASK_ENV` | Flask environment | No | production |
| `LOG_LEVEL` | Logging level | No | INFO |

### Generating a Secret Key
```
bash
# Python
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Database Setup

### MongoDB Atlas Setup (Recommended)

1. **Create MongoDB Atlas Account**
   - Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
   - Sign up for free account

2. **Create Cluster**
   - Click "Build a Database"
   - Select "Free Tier" (M0)
   - Choose cloud provider and region
   - Click "Create Cluster"

3. **Configure Database Access**
   - Go to "Database Access"
   - Click "Add New Database User"
   - Create username and password
   - Select "Read and Write to any database"

4. **Configure Network Access**
   - Go to "Network Access"
   - Click "Add IP Address"
   - Select "Allow Access from Anywhere" (0.0.0.0/0) for development

5. **Get Connection String**
   - Go to "Database" → "Connect" → "Connect your application"
   - Copy the connection string
   - Replace `<password>` with your database user password

6. **Set Environment Variable**
   
```
bash
   export MONGO_URI="mongodb+srv://username:password@cluster.mongodb.net/patientDB?appName=AppName"
   
```

### Using Local MongoDB (Alternative)

1. Install MongoDB Community Server
2. Start MongoDB: `mongod`
3. Update `app.py`:
   
```
python
   MONGO_URI = 'mongodb://localhost:27017/patientDB'
   
```

---

## Verifying Deployment

### Health Check Endpoints

After deployment, verify these endpoints work:

1. **Base URL**: `https://your-app-url.com/`
2. **MongoDB Status**: `https://your-app-url.com/mongodb/status`
3. **Model Info**: `https://your-app-url.com/model-info`

### Expected Responses

```
json
// MongoDB Status
{
  "success": true,
  "mongodb": {
    "connected": true,
    "database": "patientDB",
    "collection": "patients"
  }
}

// Model Info
{
  "risk_model_type": "Random Forest Classifier",
  "dept_model_type": "Gradient Boosting Classifier",
  "features": ["age", "blood_pressure_systolic", ...],
  "risk_levels": ["high", "medium", "low"],
  "departments": ["Cardiology", "Emergency", ...]
}
```

### Test API Endpoints

```
bash
# Test prediction endpoint
curl -X POST https://your-app-url.com/predict \
  -H "Content-Type: application/json" \
  -d '{
    "age": 45,
    "blood_pressure_systolic": 120,
    "blood_pressure_diastolic": 80,
    "heart_rate": 75,
    "temperature": 98.6,
    "oxygen_saturation": 98,
    "pain_level": 5,
    "symptoms": "chest_pain"
  }'
```

---

## Troubleshooting

### Common Issues

#### 1. MongoDB Connection Error
```
MongoClient([...]) connection timeout
```
**Solution**: 
- Check MongoDB Atlas network access settings
- Verify connection string is correct
- Ensure IP is whitelisted

#### 2. Model Files Not Found
```
FileNotFoundError: [Errno 2] No such file or directory: 'risk_model.pkl'
```
**Solution**:
- Ensure all `.pkl` files are in the project root
- Check working directory in deployment settings

#### 3. Application Crashes on Startup
```
ModuleNotFoundError: No module named 'flask'
```
**Solution**:
- Verify all dependencies in `requirements.txt`
- Reinstall dependencies: `pip install -r requirements.txt`

#### 4. Static Files Not Loading
**Solution**:
- For production, configure static file serving
- For Gunicorn, add to Procfile:
  
```
  web: gunicorn --static-prefix /static/ app:app
  
```

#### 5. Session Issues
**Solution**:
- Set a consistent `SECRET_KEY` across deployments
- Use environment variable, not hardcoded value

### Logs Location

| Platform | Where to Find Logs |
|----------|-------------------|
| Render | Dashboard → Logs |
| Heroku | CLI: `heroku logs --tail` |
| Railway | Dashboard → Deployments |
| Docker | `docker logs container-id` |
| PythonAnywhere | "Web" tab → "Logs" |

### Performance Optimization

1. **Use Gunicorn with Multiple Workers**:
   
```
   gunicorn app:app --workers 4 --threads 2
   
```

2. **Enable Database Indexing** (in MongoDB Atlas):
   
```
javascript
   db.patients.createIndex({ patient_id: 1 })
   db.patients.createIndex({ risk_level: 1 })
   db.patients.createIndex({ recommended_department: 1 })
   
```

3. **Use Redis for Sessions** (production):
   
```
python
   from flask import session
   from flask_session import Session
   app.config['SESSION_TYPE'] = 'redis'
   
```

---

## Security Considerations

1. **Never commit sensitive data** to version control
2. **Use environment variables** for secrets
3. **Enable HTTPS** in production
4. **Configure CORS** if needed:
   
```
python
   from flask_cors import CORS
   CORS(app, origins=["https://yourdomain.com"])
   
```
5. **Rate limiting** (production):
   
```
python
   from flask_limiter import Limiter
   limiter = Limiter(app, default_limits=["200 per day", "50 per hour"])
   
```

---

## Monitoring & Maintenance

### Recommended Tools
- **Sentry** - Error tracking
- **DataDog** - APM
- **UptimeRobot** - Uptime monitoring
- **MongoDB Atlas** - Built-in monitoring

### Backup Strategy
1. Enable MongoDB Atlas automatic backups
2. Export CSV data periodically:
   
```
bash
   python -c "import pandas as pd; df = pd.read_csv('synthetic_patients.csv'); df.to_csv('backup.csv')"
   
```

---

## Support

For issues or questions:
1. Check the application logs
2. Verify environment variables are set correctly
3. Ensure all required files are present
4. Check MongoDB Atlas dashboard for connection issues

---

**Last Updated**: February 2026
**Version**: 1.0.0
