import requests
import pandas as pd
import io
from supabase import create_client, Client

# --- CONFIGURATION ---
# I have filled in your URL below:
SUPABASE_URL = "https://uvimynszhofmncujwrfb.supabase.co"

# PASTE YOUR COPIED 'ANON' KEY INSIDE THE QUOTES BELOW:
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV2aW15bnN6aG9mbW5jdWp3cmZiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM1MzAwNjgsImV4cCI6MjA3OTEwNjA2OH0.Qc62_n1a0fskv9ZBTx8KOLWw2czrEbb_4X9nSj_phd0"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_nse_stocks():
    print("Fetching Master List from NSE...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    # Official NSE CSV URL
    url = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        csv_data = response.content.decode('utf-8')
        df = pd.read_csv(io.StringIO(csv_data))
        return df
    else:
        print("Error fetching data from NSE")
        return None

def upload_to_supabase(df):
    print(f"Uploading {len(df)} stocks to Supabase...")
    
    stocks_data = []
    for index, row in df.iterrows():
        symbol = f"{row['SYMBOL']}.NS"
        stocks_data.append({
            "symbol": symbol,
            "company_name": row['NAME OF COMPANY'],
            "sector": "N/A", 
            "is_active": True
        })
    
    try:
        # Upsert means: "Insert if new, Update if exists"
        data = supabase.table("stocks").upsert(stocks_data).execute()
        print("Success! Master List Updated.")
    except Exception as e:
        print(f"Error: {e}")

# --- EXECUTE ---
df = fetch_nse_stocks()
if df is not None:
    upload_to_supabase(df)