import os
import time
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()   # reads the .env file and loads its values into os.environ

# configuration
API_KEY = os.environ.get("OPENAQ_API_KEY")
if not API_KEY:
    raise SystemExit("Set the OPENAQ_API_KEY environment variable before running.")

BASE_URL = "https://api.openaq.org/v3"
HEADERS = {"X-API-Key": API_KEY}

KATHMANDU_BBOX = "85.20,27.55,85.60,27.85"   # min_lon, min_lat, max_lon, max_lat
PM25_PARAMETER_ID = 2

# User settings: change these to control what is downloaded
DAYS_BACK = 7            # 7 = one week, 365 = one year, 1825 = five years
INTERVAL = "hours"       # "measurements", "hours", or "days"
PAGE_LIMIT = 1000        # maximum rows per request allowed by the API
PAUSE_SECONDS = 1.1      # delay between requests to respect rate limits
OUTPUT_DIR = "data/raw"


# request helper
def api_get(endpoint, params=None, retries=5):
    """GET request with basic handling of rate limits (HTTP 429)."""
    for attempt in range(1, retries + 1):
        response = requests.get(
            f"{BASE_URL}/{endpoint}", headers=HEADERS, params=params, timeout=30
        )
        if response.status_code == 429:
            wait = int(response.headers.get("Retry-After", 60))
            print(f"  Rate limit reached. Waiting {wait} s (attempt {attempt}/{retries})")
            time.sleep(wait)
            continue
        response.raise_for_status()
        return response.json()
    raise RuntimeError(f"Rate limit not resolved after {retries} attempts: {endpoint}")


# stations and sensors
def get_valley_pm25_sensors():
    """Return one record per PM2.5 sensor located inside the bounding box."""
    data = api_get(
        "locations",
        {"bbox": KATHMANDU_BBOX, "parameters_id": PM25_PARAMETER_ID, "limit": 100},
    )
    sensors = []
    for station in data.get("results", []):
        coords = station.get("coordinates", {})
        for sensor in station.get("sensors", []):
            if sensor.get("parameter", {}).get("id") == PM25_PARAMETER_ID:
                sensors.append({
                    "station_id": station.get("id"),
                    "station_name": station.get("name"),
                    "latitude": coords.get("latitude"),
                    "longitude": coords.get("longitude"),
                    "sensor_id": sensor.get("id"),
                })
    return sensors


# historical data
def fetch_sensor_history(sensor_id, date_from, date_to, interval):
    """Download all pages of history for one sensor and return a list of rows."""
    rows, page = [], 1
    while True:
        data = api_get(
            f"sensors/{sensor_id}/{interval}",
            {
                "datetime_from": date_from.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "datetime_to": date_to.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "limit": PAGE_LIMIT,
                "page": page,
            },
        )
        results = data.get("results", [])
        if not results:
            break

        for item in results:
            period = item.get("period") or {}
            rows.append({
                "value": item.get("value"),
                "unit": (item.get("parameter") or {}).get("units"),
                "time_from_utc": (period.get("datetimeFrom") or {}).get("utc"),
                "time_to_utc": (period.get("datetimeTo") or {}).get("utc"),
                "time_from_local": (period.get("datetimeFrom") or {}).get("local"),
                "coverage_pct": (item.get("coverage") or {}).get("percentComplete"),
            })

        if len(results) < PAGE_LIMIT:      # last page reached
            break
        page += 1
        time.sleep(PAUSE_SECONDS)
    return rows


#main workflow
def main():
    date_to = datetime.now(timezone.utc)
    date_from = date_to - timedelta(days=DAYS_BACK)

    print(f"Period: {date_from:%Y-%m-%d} to {date_to:%Y-%m-%d} | interval: {INTERVAL}")
    print("Locating PM2.5 sensors in the Kathmandu Valley...")
    sensors = get_valley_pm25_sensors()
    if not sensors:
        print("No PM2.5 sensors found in the specified area.")
        return
    print(f"Sensors found: {len(sensors)}\n")

    frames = []
    for number, sensor in enumerate(sensors, start=1):
        label = f"{sensor['station_name']} (sensor {sensor['sensor_id']})"
        print(f"[{number}/{len(sensors)}] {label}")
        try:
            rows = fetch_sensor_history(sensor["sensor_id"], date_from, date_to, INTERVAL)
        except (requests.HTTPError, RuntimeError) as err:
            print(f"  Skipped due to error: {err}")
            continue

        if not rows:
            print("  No data in this period.")
            continue

        frame = pd.DataFrame(rows)
        for key in ("station_id", "station_name", "latitude", "longitude", "sensor_id"):
            frame[key] = sensor[key]
        frames.append(frame)
        print(f"  Rows retrieved: {len(frame)}")
        time.sleep(PAUSE_SECONDS)

    if not frames:
        print("\nNo historical data was retrieved.")
        return

    df = pd.concat(frames, ignore_index=True)
    df["time_from_utc"] = pd.to_datetime(df["time_from_utc"], utc=True)
    df = (
        df.drop_duplicates(subset=["sensor_id", "time_from_utc"])
          .sort_values(["station_name", "time_from_utc"])
          .reset_index(drop=True)
    )

    print("\n--- DataFrame Preview ---")
    print(df.head())
    print("\n--- Data Info ---")
    df.info()

    os.makedirs(OUTPUT_DIR, exist_ok=True)       # creates the folder if absent
    filename = f"kathmandu_pm25_{INTERVAL}_{date_from:%Y%m%d}_{date_to:%Y%m%d}.csv"
    output_path = os.path.join(OUTPUT_DIR, filename)
    df.to_csv(output_path, index=False)
    print(f"\nSaved {len(df)} rows to: {output_path}")


if __name__ == "__main__":
    main()