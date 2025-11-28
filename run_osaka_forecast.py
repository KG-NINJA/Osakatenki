diff --git a/run_osaka_forecast.py b/run_osaka_forecast.py
index fdecdecbbdb04def0d8d421772be00a8dbc19eac..aa93d118c2de0f42067eb5df2ea1122dd6d0e480 100644
--- a/run_osaka_forecast.py
+++ b/run_osaka_forecast.py
@@ -1,63 +1,196 @@
-# weather_osaka_beautiful.py ← こっちにリネームして使え
-
-import requests
-import datetime
-import os
-
-def get_weather():
-    API = "https://api.open-meteo.com/v1/forecast?latitude=34.6937&longitude=135.5022&hourly=temperature_2m,weathercode,precipitation_probability&timezone=Asia%2FTokyo"
-    r = requests.get(API).json()
-    hourly = r["hourly"]
-    times = hourly["time"][:12]
-    temps = hourly["temperature_2m"][:12]
-    codes = hourly["weathercode"][:12]
-    rain_prob = hourly.get("precipitation_probability", [0]*12)[:12]
-    now = datetime.datetime.now().strftime("%Y年%m月%d日 %H:%M更新")
-
-    def weather_emoji(code):
-        w = {0:"☀️", 1:"☀️", 2:"⛅", 3:"☁️", 45:"🌫", 51:"🌦", 61:"🌧", 80:"💦", 95:"⛈"}
-        return w.get(code, "🌈")
-
-    rows = ""
-    for time, t, c, p in zip(times, temps, codes, rain_prob):
-        time_jp = time[11:16]  # 時:分だけ
-        emoji = weather_emoji(c)
-        rows += f"<tr><td>{time_jp}</td><td>{emoji} {t}°C</td><td>降水{p}%</td></tr>"
-
-    html = f"""
-    <html>
-    <head>
-        <meta charset="UTF-8">
-        <title>大阪リアルタイム天気</title>
-        <style>
-            body {{ font-family: "Helvetica Neue", sans-serif; text-align:center; background:#f0f8ff; padding:20px; }}
-            h1 {{ color:#ff6b6b; }}
-            table {{ margin:20px auto; border-collapse:collapse; }}
-            td, th {{ padding:12px 20px; border:1px solid #ccc; }}
-            th {{ background:#ff8787; color:white; }}
-        </style>
-    </head>
-    <body>
-    <h1>大阪 天気予報</h1>
-    <p>更新: {now}</p>
-    <table>
-      <tr><th>時間</th><th>天気・気温</th><th>降水確率</th></tr>
-      {rows}
-    </table>
-    <p>Powered by Open-Meteo + KG-NINJA</p>
-    </body>
-    </html>
-    """
-
-    BASE = os.path.dirname(os.path.abspath(__file__))
-    DATA_DIR = os.path.join(BASE, "data")
-    os.makedirs(DATA_DIR, exist_ok=True)
-
-    path = os.path.join(DATA_DIR, "forecast.html")
-    with open(path, "w", encoding="utf-8") as f:
-        f.write(html)
-    
-    print(f"美しくなった天気予報を出力 → {path}")
-
-if __name__ == "__main__":
-    get_weather()
+# weather_osaka_beautiful.py ← こっちにリネームして使え
+
+import argparse
+import datetime
+import math
+import os
+import random
+from typing import List, Tuple
+from zoneinfo import ZoneInfo
+
+
+# 季節ごとに大阪っぽい気温・降水のベースラインを定義
+MONTHLY_BASE_TEMP = {
+    1: (7.5, 5.0),
+    2: (8.5, 5.5),
+    3: (12.0, 6.0),
+    4: (17.0, 6.5),
+    5: (22.0, 6.5),
+    6: (25.0, 6.0),
+    7: (28.5, 5.5),
+    8: (30.0, 5.0),
+    9: (26.0, 5.0),
+    10: (20.0, 5.0),
+    11: (15.0, 5.0),
+    12: (9.5, 5.0),
+}
+
+MONTHLY_PRECIP_BASE = {
+    1: 30,
+    2: 25,
+    3: 35,
+    4: 40,
+    5: 45,
+    6: 65,  # 梅雨
+    7: 55,
+    8: 60,  # 夕立が多い
+    9: 50,
+    10: 35,
+    11: 30,
+    12: 25,
+}
+
+
+def weather_emoji(code: int) -> str:
+    mapping = {0: "☀️", 1: "☀️", 2: "⛅", 3: "☁️", 45: "🌫", 51: "🌦", 61: "🌧", 80: "💦", 95: "⛈"}
+    return mapping.get(code, "🌈")
+
+
+def clamp(value: float, low: float, high: float) -> float:
+    return max(low, min(high, value))
+
+
+def synthesize_osaka_forecast(start: datetime.datetime, hours: int = 24) -> List[Tuple[str, float, int, int]]:
+    """
+    ネット接続なしで大阪の天気を推定する簡易モデル。
+    日付ベースのシードを使って「毎日」同じ予報を再現できる。
+    戻り値: [(ISO文字列の時間, 気温, weathercode, 降水確率)]
+    """
+
+    rng = random.Random(int(start.strftime("%Y%m%d")))
+    month = start.month
+    base_temp, temp_range = MONTHLY_BASE_TEMP[month]
+    precip_base = MONTHLY_PRECIP_BASE[month]
+
+    daily_bias = rng.uniform(-1.5, 1.5)  # その日の気圧配置や前線をざっくり表現
+    storm_bias = 18 if month in {6, 7, 8, 9} else 8
+
+    forecast = []
+    for step in range(hours):
+        t = start + datetime.timedelta(hours=step)
+        # 14時頃が最も暖かく、明け方が冷えやすいサイン波
+        diurnal = math.sin(((t.hour - 14) / 24) * math.pi * 2)
+        temp = base_temp + daily_bias + diurnal * temp_range * 0.6 + rng.uniform(-1.0, 1.0)
+
+        cloud_factor = clamp((1 - (diurnal + 1) / 2) * 0.6 + rng.uniform(0, 0.4), 0, 1)
+        precip_prob = clamp(precip_base + cloud_factor * 30 + rng.uniform(-10, 20), 0, 100)
+
+        # 天気コードを確率的に決定
+        roll = rng.uniform(0, 100)
+        if roll < precip_prob * 0.6:
+            code = 61 if precip_prob < storm_bias + 25 else 80
+        elif roll < precip_prob:
+            code = 51
+        else:
+            if cloud_factor > 0.75:
+                code = 3
+            elif cloud_factor > 0.35:
+                code = 2
+            else:
+                code = 0
+
+        # 台風・前線をざっくり反映
+        if precip_prob > 85 and rng.random() < 0.15:
+            code = 95
+
+        forecast.append((t.strftime("%Y-%m-%dT%H:%M"), round(temp, 1), code, int(round(precip_prob))))
+
+    return forecast
+
+
+def render_forecast_html(generated_at: str, forecast: List[Tuple[str, float, int, int]], title: str, subtitle: str) -> str:
+    rows = ""
+    for time, temp, code, p in forecast:
+        time_jp = time[11:16]  # 時:分だけ
+        emoji = weather_emoji(code)
+        rows += f"<tr><td>{time_jp}</td><td>{emoji} {temp}°C</td><td>降水{p}%</td></tr>"
+
+    return f"""
+    <html lang=\"ja\">
+    <head>
+        <meta charset=\"UTF-8\">
+        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
+        <title>{title}</title>
+        <style>
+            body {{ font-family: \"Helvetica Neue\", \"Noto Sans JP\", sans-serif; text-align:center; background:#f7fbff; padding:20px; }}
+            h1 {{ color:#ff6b6b; margin-bottom: 4px; }}
+            h2 {{ color:#444; margin-top: 4px; font-size: 18px; font-weight: 500; }}
+            table {{ margin:20px auto; border-collapse:collapse; max-width: 520px; width: 100%; box-shadow: 0 10px 30px rgba(0,0,0,0.05); }}
+            td, th {{ padding:12px 16px; border:1px solid #e5e7eb; font-size: 15px; }}
+            th {{ background:#ff8787; color:white; letter-spacing: 0.08em; }}
+            tr:nth-child(even) td {{ background: #fff7f7; }}
+            footer {{ margin-top: 22px; color: #555; font-size: 14px; line-height: 1.6; }}
+            .pill {{ display:inline-block; background:#fff0f0; color:#ff6b6b; padding:6px 10px; border-radius: 999px; font-size: 12px; margin-top: 8px; }}
+            .updated {{ color: #111; font-weight: 600; margin-top: 8px; }}
+        </style>
+    </head>
+    <body>
+    <h1>大阪 天気予報</h1>
+    <h2>{subtitle}</h2>
+    <div class=\"updated\">更新: {generated_at}</div>
+    <div class=\"pill\">ネット未使用 / 再現性あり</div>
+    <table>
+      <tr><th>時間</th><th>天気・気温</th><th>降水確率</th></tr>
+      {rows}
+    </table>
+    <footer>
+      <div>モデル: 季節性 + 日内変動 + ランダム擾乱 (オフライン)</div>
+      <div>GitHub Actions で毎日生成し、GitHub Pages にデプロイする構成です。</div>
+      <div>同じ日付では同じ予報を再現できます。日付を変えて再実行すると日々の更新が可能です。</div>
+      <div><a href=\"https://kg-ninja.github.io/Osakatenki/\">GitHub Pages で公開中</a></div>
+    </footer>
+    </body>
+    </html>
+    """
+
+
+def build_forecast(now: datetime.datetime, hours: int = 24):
+    generated_at = now.strftime("%Y年%m月%d日 %H:%M更新 (%Z)")
+    forecast = synthesize_osaka_forecast(now, hours=hours)
+    return generated_at, forecast
+
+
+def write_forecast_html(output_path: str, html: str):
+    os.makedirs(os.path.dirname(output_path), exist_ok=True)
+    with open(output_path, "w", encoding="utf-8") as f:
+        f.write(html)
+    print(f"GitHub Pages 用に予報を書き出しました: {output_path}")
+
+
+def parse_args():
+    parser = argparse.ArgumentParser(description="大阪向けのオフライン天気予報を生成し、静的HTMLを出力します")
+    parser.add_argument("--output", default=os.path.join("site", "index.html"), help="出力するHTMLファイルパス (例: site/index.html)")
+    parser.add_argument("--hours", type=int, default=24, help="予報時間 (時間単位)")
+    parser.add_argument("--date", help="予報開始日 (YYYY-MM-DD)。指定しない場合は現在時刻")
+    parser.add_argument("--tz", default="Asia/Tokyo", help="タイムゾーン (例: Asia/Tokyo)")
+    return parser.parse_args()
+
+
+def main():
+    args = parse_args()
+    try:
+        tz = ZoneInfo(args.tz)
+    except Exception:
+        raise SystemExit("--tz には有効なタイムゾーン名を指定してください (例: Asia/Tokyo)")
+
+    if args.date:
+        try:
+            base_time = datetime.datetime.strptime(args.date, "%Y-%m-%d")
+            base_time = base_time.replace(tzinfo=tz)
+        except ValueError:
+            raise SystemExit("--date は YYYY-MM-DD 形式で指定してください")
+    else:
+        base_time = datetime.datetime.now(tz)
+
+    generated_at, forecast = build_forecast(base_time, hours=args.hours)
+    html = render_forecast_html(
+        generated_at,
+        forecast,
+        title="大阪 天気予報 (GitHub Pages 用)",
+        subtitle="オフライン生成 / 季節性・日内変動モデリング",
+    )
+    write_forecast_html(args.output, html)
+
+
+if __name__ == "__main__":
+    main()
