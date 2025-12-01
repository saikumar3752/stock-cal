import yfinance as yf
import pandas as pd 
tickers=["TCS.NS","INFY.NS","TECHM.NS"]
print("-------------starting sector scan-----------")
for ticker in tickers:
    print(f"\nscanning{ticker}......")
    data=yf.download(ticker,period="1y",interval="1d")
    if isinstance(data.columns,pd.MultiIndex):
       data.columns=data.columns.get_level_values(0)
    data["sma_50"]=data["Close"].rolling(window=50).mean()
    current_price=data["Close"].iloc[-1]
    current_sma=data["sma_50"].iloc[-1]
    if current_price>current_sma:
        print(f"{ticker}:BULLISH(price{current_price:.2f}>sma{current_sma:.2f})")
    else:
        print(f"{ticker}:Bearish(price{current_price:.2f}<sma{current_sma:.2f})")





                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        