import json
import numpy as np
import requests

ACTUAL_URL = (
    "https://api.open-meteo.com/v1/forecast?"
    "latitude=34.69&longitude=135.50&hourly=temperature_2m,"
    "precipitation_probability,weathercode&past_days=1"
)

# 実測値（前日のデータ）
actual = requests.get(ACTUAL_URL).json()
hour = actual["hourly"]["time"]
temp = actual["hourly"]["temperature_2m"]
rain = actual["hourly"]["precipitation_probability"]
code = actual["hourly"]["weathercode"]

# 予測値
forecast = json.load(open("site/index.json", encoding="utf-8"))

# 最初の24件を比較
def mae(a, b):
    return float(np.mean(np.abs(np.array(a)-np.array(b))))

result = {
    "temperature_mae": mae(forecast["temp"], temp[:24]),
    "rain_mae": mae(forecast["rain"], rain[:24]),
    "weathercode_accuracy": float(
        np.mean([int(a==b) for a,b in zip(forecast["code"], code[:24])])
    )
}

json.dump(result, open("accuracy.json","w"), indent=2, ensure_ascii=False)
print(result)
