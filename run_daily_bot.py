import yfinance as yf
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import time
import os

# --- 1. SETUP ENVIRONMENT VARIABLES ---
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# --- 2. GET KEYS ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 3. CUSTOM INDICATORS (No more pandas_ta dependency!) ---
def calculate_sma(series, length):
    """Calculates Simple Moving Average"""
    return series.rolling(window=length).mean()

def calculate_rsi(series, length=14):
    """Calculates RSI using Wilder's Smoothing (Standard)"""
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    # Wilder's Smoothing
    avg_gain = gain.ewm(alpha=1/length, min_periods=length, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/length, min_periods=length, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# --- 4. MAIN LOGIC ---
def get_latest_metrics(ticker):
    try:
        # Download data
        df = yf.download(f"{ticker}.NS", period="1y", interval="1d", progress=False)
        if df.empty: return None
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # USE OUR CUSTOM FUNCTIONS
        df['RSI'] = calculate_rsi(df['Close'], length=14)
        df['SMA_50'] = calculate_sma(df['Close'], length=50)
        df['SMA_200'] = calculate_sma(df['Close'], length=200)
        
        latest = df.iloc[-1]
        
        # Safe rounding (handle NaN)
        def safe_round(val):
            return round(float(val), 2) if pd.notnull(val) else 0.0

        return {
            'close': safe_round(latest['Close']),
            'rsi': safe_round(latest['RSI']),
            'sma_50': safe_round(latest['SMA_50']),
            'sma_200': safe_round(latest['SMA_200']),
            'date': latest.name.strftime('%Y-%m-%d')
        }
    except Exception as e:
        print(f"❌ Error fetching {ticker}: {e}")
        return None

def check_condition(metrics, condition_str):
    try:
        if "RSI < 30" in condition_str:
            return metrics['rsi'] < 30, f"{metrics['rsi']}"
        elif "SMA 50 > 200" in condition_str:
            is_golden = metrics['sma_50'] > metrics['sma_200']
            return is_golden, f"{metrics['sma_50']} vs {metrics['sma_200']}"
        return False, "Unknown Rule"
    except:
        return False, "Error"

def run_bot():
    print(f"🤖 Smart Bot Waking Up... {datetime.now()}")
    
    response = supabase.table("user_deployments").select("*").eq("status", "MONITORING").execute()
    bots = response.data
    
    print(f"📋 Found {len(bots)} bots watching the market.")
    
    for bot in bots:
        ticker = bot['ticker']
        rule = bot.get('trigger_condition', 'Signal')
        print(f"   🔎 Checking {ticker} for {rule}...", end=" ")
        
        metrics = get_latest_metrics(ticker)
        if not metrics:
            print("Skipped (No Data)")
            continue
            
        triggered, current_value_str = check_condition(metrics, rule)
        
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
            supabase.table("user_deployments").update({
                "live_metric_value": str(current_value_str)
            }).eq("id", bot['id']).execute()
            
        time.sleep(0.5)

    print("🎉 Bot Run Complete.")

if __name__ == "__main__":
    run_bot()
    