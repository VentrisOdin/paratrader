import os
import time
import pandas as pd
from ta.trend import MACD
import numpy as np
import oandapyV20
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.instruments as instruments
from dotenv import load_dotenv

# --- Load .env credentials ---
load_dotenv()
ACCESS_TOKEN = os.getenv("OANDA_API_KEY")
ACCOUNT_ID = os.getenv("OANDA_ACCOUNT_ID")

# --- Constants ---
OANDA_URL = 'api-fxpractice.oanda.com'
CANDLE_COUNT = 150
TIMEFRAME = 'M15'
FIB_UNIT = 0.001  # Adjust based on pip range of instrument
client = oandapyV20.API(access_token=ACCESS_TOKEN)

# --- Fibonacci Grid (optional if you want discrete levels) ---
FIB_GRID = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]


# --- OANDA candle fetch ---
def get_candles(pair):
    try:
        params = {
            'granularity': TIMEFRAME,
            'count': CANDLE_COUNT,
            'price': 'M'
        }
        r = instruments.InstrumentsCandles(instrument=pair, params=params)
        candles = client.request(r).get("candles", [])
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


# --- MACD + Divergence Logic ---
def is_bullish_divergence(df):
    macd = MACD(close=df['close'])
    df['macd'] = macd.macd()
    df['signal'] = macd.macd_signal()

    valleys = df['close'][(df['close'].shift(1) > df['close']) &
                          (df['close'].shift(-1) > df['close'])]

    if len(valleys) < 2:
        return False

    v1, v2 = valleys.index[-2], valleys.index[-1]
    price_making_lower_lows = df['close'][v2] < df['close'][v1]
    macd_making_higher_lows = df['macd'][v2] > df['macd'][v1]

    return price_making_lower_lows and macd_making_higher_lows


def is_bearish_divergence(df):
    macd = MACD(close=df['close'])
    df['macd'] = macd.macd()

    peaks = df['close'][(df['close'].shift(1) < df['close']) &
                        (df['close'].shift(-1) < df['close'])]

    if len(peaks) < 2:
        return False

    p1, p2 = peaks.index[-2], peaks.index[-1]
    price_making_higher_highs = df['close'][p2] > df['close'][p1]
    macd_making_lower_highs = df['macd'][p2] < df['macd'][p1]

    return price_making_higher_highs and macd_making_lower_highs


# --- OANDA Order Placement ---
def place_bid(pair, units, order_type="MARKET", side="BUY"):
    order_data = {
        "order": {
            "units": units if side == "BUY" else -units,
            "instrument": pair,
            "timeInForce": "FOK",
            "type": order_type,
            "positionFill": "DEFAULT"
        }
    }

    try:
        response = client.request(orders.OrderCreate(ACCOUNT_ID, data=order_data))
        print(f"✅ Order placed: {response}")
    except oandapyV20.exceptions.V20Error as e:
        print(f"❌ Order error: {e}")


# --- Trade Monitoring Logic ---
def manage_trade(pair, entry_price):
    tp_price = entry_price + 3 * FIB_UNIT
    trailing_stop = entry_price - FIB_UNIT

    print(f"🔍 Managing {pair} - Entry: {entry_price:.5f}, TP: {tp_price:.5f}, SL: {trailing_stop:.5f}")

    while True:
        df = get_candles(pair)
        if df is None or df.empty:
            time.sleep(60)
            continue

        current_price = df['close'].iloc[-1]

        # Trailing stop logic
        if current_price > entry_price:
            trailing_stop = max(trailing_stop, current_price - FIB_UNIT)

        if current_price >= tp_price:
            print(f"🎯 TAKE PROFIT hit at {current_price:.5f}")
            break

        if current_price <= trailing_stop:
            print(f"🛑 STOP LOSS hit at {current_price:.5f}")
            break

        # Re-analysis for early exit
        macd = MACD(close=df['close'])
        df['macd'] = macd.macd()
        df['signal'] = macd.macd_signal()
        macd_bearish = df['macd'].iloc[-1] < df['signal'].iloc[-1]

        if macd_bearish and is_bearish_divergence(df):
            print(f"⚠️ Early Exit: Bearish MACD & divergence at {current_price:.5f}")
            break

        time.sleep(60)


# --- Strategy Runner ---
def run_strategy():
    forex_pairs = ['EUR_USD', 'GBP_USD', 'USD_JPY']  # You can expand this list

    for pair in forex_pairs:
        print(f"\n📊 Checking {pair}")
        df = get_candles(pair)
        if df is None or df.empty:
            continue

        macd = MACD(close=df['close'])
        df['macd'] = macd.macd()
        df['signal'] = macd.macd_signal()
        bullish_cross = df['macd'].iloc[-1] > df['signal'].iloc[-1]

        if bullish_cross and is_bullish_divergence(df):
            print(f"📈 Entry signal on {pair}")
            entry_price = df['close'].iloc[-1]
            place_bid(pair, 1000, side="BUY")
            manage_trade(pair, entry_price)
        else:
            print(f"❌ No entry signal on {pair}")


# --- Run the bot ---
if __name__ == "__main__":
    run_strategy()
