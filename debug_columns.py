import nselib
from nselib import capital_market
import pandas as pd

print("Fetching bulk deal data to inspect columns...")

try:
    # Fetch data for the last 1 month to ensure we get rows
    data = capital_market.bulk_deal_data(period='1M')
    
    if not data.empty:
        print("\n✅ SUCCESS! Data found.")
        print("------------------------------------------------")
        print("COPY AND PASTE THE LIST BELOW INTO THE CHAT:")
        print(data.columns.tolist())
        print("------------------------------------------------")
        print("\nFirst row example:")
        print(data.iloc[0])
    else:
        print("❌ No data found. NSE might be blocking or empty.")

except Exception as e:
    print(f"❌ Error: {e}")