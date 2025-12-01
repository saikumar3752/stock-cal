import requests
import pandas as pd
import gzip
import io
import json

def update_instrument_keys():
    print("📥 Downloading Upstox Instrument Master List...")
    url = "https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz"
    
    response = requests.get(url)
    if response.status_code == 200:
        # Decompress GZIP
        with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as f:
            data = json.load(f)
            
        print(f"   Processing {len(data)} instruments...")
        
        # Create a dictionary: {'TATAMOTORS': 'NSE_EQ|INE155A01022', ...}
        # We only want EQUITIES (Stocks), not Options/Futures
        instrument_map = {}
        
        for item in data:
            if item['segment'] == 'NSE_EQ' and item['instrument_type'] == 'EQ':
                symbol = item['trading_symbol']
                key = item['instrument_key']
                instrument_map[symbol] = key
        
        # Save to a JSON file for our scanner to use
        with open("instrument_keys.json", "w") as f:
            json.dump(instrument_map, f)
            
        print(f"✅ Saved {len(instrument_map)} keys to 'instrument_keys.json'")
        
    else:
        print("❌ Failed to download instruments.")

if __name__ == "__main__":
    update_instrument_keys()