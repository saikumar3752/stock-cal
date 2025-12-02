import os
import yfinance as yf
import pandas as pd
import warnings
from supabase import create_client, Client
from dotenv import load_dotenv
load_dotenv()
# --- CONFIGURATION ---
# 1. Get Keys Securely (Fixing the os.environ bug)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
# 2. Connect (or skip if keys missing)
if not SUPABASE_URL or not SUPABASE_KEY:
    print("⚠️ Keys missing. Running in Offline Mode (No Database Upload)")
    supabase = None
else:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        supabase = None

warnings.simplefilter(action='ignore', category=FutureWarning)

# --- HELPER FUNCTION: Calculate RSI manually (Removes pandas_ta dependency) ---
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

print("--- GENERATING MARKET REPORT ---")

tickers = [
    "ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS",
    "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS",
    "BEL.NS", "BHARTIARTL.NS", "COALINDIA.NS", "EICHERMOT.NS",
    "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS",
    "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "ITC.NS",
    "JSWSTEEL.NS", "KOTAKBANK.NS", "LT.NS", "MARUTI.NS",
    "NESTLEIND.NS", "NTPC.NS", "ONGC.NS", "POWERGRID.NS",
    "RELIANCE.NS", "SBILIFE.NS", "SBIN.NS", "SUNPHARMA.NS",
    "TATACONSUM.NS", "TATASTEEL.NS", "TECHM.NS",
    "TITAN.NS", "TRENT.NS", "ULTRACEMCO.NS", "WIPRO.NS",
    "INFY.NS", "TCS.NS"
]

results = []

for ticker in tickers:
    print(f"Analyzing {ticker}...")
    try:
        data = yf.download(ticker, period="1y", interval="1d", progress=False)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        
        if data.empty:
            continue

        # Calculate Indicators (Manual RSI)
        data["SMA_50"] = data["Close"].rolling(window=50).mean()
        data["RSI"] = calculate_rsi(data["Close"], period=14)
        
        price = float(data["Close"].iloc[-1])
        sma = float(data["SMA_50"].iloc[-1])
        rsi = float(data["RSI"].iloc[-1])
        
        trend = "UP" if price > sma else "DOWN"
        condition = "Overbought" if rsi > 70 else ("Oversold" if rsi < 30 else "Neutral")
        
        signal = "WAIT"
        if trend == "UP" and rsi < 70:
            signal = "BUY"
        elif trend == "DOWN":
            signal = "SELL"
            
        results.append({
            "symbol": ticker,
            "price": round(price, 2),
            "trend": trend,
            "rsi": round(rsi, 2),
            "condition": condition,
            "signal": signal
        })
    except Exception as e:
        print(f"Error analyzing {ticker}: {e}")

# --- UPLOAD TO CLOUD ---
if results and supabase:
    print("\nUploading to Supabase...")
    try:
        supabase.table('daily_scans').delete().neq('id', 0).execute()
        supabase.table('daily_scans').insert(results).execute()
        print("✅ SUCCESS: Data is live on StockCal website!")
    except Exception as e:
        print(f"❌ Database Upload Error: {e}")
else:
    print("Skipping upload.")