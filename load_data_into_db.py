
import os

import pandas as pd
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

from dotenv import load_dotenv


load_dotenv()  
# Database connection details
required = ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME"]
missing = [name for name in required if not os.environ.get(name)]
if missing:
    raise SystemExit(f"Missing values in .env: {', '.join(missing)}")

# URL.create() builds the connection safely
db_url = URL.create(
    drivername="postgresql+psycopg2",
    username=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    host=os.environ["DB_HOST"],
    port=int(os.environ["DB_PORT"]),
    database=os.environ["DB_NAME"],
)

# Create a connection string
conn_string = f"postgresql+psycopg2://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}"

# Load the cleaned data from CSV
df = pd.read_csv('data/processed/kathmandu_pm25_days_20211124_20261123_clean.csv')

# Create a SQLAlchemy engine
engine = create_engine(conn_string)

# Create dimension tables
dim_station_df = df[['station_id', 'station_name', 'latitude', 'longitude']].drop_duplicates()
dim_time_df = df[['datetime_local', 'date', 'hour', 'day_of_week', 'is_weekend']].drop_duplicates()
dim_aqi_category_df = pd.DataFrame({
    'aqi_category_id': [1, 2, 3, 4, 5, 6],
    'aqi_category': ['Good', 'Moderate', 'Unhealthy for Sensitive Groups', 'Unhealthy', 'Very Unhealthy', 'Hazardous']
})

# Load dimension tables
dim_station_df.to_sql('dim_station', engine, if_exists='replace', index=False)
dim_time_df.to_sql('dim_time', engine, if_exists='replace', index=False)
dim_aqi_category_df.to_sql('dim_aqi_category', engine, if_exists='replace', index=False)

# Create fact table
df = df.rename(columns={'aqi_category': 'aqi_category_id'})
df.to_sql('fact_air_quality', engine, if_exists='replace', index=False)

print("Data loaded successfully into the PostgreSQL database.")