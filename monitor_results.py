import logging
# Quiet the logs
logging.getLogger("urllib3").setLevel(logging.WARNING)

import requests
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import time
import random

# --- CONFIGURATION ---
SUPABASE_URL = "https://uvimynszhofmncujwrfb.supabase.co"
SUPABASE_KEY = "PASTE_YOUR_ANON_KEY_HERE"  # <--- PASTE KEY HERE
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

PARTNER_CODE = "Z773" # Your Upstox Partner ID

# NSE headers to look like a real browser (Crucial!)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://www.nseindia.com/companies-listing/corporate-filings-announcements'
}

# We need a session to keep "Cookies" alive
session = requests.Session()
session.headers.update(HEADERS)

def get_nse_cookies():
    # Visit the homepage first to get valid cookies
    try:
        session.get("https://www.nseindia.com", timeout=10)
    except:
        pass

def fetch_latest_announcements():
    print(f"⏳ Checking NSE Feed at {datetime.now().strftime('%H:%M:%S')}...")
    
    try:
        # This is the secret JSON endpoint NSE uses
        url = "https://www.nseindia.com/api/corporate-announcements?index=equities"
        response = session.get(url, timeout=10)
        
        if response.status_code == 401:
            print("🔄 Refreshing Cookies...")
            get_nse_cookies()
            response = session.get(url, timeout=10)

        data = response.json()
        
        # Convert to DataFrame for easy filtering
        df = pd.DataFrame(data)
        
        # Filter for "Financial Results"
        # NSE subjects usually contain "Financial Results" or "Unaudited Financial Results"
        results = df[df['desc'].str.contains("Financial Result", case=False, na=False)]
        
        if results.empty:
            print("   No new results found.")
            return

        # Process the top 3 newest results
        latest_results = results.head(3)
        
        articles_to_save = []
        
        for index, row in latest_results.iterrows():
            symbol = row['symbol']
            desc = row['desc'] # The headline
            pdf_link = row['attchmntFile'] # The PDF file link
            date_time = row['an_dt'] # Time string
            
            # Generate a unique slug so we don't save duplicates
            slug = f"{symbol.lower()}-result-{date_time.replace(' ','-').replace(':','').replace(',','')}"
            
            # Create the Article
            title = f"⚡ BREAKING: {symbol} Announces Financial Results"
            
            html = f"""
            <div style="border-left: 4px solid #ef4444; padding-left: 15px; margin-bottom: 20px;">
                <p style="color: #ef4444; font-weight: bold; margin: 0;">JUST IN • {date_time}</p>
                <h2 style="margin-top: 5px;">{symbol} Quarterly Results Out Now</h2>
            </div>
            
            <p class="lead"><strong>{symbol}</strong> has just filed its financial results with the NSE.</p>
            
            <p><strong>Announcement Details:</strong><br/>
            {desc}</p>
            
            <div style="margin: 20px 0; padding: 20px; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;">
                <h3 style="margin-top:0;">📥 Official Documents</h3>
                <p>Read the full profit/loss statement here:</p>
                <a href="{pdf_link}" target="_blank" style="background-color: #0f172a; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; display: inline-block;">
                    Download NSE PDF &rarr;
                </a>
            </div>

            <h3>Trading Impact</h3>
            <p>Stocks typically see high volatility within the first 15 minutes of result announcements. 
            Watch the price action closely.</p>
            
            <a href="https://upstox.com/open-account/?f={PARTNER_CODE}" style="display: block; text-align: center; background-color: #2563eb; color: white; padding: 12px; border-radius: 6px; text-decoration: none; font-weight: bold; margin-top: 20px;">
                ⚡ Trade {symbol} Volatility on Upstox
            </a>
            """
            
            articles_to_save.append({
                "symbol": symbol,
                "slug": slug,
                "title": title,
                "content": html,
                "published_at": datetime.now().isoformat()
            })
            
        if articles_to_save:
            # Upsert to DB
            supabase.table("news_articles").upsert(articles_to_save, on_conflict="slug").execute()
            print(f"✅ Published {len(articles_to_save)} Result Flashes!")
            
    except Exception as e:
        print(f"Error checking NSE: {e}")

# --- MAIN LOOP ---
# Get cookies once at startup
get_nse_cookies()

# Loop forever (Run every 60 seconds)
while True:
    fetch_latest_announcements()
    
    # Sleep for a random time between 45 and 75 seconds (To look human)
    sleep_time = random.randint(45, 75)
    print(f"   Sleeping for {sleep_time} seconds...")
    time.sleep(sleep_time)