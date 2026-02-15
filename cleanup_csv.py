import pandas as pd

# Read the CSV file
df = pd.read_csv('synthetic_patients.csv')

# Remove duplicate rows based on patient_id, keeping the first occurrence
df_cleaned = df.drop_duplicates(subset=['patient_id'], keep='first')

# Sort by patient_id for better organization
df_cleaned = df_cleaned.sort_values('patient_id').reset_index(drop=True)

# Save the cleaned CSV
df_cleaned.to_csv('synthetic_patients.csv', index=False)

print(f"Original rows: {len(df)}")
print(f"Cleaned rows: {len(df_cleaned)}")
print(f"Duplicates removed: {len(df) - len(df_cleaned)}")
print("\nFirst 20 patient IDs in cleaned file:")
print(df_cleaned['patient_id'].head(20).tolist())
