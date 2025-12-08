import yfinance as yf
import pandas as pd
import pandas_ta as ta
from supabase import create_client, Client
from datetime import datetime
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


supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)            

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_latest_metrics(ticker):
    """
    Downloads data and calculates RSI, SMA, etc.
    Returns: { 'close': 1200, 'rsi': 45, 'sma_50': 1150, 'sma_200': 1100 }
    """
    try:
        # Download slightly more data to ensure indicators calculate correctly
        df = yf.download(f"{ticker}.NS", period="1y", interval="1d", progress=False)
        if df.empty: return None
        
        # Handle MultiIndex if necessary
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Calculate Indicators
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['SMA_50'] = ta.sma(df['Close'], length=50)
        df['SMA_200'] = ta.sma(df['Close'], length=200)
        
        # Get Latest Values
        latest = df.iloc[-1]
        return {
            'close': round(float(latest['Close']), 2),
            'rsi': round(float(latest['RSI']), 2),
            'sma_50': round(float(latest['SMA_50']), 2),
            'sma_200': round(float(latest['SMA_200']), 2),
            'date': latest.name.strftime('%Y-%m-%d')
        }
    except Exception as e:
        print(f"❌ Error fetching {ticker}: {e}")
        return None

def check_condition(metrics, condition_str):
    """
    Parses string like "RSI < 30" and checks if true.
    """
    try:
        if "RSI < 30" in condition_str:
            return metrics['rsi'] < 30, f"{metrics['rsi']}"
        
        elif "SMA 50 > 200" in condition_str:
            is_golden = metrics['sma_50'] > metrics['sma_200']
            return is_golden, f"{metrics['sma_50']} vs {metrics['sma_200']}"
            
        elif "MACD" in condition_str:
            # Simple placeholder logic for MACD
            return False, "Pending"
            
        return False, "Unknown Rule"
    except:
        return False, "Error"

def run_bot():
    print(f"🤖 Smart Bot Waking Up... {datetime.now()}")
    
    # 1. Fetch All 'MONITORING' Bots
    response = supabase.table("user_deployments").select("*").eq("status", "MONITORING").execute()
    bots = response.data
    
    print(f"📋 Found {len(bots)} bots watching the market.")
    
    for bot in bots:
        ticker = bot['ticker']
        rule = bot.get('trigger_condition', 'Signal')
        print(f"   🔎 Checking {ticker} for {rule}...", end=" ")
        
        # 2. Get Real Data
        metrics = get_latest_metrics(ticker)
        if not metrics:
            print("Skipped (No Data)")
            continue
            
        # 3. Check Rules
        triggered, current_value_str = check_condition(metrics, rule)
        
        # 4. Update Database
        if triggered:
            print(f"✅ TRIGGERED! Buying at ₹{metrics['close']}")
            supabase.table("user_deployments").update({
                "status": "ACTIVE",
                "entry_price": metrics['close'],
                "entry_date": metrics['date'],
                "live_metric_value": f"Triggered at {current_value_str}"
            }).eq("id", bot['id']).execute()
            
        else:
            print(f"⏳ Waiting (Current: {current_value_str})")
            # Just update the display value so user sees live progress
            supabase.table("user_deployments").update({
                "live_metric_value": str(current_value_str)
            }).eq("id", bot['id']).execute()
            
        time.sleep(0.5) # Be nice to Yahoo API

    print("🎉 Bot Run Complete.")

if __name__ == "__main__":
    run_bot()