from neo_api_client import NeoAPI

# --- PASTE YOUR DETAILS HERE ---
API_KEY = "BU5EO"        # Consumer Key
API_SECRET = "affe909b-8868-4462-a6ca-491335625515"  # Consumer Secret
MOBILE = "9000589762"   # 10 digits only (No +91)
PASSWORD = "Sai@sam123"      # Your Neo Login Password


print(f"Testing Login for User: {MOBILE}")
print(f"Using API Key: {API_KEY[:5]}*******")

try:
    # 1. Initialize
    client = NeoAPI(consumer_key=API_KEY, consumer_secret=API_SECRET, environment='PROD')
    
    # 2. Login
    print("Attempting Login...")
    client.login(mobilenumber=MOBILE, password=PASSWORD)
    
    # 3. 2FA
    print("Attempting 2FA...")
    client.session_2fa(MPIN)
    
    print("\n✅ SUCCESS! You are connected.")
    
except Exception as e:
    print(f"\n❌ FAILED: {e}")
    print("Suggestion: Check if 'Trade API' is enabled in your Kotak Settings.")