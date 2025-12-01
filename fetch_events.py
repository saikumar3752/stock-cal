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
    # Get the same list we used before
    response = supabase.table("stocks").select("symbol").eq("is_active", True).execute()
    return [item['symbol'] for item in response.data]

def fetch_dividends(symbol):
    print(f"Checking Dividends: {symbol} ... ", end="")
    try:
        stock = yf.Ticker(symbol)
        dividends = stock.dividends
        
        if len(dividends) == 0:
            print("No dividends found.")
            return

        # Prepare data for Supabase
        records = []
        for date, amount in dividends.items():
            records.append({
                "symbol": symbol,
                "event_type": "Dividend",
                "event_date": date.strftime('%Y-%m-%d'),
                "details": str(amount)
            })
            
        # Upload
        supabase.table("corporate_actions").upsert(records, on_conflict="symbol, event_date, event_type").execute()
        print(f"✅ Saved {len(records)} dividends.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

# --- EXECUTE ---
# Run for the same first 10 stocks to match your price data
all_stocks = get_active_stocks()

print("--- STARTING EVENT SCRAPER ---")
for stock in all_stocks[:10]:
    fetch_dividends(stock)
    time.sleep(1)

print("--- COMPLETED ---")