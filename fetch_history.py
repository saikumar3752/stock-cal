import yfinance as yf
import pandas as pd
from supabase import create_client, Client
import time
import os
# --- CONFIGURATION ---
# 1. PASTE YOUR SUPABASE URL & KEY HERE
SUPABASE_URL =os.environ.get("https://uvimynszhofmncujwrfb.supabase.co")
SUPABASE_KEY =os.environ.get("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV2aW15bnN6aG9mbW5jdWp3cmZiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM1MzAwNjgsImV4cCI6MjA3OTEwNjA2OH0.Qc62_n1a0fskv9ZBTx8KOLWw2czrEbb_4X9nSj_phd0")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ CRITICAL ERROR: Supabase Keys are missing from Environment Variables!")
# 2. Connect to Database
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_active_stocks():
    print("Fetching stock list from Database...")
    # Fetch active stocks from your 'stocks' table
    response = supabase.table("stocks").select("symbol").eq("is_active", True).execute()
    return [item['symbol'] for item in response.data]

def update_history(symbol):
    print(f"Processing: {symbol} ... ", end="")
    try:
        # 1. Fetch 5 years of data from Yahoo
        stock = yf.Ticker(symbol)
        hist = stock.history(period="5y")
        
        if hist.empty:
            print("❌ No Data Found.")
            return

        # 2. Convert Data to list of dictionaries (for Supabase)
        records = []
        for date, row in hist.iterrows():
            records.append({
                "symbol": symbol,
                "date": date.strftime('%Y-%m-%d'),
                "close_price": round(row['Close'], 2),
                "volume": int(row['Volume'])
            })
        
        # 3. Upload in chunks (Supabase limit is usually 1000 rows per request)
        batch_size = 1000
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            # 'upsert' ensures we don't create duplicate dates for the same stock
            supabase.table("market_data").upsert(batch, on_conflict="symbol, date").execute()
            
        print(f"✅ Uploaded {len(records)} days of data.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

# --- EXECUTE ---
# 1. Get the list
all_stocks = get_active_stocks()

# 2. Run for just the first 10 stocks (TEST MODE)
print(f"\nStarting Test Run for first 10 stocks out of {len(all_stocks)}...")

for stock in all_stocks[:10]: 
    update_history(stock)
    time.sleep(1) # Be polite to Yahoo (prevents banning)

print("\n[SUCCESS] Test Run Complete. Check Supabase 'market_data' table.")