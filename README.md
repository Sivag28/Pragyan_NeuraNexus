# AI Patient Triage System

An AI-powered patient triage system that uses machine learning to assess patient risk levels and prioritize care accordingly.

## Project Structure

```
ai_patient_triage/
├── app.py                   # Flask backend
├── risk_model.pkl           # Trained ML model (saved with joblib)
├── synthetic_patients.csv   # Synthetic training dataset
├── templates/
│    └── index.html          # Frontend HTML form & dashboard
├── static/
│    ├── css/
│    │    └── style.css      # Optional custom styles
│    └── js/
│         └── script.js      # Optional external JS
├── requirements.txt         # All Python dependencies
└── README.md                # Project overview and instructions
```

## Features

- **Risk Assessment**: Uses machine learning to predict patient risk levels
- **User-Friendly Interface**: Simple form for entering patient data
- **Real-time Predictions**: Get instant risk assessments
- **Dashboard View**: Visual overview of patient triage status

## Installation

1. Clone the repository or navigate to the project directory
2. Install dependencies:
   
```
bash
   pip install -r requirements.txt
   
```

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

3. Enter patient information in the form and click "Assess Risk" to get the triage prediction.

## Model Information

The risk model is trained on synthetic patient data and uses the following features:
- Age
- Blood Pressure (Systolic/Diastolic)
- Heart Rate
- Temperature
- Oxygen Saturation
- Pain Level (1-10)
- Symptoms

The model predicts risk levels:
- **Low Risk**: Minor concerns, routine follow-up
- **Medium Risk**: Requires attention, monitor closely
- **High Risk**: Immediate attention required

## Dependencies

- Flask - Web framework
- scikit-learn - Machine learning
- joblib - Model serialization
- pandas - Data manipulation
- numpy - Numerical computing

## License

MIT License
