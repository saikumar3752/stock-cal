import os 
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import warnings
from supabase import create_client, Client # NEW IMPORT

# --- CONFIGURATION ---
# REPLACE THESE WITH YOUR ACTUAL SUPABASE KEYS from your project settings!
SUPABASE_URL =os.environ.get("https://uvimynszhofmncujwrfb.supabase.co")
SUPABASE_KEY =os.environ.get("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV2aW15bnN6aG9mbW5jdWp3cmZiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM1MzAwNjgsImV4cCI6MjA3OTEwNjA2OH0.Qc62_n1a0fskv9ZBTx8KOLWw2czrEbb_4X9nSj_phd0")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ CRITICAL ERROR: Supabase Keys are missing from Environment Variables!")
# Connect to Database
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

warnings.simplefilter(action='ignore', category=FutureWarning)

print("--- GENERATING MARKET REPORT & UPLOADING ---")

tickers = [
    "ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS",
    "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS",
    "BEL.NS", "BHARTIARTL.NS", "COALINDIA.NS", "EICHERMOT.NS",
    "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS",
    "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "ITC.NS",
    "JSWSTEEL.NS", "KOTAKBANK.NS", "LT.NS", "MARUTI.NS",
    "NESTLEIND.NS", "NTPC.NS", "ONGC.NS", "POWERGRID.NS",
    "RELIANCE.NS", "SBILIFE.NS", "SBIN.NS", "SUNPHARMA.NS",
    "TATACONSUM.NS",  "TATASTEEL.NS", "TECHM.NS",
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

        data["SMA_50"] = data["Close"].rolling(window=50).mean()
        data["RSI"] = data.ta.rsi(length=14)
        
        price = float(data["Close"].iloc[-1]) # Convert to float for DB
        sma = float(data["SMA_50"].iloc[-1])
        rsi = float(data["RSI"].iloc[-1])
        
        trend = "UP" if price > sma else "DOWN"
        condition = "Overbought" if rsi > 70 else ("Oversold" if rsi < 30 else "Neutral")
        
        signal = "WAIT"
        if trend == "UP" and rsi < 70:
            signal = "BUY"
        elif trend == "DOWN":
            signal = "SELL"
            
        # Add to list
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
if results:
    print("\nUploading to Supabase...")
    
    # 1. Clear old data (Optional: if you only want today's list)
    supabase.table('daily_scans').delete().neq('id', 0).execute()
    
    # 2. Insert new data
    response = supabase.table('daily_scans').insert(results).execute()
    
    print("✅ SUCCESS: Data is live on StockCal website!")
else:
    print("No data found to upload.")