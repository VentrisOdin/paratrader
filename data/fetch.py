# data/fetch.py

import requests
import pandas as pd
import os

def fetch_candles(instrument="EUR_USD", count=300, granularity="H1"):
    url = f"{os.getenv('OANDA_API_URL')}/instruments/{instrument}/candles"
    headers = {
        "Authorization": f"Bearer {os.getenv('OANDA_API_KEY')}"
    }
    params = {
        "count": count,
        "granularity": granularity,
        "price": "M"
    }
    r = requests.get(url, headers=headers, params=params)
    data = r.json()["candles"]

    df = pd.DataFrame([{
        "time": c["time"],
        "open": float(c["mid"]["o"]),
        "high": float(c["mid"]["h"]),
        "low": float(c["mid"]["l"]),
        "close": float(c["mid"]["c"]),
    } for c in data if c["complete"]])

    df["time"] = pd.to_datetime(df["time"])
    return df
