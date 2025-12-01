import yfinance as yf
import pandas as pd

ticker = "HDFCAMC.NS"
print("1. Downloading Data...")
data = yf.download(ticker, period="1mo", interval="1d") # Just 1 month for testing

print("\n--- RAW DATA (Messy Double Header) ---")
print(data.head(2)) # See the messy top rows?

# The Fix
if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)

print("\n--- CLEAN DATA (Single Header) ---")
print(data.head(2)) # Clean!

print("\n3. Calculating SMA (Rolling)...")
# Let's do a tiny window of 3 days so we can see it work
data["SMA_3"] = data["Close"].rolling(window=3).mean()

print("\n--- DATA WITH SMA COLUMN ---")
# showing the last 5 rows to see the numbers
print(data[["Close", "SMA_3"]].tail(5))