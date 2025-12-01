import pandas as pd
import requests
import io
from supabase import create_client, Client

# --- CONFIGURATION ---
SUPABASE_URL =os.environ.get("https://uvimynszhofmncujwrfb.supabase.co")
SUPABASE_KEY =os.environ.get("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV2aW15bnN6aG9mbW5jdWp3cmZiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM1MzAwNjgsImV4cCI6MjA3OTEwNjA2OH0.Qc62_n1a0fskv9ZBTx8KOLWw2czrEbb_4X9nSj_phd0")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ CRITICAL ERROR: Supabase Keys are missing from Environment Variables!")

def update_active_stocks():
    print("🚀 Fetching Official Nifty 500 List...")
    
    # 1. Direct Link to NSE's Official CSV
    url = "https://www.niftyindices.com/IndexConstituent/ind_nifty500list.csv"
    
    try:
        # Fetch CSV
        headers = {'User-Agent': 'Mozilla/5.0'}
        s = requests.get(url, headers=headers).content
        df = pd.read_csv(io.StringIO(s.decode('utf-8')))
        
        # Get list of symbols (Add .NS for Yahoo)
        nifty_symbols = [f"{sym}.NS" for sym in df['Symbol'].tolist()]
        print(f"✅ Found {len(nifty_symbols)} stocks in Nifty 500.")

        # 2. Reset ALL stocks to Inactive first
        print("Seding all stocks to INACTIVE (Clean Slate)...")
        supabase.table("stocks").update({"is_active": False}).neq("symbol", "PLACEHOLDER").execute()
        
        # 3. Mark ONLY Nifty 500 as Active
        print("Activating Nifty 500 stocks...")
        
        # We do this in batches of 100 to be safe
        batch_size = 100
        for i in range(0, len(nifty_symbols), batch_size):
            batch = nifty_symbols[i:i+batch_size]
            
            supabase.table("stocks")\
                .update({"is_active": True})\
                .in_("symbol", batch)\
                .execute()
                
            print(f"Activated batch {i} - {i+batch_size}")

        print("\n🎉 SUCCESS! Database is now filtered to Nifty 500 only.")
        print("You can now run 'fetch_missing_data.py' and it will download ONLY these 500.")

    except Exception as e:
        print(f"Error: {e}")

update_active_stocks()