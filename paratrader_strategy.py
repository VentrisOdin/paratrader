import os
import time
import pandas as pd
from ta.trend import MACD
import numpy as np
import oandapyV20
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.positions as positions
import oandapyV20.endpoints.instruments as instruments
import oandapyV20.endpoints.accounts as accounts
import oandapyV20.endpoints.trades as trades  # Import the correct endpoint  # make sure this import is at the top
from dotenv import load_dotenv
import threading



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

    df['valley'] = (df['close'].shift(1) > df['close']) & (df['close'].shift(-1) > df['close'])

    valleys = df[df['valley']]

    if len(valleys) < 2:
        return False

    # Get the last two valleys
    v1_idx = valleys.index[-2]
    v2_idx = valleys.index[-1]

    price_lower_low = df.loc[v2_idx, 'close'] < df.loc[v1_idx, 'close']
    macd_higher_low = df.loc[v2_idx, 'macd'] > df.loc[v1_idx, 'macd']

    # Additional condition: MACD must be below zero and turning up
    macd_below_zero = df.loc[v2_idx, 'macd'] < 0
    macd_crossing_up = df['macd'].iloc[-1] > df['signal'].iloc[-1]

    return price_lower_low and macd_higher_low and macd_below_zero and macd_crossing_up

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
def place_bid(pair, units, order_type="MARKET", side="BUY", trailing_pips=25, take_profit_pips=75):
    direction_units = units if side == "BUY" else -units
    pip_value = 0.01 if "JPY" in pair else 0.0001

    trailing_distance = round(trailing_pips * pip_value, 5)
    entry_price = get_candles(pair)['close'].iloc[-1]  # Get current price
    tp_price = round(entry_price + (take_profit_pips * pip_value), 5) if side == "BUY" else round(entry_price - (take_profit_pips * pip_value), 5)

    order_body = {
        "units": direction_units,
        "instrument": pair,
        "timeInForce": "FOK",
        "type": order_type,
        "positionFill": "DEFAULT",
        "trailingStopLossOnFill": {
            "distance": str(trailing_distance)
        },
        "takeProfitOnFill": {
            "price": str(tp_price)
        }
    }

    order_data = { "order": order_body }

    try:
        response = client.request(orders.OrderCreate(ACCOUNT_ID, data=order_data))
        print(f"✅ Order placed for {pair}: TP at {tp_price}, trailing stop {trailing_pips} pips ({trailing_distance})")
    except oandapyV20.exceptions.V20Error as e:
        print(f"❌ Order error for {pair}: {e}")

def sell_position(instrument, units):
    """Close a position for a specific instrument."""
    url = f"{OANDA_API_URL}/accounts/{OANDA_ACCOUNT_ID}/orders"
    headers = {
        "Authorization": f"Bearer {OANDA_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "order": {
            "instrument": instrument,
            "units": str(-units),  # Negative units to sell
            "type": "MARKET",
            "positionFill": "REDUCE_ONLY"
        }
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        print(f"Error selling position for {instrument}: {response.status_code} - {response.text}")
    else:
        print(f"Sold position for {instrument}: {response.json()}")

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

import oandapyV20.endpoints.accounts as accounts  # make sure this import is at the top

def get_forex_pairs():
    try:
        request = accounts.AccountInstruments(accountID=ACCOUNT_ID)
        response = client.request(request)
        instruments = response.get("instruments", [])
        return [i['name'] for i in instruments if i['type'] == "CURRENCY"]
    except Exception as e:
        print(f"Error fetching forex pairs: {e}")
        return ['EUR_USD', 'GBP_USD', 'USD_JPY']  # fallback

def get_open_trade_pairs():
    try:
        request = oandapyV20.endpoints.positions.OpenPositions(accountID=ACCOUNT_ID)
        response = client.request(request)
        open_positions = response.get("positions", [])
        return [pos['instrument'] for pos in open_positions]
    except Exception as e:
        print(f"⚠️ Error fetching open trades: {e}")
        return []

def run_strategy():
    while True:
        forex_pairs = get_forex_pairs()
        print(f"\n🧭 Scanning {len(forex_pairs)} currency pairs...")

        open_pairs = get_open_trade_pairs()

        for pair in forex_pairs:
            print(f"\n📊 Checking {pair}")

            if pair in open_pairs:
                print(f"⏭️ Skipping {pair}, already has an open trade")
                df = get_candles(pair)
                if df is None or df.empty:
                    continue

                # Check for bearish divergence in open positions
                if is_bearish_divergence(df):
                    print(f"⚠️ Bearish divergence detected on {pair}, closing position")
                    units = get_position_units(pair)  # Fetch the open position size for the pair
                    sell_position(pair, units)  # Close the open position
                continue  # Skip checking for entry signals for pairs with open positions

            # Entry logic (MACD bullish cross + bullish divergence)
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
                place_bid(pair, 1000, side="BUY", trailing_pips=25, take_profit_pips=75)
                threading.Thread(target=manage_trade, args=(pair, entry_price), daemon=True).start()

        print("⏳ Sleeping for 15 minutes before next scan...\n")
        time.sleep(900)  # 15 minutes

# --- Run the bot ---
if __name__ == "__main__":
    run_strategy()
