import yfinance as yf
import pandas as pd
from supabase import create_client, Client
from datetime import timedelta

# --- CONFIGURATION ---
SUPABASE_URL =os.environ.get("https://uvimynszhofmncujwrfb.supabase.co")
SUPABASE_KEY =os.environ.get("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV2aW15bnN6aG9mbW5jdWp3cmZiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM1MzAwNjgsImV4cCI6MjA3OTEwNjA2OH0.Qc62_n1a0fskv9ZBTx8KOLWw2czrEbb_4X9nSj_phd0")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ CRITICAL ERROR: Supabase Keys are missing from Environment Variables!")

def get_all_active_stocks():
    print("Fetching stock list from Database...")
    response = supabase.table("stocks").select("symbol").eq("is_active", True).execute()
    return [item['symbol'] for item in response.data]

def save_result_impact(symbol):
    print(f"Analyzing: {symbol} ... ", end="")
    
    try:
        stock = yf.Ticker(symbol)
        earnings = stock.earnings_dates
        
        if earnings is None or earnings.empty:
            print("No Calendar.")
            return

        # Clean dates
        earnings.index = earnings.index.tz_localize(None)
        past_earnings = earnings[earnings.index < pd.Timestamp.now()].head(8)

        results_to_save = []

        for event_date in past_earnings.index:
            date_before = (event_date - timedelta(days=2)).strftime('%Y-%m-%d')
            date_after = (event_date + timedelta(days=2)).strftime('%Y-%m-%d')

            # Fetch price history from YOUR database
            response = supabase.table("market_data")\
                .select("date, close_price")\
                .eq("symbol", symbol)\
                .gte("date", date_before)\
                .lte("date", date_after)\
                .execute()
            
            prices = pd.DataFrame(response.data)
            
            if not prices.empty and len(prices) >= 2:
                prices = prices.sort_values('date')
                price_pre = prices.iloc[0]['close_price']
                price_post = prices.iloc[-1]['close_price']
                change = ((price_post - price_pre) / price_pre) * 100
                
                verdict = "🚀 BOOM" if change > 3 else ("⚠️ CRASH" if change < -3 else "😐 FLAT")
                
                results_to_save.append({
                    "symbol": symbol,
                    "event_type": "Earnings",
                    "event_date": event_date.strftime('%Y-%m-%d'),
                    "price_before": price_pre,
                    "price_after": price_post,
                    "impact_pct": round(change, 2),
                    "verdict": verdict
                })

        if results_to_save:
            # THIS LINE SAVES IT TO SUPABASE
            supabase.table("analysis_results").upsert(results_to_save).execute()
            print(f"✅ Saved {len(results_to_save)} events.")
        else:
            print("Not enough price data yet.")

    except Exception as e:
        print(f"Skipping (Error): {e}")

# --- EXECUTE ---
all_stocks = get_all_active_stocks()
print(f"🚀 Starting Analysis on {len(all_stocks)} stocks...")

for i, stock in enumerate(all_stocks):
    save_result_impact(stock)

    # ... (Keep imports and setup) ...

def generate_article(stock, date, pre, post, change, verdict):
    # 1. Create a Catchy Title
    direction = "Jumps" if change > 0 else "Falls"
    title = f"{stock} Share Price {direction} {change}% After Results - Buy or Sell?"
    
    # 2. Create the Content (The Article)
    content = f"""
    <h3>{stock} Earnings Analysis</h3>
    <p>The financial results for <strong>{stock}</strong> were announced on {date}. 
    Market reaction has been significant.</p>
    
    <p>The stock price moved from <strong>₹{pre}</strong> to <strong>₹{post}</strong>, 
    registering a change of <span style='color:{'green' if change>0 else 'red'}'>{change}%</span>.</p>
    
    <h4>The Verdict: {verdict}</h4>
    <p>Our AI analysis flags this as a <strong>{verdict}</strong> signal. 
    Historically, this indicates strong momentum.</p>
    
    <p><em>Disclaimer: This is an automated report based on NSE data.</em></p>
    """
    
    slug = f"{stock.replace('.NS','').lower()}-results-{date}"
    
    return {"symbol": stock, "title": title, "content": content, "slug": slug}

# ... (Inside your save_result_impact loop) ...
# After finding a result:
article = generate_article(symbol, event_date, price_pre, price_post, change, verdict)
supabase.table("news_articles").upsert(article, on_conflict="slug").execute()
print(f"📰 Published Article: {article['title']}")