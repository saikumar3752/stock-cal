import upstox_client
from upstox_client.rest import ApiException
from supabase import create_client, Client
from datetime import datetime, timedelta
import time
import json
import math
import numpy as np

# --- CONFIGURATION ---
SUPABASE_URL =os.environ.get("https://uvimynszhofmncujwrfb.supabase.co")
SUPABASE_KEY =os.environ.get("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV2aW15bnN6aG9mbW5jdWp3cmZiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM1MzAwNjgsImV4cCI6MjA3OTEwNjA2OH0.Qc62_n1a0fskv9ZBTx8KOLWw2czrEbb_4X9nSj_phd0")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ CRITICAL ERROR: Supabase Keys are missing from Environment Variables!")
# --- TRADING RULES ---
CAPITAL_PER_TRADE = 10000
LEVERAGE_X = 5            # 5x Leverage for Intraday
MAX_TRADES = 5            

# LOAD KEYS
try:
    with open("access_token.txt", "r") as f: ACCESS_TOKEN = f.read().strip()
    with open("instrument_keys.json", "r") as f: INSTRUMENT_MAP = json.load(f)
    print(f"✅ Loaded {len(INSTRUMENT_MAP)} Stocks from Database.")
except:
    print("❌ Missing Keys. Run auth/update scripts.")
    exit()

# API SETUP
config = upstox_client.Configuration()
config.access_token = ACCESS_TOKEN
config.connect_timeout = 30000 
config.read_timeout = 30000

api_client = upstox_client.ApiClient(config)
market_api = upstox_client.MarketQuoteApi(api_client)
history_api = upstox_client.HistoryApi(api_client)
order_api = upstox_client.OrderApi(api_client)
user_api = upstox_client.UserApi(api_client)

ALL_SYMBOLS = list(INSTRUMENT_MAP.keys())

# TRACKERS
# Format: {'RELIANCE': {'sl': 2400, 'target': 2500, 'qty': 10, 'key': 'NSE_EQ|...'}}
active_positions = {} 
trades_taken = 0

def get_funds():
    try:
        resp = user_api.get_user_fund_margin("2.0")
        if hasattr(resp.data, 'equity'): 
            return float(resp.data.equity.available_margin)
        else: 
            return float(resp.data['equity']['available_margin'])
    except Exception as e:
        print(f"⚠️ Error fetching funds: {e}")
        return 0.0

def get_instrument_key(symbol):
    if symbol in INSTRUMENT_MAP: return INSTRUMENT_MAP[symbol]
    if symbol + ".NS" in INSTRUMENT_MAP: return INSTRUMENT_MAP[symbol + ".NS"]
    clean = symbol.replace(".NS", "")
    if clean in INSTRUMENT_MAP: return INSTRUMENT_MAP[clean]
    return None

def calculate_atr(candles, period=14):
    try:
        highs = np.array([c[2] for c in candles])
        lows = np.array([c[3] for c in candles])
        closes = np.array([c[4] for c in candles])
        tr1 = highs[1:] - lows[1:]
        tr2 = np.abs(highs[1:] - closes[:-1])
        tr3 = np.abs(lows[1:] - closes[:-1])
        tr = np.maximum(tr1, np.maximum(tr2, tr3))
        return np.mean(tr[-period:]) 
    except: return 0

def analyze_structure(instrument_key):
    try:
        to_date = datetime.now().strftime('%Y-%m-%d')
        from_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
        time.sleep(0.05) 
        response = history_api.get_historical_candle_data1(instrument_key, "30minute", to_date, from_date, "2.0")
        if response.status == "success" and response.data and response.data.candles:
            candles = response.data.candles
            if len(candles) < 20: return None
            highs = [c[2] for c in candles]
            atr = calculate_atr(candles)
            recent_high = max(highs[-25:])
            return { "recent_high": recent_high, "atr": atr }
    except: pass
    return None

def place_order(symbol, qty, transaction_type, price=0.0, product="I", order_type="LIMIT"):
    """Generic function for both BUY and SELL."""
    key = get_instrument_key(symbol)
    if not key: return False

    print(f"🚀 {transaction_type} ORDER: {symbol} | Qty: {qty} | Price: {price}")

    try:
        body = upstox_client.PlaceOrderRequest(
            quantity=qty, 
            product=product,     
            validity="DAY", 
            price=price, 
            tag="StockCal_Bot", 
            instrument_token=key, 
            order_type=order_type, 
            transaction_type=transaction_type, 
            disclosed_quantity=0, 
            trigger_price=0.0, 
            is_amo=False
        )
        order_api.place_order(body, "2.0")
        
        # Log to Supabase
        supabase.table("trade_logs").insert({
            "symbol": symbol, "quantity": qty, "buy_price": price if transaction_type == "BUY" else 0, 
            "status": "OPEN" if transaction_type == "BUY" else "CLOSED",
            "strategy": "Bot Execution", "trade_date": datetime.now().strftime('%Y-%m-%d')
        }).execute()
        return True
    
    except ApiException as e:
        error_body = json.loads(e.body)
        error_msg = error_body.get('errors', [{'message': 'Unknown Error'}])[0].get('message')
        print(f"🛑 REJECTED {symbol}: {error_msg}")
        return False
    except Exception as e:
        print(f"❌ Python Error: {e}")
        return False

def sync_daily_orders():
    """Syncs Orders AND checks if we need to track them for exit."""
    global trades_taken, active_positions
    try:
        response = order_api.get_order_book("2.0")
        if not response.data: return

        valid_orders = 0
        
        for order in response.data:
            # We only care about OPEN Buy positions from today
            if order.order_date == datetime.now().strftime('%Y-%m-%d'):
                 if order.transaction_type == "BUY" and order.status == "complete":
                     valid_orders += 1
                     sym = order.trading_symbol
                     
                     # If we don't have targets for this (e.g., after restart), 
                     # we must add it to active_positions to track it!
                     if sym not in active_positions:
                         # Default fallback: 1% Target, 0.5% SL (since we lost memory of original calculation)
                         buy_price = float(order.average_price)
                         active_positions[sym] = {
                             'sl': buy_price * 0.995, 
                             'target': buy_price * 1.01, 
                             'qty': int(order.quantity),
                             'key': order.instrument_token
                         }

        trades_taken = valid_orders

    except Exception as e:
        print(f"Sync Warning: {e}")

# --- NEW FUNCTION: MONITOR EXITS ---
def monitor_exits():
    """Checks current prices of active positions and sells if Target/SL hit."""
    global active_positions
    
    if not active_positions: return

    print(f"\n👀 Monitoring {len(active_positions)} Active Positions...")
    
    # Get keys to fetch live prices
    keys = [data['key'] for sym, data in active_positions.items()]
    keys_str = ",".join(keys)
    
    try:
        response = market_api.get_full_market_quote(keys_str, "2.0")
        quotes = response.data
        
        # Create a list of positions to remove after selling
        to_remove = []

        for key, quote in quotes.items():
            # Find which symbol this key belongs to
            symbol = next((k for k, v in active_positions.items() if v['key'] == key), None)
            if not symbol: continue
            
            data = active_positions[symbol]
            ltp = quote.last_price
            
            # CHECK TARGET
            if ltp >= data['target']:
                print(f"💰 TARGET HIT: {symbol} @ {ltp} (Target: {data['target']:.2f})")
                # Place MARKET Sell Order for instant exit
                if place_order(symbol, data['qty'], "SELL", order_type="MARKET"):
                    to_remove.append(symbol)

            # CHECK STOP LOSS
            elif ltp <= data['sl']:
                print(f"🛡️ STOP LOSS HIT: {symbol} @ {ltp} (SL: {data['sl']:.2f})")
                # Place MARKET Sell Order
                if place_order(symbol, data['qty'], "SELL", order_type="MARKET"):
                    to_remove.append(symbol)
            else:
                # Just print status
                pnl = (ltp - (data['target']/1.02)) * data['qty'] # Approx PnL
                # print(f"   {symbol}: LTP {ltp} | SL {data['sl']:.1f} | TGT {data['target']:.1f}")

        # Clean up closed positions from our tracker
        for sym in to_remove:
            del active_positions[sym]
            
    except Exception as e:
        print(f"Monitor Error: {e}")

def run_scanner():
    global trades_taken
    
    # 1. First, check if we need to SELL anything
    monitor_exits()
    
    # 2. Sync Order Book
    sync_daily_orders()
    
    funds = get_funds()
    print(f"\n🔎 Scanning... (Trades: {trades_taken}/{MAX_TRADES} | Funds: ₹{funds:.2f})")
    
    if trades_taken >= MAX_TRADES: 
        print(f"🛑 Max trades ({MAX_TRADES}) reached. Only monitoring exits now.")
        time.sleep(10) # Just wait and monitor
        return

    BATCH_SIZE = 50 
    near_high_count = 0
    key_to_symbol_map = {v: k for k, v in INSTRUMENT_MAP.items()}

    for i in range(0, len(ALL_SYMBOLS), BATCH_SIZE):
        batch_symbols = ALL_SYMBOLS[i : i + BATCH_SIZE]
        keys = []
        for sym in batch_symbols:
            key = get_instrument_key(sym)
            if key: keys.append(key)

        if not keys: continue
        keys_str = ",".join(keys)

        quotes = None
        for attempt in range(3): 
            try:
                response = market_api.get_full_market_quote(keys_str, "2.0")
                quotes = response.data
                break 
            except: time.sleep(1) 
        
        if not quotes: continue

        for _, quote in quotes.items():
            true_instrument_key = quote.instrument_token 
            symbol = key_to_symbol_map.get(true_instrument_key, "Unknown")
            
            if symbol == "Unknown":
                try: symbol = _.split(":")[1] 
                except: pass
            if symbol == "Unknown" or symbol in active_positions: continue
            
            ltp = quote.last_price
            if ltp < 50 or quote.volume < 10000: continue
            if "BEES" in symbol or "IETF" in symbol or "GOLD" in symbol: continue 

            if quote.ohlc.high > 0 and ltp >= (quote.ohlc.high * 0.99):
                near_high_count += 1
                
                analysis = analyze_structure(true_instrument_key)
                
                if not analysis:
                    recent_high = quote.ohlc.high
                    atr = ltp * 0.01 
                else:
                    recent_high = analysis['recent_high']
                    atr = analysis['atr']
                
                strategy = None
                if ltp >= recent_high:
                    strategy = "Breakout Buy"
                    entry = ltp
                    sl = entry - (2 * atr)
                    target = entry + (4 * atr) 
                elif ltp < recent_high:
                    pullback_pct = ((recent_high - ltp) / recent_high) * 100
                    if 0.1 < pullback_pct < 4.0: 
                        strategy = f"Pullback Buy ({pullback_pct:.1f}%)"
                        entry = ltp
                        sl = entry - (2 * atr)
                        target = recent_high * 1.02 

                if strategy:
                    qty = math.floor((CAPITAL_PER_TRADE * LEVERAGE_X) / entry)
                    if qty < 1: continue

                    print(f"   ✅ SETUP: {symbol} | {strategy}")

                    if trades_taken < MAX_TRADES:
                        if place_order(symbol, qty, "BUY", price=entry):
                            trades_taken += 1
                            # SAVE DATA FOR EXIT MONITOR
                            active_positions[symbol] = {
                                'sl': sl, 
                                'target': target, 
                                'qty': qty, 
                                'key': true_instrument_key
                            }
                             
        time.sleep(0.5) 

    print(f"   📊 Scan finished. Found {near_high_count} stocks near Day High.")

if __name__ == "__main__":
    while True:
        run_scanner()
        print("⏳ Sleeping 2 minutes...") 
        time.sleep(120)