import pandas as pd
import numpy as np
import os

# 1. Define file paths
RAW_FILE = "data/raw/kathmandu_pm25_raw.csv"
PROCESSED_FILE = "data/processed/kathmandu_pm25_clean.csv"

# Ensure the processed directory exists
os.makedirs("data/processed", exist_ok=True)

print(f"Loading raw data from {RAW_FILE}...")
df = pd.read_csv(RAW_FILE)

print(f"Original rows: {len(df)}")

# 2. Handle Missing Data
# Drop rows where pm25_value is NaN (sensor is offline or hasn't reported)
# We use inplace=False to create a new cleaned dataframe, preserving the original logic
df_clean = df.dropna(subset=['pm25_value']).copy()

print(f"Rows after dropping missing PM2.5 values: {len(df_clean)}")

# 3. Calculate US EPA AQI from PM2.5
# This function maps PM2.5 concentrations to the official EPA AQI breakpoints
def calculate_aqi(pm25):
    if pm25 <= 12.0:
        return round((50 / 12.0) * pm25)
    elif pm25 <= 35.4:
        return round(51 + ((100 - 51) / (35.4 - 12.1)) * (pm25 - 12.1))
    elif pm25 <= 55.4:
        return round(101 + ((150 - 101) / (55.4 - 35.5)) * (pm25 - 35.5))
    elif pm25 <= 150.4:
        return round(151 + ((200 - 151) / (150.4 - 55.5)) * (pm25 - 55.5))
    elif pm25 <= 250.4:
        return round(201 + ((300 - 201) / (250.4 - 150.5)) * (pm25 - 150.5))
    elif pm25 <= 500.4:
        return round(301 + ((500 - 301) / (500.4 - 250.5)) * (pm25 - 250.5))
    else:
        return 500 # Cap at max AQI

# Apply the function to create a new 'aqi' column
df_clean['aqi'] = df_clean['pm25_value'].apply(calculate_aqi)

# 4. Categorize the AQI for easy PowerBI filtering
def get_aqi_category(aqi):
    if aqi <= 50: return "Good"
    elif aqi <= 100: return "Moderate"
    elif aqi <= 150: return "Unhealthy for Sensitive Groups"
    elif aqi <= 200: return "Unhealthy"
    elif aqi <= 300: return "Very Unhealthy"
    else: return "Hazardous"

df_clean['aqi_category'] = df_clean['aqi'].apply(get_aqi_category)

# 5. Ensure correct data types
df_clean['last_updated'] = pd.to_datetime(df_clean['last_updated'], errors='coerce')

# 6. Save to processed folder
df_clean.to_csv(PROCESSED_FILE, index=False)
print(f"\n✅ Success! Clean data saved to: {PROCESSED_FILE}")

# Show a quick preview
print("\n--- Cleaned Data Preview ---")
print(df_clean[['station_name', 'pm25_value', 'aqi', 'aqi_category']].head(10))