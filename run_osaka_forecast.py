# weather_osaka_beautiful.py ← こっちにリネームして使え

import datetime
import math
import os
import random
from typing import List, Tuple


# 季節ごとに大阪っぽい気温・降水のベースラインを定義
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
    1: 30,
    2: 25,
    3: 35,
    4: 40,
    5: 45,
    6: 65,  # 梅雨
    7: 55,
    8: 60,  # 夕立が多い
    9: 50,
    10: 35,
    11: 30,
    12: 25,
}


def weather_emoji(code: int) -> str:
    mapping = {0: "☀️", 1: "☀️", 2: "⛅", 3: "☁️", 45: "🌫", 51: "🌦", 61: "🌧", 80: "💦", 95: "⛈"}
    return mapping.get(code, "🌈")


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def synthesize_osaka_forecast(start: datetime.datetime, hours: int = 24) -> List[Tuple[str, float, int, int]]:
    """
    ネット接続なしで大阪の天気を推定する簡易モデル。
    日付ベースのシードを使って「毎日」同じ予報を再現できる。
    戻り値: [(ISO文字列の時間, 気温, weathercode, 降水確率)]
    """

    rng = random.Random(int(start.strftime("%Y%m%d")))
    month = start.month
    base_temp, temp_range = MONTHLY_BASE_TEMP[month]
    precip_base = MONTHLY_PRECIP_BASE[month]

    daily_bias = rng.uniform(-1.5, 1.5)  # その日の気圧配置や前線をざっくり表現
    storm_bias = 18 if month in {6, 7, 8, 9} else 8

    forecast = []
    for step in range(hours):
        t = start + datetime.timedelta(hours=step)
        # 14時頃が最も暖かく、明け方が冷えやすいサイン波
        diurnal = math.sin(((t.hour - 14) / 24) * math.pi * 2)
        temp = base_temp + daily_bias + diurnal * temp_range * 0.6 + rng.uniform(-1.0, 1.0)

        cloud_factor = clamp((1 - (diurnal + 1) / 2) * 0.6 + rng.uniform(0, 0.4), 0, 1)
        precip_prob = clamp(precip_base + cloud_factor * 30 + rng.uniform(-10, 20), 0, 100)

        # 天気コードを確率的に決定
        roll = rng.uniform(0, 100)
        if roll < precip_prob * 0.6:
            code = 61 if precip_prob < storm_bias + 25 else 80
        elif roll < precip_prob:
            code = 51
        else:
            if cloud_factor > 0.75:
                code = 3
            elif cloud_factor > 0.35:
                code = 2
            else:
                code = 0

        # 台風・前線をざっくり反映
        if precip_prob > 85 and rng.random() < 0.15:
            code = 95

        forecast.append((t.strftime("%Y-%m-%dT%H:%M"), round(temp, 1), code, int(round(precip_prob))))

    return forecast


def get_weather():
    now = datetime.datetime.now()
    generated_at = now.strftime("%Y年%m月%d日 %H:%M更新")
    forecast = synthesize_osaka_forecast(now, hours=24)

    rows = ""
    for time, temp, code, p in forecast:
        time_jp = time[11:16]  # 時:分だけ
        emoji = weather_emoji(code)
        rows += f"<tr><td>{time_jp}</td><td>{emoji} {temp}°C</td><td>降水{p}%</td></tr>"

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
            footer {{ margin-top: 18px; color: #666; font-size: 14px; }}
        </style>
    </head>
    <body>
    <h1>大阪 天気予報</h1>
    <p>更新: {generated_at}</p>
    <table>
      <tr><th>時間</th><th>天気・気温</th><th>降水確率</th></tr>
      {rows}
    </table>
    <footer>
      <div>モデル: 季節性 + 日内変動 + ランダム擾乱 (ネット未使用)</div>
      <div>同じ日付では同じ予報を再現できます。毎日このスクリプトを実行して最新を生成してください。</div>
    </footer>
    </body>
    </html>
    """

    base = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base, "data")
    os.makedirs(data_dir, exist_ok=True)

    path = os.path.join(data_dir, "forecast.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"ローカル予報を出力 → {path}")


if __name__ == "__main__":
    get_weather()
