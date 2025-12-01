from upstox_client.api import login_api
import webbrowser

# --- CONFIGURATION ---
API_KEY = "7585e47d-2494-4dd2-97f9-d4bd003abaab"       # Paste your API Key here
API_SECRET = "nu5p9qyp39" # Paste your API Secret here
REDIRECT_URI = "https://www.stockcal.in/"

def get_access_token():
    # 1. Generate Login URL
    login_url = f"https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id={API_KEY}&redirect_uri={REDIRECT_URI}"
    
    print("1. Opening Login Page...")
    print(f"   If it doesn't open, click here: {login_url}")
    webbrowser.open(login_url)
    
    # 2. User Input
    print("\n2. After logging in, the browser will redirect to localhost.")
    print("   Look at the URL bar. It will look like: http://localhost:3000/?code=ELK5...")
    auth_code = input("   📋 PASTE THE 'CODE' PART HERE: ")
    
    # 3. Exchange Code for Token
    api_instance = login_api.LoginApi()
    try:
        api_response = api_instance.token(
            api_version="2.0",
            code=auth_code,
            client_id=API_KEY,
            client_secret=API_SECRET,
            redirect_uri=REDIRECT_URI,
            grant_type="authorization_code"
        )
        
        access_token = api_response.access_token
        print(f"\n✅ SUCCESS! Your Access Token is:\n{access_token}")
        
        # Save to file
        with open("access_token.txt", "w") as f:
            f.write(access_token)
        print("💾 Token saved to 'access_token.txt'")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    get_access_token()