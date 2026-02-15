"""
Generate synthetic patient data using Faker + pandas
This script generates realistic-looking synthetic patient data.
"""

import pandas as pd
import numpy as np
from faker import Faker
import random
import warnings
warnings.filterwarnings('ignore')

# Initialize Faker
fake = Faker()
Faker.seed(42)
np.random.seed(42)

# Define possible values for categorical variables
SYMPTOMS = [
    'chest_pain', 'shortness_of_breath', 'headache', 'fatigue', 'cough',
    'abdominal_pain', 'dizziness', 'sore_throat', 'back_pain', 'joint_pain_swelling',
    'leg_pain_swelling', 'leg_swelling', 'chest_discomfort', 'fever_chills', 'skin_rash',
    'mild_cough', 'mild_fatigue', 'mild_discomfort', 'minor_symptoms', 'persistent_cough',
    'fever_cough', 'cough_weakness', 'fatigue_cough', 'fever_fatigue', 'headache_nausea',
    'headache_dizziness', 'headache_mild_cough', 'abdominal_pain_fever', 'abdominal_pain_nausea',
    'sore_throat_cough', 'shortness_of_breath_wheezing', 'cough_blood', 'fatigue_shortness_of_breath',
    'shortness_of_breath_fatigue', 'chest_pain_sweating', 'chest_pain_palpitations', 
    'severe_chest_pain', 'chest_pain_confusion_sweating', 'shortness_of_breath_confusion',
    'chest_pain_difficulty_breathing', 'general_discomfort', 'fatigue_headache'
]

PRE_EXISTING_CONDITIONS = [
    'none', 'hypertension', 'diabetes', 'asthma', 'heart_disease', 
    'copd', 'arthritis', 'thyroid', 'migraine', 'smoker'
]

RISK_LEVELS = ['low', 'medium', 'high']

DEPARTMENTS = [
    'General Medicine', 'Emergency', 'Cardiology', 'Neurology', 'General Surgery',
    'Pulmonology', 'Orthopedics', 'ENT', 'Dermatology', 'Gastroenterology',
    'Vascular Surgery', 'Infectious Disease'
]

# Define mappings between symptoms and departments
SYMPTOM_DEPT_MAPPING = {
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

def determine_risk_level(age, bp_systolic, bp_diastolic, heart_rate, temperature, oxygen_saturation, pain_level):
    """Determine risk level based on vital signs and symptoms"""
    risk_score = 0
    
    # Age factor
    if age > 65:
        risk_score += 2
    elif age > 50:
        risk_score += 1
    
    # Blood pressure factor
    if bp_systolic > 160 or bp_diastolic > 100:
        risk_score += 3
    elif bp_systolic > 140 or bp_diastolic > 90:
        risk_score += 2
    elif bp_systolic > 130 or bp_diastolic > 85:
        risk_score += 1
    
    # Heart rate factor
    if heart_rate > 120 or heart_rate < 50:
        risk_score += 2
    elif heart_rate > 100 or heart_rate < 60:
        risk_score += 1
    
    # Temperature factor
    if temperature > 102:
        risk_score += 2
    elif temperature > 100.4:
        risk_score += 1
    
    # Oxygen saturation factor
    if oxygen_saturation < 92:
        risk_score += 3
    elif oxygen_saturation < 95:
        risk_score += 2
    elif oxygen_saturation < 97:
        risk_score += 1
    
    # Pain level factor
    if pain_level >= 8:
        risk_score += 3
    elif pain_level >= 5:
        risk_score += 2
    elif pain_level >= 3:
        risk_score += 1
    
    # Determine risk level
    if risk_score >= 8:
        return 'high'
    elif risk_score >= 4:
        return 'medium'
    else:
        return 'low'

def generate_patient_data(num_samples=50):
    """Generate synthetic patient data"""
    patients = []
    
    for i in range(num_samples):
        # Generate basic demographics
        age = random.randint(18, 80)
        gender = random.choice(['Male', 'Female'])
        
        # Generate vital signs with realistic ranges and correlations
        # Older patients tend to have higher blood pressure
        base_bp_systolic = 110 + (age // 5) * 5
        base_bp_diastolic = 70 + (age // 10) * 3
        
        bp_systolic = base_bp_systolic + random.randint(-15, 25)
        bp_diastolic = base_bp_diastolic + random.randint(-10, 15)
        
        # Heart rate
        heart_rate = random.randint(60, 100)
        
        # Temperature (in Fahrenheit)
        temperature = round(random.uniform(97.5, 101.5), 1)
        
        # Oxygen saturation
        oxygen_saturation = random.randint(92, 100)
        
        # Pain level
        pain_level = random.randint(1, 10)
        
        # Symptoms
        symptoms = random.choice(SYMPTOMS)
        
        # Pre-existing conditions (more likely for older patients)
        if random.random() < (0.3 + age/200):
            pre_existing_condition = random.choice(PRE_EXISTING_CONDITIONS[1:])  # Exclude 'none'
        else:
            pre_existing_condition = 'none'
        
        # Determine risk level based on vitals
        risk_level = determine_risk_level(age, bp_systolic, bp_diastolic, heart_rate, 
                                          temperature, oxygen_saturation, pain_level)
        
        # Determine recommended department based on symptoms
        recommended_department = SYMPTOM_DEPT_MAPPING.get(symptoms, 'General Medicine')
        
        patient = {
            'patient_id': f'P{i+1:03d}',
            'age': age,
            'gender': gender,
            'blood_pressure_systolic': bp_systolic,
            'blood_pressure_diastolic': bp_diastolic,
            'heart_rate': heart_rate,
            'temperature': temperature,
            'oxygen_saturation': oxygen_saturation,
            'pain_level': pain_level,
            'symptoms': symptoms,
            'pre_existing_conditions': pre_existing_condition,
            'risk_level': risk_level,
            'recommended_department': recommended_department
        }
        
        patients.append(patient)
    
    return pd.DataFrame(patients)

# Generate the data
print("Generating synthetic patient data using Faker + pandas...")
print("=" * 60)

# Generate 50 patients
df = generate_patient_data(50)

# Save to CSV
output_file = 'synthetic_patients.csv'
df.to_csv(output_file, index=False)

print(f"\n✓ Synthetic data generated successfully!")
print(f"✓ Output file: {output_file}")
print(f"✓ Number of records: {len(df)}")
print(f"\n" + "=" * 60)
print("SAMPLE DATA (First 10 records):")
print("=" * 60)
print(df.head(10).to_string())

print(f"\n" + "=" * 60)
print("DATA STATISTICS:")
print("=" * 60)
print(f"\nAge distribution:")
print(f"  Mean: {df['age'].mean():.1f}")
print(f"  Min: {df['age'].min()}, Max: {df['age'].max()}")

print(f"\nBlood Pressure (Systolic):")
print(f"  Mean: {df['blood_pressure_systolic'].mean():.1f}")
print(f"  Min: {df['blood_pressure_systolic'].min()}, Max: {df['blood_pressure_systolic'].max()}")

print(f"\nRisk Level Distribution:")
print(df['risk_level'].value_counts().to_string())

print(f"\nDepartment Distribution:")
print(df['recommended_department'].value_counts().to_string())

print(f"\nGender Distribution:")
print(df['gender'].value_counts().to_string())

print(f"\n" + "=" * 60)
print("DATA GENERATION COMPLETE!")
print("=" * 60)
