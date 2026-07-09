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
    "end_date": "2026-06-30",
    "daily": ["temperature_2m_mean", "precipitation_sum"],
    "timezone": "Asia/Seoul"
}

# HTTP GET request using weatehr parameters
weather_res = requests.get(weather_url, params=weather_params) 

# Convert response to python dictionary
weather_data = weather_res.json() 

weather_df = pd.DataFrame({
    'Date': pd.to_datetime(weather_data['daily']['time']),
    'Avg_Temp': weather_data['daily']['temperature_2m_mean'],
    'Precipitation': weather_data['daily']['precipitation_sum']
})

# ----- Transit Data Aquisition -----
API_KEY = "6e7161785473616c31313553426f5744"
date_range = pd.date_range(start="2026-04-01", end="2026-06-30")
transit_passenger_volumes = []

for date in date_range:
    date_str = date.strftime('%Y%m%d')
    url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/tpssEmdOdtc/1/1000/{date_str}"
    
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code == 200:
            data = response.json()
            if 'tpssEmdOdtc' in data:
                df = pd.DataFrame(data['tpssEmdOdtc']['row'])
                df['전체_승객_수'] = pd.to_numeric(df['전체_승객_수'], errors='coerce')
                transit_passenger_volumes.append({'Date': date, 'Total_Volume': df['전체_승객_수'].sum()})
        time.sleep(1)
    except Exception as e:
        print(f"Failed on {date_str}: {e}")

transit_df = pd.DataFrame(transit_passenger_volumes)

# Merge and save dataframes
final_df = pd.merge(transit_df, weather_df, on='Date', how='inner')
final_df.to_csv('data/raw/Transit_Weather_Raw.csv', index=False)