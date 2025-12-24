import yfinance as yf
from supabase import create_client
import os
import argparse # To choose between "Buying" mode and "Live Update" mode

# --- 1. CONFIGURATION ---
TOTAL_CAPITAL_LIMIT = 1500000  # 15 Lakhs
TRANCHE_SIZE = 10000           # Invest 10k per go

# --- 2. SETUP DATABASE ---
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

# --- 3. YOUR MASTER LIST (33 Stocks) ---
FORTRESS_TICKERS = [
     "GLENMARK.NS",
    "DLF.NS",
    "TMCV.NS",
    "HCLTECH.NS",
    "AFFLE.NS",
    "TATAELXSI.NS",
    "PERSISTENT.NS",
    "NETWEB.NS",
    "DIXON.NS",
    "ADANIGREEN.NS",
    "TCS.NS",
    "BHARTIARTL.NS",
    "RELIANCE.NS",
    "ADANIENT.NS",
    "ADANIPORTS.NS",
    "AMBUJACEM.NS",
    "BHEL.NS",
    "HAL.NS",
    "GMDC.NS",
    "PARAS.NS",
    "DATAPATTNS.NS",
    "MFSL.NS",
    "MAXHEALTH.NS",
    "RADICO.NS",
    "GMBREW.NS",
    "EICHERMOT.NS",
    "HINDZINC.NS",
    "HINDCOPPER.NS",
    "SILVERBEES.NS",
    "M&M.NS",
    "FEDERALBNK.NS",
    "SHRIRAMFIN.NS",
     "KFINTECH.NS",     # KFin Technologies
    "CAMS.NS",         # Computer Age Management Services
    "NSDL.NS",         # National Securities Depository Ltd
    "CDSL.NS",         # Central Depository Services (India)
    "KPIGREEN.NS",     # KPI Green Energy
    "GESHIP.NS",       # The Great Eastern Shipping Company
    "NAMSINDIA.NS",    # NAMS India
    "MUTHOOTFIN.NS"    # Muthoot Finance

]

# ==========================================
# FUNCTION 1: LIVE DASHBOARD UPDATER (Runs every minute)
# ==========================================
def update_live_prices():
    """
    Fetches real-time prices for your 33 stocks and updates the UI.
    Does NOT buy or sell anything. Just updates P&L.
    """
    print("⚡ Updating Live Portfolio Values...")
    
    # Get current holdings from DB
    assets = supabase.table('basket_assets').select('*').execute().data
    
    if not assets:
        print("No assets found in DB.")
        return

    total_value = 0
    total_invested = 0
    
    # Download live data in one batch (faster)
    # We use the tickers from the DB, not just the list, to ensure we track what we own
    db_tickers = [a['ticker'] for a in assets]
    if not db_tickers: return

    tickers_space = " ".join(db_tickers)
    
    try:
        # Fetch 1 minute data for live updates
        data = yf.download(tickers_space, period="1d", interval="1m", progress=False)['Close']
        
        # Handle single ticker vs multiple ticker return format
        if len(db_tickers) == 1:
            # If only 1 stock, data is a Series, not DataFrame
            live_prices = {db_tickers[0]: data.iloc[-1]}
        else:
            live_prices = data.iloc[-1].to_dict()

        for asset in assets:
            ticker = asset['ticker']
            shares = asset['total_shares']
            avg_price = asset['avg_price']
            
            # If we own shares, calculate value
            if shares > 0:
                # Fallback: If yfinance failed for one stock, use previous close
                current_price = live_prices.get(ticker, asset['last_buy_price']) 
                
                investment = shares * avg_price
                current_val = shares * current_price
                
                total_invested += investment
                total_value += current_val
                
        # Update the Dashboard Table
        pnl = total_value - total_invested
        pnl_pct = (pnl / total_invested * 100) if total_invested > 0 else 0
        
        supabase.table('basket_performance').update({
            'total_invested': round(total_invested, 2),
            'current_value': round(total_value, 2),
            'total_pnl': round(pnl, 2),
            'pnl_percent': round(pnl_pct, 2),
            'last_updated': "now()"
        }).eq('id', 1).execute()
        
        print(f"✅ Dashboard Updated: Current Value ₹{total_value:,.2f} ({pnl_pct:.2f}%)")
        
    except Exception as e:
        print(f"⚠️ Error updating live prices: {e}")

# ==========================================
# FUNCTION 2: WEALTH MANAGER (Runs Weekly/Daily)
# ==========================================
def run_wealth_manager():
    print("🏰 Starting Fortress Wealth Manager (Buying Logic)...")

    # A. CHECK TOTAL BUDGET
    perf_row = supabase.table('basket_performance').select('total_invested').single().execute()
    current_invested = perf_row.data.get('total_invested', 0) if perf_row.data else 0

    print(f"💰 Fund Status: ₹{current_invested:,.2f} / ₹{TOTAL_CAPITAL_LIMIT:,.2f}")

    if current_invested >= TOTAL_CAPITAL_LIMIT:
        print("🛑 Max Budget of 15L Reached. No new buys allowed.")
        return

    # B. ANALYZE STOCKS
    for ticker in FORTRESS_TICKERS:
        try:
            print(f"🔎 Checking {ticker}...", end=" ")
            
            # Get Data (1 Month for averages)
            df = yf.download(ticker, period="1mo", interval="1d", progress=False, auto_adjust=True)
            if df.empty: continue
            
            # Flatten columns if needed
            if hasattr(df.columns, 'nlevels') and df.columns.nlevels > 1:
                df.columns = df.columns.get_level_values(0)

            current_price = df['Close'].iloc[-1]
            
            # Get Asset History
            asset_record = supabase.table('basket_assets').select('*').eq('ticker', ticker).execute()
            if not asset_record.data:
                # Initialize if new
                supabase.table('basket_assets').insert({"ticker": ticker}).execute()
                asset_data = {"ticker": ticker, "last_buy_price": 0, "dip_buy_count": 0, "total_shares": 0, "avg_price": 0}
            else:
                asset_data = asset_record.data[0]

            # Strategy Logic
            sma_20 = df['Close'].rolling(20).mean().iloc[-1]
            sma_5 = df['Close'].rolling(5).mean().iloc[-1]
            
            should_buy = False
            reason = ""

            # 1. Initial Entry
            if asset_data['total_shares'] == 0:
                should_buy = True
                reason = "INITIAL_ENTRY"

            # 2. Momentum Dip
            elif (current_price > sma_20) and (current_price < sma_5):
                 should_buy = True
                 reason = "MOMENTUM_DIP"
                 # Reset dip count on momentum buy
                 supabase.table('basket_assets').update({'dip_buy_count': 0}).eq('ticker', ticker).execute()

            # 3. Falling Knife (Max 3)
            elif asset_data['last_buy_price'] > 0:
                last_price = asset_data['last_buy_price']
                drop_pct = ((current_price - last_price) / last_price) * 100
                
                if drop_pct <= -5.0 and asset_data['dip_buy_count'] < 3:
                    should_buy = True
                    reason = f"DIP_BUY_{asset_data['dip_buy_count']+1}"
                    # Increment dip count
                    supabase.table('basket_assets').update({'dip_buy_count': asset_data['dip_buy_count'] + 1}).eq('ticker', ticker).execute()

            # Execution
            if should_buy:
                # QUANTITY LOGIC (10k or 1 share)
                qty = 0
                if current_price > TRANCHE_SIZE:
                    qty = 1
                else:
                    qty = int(TRANCHE_SIZE / current_price)
                
                if qty == 0: qty = 1 # Safety net
                
                cost = qty * current_price
                
                if (current_invested + cost) > TOTAL_CAPITAL_LIMIT:
                    print("❌ Insufficient Budget.")
                    continue

                print(f"✅ BUYING! ({reason}) -> {qty} shares @ ₹{current_price:.2f}")

                # UPDATE DB
                new_shares = asset_data['total_shares'] + qty
                old_cost = asset_data['total_shares'] * asset_data['avg_price']
                new_avg = (old_cost + cost) / new_shares
                
                supabase.table('basket_assets').update({
                    'total_shares': new_shares,
                    'avg_price': new_avg,
                    'last_buy_price': current_price
                }).eq('ticker', ticker).execute()
                
                # LOG TRANSACTION
                supabase.table('basket_transactions').insert({
                    'ticker': ticker, 'action': reason, 'price': current_price, 'shares': qty, 'amount': cost
                }).execute()
                
                current_invested += cost
            else:
                print("Wait.")

        except Exception as e:
            print(f"Error on {ticker}: {e}")

# ==========================================
# MAIN COMMAND CENTER
# ==========================================
if __name__ == "__main__":
    # Create a simple command line switch
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['live', 'strategy'], default='live', help='Run "live" for dashboard updates or "strategy" for buying.')
    args = parser.parse_args()

    if args.mode == 'strategy':
        run_wealth_manager()
    else:
        update_live_prices()

        