import yfinance as yf
import pandas as pd 
ticker="HDFCAMC.NS"
data=yf.download(ticker,period="1y",interval="1d")
if isinstance(data.columns,pd.MultiIndex):
    data.columns=data.columns.get_level_values(0)
data["sma_50"]=data["Close"].rolling(window=50).mean()
current_price=data["Close"].iloc[-1]
current_sma=data["sma_50"].iloc[-1]
print(f"Price:{current_price:.2f}")
print(f"sma_50:{current_sma:.2f}")
if current_price>current_sma:
    print("signal:up trend (price is above average )")
else:
    print("signal:downtrend(price is below average)")       