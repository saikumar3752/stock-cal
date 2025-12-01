import pandas as pd
from supabase import create_client, Client

# --- CONFIGURATION ---
SUPABASE_URL =os.environ.get("https://uvimynszhofmncujwrfb.supabase.co")
SUPABASE_KEY =os.environ.get("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV2aW15bnN6aG9mbW5jdWp3cmZiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM1MzAwNjgsImV4cCI6MjA3OTEwNjA2OH0.Qc62_n1a0fskv9ZBTx8KOLWw2czrEbb_4X9nSj_phd0")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ CRITICAL ERROR: Supabase Keys are missing from Environment Variables!")
def analyze_dividend_impact(symbol):
    # 1. Fetch Dividends from DB
    events_resp = supabase.table("corporate_actions")\
        .select("*").eq("symbol", symbol).eq("event_type", "Dividend").execute()
    events_df = pd.DataFrame(events_resp.data)
    
    if events_df.empty:
        return

    # 2. Fetch Price History from DB
    prices_resp = supabase.table("market_data")\
        .select("date, close_price").eq("symbol", symbol).execute()
    prices_df = pd.DataFrame(prices_resp.data)
    
    # Convert dates to standard format for math
    events_df['event_date'] = pd.to_datetime(events_df['event_date'])
    prices_df['date'] = pd.to_datetime(prices_df['date'])
    prices_df = prices_df.sort_values('date').set_index('date')

    print(f"\n📊 ANALYSIS REPORT: {symbol}")
    print("-" * 50)
    print(f"{'Date':<12} | {'Div Amt':<8} | {'Price Before':<12} | {'Price After':<12} | {'Effect %':<10}")
    print("-" * 50)

    # 3. The "Time Machine" Logic
    for _, event in events_df.iterrows():
        ev_date = event['event_date']
        div_amount = float(event['details'])
        
        # Find price 1 day BEFORE and 1 day AFTER
        # We use 'asof' to find the closest date if the exact date is a holiday
        try:
            idx_before = prices_df.index.get_indexer([ev_date - pd.Timedelta(days=1)], method='ffill')[0]
            idx_after = prices_df.index.get_indexer([ev_date + pd.Timedelta(days=1)], method='bfill')[0]
            
            price_before = prices_df.iloc[idx_before]['close_price']
            price_after = prices_df.iloc[idx_after]['close_price']
            
            # Calculate the real drop
            actual_drop = price_before - price_after
            drop_pct = (actual_drop / price_before) * 100
            
            # Is it a "Trap"? (If Price drops MORE than Dividend)
            status = "✅ PROFIT" if actual_drop < div_amount else "❌ TRAP"
            
            print(f"{ev_date.date()}   | ₹{div_amount:<7} | ₹{price_before:<11} | ₹{price_after:<11} | {status}")
            
        except Exception as e:
            continue # Skip if data is missing for that specific date

# --- EXECUTE ---
# Get list of stocks that actually have events
response = supabase.table("corporate_actions").select("symbol").execute()
unique_symbols = list(set([row['symbol'] for row in response.data]))

print(f"Analyzing {len(unique_symbols)} stocks...")
for stock in unique_symbols:
    analyze_dividend_impact(stock)