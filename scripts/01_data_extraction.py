import requests
import pandas as pd
import time

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-US,en;q=0.9",
}

# ----- Weather Data Aquisition -----
weather_url = "https://archive-api.open-meteo.com/v1/archive"
weather_params = {
    "latitude": 37.5665,
    "longitude": 126.9780,
    "start_date": "2026-04-01",
    "end_date": "2026-04-30",
    "daily": ["temperature_2m_mean", "precipitation_sum"],
    "timezone": "Asia/Seoul"
}
weather_res = requests.get(weather_url, params=weather_params)
weather_data = weather_res.json()

weather_df = pd.DataFrame({
    'Date': pd.to_datetime(weather_data['daily']['time']),
    'Avg_Temp': weather_data['daily']['temperature_2m_mean'],
    'Precipitation': weather_data['daily']['precipitation_sum']
})

print(weather_df.head())