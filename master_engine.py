import os
import importlib.util
import yfinance as yf
import pandas as pd
from supabase import create_client, Client

# --- IMPORT THE MASTER LIST ---
from nifty500_list import NIFTY_MASTER_LIST 

# --- CONFIG ---
# --- CONFIG ---
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

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def load_strategies():
    strat_modules = []
    # Ensure the folder exists
    if not os.path.exists("strategies"):
        print("❌ Error: 'strategies' folder not found.")
        return []
        
    for filename in os.listdir("strategies"):
        if filename.endswith(".py"):
            spec = importlib.util.spec_from_file_location("strategy", f"strategies/{filename}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            strat_modules.append(module)
    return strat_modules

def run_all():
    print("🧠 Master Engine Starting...")
    strategies = load_strategies()
    
    if not strategies:
        print("⚠️ No strategies found in 'strategies' folder. Please add 'golden_cross.py'.")
        return

    print(f"🔌 Loaded {len(strategies)} Strategy Plugins.")
    
    # USE THE FILE LIST, NOT THE DATABASE QUERY
    tickers = NIFTY_MASTER_LIST 
    print(f"📋 Processing {len(tickers)} stocks from Master List...")

    for t in tickers:
        clean_ticker = t.replace(".NS", "")
        print(f"   Analyzing {clean_ticker}...", end=" ")
        
        try:
            # 1. Check if we actually have data for this stock in DB
            # We skip this check to save time and let yfinance handle it, 
            # or we could do a quick DB check. For now, we proceed.
            
            # 2. Download Fresh Data for Calc (Ensures indicators are accurate)
            df = yf.download(t, period="2y", interval="1d", progress=False)
            
            if df.empty:
                print("Skipped (No Data)")
                continue
                
            if isinstance(df.columns, pd.MultiIndex): 
                df.columns = df.columns.get_level_values(0)

            # 3. Run Every Strategy
            for strat_module in strategies:
                result = strat_module.run(df)
                
                # Upload Stats
                supabase.table("strategy_performance").upsert({
                    "ticker": clean_ticker,
                    "strategy_name": result['name'],
                    "total_return": result['roi'],
                    "win_rate": result['win_rate']
                }, on_conflict="ticker,strategy_name").execute()

                # Upload Signals
                supabase.table("strategy_signals").delete().eq("ticker", clean_ticker).eq("strategy_name", result['name']).execute()
                
                if result['signals']:
                    formatted_signals = [{
                        "ticker": clean_ticker, 
                        "strategy_name": result['name'], 
                        "signal_date": s['date'], 
                        "signal_type": s['type'], 
                        "price": s['price']
                    } for s in result['signals']]
                    
                    supabase.table("strategy_signals").insert(formatted_signals).execute()
            print("✅")
            
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_all()