# weather_osaka_beautiful.py ← こっちにリネームして使え

import requests
import datetime
import os

def get_weather():
    API = "https://api.open-meteo.com/v1/forecast?latitude=34.6937&longitude=135.5022&hourly=temperature_2m,weathercode,precipitation_probability&timezone=Asia%2FTokyo"
    r = requests.get(API).json()
    hourly = r["hourly"]
    times = hourly["time"][:12]
    temps = hourly["temperature_2m"][:12]
    codes = hourly["weathercode"][:12]
    rain_prob = hourly.get("precipitation_probability", [0]*12)[:12]
    now = datetime.datetime.now().strftime("%Y年%m月%d日 %H:%M更新")

    def weather_emoji(code):
        w = {0:"☀️", 1:"☀️", 2:"⛅", 3:"☁️", 45:"🌫", 51:"🌦", 61:"🌧", 80:"💦", 95:"⛈"}
        return w.get(code, "🌈")

    rows = ""
    for time, t, c, p in zip(times, temps, codes, rain_prob):
        time_jp = time[11:16]  # 時:分だけ
        emoji = weather_emoji(c)
        rows += f"<tr><td>{time_jp}</td><td>{emoji} {t}°C</td><td>降水{p}%</td></tr>"

    html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>大阪リアルタイム天気</title>
        <style>
            body {{ font-family: "Helvetica Neue", sans-serif; text-align:center; background:#f0f8ff; padding:20px; }}
            h1 {{ color:#ff6b6b; }}
            table {{ margin:20px auto; border-collapse:collapse; }}
            td, th {{ padding:12px 20px; border:1px solid #ccc; }}
            th {{ background:#ff8787; color:white; }}
        </style>
    </head>
    <body>
    <h1>大阪 天気予報</h1>
    <p>更新: {now}</p>
    <table>
      <tr><th>時間</th><th>天気・気温</th><th>降水確率</th></tr>
      {rows}
    </table>
    <p>Powered by Open-Meteo + KG-NINJA</p>
    </body>
    </html>
    """

    BASE = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE, "data")
    os.makedirs(DATA_DIR, exist_ok=True)

    path = os.path.join(DATA_DIR, "forecast.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"美しくなった天気予報を出力 → {path}")

if __name__ == "__main__":
    get_weather()
