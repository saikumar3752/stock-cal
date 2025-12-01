import upstox_client
from upstox_client.rest import ApiException
from supabase import create_client, Client
from datetime import datetime
import time
import json
import math

# --- CONFIGURATION ---
SUPABASE_URL = "https://uvimynszhofmncujwrfb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV2aW15bnN6aG9mbW5jdWp3cmZiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM1MzAwNjgsImV4cCI6MjA3OTEwNjA2OH0.Qc62_n1a0fskv9ZBTx8KOLWw2czrEbb_4X9nSj_phd0" 
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Load Token
try:
    with open("access_token.txt", "r") as f: ACCESS_TOKEN = f.read().strip()
except:
    print("❌ Token missing. Run upstox_auth.py first.")
    exit()

# Load Keys
try:
    with open("instrument_keys.json", "r") as f: INSTRUMENT_MAP = json.load(f)
    print(f"✅ Loaded {len(INSTRUMENT_MAP)} instrument keys.")
except:
    print("❌ Keys missing. Run update_instruments.py")
    exit()

# Init API
config = upstox_client.Configuration()
config.access_token = ACCESS_TOKEN
api_client = upstox_client.ApiClient(config)
market_api = upstox_client.MarketQuoteApi(api_client)

# WATCHLIST (Use SIMPLE names, NO .NS)
WATCHLIST = ["RELIANCE", "TCS", "eternal", "HDFCBANK", "SBIN", "INFY"]

def run_scanner():
    print(f"\n🔎 Scanning Market at {datetime.now().strftime('%H:%M:%S')}...")
    
    # 1. Prepare Keys
    keys = []
    valid_symbols = []
    
    print("   Mapping Symbols to Keys:")
    for sym in WATCHLIST:
        # Try exact match
        key = INSTRUMENT_MAP.get(sym)
        
        # If not found, try adding NSE_EQ| prefix manually (common fallback)
        if not key:
             # Search manually in map keys? No, too slow.
             print(f"   ⚠️ Key NOT FOUND for: {sym}")
             continue
             
        keys.append(key)
        valid_symbols.append(sym)
        print(f"   - {sym} -> {key}")

    if not keys:
        print("❌ No valid keys found! Check your WATCHLIST vs instrument_keys.json")
        return

    try:
        # 2. Fetch Live Quotes
        keys_str = ",".join(keys)
        print(f"   📤 Sending Request for: {keys_str}")
        
        response = market_api.get_full_market_quote(keys_str, "2.0")
        quotes = response.data
        
        print(f"   ✅ Received Data for {len(quotes)} stocks.")
        
        # Process Data... (Simplified for Debug)
        for sym in valid_symbols:
            key = INSTRUMENT_MAP.get(sym)
            if key in quotes:
                quote = quotes[key]
                ltp = quote.last_price
                print(f"      > {sym}: ₹{ltp}")

    except ApiException as e:
        print(f"❌ Upstox API Error: {e.body}")
    except Exception as e:
        print(f"❌ General Error: {e}")

if __name__ == "__main__":
    run_scanner()