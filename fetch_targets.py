import yfinance as yf
import pandas as pd
from supabase import create_client, Client
import time
import os


# --- CONFIGURATION ---
SUPABASE_URL =os.environ.get("https://uvimynszhofmncujwrfb.supabase.co")
SUPABASE_KEY =os.environ.get("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV2aW15bnN6aG9mbW5jdWp3cmZiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM1MzAwNjgsImV4cCI6MjA3OTEwNjA2OH0.Qc62_n1a0fskv9ZBTx8KOLWw2czrEbb_4X9nSj_phd0")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ CRITICAL ERROR: Supabase Keys are missing from Environment Variables!")
def get_active_stocks():
    print("Fetching Nifty 500 list...")
    response = supabase.table("stocks").select("symbol").eq("is_active", True).execute()
    return [item['symbol'] for item in response.data]

def fetch_analyst_targets(symbol):
    print(f"Analyzing Targets: {symbol} ... ", end="")
    try:
        ticker = yf.Ticker(symbol)
        
        # Get data efficiently
        # 'financialData' usually has target prices
        # 'defaultKeyStatistics' has margins
        info = ticker.info
        
        current_price = info.get('currentPrice', 0)
        target_mean = info.get('targetMeanPrice', 0)
        target_high = info.get('targetHighPrice', 0)
        target_low = info.get('targetLowPrice', 0)
        recommendation = info.get('recommendationKey', 'none').replace('_', ' ').upper()
        analyst_count = info.get('numberOfAnalystOpinions', 0)

        # Validation: If data is missing, skip
        if target_mean == 0 or current_price == 0:
            print("No analyst coverage.")
            return

        # Calculate Upside
        upside = round(((target_mean - current_price) / current_price) * 100, 2)
        
        data = {
            "symbol": symbol,
            "current_price": current_price,
            "target_mean": target_mean,
            "target_high": target_high,
            "target_low": target_low,
            "recommendation": recommendation,
            "analyst_count": analyst_count,
            "upside_pct": upside,
            "updated_at": pd.Timestamp.now().isoformat()
        }
        
        # Save to DB
        supabase.table("broker_targets").upsert(data, on_conflict="symbol").execute()
        print(f"✅ Target: ₹{target_mean} (Upside: {upside}%)")
        
    except Exception as e:
        print(f"Error: {e}")

# --- EXECUTE ---
stocks = get_active_stocks()
# Let's process top 50 first to test speed
print(f"🚀 Fetching Analyst Ratings for {len(stocks)} stocks...")

for stock in stocks[:50]: # Remove [:50] later to run full list
    fetch_analyst_targets(stock)