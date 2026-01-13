
import openmeteo_requests
import pandas as pd
import numpy as np
import requests_cache
from retry_requests import retry
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from datetime import datetime, timedelta
import time
import traceback

# run in the terminal
# pip install openmeteo_requests
# pip install requests-cache
# pip install retry-requests



print("Karachi Live Flood Monitoring System")
print("-" * 60)

# api client setup
cache_session = requests_cache.CachedSession('.cache', expire_after=1800)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

url = "https://api.open-meteo.com/v1/forecast"



# training the model
params_training = {
    "latitude": 24.8608,
    "longitude": 67.0104,
    "hourly": ["surface_pressure", "precipitation", "relative_humidity_2m"],
    "past_days": 92,
    "forecast_days": 0,
    "precipitation_unit": "inch",
}

responses = openmeteo.weather_api(url, params_training)
response = responses[0]
hourly = response.Hourly()

hourly_data = {
    "date": pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    ),
    "api_pressure": hourly.Variables(0).ValuesAsNumpy(),
    "precipitation": hourly.Variables(1).ValuesAsNumpy(),
    "humidity": hourly.Variables(2).ValuesAsNumpy()
}
api_df = pd.DataFrame(data=hourly_data)

# specific training dataset (from the floods in Karachi in 2025)
pressure_hpa = [
    1002.37, 998.99, 1002.37, 998.99, 998.99, 998.99, 1002.37, 1002.37, 998.99, 998.99,
    998.99, 1002.37, 1005.76, 1005.76, 1009.14, 1009.14, 1009.14, 1009.14, 1009.14, 1009.14,
    1009.14, 1009.14, 1005.76, 1005.76, 1002.37, 1002.37, 998.99, 998.99, 998.99, 998.99,
    998.99, 995.6, 995.6, 995.6, 995.6, 995.6, 995.6, 998.99, 998.99, 998.99,
    998.99, 998.99, 998.99, 995.6, 995.6, 995.6, 998.99, 998.99, 998.99, 1002.37,
    1002.37, 998.99, 998.99, 995.6, 995.6, 992.21, 992.21, 995.6, 995.6, 998.99,
    998.99, 998.99, 1002.37, 1002.37, 998.99, 998.99, 998.99, 998.99, 998.99, 998.99
]

manual_dates = [datetime(2024, 5, 1) + timedelta(days=i) for i in range(len(pressure_hpa))]
manual_df = pd.DataFrame({
    'date_only': [d.date() for d in manual_dates],
    'surface_pressure': pressure_hpa
})

api_df['date_only'] = api_df['date'].dt.date
df = pd.merge(api_df, manual_df, on='date_only', how='inner')

df['pressure_trend'] = df['surface_pressure'].diff(periods=3).fillna(0)
df['flood_label'] = 0
df.loc[(df['precipitation'].between(0.4, 0.9)) & (df['surface_pressure'] < 1005), 'flood_label'] = 1
df.loc[(df['precipitation'] >= 1.0) | (df['surface_pressure'] <= 1000), 'flood_label'] = 2

# synthetic data in order to balance the model
np.random.seed(42)
num_samples = 50

normal_examples = pd.DataFrame({
    'surface_pressure': np.random.normal(1010, 3, num_samples),
    'precipitation': np.random.uniform(0, 0.3, num_samples),
    'humidity': np.random.normal(65, 8, num_samples),
    'pressure_trend': np.random.normal(0, 0.8, num_samples),
    'flood_label': 0
})

watch_examples = pd.DataFrame({
    'surface_pressure': np.random.normal(1002, 2, num_samples),
    'precipitation': np.random.uniform(0.4, 0.9, num_samples),
    'humidity': np.random.normal(85, 5, num_samples),
    'pressure_trend': np.random.normal(-1.5, 0.6, num_samples),
    'flood_label': 1
})

warning_examples = pd.DataFrame({
    'surface_pressure': np.random.normal(995, 3, num_samples),
    'precipitation': np.random.uniform(1.0, 3.5, num_samples),
    'humidity': np.random.normal(95, 3, num_samples),
    'pressure_trend': np.random.normal(-5.0, 1.5, num_samples),
    'flood_label': 2
})

final_df = pd.concat([
    df[['surface_pressure', 'precipitation', 'humidity', 'pressure_trend', 'flood_label']],
    normal_examples,
    watch_examples,
    warning_examples
], ignore_index=True).fillna(0)

X = final_df[['surface_pressure', 'precipitation', 'humidity', 'pressure_trend']]
y = final_df['flood_label']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestClassifier(
    n_estimators=100,
    max_depth=5,
    class_weight='balanced',
    random_state=42
)
model.fit(X_train, y_train)

print(f"Model trained. Accuracy: {model.score(X_test, y_test)*100:.1f}%")

# live weather fetch in Karachi
previous_data_key = None

def fetch_current_weather():
    """Fetch current weather using the hour closest to NOW, then convert to Pakistan time."""
    params_live = {
        "latitude": 24.8608,
        "longitude": 67.0104,
        "hourly": ["surface_pressure", "precipitation", "relative_humidity_2m"],
        "forecast_days": 1,
        "precipitation_unit": "inch",
    }

    try:
        responses = openmeteo.weather_api(url, params_live)
        response = responses[0]
        hourly = response.Hourly()

        pressure_array = hourly.Variables(0).ValuesAsNumpy()
        precip_array = hourly.Variables(1).ValuesAsNumpy()
        humidity_array = hourly.Variables(2).ValuesAsNumpy()

        data_times = pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left"
        )

        # for errors in the api, selects the closest avaliable time
        now = pd.Timestamp.utcnow()
        time_diffs = np.abs((data_times - now).total_seconds())
        idx = int(np.argmin(time_diffs))

        # converting to pakistan time
        pk_time = data_times[idx] + pd.Timedelta(hours=5)

        pressure = float(pressure_array[idx])
        precip = float(precip_array[idx])
        humidity = float(humidity_array[idx])

        # calculation of trends
        if idx + 3 < len(pressure_array):
            trend = float(pressure_array[idx + 3] - pressure_array[idx])
        else:
            trend = 0.0

        return {
            "pressure": pressure,
            "precipitation": precip,
            "humidity": humidity,
            "trend": trend,
            "timestamp": datetime.now(),
            "data_hour_utc": data_times[idx],
            "data_hour_pk": pk_time,
            "data_index": idx
        }

    except Exception as e:
        print("Error fetching weather:", e)
        traceback.print_exc()
        return None


def predict_flood_risk(weather):
    input_df = pd.DataFrame([[
        weather['pressure'],
        weather['precipitation'],
        weather['humidity'],
        weather['trend']
    ]], columns=['surface_pressure', 'precipitation', 'humidity', 'pressure_trend'])

    pred = model.predict(input_df)[0]
    conf = model.predict_proba(input_df)[0][pred] * 100

    status_map = {
        0: ("NORMAL", "GREEN"),
        1: ("FLOOD WATCH", "YELLOW"),
        2: ("EMERGENCY WARNING", "RED")
    }

    status, color = status_map[pred]

    return {
        "prediction": pred,
        "status": status,
        "color": color,
        "confidence": conf
    }


def display_alert(weather, prediction, data_changed=True):
    print("\n" + "="*60)
    print(f"FLOOD STATUS: {prediction['status']}")
    print("="*60)
    print(f"Check Time (Local System): {weather['timestamp']}")
    print(f"Data Hour (UTC): {weather['data_hour_utc']}")
    print(f"Data Hour (Pakistan): {weather['data_hour_pk']}")
    print(f"Pressure: {weather['pressure']}")
    print(f"Rain: {weather['precipitation']}")
    print(f"Humidity: {weather['humidity']}")
    print(f"Trend: {weather['trend']}")
    print(f"Confidence: {prediction['confidence']:.1f}%")
    print("="*60)


# live monitoring at specific intervals
def monitor_flood_risk(check_interval_minutes=5, max_checks=1000):
    """
    Live monitoring loop:
    - Fetches current weather every X minutes
    - Detects when a new hour of data arrives
    - Logs only new data
    - Prints updated alerts
    """
    global previous_data_key

    print("\n LIVE MONITORING STARTED")
    print(f"Checking every {check_interval_minutes} minutes")
    print(f"Pakistan Time Now: {(datetime.utcnow() + timedelta(hours=5)).strftime('%Y-%m-%d %H:%M')}")
    print("-" * 60)

    check_count = 0

    try:
        while check_count < max_checks:
            check_count += 1
            print(f"\n Check #{check_count}")

            weather = fetch_current_weather()

            if weather:
                # Build a unique key for this hour + pressure
                current_key = f"{weather['data_hour_utc']}_{weather['pressure']}"

                data_changed = (previous_data_key != current_key)
                previous_data_key = current_key

                prediction = predict_flood_risk(weather)
                display_alert(weather, prediction, data_changed)

                # Log only if new hour
                if data_changed:
                    with open("flood_log.csv", "a") as f:
                        f.write(
                            f"{weather['timestamp']},"
                            f"{weather['data_hour_pk']},"
                            f"{prediction['status']},"
                            f"{prediction['confidence']:.1f},"
                            f"{weather['pressure']},"
                            f"{weather['precipitation']},"
                            f"{weather['humidity']},"
                            f"{weather['trend']}\n"
                        )
                    print(" Logged new hourly data.")

            # Wait for next cycle
            print(f"Next check in {check_interval_minutes} minutes...")
            time.sleep(check_interval_minutes * 60)

    except KeyboardInterrupt:
        print("\n Monitoring stopped manually.")

    print("\n Monitoring session complete.")


# single check
weather = fetch_current_weather()
if weather:
    pred = predict_flood_risk(weather)
    display_alert(weather, pred)

# for live monitoring every five minutes, uncomment below
#monitor_flood_risk(check_interval_minutes=5)
