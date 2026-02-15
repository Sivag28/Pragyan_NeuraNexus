# AI Patient Triage System

An AI-powered patient triage system that uses machine learning to assess patient risk levels, recommend departments, and prioritize care accordingly.

## Project Structure

```
ai_patient_triage/
├── app.py                      # Main Flask application
├── api/
│   └── index.py               # API handler (Vercel deployment)
├── risk_model.pkl              # Trained Risk Prediction Model
├── dept_model.pkl             # Trained Department Recommendation Model
├── scaler.pkl                 # Feature scaler
├── label_encoder.pkl           # Risk label encoder
├── dept_encoder.pkl           # Department label encoder
├── symptoms_encoder.pkl        # Symptoms encoder
├── synthetic_patients.csv      # Training dataset
├── department_capacity.json    # Department capacity config
├── templates/                  # HTML templates
│   ├── index.html
│   ├── login.html
│   └── dashboard.html
├── static/                    # Static assets
│   ├── css/
│   └── js/
├── frontend/                  # Frontend files
│   ├── index.html
│   ├── login.html
│   ├── dashboard.html
│   ├── css/
│   └── js/
├── chatbot_rules.py           # Chatbot rules
├── hf_integration.py         # HuggingFace integration
└── requirements.txt           # Dependencies
```

## System Architecture
![system architechture](https://github.com/user-attachments/assets/aaae6e90-54a3-4d4f-9955-dd1b070c51e0)

## Features

### Core Features
- **Risk Assessment**: Machine learning model (Random Forest) to predict patient risk levels (Low/Medium/High)
- **Department Recommendation**: ML model (Gradient Boosting) to recommend appropriate hospital departments
- **Explainability**: Detailed explanation of factors contributing to risk assessment

### Data Integration
- **MongoDB Integration**: Store and retrieve patient records from MongoDB Atlas
- **EHR/EMR Import**: Import patient data from electronic health records (JSON, PDF, DOCX)
- **Wearable Device Import**: Import patient vitals from wearable devices
- **Document Upload**: OCR support for extracting data from images

### Real-time Features
- **Real-time Triage Simulation**: Process multiple patients with load balancing
- **Department Queue Management**: Track patient queues and wait times
- **Resource Utilization**: Monitor department capacity and utilization

### Analytics & Fairness
- **Fairness Analysis**: Comprehensive bias and fairness analysis across demographics
- **Bias Detection**: Detect potential biases in model predictions
- **Resource Allocation**: Analyze and recommend resource distribution

### User Features
- **User Authentication**: Secure login/registration system
- **Dashboard**: Visual overview of triage status and analytics
- **Patient Search**: Search and retrieve patient records

### AI Features
- **Chatbot**: AI-powered chatbot for hospital staff assistance
- **HuggingFace Integration**: Optional NLP embeddings for advanced features

## Tools and Technologies
![tools and technologies](https://github.com/user-attachments/assets/fd9e170d-abbc-486e-9bf2-6d669f34ed74)

## Installation

1. Clone the repository or navigate to the project directory
2. Install dependencies:
   
```
bash
pip install -r requirements.txt
```

3. (Optional) Set up MongoDB Atlas:
   - Create a MongoDB Atlas account
   - Get your connection string
   - Set the MONGO_URI environment variable

4. (Optional) Set up HuggingFace:
   - Get your HF token
   - Configure via the `/hf/configure` endpoint

## Usage

1. Run the Flask application:
   
```
bash
python app.py
```

2. Open your web browser and navigate to:
   
```
http://localhost:5000
```

3. Login or register an account
4. Enter patient information to get risk assessment and department recommendation

## API Endpoints

### Authentication
- `POST /login` - User login
- `POST /register` - User registration
- `POST /logout` - User logout
- `GET /check-auth` - Check authentication status

### Prediction
- `POST /predict` - Single patient risk prediction
- `POST /predict-batch` - Batch prediction for multiple patients
- `GET /model-info` - Get model information

### Triage (Real-time)
- `POST /init-triage-session` - Initialize triage session
- `POST /triage-patient` - Add patient to triage queue
- `POST /triage-batch-stream` - Batch triage processing
- `GET /department-status` - Get real-time department status
- `GET /queue-priority` - Get prioritized patient queue
- `GET /resource-utilization` - Get resource utilization metrics

### Data Import
- `POST /ehr-import` - Import from EHR/EMR documents
- `POST /wearable-import` - Import from wearable devices
- `POST /upload-document` - Upload and extract from documents

### Analytics
- `GET /fairness-analysis` - Comprehensive fairness analysis
- `GET /department-fairness` - Department-level fairness
- `GET /bias-detection` - Bias detection and mitigation
- `GET /resource-allocation` - Resource allocation analysis

### Patient Data
- `POST /search-patient` - Search patients
- `POST /get-patient-record` - Get patient details
- `GET /get-recent-patients` - Get recent patients
- `GET /dashboard-data` - Get dashboard data

### Chatbot
- `POST /chatbot/message` - Send chatbot message
- `GET /chatbot/history` - Get conversation history
- `POST /chatbot/clear` - Clear conversation

### System
- `GET /mongodb/status` - MongoDB connection status
- `GET /update-department-capacity` - Update department capacity
- `GET /get-department-capacity` - Get department capacity

## Model Information

The models are trained on synthetic patient data and use the following features:
- Age
- Blood Pressure (Systolic/Diastolic)
- Heart Rate
- Temperature
- Oxygen Saturation
- Pain Level (1-10)
- Symptoms

### Risk Levels
- **Low Risk**: Minor concerns, routine follow-up
- **Medium Risk**: Requires attention, monitor closely
- **High Risk**: Immediate attention required

### Departments
Cardiology, Pulmonology, Emergency, Neurology, General Surgery, General Medicine, Orthopedics, ENT, Dermatology, Gastroenterology, Vascular Surgery, Infectious Disease

## Dependencies

- Flask - Web framework
- scikit-learn - Machine learning
- joblib - Model serialization
- pandas - Data manipulation
- numpy - Numerical computing
- pymongo - MongoDB driver
- python-dotenv - Environment variables


