import yfinance as yf
import pandas as pd 
import pandas_ta as ta 
import warnings
warnings.simplefilter(action='ignore',category=FutureWarning)
tickers=["TCS.NS", "INFY.NS", "TECHM.NS", "HDFCBANK.NS", "RELIANCE.NS","HDFCAMC.NS","ULTRACEMCO.NS"]
print("----------starting scanner------------")
for ticker in tickers:
    print(f"\nscanning{ticker}")
    data=yf.download(ticker,period="1y",interval="1d")
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
        data["sma_50"]=data["Close"].rolling(window=50).mean()
        data["rsi"]=data.ta.rsi(length=14)
        price=data["Close"].iloc[-1]
        sma=data["sma_50"].iloc[-1]
        rsi=data["rsi"].iloc[-1]
        if price>sma and rsi<70:
           print(f"{ticker}:Strong BUY (TREND UP+RSI {rsi:.2f}is safe )")
        elif price>sma and rsi >70:
           print(f"{ticker}:Caution  (TREND UP but RSI {rsi:.2f}is expensive )")
        else:
         print(f"{ticker}:weak(trend down)")
         print("\n---------scan complete------------")


      
