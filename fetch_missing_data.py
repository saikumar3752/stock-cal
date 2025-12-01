import yfinance as yf
from supabase import create_client, Client
import time
import os 

# --- CONFIGURATION ---
SUPABASE_URL =os.environ.get("https://uvimynszhofmncujwrfb.supabase.co")
SUPABASE_KEY =os.environ.get("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV2aW15bnN6aG9mbW5jdWp3cmZiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM1MzAwNjgsImV4cCI6MjA3OTEwNjA2OH0.Qc62_n1a0fskv9ZBTx8KOLWw2czrEbb_4X9nSj_phd0")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ CRITICAL ERROR: Supabase Keys are missing from Environment Variables!")
def get_active_stocks():
    print("Fetching Nifty 500 list from Database...")
    # 1. Fetch ALL active symbols from your 'stocks' table
    response = supabase.table("stocks").select("symbol").eq("is_active", True).execute()
    return [item['symbol'] for item in response.data]

def batch_download():
    # Get the full list (Should be ~500 stocks now)
    all_symbols = get_active_stocks()
    
    print(f"🚀 Starting Download for {len(all_symbols)} stocks...")
    print("This will take about 20 minutes. Keep this window open.")
    
    for i, symbol in enumerate(all_symbols):
        print(f"[{i+1}/{len(all_symbols)}] Processing {symbol}...", end="")
        
        try:
            # 1. Fetch History
            stock = yf.Ticker(symbol)
            # downloading 'max' history to be safe, or '5y'
            hist = stock.history(period="5y")
            
            if hist.empty:
                print(" ❌ No Data.")
                continue

            # 2. Prepare Data
            records = []
            for date, row in hist.iterrows():
                records.append({
                    "symbol": symbol,
                    "date": date.strftime('%Y-%m-%d'),
                    "close_price": round(row['Close'], 2),
                    "volume": int(row['Volume'])
                })
            
            # 3. Upload in Batches
            batch_size = 1000
            for j in range(0, len(records), batch_size):
                batch = records[j:j + batch_size]
                supabase.table("market_data").upsert(batch, on_conflict="symbol, date").execute()
                
            print(" ✅ Done.")
            
            # CRITICAL: Sleep to prevent blocking
            time.sleep(1) 
            
        except Exception as e:
            print(f" Error: {e}")

batch_download()