import pandas as pd
import numpy as np
import oandapyV20
from ta.trend import MACD
from dotenv import load_dotenv
import os
import requests

# --- CONFIG ---
load_dotenv()  # Load environment variables from .env file

# Fetching credentials from environment variables
ACCESS_TOKEN = os.getenv("OANDA_API_KEY")  # Get the OANDA API key from the .env file
ACCOUNT_ID = os.getenv("OANDA_ACCOUNT_ID")  # Get OANDA Account ID
OANDA_URL = 'api-fxpractice.oanda.com'  # For demo; replace with 'api-fxtrade.oanda.com' for live
PORT = 443
CANDLE_COUNT = 150
TIMEFRAME = 'H4'

# Initialize OANDA client
client = oandapyV20.API(access_token=ACCESS_TOKEN)

# Get all tradeable forex pairs
def get_forex_pairs():
    # Correct request to fetch instruments
    params = {"accountID": ACCOUNT_ID}
    request = oandapyV20.endpoints.accounts.Instruments(accountID=ACCOUNT_ID)
    response = client.request(request)
    instruments = response.get("instruments", [])
    return [i['name'] for i in instruments if i['type'] == "CURRENCY"]

# Fetch historical candles
def get_candles(pair):
    try:
        params = {
            'granularity': TIMEFRAME,
            'count': CANDLE_COUNT,
            'price': 'M'
        }
        response = client.request(oandapyV20.endpoints.instruments.Candles(pair, params=params))
        candles = response.get("candles", [])
        data = [{
            'time': c['time'],
            'close': float(c['mid']['c']),
            'high': float(c['mid']['h']),
            'low': float(c['mid']['l'])
        } for c in candles if c['complete']]
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Error fetching candles for {pair}: {e}")
        return None

# Bullish divergence detection
def is_bullish_divergence(df):
    macd = MACD(close=df['close'])
    df['macd'] = macd.macd()
    df['signal'] = macd.macd_signal()
    df['hist'] = macd.macd_diff()

    # Local lows in price
    valleys = (df['close'][(df['close'].shift(1) > df['close']) &
                           (df['close'].shift(-1) > df['close'])])
    
    if len(valleys) < 2:
        return False

    # Compare last two valleys
    v1, v2 = valleys.index[-2], valleys.index[-1]
    price_making_lower_lows = df['close'][v2] < df['close'][v1]
    macd_making_higher_lows = df['macd'][v2] > df['macd'][v1]

    return price_making_lower_lows and macd_making_higher_lows

# MAIN LOOP
bullish_pairs = []
all_pairs = get_forex_pairs()

for pair in all_pairs:
    df = get_candles(pair)
    if df is not None and is_bullish_divergence(df):
        bullish_pairs.append(pair)

print("\n📈 Bullish Divergence Detected In:")
for pair in bullish_pairs:
    print(f" - {pair}")
