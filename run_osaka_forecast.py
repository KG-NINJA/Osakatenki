import requests
import datetime
import os

def get_weather():
    API = "https://api.open-meteo.com/v1/forecast?latitude=34.6937&longitude=135.5022&hourly=temperature_2m,weathercode&timezone=Asia%2FTokyo"
    r = requests.get(API).json()
    hourly = r["hourly"]
    temps = hourly["temperature_2m"][:12]
    codes = hourly["weathercode"][:12]
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    rows = ""
    for t, c in zip(temps, codes):
        rows += f"<tr><td>{t}°C</td><td>{c}</td></tr>"

    html = f"""
    <html>
    <head><meta charset="UTF-8"><title>Osaka Weather Forecast</title></head>
    <body>
    <h1>大阪 天気予報</h1>
    <p>更新時刻: {now}</p>
    <table border="1">
      <tr><th>気温</th><th>天気コード</th></tr>
      {rows}
    </table>
    </body>
    </html>
    """

    BASE = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE, "data")
    os.makedirs(DATA_DIR, exist_ok=True)

    with open(os.path.join(DATA_DIR, "forecast.html"), "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    get_weather()
    print("HTML exported → data/forecast.html")
