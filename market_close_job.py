import os
import yfinance as yf
from supabase import create_client, Client
from datetime import date
import time

# 1. SETUP & AUTH
# We grab these from GitHub Secrets (or .env locally)
URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_KEY")

if not URL or not KEY:
    raise ValueError("❌ Error: Missing Supabase Credentials")

supabase: Client = create_client(URL, KEY)

def run_market_judge():
    print(f"🚀 Starting Market Judge for {date.today()}...")

    # 2. FETCH ACTIVE TRADES
    # We only check 'ACTIVE' rows to save API calls
    response = supabase.table('recommendations') \
        .select("*") \
        .eq('status', 'ACTIVE') \
        .execute()
    
    active_recs = response.data
    
    if not active_recs:
        print("💤 No active trades to track today.")
        return

    print(f"📊 Tracking {len(active_recs)} active positions...")

    # 3. THE LOOP
    for rec in active_recs:
        # Auto-fix Indian tickers if needed (e.g. "TCS" -> "TCS.NS")
        ticker = rec['stock_ticker']
        if not ticker.endswith(('.NS', '.BO')):
            ticker += '.NS'

        target = float(rec['target_price'])
        stop_loss = float(rec['stop_loss']) if rec['stop_loss'] else 0.0
        rec_type = rec['rec_type'] # 'BUY' or 'SELL'
        
        try:
            # 4. GET TODAY'S OHLC DATA
            # period="1d" gets specifically today's candle
            stock = yf.Ticker(ticker)
            history = stock.history(period="1d")
            
            if history.empty:
                print(f"⚠️ Data missing for {ticker}, skipping...")
                continue
                
            # Extract today's price action
            today_high = history['High'].iloc[-1]
            today_low = history['Low'].iloc[-1]
            today_close = history['Close'].iloc[-1]
            
            new_status = None
            exit_price = None

            # 5. JUDGEMENT LOGIC (Buy Side)
            if rec_type == 'BUY':
                if today_high >= target:
                    new_status = 'TARGET_HIT'
                    exit_price = target
                    print(f"✅ {ticker} WON! Hit {target}")
                
                elif stop_loss > 0 and today_low <= stop_loss:
                    new_status = 'STOP_LOSS_HIT'
                    exit_price = stop_loss
                    print(f"❌ {ticker} LOST! Hit {stop_loss}")

            # 6. DATABASE UPDATE
            if new_status:
                update_data = {
                    "status": new_status,
                    "close_price": exit_price,
                    "close_date": str(date.today())
                }
                supabase.table('recommendations').update(update_data).eq('id', rec['id']).execute()
                
                # Update the Broker's Accuracy Score immediately
                update_broker_score(rec['broker_id'])

            # 7. LOG DAILY SNAPSHOT (For Charts)
            # This lets you build those "performance over time" line charts later
            snapshot_data = {
                "recommendation_id": rec['id'],
                "date": str(date.today()),
                "high_price": today_high,
                "low_price": today_low,
                "close_price": today_close
            }
            # Using upsert to prevent duplicate logs for the same day
            supabase.table('daily_snapshots').upsert(snapshot_data).execute()

            # Be nice to the API
            time.sleep(1) 

        except Exception as e:
            print(f"💀 Critical error on {ticker}: {e}")

    print("🏁 Job Done.")

def update_broker_score(broker_id):
    # Quick function to recalculate a broker's win rate
    # Fetch all CLOSED trades for this broker
    res = supabase.table('recommendations').select("status").eq('broker_id', broker_id).in_('status', ['TARGET_HIT', 'STOP_LOSS_HIT']).execute()
    trades = res.data
    
    if not trades: return

    wins = sum(1 for t in trades if t['status'] == 'TARGET_HIT')
    total = len(trades)
    new_score = round((wins / total) * 100, 2)
    
    supabase.table('brokers').update({"accuracy_score": new_score, "total_calls": total}).eq('id', broker_id).execute()
    print(f"🔄 Updated Broker {broker_id} score to {new_score}%")

if __name__ == "__main__":
    run_market_judge()