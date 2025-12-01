import feedparser
import requests
from bs4 import BeautifulSoup
from supabase import create_client, Client
from datetime import datetime
import re
import time
import os

# --- CONFIGURATION (LOCAL TEST MODE) ---
# 1. Enter your URL (Keep this exactly as is)
SUPABASE_URL =os.environ.get("https://uvimynszhofmncujwrfb.supabase.co")

# 2. Enter your Key (PASTE YOUR LONG KEY INSIDE THE QUOTES BELOW)
SUPABASE_KEY = ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV2aW15bnN6aG9mbW5jdWp3cmZiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM1MzAwNjgsImV4cCI6MjA3OTEwNjA2OH0.Qc62_n1a0fskv9ZBTx8KOLWw2czrEbb_4X9nSj_phd0")
if not SUPABASE_URL or not SUPABASE_KEY:
    print("⚠️ Warning: Keys missing. Running in Offline Mode (No Database Upload)")
# 3. CONNECT (This is the line you were missing!)
try:
    if "PASTE_YOUR" in SUPABASE_KEY:
        print("❌ STOP: You forgot to paste your actual Supabase Key in the code!")
        exit()
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"❌ Connection Failed: {e}")
    exit()

# Browser Headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def get_google_news_url(query):
    return f"https://news.google.com/rss/search?q={query.replace(' ', '+')}+when:1d&hl=en-IN&gl=IN&ceid=IN:en"

SEARCH_TOPICS = [
    {"topic": "Broker Target", "query": "buy rating target price india stock"},
    {"topic": "RBI Action", "query": "RBI penalty bank NBFC india"},
    {"topic": "Management Change", "query": "resigns CEO CFO India stock"},
    {"topic": "Order Win", "query": "bagged order contract india stock"}
]

def get_broker_context():
    print("🧠 Loading Analyst Data for Context...")
    try:
        response = supabase.table("broker_targets").select("symbol, target_mean, upside_pct, recommendation").execute()
        context_map = {}
        for item in response.data:
            clean_name = item['symbol'].replace('.NS', '')
            context_map[clean_name] = item
        return context_map
    except:
        return {}

def clean_slug(text):
    text = text.lower().replace('%', '-percent-')
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    return re.sub(r'-+', '-', text.replace(' ', '-'))

def extract_full_text(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        paragraphs = soup.find_all('p')
        text_content = ""
        for p in paragraphs:
            if len(p.text) > 50:
                text_content += f"<p>{p.text}</p>"
        
        if len(text_content) < 200:
            return None
        return text_content
    except:
        return None

def fetch_rss_news():
    print(f"📰 Scanning News & Extracting Full Text...")
    broker_map = get_broker_context()
    articles_to_save = []
    
    for topic in SEARCH_TOPICS:
        print(f"   Searching: {topic['topic']}...")
        try:
            feed = feedparser.parse(get_google_news_url(topic['query']))
            
            for entry in feed.entries[:2]: 
                title = entry.title
                link = entry.link
                
                print(f"      Reading: {title[:30]}...")
                full_text_html = extract_full_text(link)
                
                if not full_text_html:
                    full_text_html = f"<p>{entry.summary}</p><p><em>(Full text could not be extracted. Read source link below.)</em></p>"

                # Context Injection
                context_html = ""
                matched_symbol = "MARKET-NEWS"
                
                for stock_name, data in broker_map.items():
                    if stock_name in title.upper():
                        matched_symbol = f"{stock_name}.NS"
                        upside_color = "green" if data['upside_pct'] > 0 else "red"
                        context_html = f"""
                        <div style="margin: 20px 0; padding: 20px; background-color: #f0fdf4; border-left: 5px solid {upside_color}; border-radius: 8px;">
                            <h3 style="margin:0; color: #166534;">StockCal Reality Check: {stock_name}</h3>
                            <ul>
                                <li><strong>Consensus:</strong> {data['recommendation']}</li>
                                <li><strong>Target Price:</strong> ₹{data['target_mean']}</li>
                                <li><strong>Upside:</strong> <span style="color:{upside_color}; font-weight:bold;">{data['upside_pct']}%</span></li>
                            </ul>
                        </div>
                        """
                        break 

                safe_slug = clean_slug(title)
                slug = f"news-{safe_slug[:50]}-{datetime.now().strftime('%Y%m%d%H%M')}"
                
                # Final HTML Structure
                final_html = f"""
                <p class="text-sm font-bold text-blue-600 uppercase">{topic['topic']}</p>
                <h1 class="text-2xl font-bold mb-4">{title}</h1>
                {context_html} 
                <div class="prose prose-lg text-slate-700">
                    {full_text_html}
                </div>
                <p style="margin-top: 30px; font-size: 0.8em; color: #666;">
                    Source: <a href="{link}" target="_blank" style="text-decoration:underline;">Read Original</a>
                </p>
                """

                articles_to_save.append({
                    "symbol": matched_symbol,
                    "slug": slug,
                    "title": title,
                    "content": final_html,
                    "published_at": datetime.now().isoformat()
                })
                
        except Exception as e:
            print(f"Skipping topic due to error: {e}")
            continue

    if articles_to_save:
        try:
            # THIS IS THE LINE THAT WAS FAILING
            supabase.table("news_articles").upsert(articles_to_save, on_conflict="slug").execute()
            print(f"✅ Success! Saved {len(articles_to_save)} articles to database.")
        except Exception as e:
            print(f"❌ Database Error: {e}")
    else:
        print("   No new news found.")

if __name__ == "__main__":
    fetch_rss_news()