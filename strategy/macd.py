# strategy/macd.py

def calculate_macd(df, fast=12, slow=26, signal=9):
    df["EMA_fast"] = df["close"].ewm(span=fast, adjust=False).mean()
    df["EMA_slow"] = df["close"].ewm(span=slow, adjust=False).mean()
    df["MACD"] = df["EMA_fast"] - df["EMA_slow"]
    df["Signal"] = df["MACD"].ewm(span=signal, adjust=False).mean()
    df["MACD_Hist"] = df["MACD"] - df["Signal"]
    return df

def detect_crossovers(df):
    df["Crossover"] = (df["MACD"] > df["Signal"]) & (df["MACD"].shift(1) < df["Signal"].shift(1))
    df["Crossunder"] = (df["MACD"] < df["Signal"]) & (df["MACD"].shift(1) > df["Signal"].shift(1))
    return df
