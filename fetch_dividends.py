import yfinance as yf
import pandas as pd

# 1. Define the Stock (Reliance Industries)
ticker_symbol = "RELIANCE.NS" 
print(f"Fetching data for {ticker_symbol}...")

# 2. Fetch the Data
stock = yf.Ticker(ticker_symbol)

# 3. Get Dividend History
dividends = stock.dividends

# 4. Filter for the last 1 year only
one_year_ago = pd.Timestamp.now(tz=dividends.index.tz) - pd.DateOffset(years=1)
recent_dividends = dividends[dividends.index > one_year_ago]

# 5. Calculate Stats
total_dividend = recent_dividends.sum()
current_price = stock.history(period="1d")['Close'].iloc[-1]
yield_percent = (total_dividend / current_price) * 100

# 6. Display the "Clean Data"
print("\n--- DIVIDEND REPORT ---")
print(f"Stock: {ticker_symbol}")
print(f"Current Price: ₹{current_price:.2f}")
print(f"Total Dividend (Last 1 Year): ₹{total_dividend:.2f}")
print(f"Actual Yield: {yield_percent:.2f}%")
print("\nDetailed History:")
print(recent_dividends)

# 7. Save to CSV
filename = f"{ticker_symbol}_dividends.csv"
recent_dividends.to_csv(filename)
print(f"\n[SUCCESS] Data saved to {filename}")