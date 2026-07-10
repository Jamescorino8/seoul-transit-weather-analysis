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
SERVICE_NAME = "tpssPassengerCnt"
PAGE_SIZE = 1000

START_DATE = pd.Timestamp("2026-04-01")
END_DATE = pd.Timestamp("2026-06-30")


def request_transit_page(start_index, end_index):
    url = (
        f"http://openapi.seoul.go.kr:8088/"
        f"{API_KEY}/json/{SERVICE_NAME}/"
        f"{start_index}/{end_index}/"
    )

    response = requests.get(
        url,
        timeout=60
    )

    response.raise_for_status()
    data = response.json()

    if SERVICE_NAME not in data:
        raise RuntimeError(
            f"Transit API error: {data}"
        )

    service_data = data[SERVICE_NAME]

    rows = service_data.get("row", [])
    total_count = int(
        service_data.get("list_total_count", 0)
    )
    return rows, total_count


# Check total number of records
_, total_count = request_transit_page(1, 1)
print("Total transit records:", total_count)


# Download all pages
all_rows = []

for start_index in range(1, total_count + 1, PAGE_SIZE):
    end_index = min(
        start_index + PAGE_SIZE - 1,
        total_count
    )

    try:
        rows, _ = request_transit_page(
            start_index,
            end_index
        )

        all_rows.extend(rows)

        print(
            f"Downloaded {start_index:,}-{end_index:,} "
            f"({len(all_rows):,}/{total_count:,})"
        )

    except Exception as e:
        print(
            f"Failed on rows "
            f"{start_index}-{end_index}: {e}"
        )

    time.sleep(0.1)


# ----- Create Daily Transit Data -----
transit_raw_df = pd.DataFrame(all_rows)

transit_raw_df["Date"] = pd.to_datetime(
    transit_raw_df["CRTR_DD"],
    format="%Y%m%d",
    errors="coerce"
)

transit_raw_df["PSNG_NO"] = pd.to_numeric(
    transit_raw_df["PSNG_NO"],
    errors="coerce"
)

transit_df = (
    transit_raw_df[
        transit_raw_df["Date"].between(
            START_DATE,
            END_DATE
        )
    ]
    .groupby("Date", as_index=False)
    .agg(
        Total_Volume=("PSNG_NO", "sum")
    )
)

# Merge and save dataframes
final_df = pd.merge(transit_df, weather_df, on='Date', how='inner')
final_df.to_csv('data/raw/Transit_Weather_Raw.csv', index=False)

print("\nSaved")
print(final_df.head())
print(final_df.shape)