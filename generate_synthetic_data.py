"""
Generate synthetic patient data using SDV (Synthetic Data Vault)
This script reads the existing synthetic_patients.csv and generates new synthetic data
that preserves the statistical properties and correlations of the original data.
"""

import pandas as pd
import numpy as np
from sdv.tabular import GaussianCopula
import warnings
warnings.filterwarnings('ignore')

# Load the original data
print("Loading original data...")
df = pd.read_csv('synthetic_patients.csv')

print(f"Original data shape: {df.shape}")
print(f"Columns: {list(df.columns)}")

# Drop patient_id as it's just an identifier
df_model = df.drop('patient_id', axis=1)

# Convert categorical columns to string type for SDV
categorical_columns = ['gender', 'symptoms', 'pre_existing_conditions', 'risk_level', 'recommended_department']
for col in categorical_columns:
    df_model[col] = df_model[col].astype(str)

# Create and fit the SDV model
print("\nTraining SDV model (GaussianCopula)...")
model = GaussianCopula(
    nan_strategy='sample',
    enum_strategy='random'
)
model.fit(df_model)

# Generate new synthetic data
print("Generating synthetic data...")
num_samples = 50  # Generate same number as original
synthetic_data = model.sample(num_samples)

# Add patient IDs
synthetic_data.insert(0, 'patient_id', [f'P{i+1:03d}' for i in range(num_samples)])

# Ensure gender is properly formatted
synthetic_data['gender'] = synthetic_data['gender'].apply(lambda x: 'Male' if x.lower() in ['male', 'm'] else 'Female')

# Round numeric values to make them more realistic
synthetic_data['age'] = synthetic_data['age'].round(0).astype(int)
synthetic_data['blood_pressure_systolic'] = synthetic_data['blood_pressure_systolic'].round(0).astype(int)
synthetic_data['blood_pressure_diastolic'] = synthetic_data['blood_pressure_diastolic'].round(0).astype(int)
synthetic_data['heart_rate'] = synthetic_data['heart_rate'].round(0).astype(int)
synthetic_data['temperature'] = synthetic_data['temperature'].round(1)
synthetic_data['oxygen_saturation'] = synthetic_data['oxygen_saturation'].clip(90, 100).round(0).astype(int)
synthetic_data['pain_level'] = synthetic_data['pain_level'].clip(1, 10).round(0).astype(int)

# Save the synthetic data
output_file = 'synthetic_patients.csv'
synthetic_data.to_csv(output_file, index=False)

print(f"\nSynthetic data generated successfully!")
print(f"Output file: {output_file}")
print(f"New data shape: {synthetic_data.shape}")

# Show sample of generated data
print("\nSample of generated data:")
print(synthetic_data.head(10).to_string())

# Show comparison of distributions
print("\n--- Comparison of Key Statistics ---")
print("\nOriginal data:")
print(df[['age', 'blood_pressure_systolic', 'blood_pressure_diastolic', 'heart_rate', 'temperature', 'oxygen_saturation', 'pain_level']].describe())
print("\nSynthetic data:")
print(synthetic_data[['age', 'blood_pressure_systolic', 'blood_pressure_diastolic', 'heart_rate', 'temperature', 'oxygen_saturation', 'pain_level']].describe())
