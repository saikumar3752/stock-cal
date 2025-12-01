import logging
logging.getLogger("urllib3").setLevel(logging.WARNING)

import requests
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import time
import random

# --- CONFIGURATION ---
SUPABASE_URL =os.environ.get("https://uvimynszhofmncujwrfb.supabase.co")
SUPABASE_KEY =os.environ.get("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV2aW15bnN6aG9mbW5jdWp3cmZiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM1MzAwNjgsImV4cCI6MjA3OTEwNjA2OH0.Qc62_n1a0fskv9ZBTx8KOLWw2czrEbb_4X9nSj_phd0")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ CRITICAL ERROR: Supabase Keys are missing from Environment Variables!")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
session = requests.Session()
session.headers.update(HEADERS)

def get_nse_cookies():
    try:
        session.get("https://www.nseindia.com", timeout=10)
    except:
        pass

def check_filings():
    print(f"⏳ Checking NSE Filings at {datetime.now().strftime('%H:%M:%S')}...")
    
    try:
        url = "https://www.nseindia.com/api/corporate-announcements?index=equities"
        response = session.get(url, timeout=10)
        data = response.json()
        df = pd.DataFrame(data)
        
        # Filter for Keywords
        keywords = ["Resignation", "Appointment", "Order", "Awarded", "FDA", "Acquisition"]
        # Creates a filter: does the description contain ANY of these words?
        pattern = '|'.join(keywords)
        relevant_news = df[df['desc'].str.contains(pattern, case=False, na=False)]
        
        if relevant_news.empty:
            print("   No major filings found.")
            return

        articles = []
        for index, row in relevant_news.head(3).iterrows():
            symbol = row['symbol']
            desc = row['desc']
            
            # Simple logic to decide color
            is_bad = "Resignation" in desc or "FDA" in desc
            color = "red" if is_bad else "green"
            type_label = "ALERT" if is_bad else "GOOD NEWS"
            
            slug = f"{symbol.lower()}-filing-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            html = f"""
            <p class="lead"><strong>{symbol}</strong> has submitted a critical filing to the NSE.</p>
            
            <div style="border-left: 4px solid {color}; padding-left: 15px; margin: 20px 0;">
                <h3 style="margin:0;">{type_label}</h3>
                <p style="font-size: 1.1em;">{desc}</p>
            </div>
            
            <p>This is an official corporate announcement. Markets may react to this information immediately.</p>
            <p><a href="{row.get('attchmntFile', '#')}" target="_blank">Download Official PDF</a></p>
            """
            
            articles.append({
                "symbol": symbol,
                "slug": slug,
                "title": f"📢 NSE Filing: {symbol} - {desc[:50]}...",
                "content": html,
                "published_at": datetime.now().isoformat()
            })
            
        if articles:
            supabase.table("news_articles").upsert(articles, on_conflict="slug").execute()
            print(f"✅ Published {len(articles)} Filing Alerts!")

    except Exception as e:
        print(f"Error: {e}")

# Run Loop
get_nse_cookies()
while True:
    check_filings()
    time.sleep(120) # Check every 2 minutes