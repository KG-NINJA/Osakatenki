"""
Offline Osaka weather forecast generator for GitHub Pages.

Generates reproducible daily forecasts without network access and writes:
- index.html (for GitHub Pages)
- forecast.json (for accuracy comparison)
"""

import argparse
import datetime
import math
import os
import random
import json
from typing import List, Tuple
from zoneinfo import ZoneInfo

# 季節ごとの大阪ベース気温・降水
MONTHLY_BASE_TEMP = {
    1: (7.5, 5.0),
    2: (8.5, 5.5),
    3: (12.0, 6.0),
    4: (17.0, 6.5),
    5: (22.0, 6.5),
    6: (25.0, 6.0),
    7: (28.5, 5.5),
    8: (30.0, 5.0),
    9: (26.0, 5.0),
    10: (20.0, 5.0),
    11: (15.0, 5.0),
    12: (9.5, 5.0),
}

MONTHLY_PRECIP_BASE = {
    1: 30, 2: 25, 3: 35, 4: 40, 5: 45,
    6: 65, 7: 55, 8: 60, 9: 50, 10: 35,
    11: 30, 12: 25
}

def weather_emoji(code: int) -> str:
    mapping = {0:"☀️",1:"☀️",2:"⛅",3:"☁️",45:"🌫",51:"🌦",61:"🌧",80:"💦",95:"⛈"}
    return mapping.get(code, "🌈")

def clamp(v, low, high):
    return max(low, min(high, v))

def synthesize_osaka_forecast(start: datetime.datetime, hours=24):
    rng = random.Random(int(start.strftime("%Y%m%d")))
    month = start.month
    base_temp, temp_range = MONTHLY_BASE_TEMP[month]
    precip_base = MONTHLY_PRECIP_BASE[month]

    daily_bias = rng.uniform(-1.5,1.5)
    storm_bias = 18 if month in {6,7,8,9} else 8

    forecast = []
    for step in range(hours):
        t = start + datetime.timedelta(hours=step)

        diurnal = math.sin(((t.hour - 14) / 24) * math.pi * 2)
        temp = base_temp + daily_bias + diurnal * temp_range * 0.6 + rng.uniform(-1,1)

        cloud_factor = clamp((1 - (diurnal + 1)/2) * 0.6 + rng.uniform(0,0.4),0,1)
        precip_prob = clamp(precip_base + cloud_factor * 30 + rng.uniform(-10,20),0,100)

        roll = rng.uniform(0,100)
        if roll < precip_prob * 0.6:
            code = 61 if precip_prob < storm_bias+25 else 80
        elif roll < precip_prob:
            code = 51
        else:
            code = 3 if cloud_factor > 0.75 else (2 if cloud_factor > 0.35 else 0)

        if precip_prob > 85 and rng.random() < 0.15:
            code = 95

        forecast.append((
            t.strftime("%Y-%m-%dT%H:%M"),
            round(temp,1),
            code,
            int(round(precip_prob))
        ))
    return forecast

def render_forecast_html(generated_at, forecast, title, subtitle):
    rows=""
    for t,temp,code,p in forecast:
        jp = t[11:16]
        rows += f"<tr><td>{jp}</td><td>{weather_emoji(code)} {temp}°C</td><td>降水{p}%</td></tr>"

    return f"""
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
body {{ font-family:'Noto Sans JP',sans-serif; background:#f7fbff; padding:20px; text-align:center; }}
h1 {{ color:#ff6b6b; }}
table {{ margin:20px auto; border-collapse:collapse; width:520px; max-width:100%; }}
td,th {{ border:1px solid #ddd; padding:10px; }}
th {{ background:#ff8787; color:white; }}
tr:nth-child(even) td {{ background:#fff0f0; }}
</style>
</head>
<body>
<h1>大阪 天気予報</h1>
<div>更新: {generated_at}</div>
<div>オフライン生成 / 季節性・日内変動モデリング</div>
<table>
<tr><th>時間</th><th>天気・気温</th><th>降水確率</th></tr>
{rows}
</table>
</body>
</html>
"""

def write_html(path, html):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path,"w",encoding="utf-8") as f:
        f.write(html)
    print("HTML出力:", path)

def write_json(path, forecast):
    out = {
        "time":[t for (t,_,_,_) in forecast],
        "temp":[temp for (_,temp,_,_) in forecast],
        "code":[code for (_,_,code,_) in forecast],
        "rain":[rain for (_,_,_,rain) in forecast]
    }
    json_path = path.replace(".html",".json")
    with open(json_path,"w",encoding="utf-8") as f:
        json.dump(out,f,ensure_ascii=False,indent=2)
    print("JSON出力:", json_path)

def main():
    now = datetime.datetime.now(ZoneInfo("Asia/Tokyo"))
    generated_at = now.strftime("%Y-%m-%d %H:%M (%Z)")
    forecast = synthesize_osaka_forecast(now, 24)

    html = render_forecast_html(generated_at, forecast,
                                "大阪 天気予報 (GitHub Pages 用)",
                                "オフライン生成・季節性モデリング")

    write_html("site/index.html", html)
    write_json("site/index.html", forecast)

if __name__ == "__main__":
    main()
