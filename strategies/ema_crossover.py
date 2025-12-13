import pandas as pd
import numpy as np

def run(df):
    """
    EMA Crossover Strategy:
    Buy when 9 EMA crosses above 21 EMA.
    """
    # 1. Calculate Indicators
    # Use standard pandas EWM (Exponential Weighted Mean)
    df['EMA_Short'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA_Long'] = df['Close'].ewm(span=21, adjust=False).mean()

    # 2. Logic: Crossover
    # We check the relationship TODAY vs YESTERDAY
    
    # Current values (Latest candle)
    curr_short = df['EMA_Short'].iloc[-1]
    curr_long = df['EMA_Long'].iloc[-1]
    
    # Previous values (Yesterday's candle)
    prev_short = df['EMA_Short'].iloc[-2]
    prev_long = df['EMA_Long'].iloc[-2]

    signal = "NEUTRAL"
    
    # BUY: Short crosses ABOVE Long (It was below yesterday, is above today)
    if prev_short < prev_long and curr_short > curr_long:
        signal = "BUY"
        
    # SELL: Short crosses BELOW Long
    elif prev_short > prev_long and curr_short < curr_long:
        signal = "SELL"

    # 3. Return Standard Result for Master Engine
    # Note: We return the Price so the website knows entry price
    return {
        "strategy_name": "EMA Crossover",
        "signal": signal,
        "ticker": "UNKNOWN", # Master Engine fills this
        "price": round(df['Close'].iloc[-1], 2),
        "date": df.index[-1].strftime('%Y-%m-%d')
    }