"""Seed historical data from Open-Meteo Archive API for AI training."""

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import Config
from backend.database.db import get_connection

def seed_data(location_id: int = 1, lat: float = 22.71, lon: float = 75.86, days: int = 60):
    connection = get_connection(Config.DATABASE_URL, PROJECT_ROOT)
    
    end_date = datetime.now(timezone.utc) - timedelta(days=5) # Archive API has 5 days delay
    start_date = end_date - timedelta(days=days)
    
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,surface_pressure,wind_speed_10m,cloud_cover"
    }
    
    print(f"Fetching {days} days of historical data for location {location_id}...")
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Failed to fetch data: {e}")
        return 1
        
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    if not times:
        print("No hourly data received.")
        return 1
        
    cursor = connection.cursor()
    inserted = 0
    now_iso = datetime.now(timezone.utc).isoformat()
    
    for i, t in enumerate(times):
        ts = t + "Z" if not t.endswith("Z") else t
        
        # Ensure we have valid values (API can sometimes return nulls)
        temp = hourly["temperature_2m"][i]
        if temp is None:
            continue
            
        rain = hourly["precipitation"][i] or 0.0
        humidity = hourly["relative_humidity_2m"][i] or 50.0
        pressure = hourly["surface_pressure"][i] or 1013.25
        wind = hourly["wind_speed_10m"][i] or 0.0
        cloud = hourly["cloud_cover"][i] or 0.0
        
        obs_key = f"{location_id}-{ts}"
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO weather_observations 
                (location_id, timestamp, temperature, rainfall, humidity, pressure, wind_speed, cloud_cover, source, ingested_at, observation_key)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (location_id, ts, temp, rain, humidity, pressure, wind, cloud, "open-meteo-archive", now_iso, obs_key))
            inserted += 1
        except Exception as e:
            print(f"Insert failed at {ts}: {e}")
            
    connection.commit()
    connection.close()
    
    print(f"Successfully seeded {inserted} historical records!")
    return 0

if __name__ == "__main__":
    sys.exit(seed_data())
