import yfinance as yf
import pandas as pd
from supabase import create_client, Client
import time
import os  # Essential

# --- 1. SETUP ENVIRONMENT VARIABLES ---
# We try to load .env for local development, but we don't crash if it fails.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # This is expected on GitHub Actions (we use Secrets there)
    pass

# --- 2. GET KEYS SAFELY ---
# We fetch these from the OS environment (works for both Local .env and GitHub Secrets)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# --- IMPORT THE LIST WE JUST MADE ---
from nifty500_list import NIFTY_MASTER_LIST

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_and_store():
    print(f"🚀 Starting Ingestion for {len(NIFTY_MASTER_LIST)} stocks...")
    
    for ticker in NIFTY_MASTER_LIST:
        print(f"📥 Downloading {ticker}...", end=" ")
        try:
            # Download 2 years of history
            df = yf.download(ticker, period="2y", interval="1d", progress=False)
            
            if df.empty:
                print("❌ No Data.")
                continue

            # Fix Yahoo's Multi-Level Columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            df.reset_index(inplace=True)
            
            # Prepare Records
            clean_ticker = ticker.replace(".NS", "")
            records = []
            
            for index, row in df.iterrows():
                records.append({
                    "ticker": clean_ticker,
                    "date": row['Date'].strftime('%Y-%m-%d'),
                    "close_price": round(float(row['Close']), 2),
                    "volume": int(row['Volume']) if 'Volume' in row else 0
                })
            
            # Upload in batches of 1000 to prevent timeouts
            for i in range(0, len(records), 1000):
                chunk = records[i:i + 1000]
                supabase.table("stock_prices").upsert(chunk, on_conflict="ticker,date").execute()
                
            print(f"✅ Saved {len(records)} days.")
            
        except Exception as e:
            print(f"⚠️ Error: {e}")
            
    print("🎉 Ingestion Complete.")

if __name__ == "__main__":
    fetch_and_store()