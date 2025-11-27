# weather_blowdart_engine.py
# 2025-11-27 宗叡・気象予測改変版 (Weather Adaptation)

import os
import json
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.preprocessing import StandardScaler, RobustScaler
from pathlib import Path
import pickle
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

MODELS_ROOT = Path("weather_models")
MODELS_ROOT.mkdir(parents=True, exist_ok=True)

LEAK_FEATURES = {
    'Future_Temp', 'Future_Rain', 'Target_12h', 'Target_24h'
}

def detect_weather_regime(df, lookback=24):
    if len(df) < lookback:
        return 'STABLE', 0.5, 0.5
    recent = df.iloc[-lookback:]
    pressure_change = recent['pressure_msl'].diff().dropna()
    vol = pressure_change.std()
    trend = abs((recent['temperature_2m'].diff() > 0).sum() - (recent['temperature_2m'].diff() < 0).sum()) / lookback
    
    if vol > 1.5:
        regime = 'UNSTABLE'
        w_s = 0.2
        w_a = 0.8
    else:
        regime = 'STABLE'
        w_s = 0.7
        w_a = 0.3
    return regime, float(vol), float(trend), w_s, w_a

def train_weather_model(location_name, features_df, target_col='Target_12h'):
    print(f"[SOEI-WEATHER] Training -> {location_name} ({target_col})")
    df = features_df.copy()
    df = df.dropna(subset=[target_col])
    cols = [c for c in df.columns if c not in ['time', target_col, 'Target_12h', 'Target_24h'] and c not in LEAK_FEATURES]
    X = df[cols].replace([np.inf, -np.inf], np.nan).fillna(0)
    y = df[target_col]
    regime, vol, trend, w_s, w_a = detect_weather_regime(df)
    
    scaler_s = StandardScaler()
    X_s = scaler_s.fit_transform(X)
    model_s = xgb.XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, random_state=42)
    model_s.fit(X_s, y)
    
    scaler_a = RobustScaler()
    X_a = scaler_a.fit_transform(X)
    models_a = [xgb.XGBClassifier(n_estimators=200, max_depth=5+i%2, learning_rate=0.08, subsample=0.7+i*0.04, random_state=42+i).fit(X_a, y) for i in range(3)]
    
    path = MODELS_ROOT / f"{location_name}_{target_col}"
    path.mkdir(parents=True, exist_ok=True)
    
    model_s.save_model(str(path/"model_simple.json"))
    for i, m in enumerate(models_a):
        m.save_model(str(path/f"model_agg_{i}.json"))
    pickle.dump(scaler_s, open(path/"scaler_simple.pkl", "wb"))
    pickle.dump(scaler_a, open(path/"scaler_agg.pkl", "wb"))
    pickle.dump(cols, open(path/"features.pkl", "wb"))
    
    metadata = {"location": location_name, "target": target_col, "regime": regime, "weights": {"simple": w_s, "aggressive": w_a}, "volatility": vol, "features": cols, "timestamp": datetime.now().isoformat()}
    with open(path/"metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    return metadata

def predict_weather(location_name, current_df, target_label='12h'):
    target_col = f'Target_{target_label}'
    path = MODELS_ROOT / f"{location_name}_{target_col}"
    if not (path/"metadata.json").exists(): return None
    
    with open(path/"metadata.json", "r") as f: meta = json.load(f)
    cols = pickle.load(open(path/"features.pkl", "rb"))
    scaler_s = pickle.load(open(path/"scaler_simple.pkl", "rb"))
    scaler_a = pickle.load(open(path/"scaler_agg.pkl", "rb"))
    
    latest_data = current_df.iloc[-1:][cols].fillna(0)
    model_s = xgb.XGBClassifier()
    model_s.load_model(str(path/"model_simple.json"))
    prob_s = model_s.predict_proba(scaler_s.transform(latest_data))[0][1]
    
    probs_a = []
    for i in range(3):
        m = xgb.XGBClassifier()
        m.load_model(str(path/f"model_agg_{i}.json"))
        probs_a.append(m.predict_proba(scaler_a.transform(latest_data))[0][1])
    
    final_prob = (prob_s * meta['weights']['simple']) + (np.mean(probs_a) * meta['weights']['aggressive'])
    return {"target": target_label, "probability": float(final_prob), "prediction": "Rain" if final_prob > 0.5 else "Clear", "regime": meta['regime']}
