import pandas as pd
import numpy as np
import os

# 1. Define file paths
# Update this filename to match the exact name of the historical CSV you just downloaded
RAW_FILE = "data/raw/kathmandu_pm25_days_20211124_20261123.csv"
PROCESSED_FILE = "data/processed/kathmandu_pm25_days_20211124_20261123_clean.csv"

# Ensure the processed directory exists
os.makedirs("data/processed", exist_ok=True)

print(f"📥 Loading raw historical data from {RAW_FILE}...")
df = pd.read_csv(RAW_FILE)

print(f"Original rows: {len(df)}")

# 2. Handle Missing Data & Quality Control
# Drop rows where the PM2.5 value is missing
df_clean = df.dropna(subset=['value']).copy()

# Optional but recommended: Filter out readings with low data coverage (e.g., < 75%)
# This ensures we only analyze high-quality, reliable sensor readings
df_clean = df_clean[df_clean['coverage_pct'] >= 75].copy()

print(f"Rows after dropping missing/low-quality values: {len(df_clean)}")

# 3. Convert Time to proper Datetime objects
# We use 'time_from_local' because it already includes the +05:45 Nepal Time offset!
df_clean['datetime_local'] = pd.to_datetime(df_clean['time_from_local'])

# 4. FEATURE ENGINEERING: Extract time components for easy PowerBI/SQL analysis
# This is how we will answer "Is pollution worse at 8 AM or 8 PM?"
df_clean['date'] = df_clean['datetime_local'].dt.date
df_clean['hour'] = df_clean['datetime_local'].dt.hour
df_clean['day_of_week'] = df_clean['datetime_local'].dt.day_name()
df_clean['is_weekend'] = df_clean['day_of_week'].isin(['Saturday', 'Sunday'])

# 5. Calculate US EPA AQI from PM2.5 (value column)
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

df_clean['aqi'] = df_clean['value'].apply(calculate_aqi)

# 6. Categorize the AQI for easy PowerBI filtering
def get_aqi_category(aqi):
    if aqi <= 50: return "Good"
    elif aqi <= 100: return "Moderate"
    elif aqi <= 150: return "Unhealthy for Sensitive Groups"
    elif aqi <= 200: return "Unhealthy"
    elif aqi <= 300: return "Very Unhealthy"
    else: return "Hazardous"

df_clean['aqi_category'] = df_clean['aqi'].apply(get_aqi_category)

# 7. Sort the data chronologically for neatness
df_clean = df_clean.sort_values(by=['station_name', 'datetime_local']).reset_index(drop=True)

# 8. Save to processed folder
# We select only the most useful columns to keep the final dataset clean and lightweight
final_columns = [
    'station_id', 'station_name', 'latitude', 'longitude', 
    'datetime_local', 'date', 'hour', 'day_of_week', 'is_weekend',
    'value', 'unit', 'coverage_pct', 'aqi', 'aqi_category'
]

df_clean[final_columns].to_csv(PROCESSED_FILE, index=False)
print(f"\n✅ Success! Clean historical data saved to: {PROCESSED_FILE}")

# Show a quick preview
print("\n--- Cleaned Historical Data Preview ---")
print(df_clean[['station_name', 'datetime_local', 'hour', 'value', 'aqi', 'aqi_category']].head(10))