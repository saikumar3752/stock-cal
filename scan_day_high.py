import yfinance as yf
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import time
import warnings

# Silence the annoying Pandas warning
warnings.simplefilter(action='ignore', category=pd.errors.SettingWithCopyWarning)

# --- CONFIGURATION ---
SUPABASE_URL = "https://uvimynszhofmncujwrfb.supabase.co"
SUPABASE_KEY ="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV2aW15bnN6aG9mbW5jdWp3cmZiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM1MzAwNjgsImV4cCI6MjA3OTEwNjA2OH0.Qc62_n1a0fskv9ZBTx8KOLWw2czrEbb_4X9nSj_phd0"  
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# List of bad stocks to permanently ignore (Add more if you find them)
BLACKLIST = ["ADANI-RE.NS", "ABMINTLLTD.NS"]

def get_nifty500_symbols():
    print("📥 Fetching Nifty 500 list from Database...")
    try:
        response = supabase.table("stocks").select("symbol").eq("is_active", True).execute()
        # Filter out the blacklist instantly
        return [item['symbol'] for item in response.data if item['symbol'] not in BLACKLIST]
    except:
        # Fallback if DB fails
        return ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "TATAMOTORS.NS", "ZOMATO.NS"]

def scan_and_track():
    print(f"\n🔎 Scanning Nifty 500 at {datetime.now().strftime('%H:%M:%S')}...")
    
    full_watchlist = get_nifty500_symbols()
    
    # BATCH PROCESSING
    batch_size = 50
    
    today_start = datetime.now().strftime('%Y-%m-%d 00:00:00')
    existing_response = supabase.table("intraday_alerts").select("*").gte("alert_time", today_start).execute()
    existing_map = {item['symbol']: item for item in existing_response.data}
    
    alerts_to_upsert = []

    for i in range(0, len(full_watchlist), batch_size):
        batch = full_watchlist[i:i+batch_size]
        
        try:
            # 'shared._ERRORS' helps us suppress Yahoo's noisy prints if needed, 
            # but 'auto_adjust=True' usually helps.
            data = yf.download(batch, period="1d", interval="5m", group_by='ticker', progress=False, threads=False, auto_adjust=True)
            
            for symbol in batch:
                try:
                    # FIX: Handle Dataframe Copy
                    if len(batch) == 1: 
                        df = data.copy()
                    else: 
                        # Check if symbol exists in data columns
                        if symbol not in data.columns.levels[0]:
                            continue
                        df = data[symbol].copy() # <--- THIS FIXES THE WARNING
                    
                    if df.empty: continue

                    # Latest Candle Data
                    current_price = float(df['Close'].iloc[-1])
                    day_high = float(df['High'].max())
                    volume = int(df['Volume'].iloc[-1])
                    
                    # Skip penny stocks (< 20 Rs)
                    if current_price < 20: continue 

                    # SCENARIO A: Update Existing Alert
                    if symbol in existing_map:
                        entry_price = float(existing_map[symbol]['entry_price'])
                        profit_pct = ((current_price - entry_price) / entry_price) * 100
                        
                        alerts_to_upsert.append({
                            "id": existing_map[symbol]['id'],
                            "symbol": symbol,
                            "entry_price": entry_price,
                            "current_price": current_price,
                            "profit_pct": round(profit_pct, 2),
                            "volume": volume,
                            "alert_time": existing_map[symbol]['alert_time'],
                            "breakout_type": "Day High"
                        })

                    # SCENARIO B: New Breakout
                    elif current_price >= (day_high * 0.999):
                        print(f"   🚀 BREAKOUT: {symbol} @ ₹{current_price}")
                        alerts_to_upsert.append({
                            "symbol": symbol,
                            "entry_price": current_price,
                            "current_price": current_price,
                            "profit_pct": 0.0,
                            "volume": volume,
                            "alert_time": datetime.now().isoformat(),
                            "breakout_type": "Day High"
                        })

                except Exception:
                    continue
            
        except Exception:
            continue

    # Save Changes to DB
    if alerts_to_upsert:
        for j in range(0, len(alerts_to_upsert), 100):
            chunk = alerts_to_upsert[j:j+100]
            supabase.table("intraday_alerts").upsert(chunk).execute()
        print(f"✅ Database Updated ({len(alerts_to_upsert)} records).")

# --- LOOP ---
while True:
    scan_and_track()
    print("Sleeping 60 seconds...")
    time.sleep(60)