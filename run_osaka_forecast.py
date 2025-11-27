# run_osaka_forecast.py
import os
import requests
import pandas as pd
from weather_blowdart_engine import train_weather_model, predict_weather

LAT = 34.6937
LON = 135.5023

def get_weather_data():
    print("📡 Fetching Osaka weather data...")
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": LAT, "longitude": LON,
        "start_date": (pd.Timestamp.now() - pd.Timedelta(days=90)).strftime('%Y-%m-%d'),
        "end_date": pd.Timestamp.now().strftime('%Y-%m-%d'),
        "hourly": "temperature_2m,relative_humidity_2m,rain,pressure_msl",
        "timezone": "Asia/Tokyo"
    }
    response = requests.get(url, params=params)
    df = pd.DataFrame(response.json()['hourly'])
    df['time'] = pd.to_datetime(df['time'])
    df['rain_binary'] = (df['rain'] > 0).astype(int)
    df['Target_12h'] = df['rain_binary'].shift(-12)
    df['Target_24h'] = df['rain_binary'].shift(-24)
    df['pressure_diff'] = df['pressure_msl'].diff()
    df['temp_diff'] = df['temperature_2m'].diff()
    return df

def generate_markdown_report(pred_12h, pred_24h):
    icon_12 = "☔" if "Rain" in pred_12h['prediction'] else "☀"
    icon_24 = "☔" if "Rain" in pred_24h['prediction'] else "☀"
    
    md = f"""
# 🏯 Osaka Weather Forecast (Soei Engine)
**Generated at:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M JST')}

| Prediction Time | Forecast | Confidence | Regime (Atmosphere) |
| :--- | :--- | :--- | :--- |
| **+12 Hours** | {icon_12} **{pred_12h['prediction']}** | `{pred_12h['probability']*100:.1f}%` | {pred_12h['regime']} |
| **+24 Hours** | {icon_24} **{pred_24h['prediction']}** | `{pred_24h['probability']*100:.1f}%` | {pred_24h['regime']} |

### 🧠 Engine Status
- **Engine Core:** XGBoost Hybrid (Simple + Aggressive)
- **Data Source:** Open-Meteo API (Real-time)
"""
    if 'GITHUB_STEP_SUMMARY' in os.environ:
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as f: f.write(md)
    else:
        print(md)

def main():
    df = get_weather_data()
    train_df = df.iloc[:-24].copy()
    train_weather_model("OSAKA", train_df, target_col='Target_12h')
    train_weather_model("OSAKA", train_df, target_col='Target_24h')
    pred_12h = predict_weather("OSAKA", df, target_label='12h')
    pred_24h = predict_weather("OSAKA", df, target_label='24h')
    generate_markdown_report(pred_12h, pred_24h)

if __name__ == "__main__":
    main()
