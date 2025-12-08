import pandas_ta as ta

def run(df):
    """
    Input: DataFrame with 'Close'
    Output: List of Buy/Sell signals and Stats
    """
    df['SMA_50'] = ta.sma(df['Close'], length=50)
    df['SMA_200'] = ta.sma(df['Close'], length=200)
    
    signals = []
    position = None
    buy_price = 0
    wins = 0; trades = 0; capital = 100000

    # Simulation Logic
    for i in range(200, len(df)):
        price = float(df['Close'].iloc[i])
        date = df.index[i].strftime('%Y-%m-%d')
        
        # BUY
        if df['SMA_50'].iloc[i] > df['SMA_200'].iloc[i] and df['SMA_50'].iloc[i-1] <= df['SMA_200'].iloc[i-1]:
            if position is None:
                position = "BUY"; buy_price = price
                signals.append({"date": date, "type": "BUY", "price": price})

        # SELL
        elif df['SMA_50'].iloc[i] < df['SMA_200'].iloc[i] and df['SMA_50'].iloc[i-1] >= df['SMA_200'].iloc[i-1]:
            if position == "BUY":
                position = None
                signals.append({"date": date, "type": "SELL", "price": price})
                trades += 1
                if price > buy_price: wins += 1
                capital = capital * (1 + ((price - buy_price)/buy_price))

    return {
        "name": "Golden Cross",
        "roi": round(((capital - 100000)/100000)*100, 2),
        "win_rate": round((wins/trades)*100, 1) if trades > 0 else 0,
        "signals": signals
    }