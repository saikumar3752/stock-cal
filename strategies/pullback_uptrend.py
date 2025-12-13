import pandas as pd

def run(df):
    # 1. Calculate Indicators (Standard Math)
    df['SMA_200'] = df['Close'].rolling(window=200).mean()
    
    # RSI Calculation
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # 2. Logic: Buy Dip (RSI < 40) in Uptrend (Price > SMA 200)
    signals = []
    capital = 100000
    position = 0
    buy_price = 0
    wins = 0
    total_trades = 0

    for i in range(1, len(df)):
        # Skip if SMA_200 is NaN
        if pd.isna(df['SMA_200'].iloc[i]): continue

        # BUY CONDITION
        if position == 0:
            is_uptrend = df['Close'].iloc[i] > df['SMA_200'].iloc[i]
            is_dip = df['RSI'].iloc[i] < 40
            
            if is_uptrend and is_dip:
                buy_price = df['Close'].iloc[i]
                position = (capital / buy_price)
                signals.append({"date": df['Date'].iloc[i].strftime('%Y-%m-%d'), "type": "BUY", "price": round(buy_price, 2)})

        # SELL CONDITION (RSI recovers above 70)
        elif position > 0:
            if df['RSI'].iloc[i] > 70:
                current_price = df['Close'].iloc[i]
                capital = position * current_price
                position = 0
                wins += 1
                total_trades += 1
                signals.append({"date": df['Date'].iloc[i].strftime('%Y-%m-%d'), "type": "SELL", "price": round(current_price, 2)})

    # 3. Calculate Stats
    roi = ((capital - 100000) / 100000) * 100
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
    
    return {
        "name": "Pullback Uptrend",
        "roi": round(roi, 2),
        "win_rate": round(win_rate, 1),
        "signals": signals
    }