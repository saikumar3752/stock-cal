import logging
# Quiet logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

import nselib
from nselib import capital_market
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import os

# --- CONFIGURATION ---
# REPLACE THESE WITH YOUR ACTUAL SUPABASE KEYS from your project settings!
SUPABASE_URL =os.environ.get("https://uvimynszhofmncujwrfb.supabase.co")
SUPABASE_KEY =os.environ.get("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV2aW15bnN6aG9mbW5jdWp3cmZiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM1MzAwNjgsImV4cCI6MjA3OTEwNjA2OH0.Qc62_n1a0fskv9ZBTx8KOLWw2czrEbb_4X9nSj_phd0")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ CRITICAL ERROR: Supabase Keys are missing from Environment Variables!")
PARTNER_CODE = "Z773" 

def generate_whale_article(deal):
    # --- 1. EXACT COLUMN MAPPING (Based on your Debug Output) ---
    symbol = deal.get('Symbol', 'Unknown')
    client = deal.get('ClientName', 'Unknown')       # No space!
    security = deal.get('SecurityName', symbol)      # No space!
    action = deal.get('Buy/Sell', 'Unknown')
    
    # Handle Numbers (Remove commas if they are strings)
    raw_price = deal.get('TradePrice/Wght.Avg.Price', 0)
    raw_qty = deal.get('QuantityTraded', 0)
    
    price = float(str(raw_price).replace(',', '')) if raw_price else 0.0
    qty = int(str(raw_qty).replace(',', '')) if raw_qty else 0
    
    # Handle Date (Format: 17-OCT-2025)
    raw_date = deal.get('Date', datetime.now().strftime('%d-%b-%Y'))
    
    # --- 2. DATA CLEANING ---
    try:
        # Parse '17-OCT-2025' to '2025-10-17'
        date_obj = datetime.strptime(raw_date, '%d-%b-%Y')
        clean_date = date_obj.strftime('%Y-%m-%d')
    except:
        clean_date = datetime.now().strftime('%Y-%m-%d')

    # Calculate Value in Crores
    val_cr = round((price * qty) / 10000000, 2)

    color = "green" if action == "BUY" else "red"
    action_verb = "BOUGHT" if action == "BUY" else "SOLD"
    
    # Create unique URL
    safe_client = str(client).lower().replace(' ', '-').replace('.', '').replace(',', '')
    slug = f"{symbol.lower()}-bulk-deal-{safe_client}-{clean_date}"
    
    title = f"🚨 Whale Alert: {client} {action_verb} ₹{val_cr}Cr of {symbol}"
    
    html = f"""
    <p class="lead">Big movement detected in <strong>{security} ({symbol})</strong> on {raw_date}.</p>
    
    <h2>The Trade Details</h2>
    <table style="width:100%; border-collapse: collapse; margin: 20px 0;">
        <tr style="border-bottom: 1px solid #ddd;">
            <td style="padding: 8px;"><strong>Client (Whale):</strong></td>
            <td style="padding: 8px;">{client}</td>
        </tr>
        <tr style="border-bottom: 1px solid #ddd;">
            <td style="padding: 8px;"><strong>Action:</strong></td>
            <td style="padding: 8px; color: {color}; font-weight: bold;">{action}</td>
        </tr>
        <tr style="border-bottom: 1px solid #ddd;">
            <td style="padding: 8px;"><strong>Quantity:</strong></td>
            <td style="padding: 8px;">{qty:,} shares</td>
        </tr>
        <tr style="border-bottom: 1px solid #ddd;">
            <td style="padding: 8px;"><strong>Avg Price:</strong></td>
            <td style="padding: 8px;">₹{price}</td>
        </tr>
        <tr>
            <td style="padding: 8px;"><strong>Total Value:</strong></td>
            <td style="padding: 8px;">₹{val_cr} Crores</td>
        </tr>
    </table>
    
    <h3>What does this mean?</h3>
    <p><strong>{client}</strong> is a significant market participant. 
    This <strong>{action}</strong> order suggests high conviction at the ₹{price} level.</p>
    
    <div style="margin-top: 20px; padding: 15px; background-color: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px;">
        <strong>⚡ Action:</strong><br/>
        <a href="https://upstox.com/open-account/?f="Z773" style="color: #1d4ed8; font-weight: bold; text-decoration: none;">
            👉 Open Upstox Account to Trade {symbol}
        </a>
    </div>
    """
    
    return {
        "symbol": symbol,
        "slug": slug,
        "title": title,
        "content": html,
        "published_at": clean_date
    }

def fetch_and_process_deals():
    print("🚀 Fetching Bulk Deals...")
    try:
        # Fetch last 1 month
        data = capital_market.bulk_deal_data(period='1M') 
        print(f"📊 Found {len(data)} raw deals.")

        # Filter: Take top 10 most recent
        recent_deals = data.head(10)
        
        articles_to_save = []
        seen_slugs = set()

        for index, row in recent_deals.iterrows():
            try:
                article = generate_whale_article(row)
                
                # Deduplicate
                if article['slug'] in seen_slugs: continue
                seen_slugs.add(article['slug'])
                
                articles_to_save.append(article)

            except Exception as inner_e:
                print(f"Error processing row: {inner_e}")
                continue

        if articles_to_save:
            supabase.table("news_articles").upsert(articles_to_save, on_conflict="slug").execute()
            print(f"✅ Published {len(articles_to_save)} Whale Alert Articles!")
            print(f"🔗 Check: http://localhost:3000/news/{articles_to_save[0]['slug']}")
        else:
            print("No new unique articles to save.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_and_process_deals()